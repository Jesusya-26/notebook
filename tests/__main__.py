import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from main import Notebook, Item, db_sess

class TestNotebook(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self):
        self.notebook = Notebook()

    def test_init_table_empty(self):
        """Тест инициализации таблицы с пустой базой данных"""
        db_sess.query = MagicMock(return_value=[])
        self.notebook.init_table()
        self.assertEqual(self.notebook.shopping_list.rowCount(), 0, "Таблица должна быть пустой.")

    def test_add_item_to_table(self):
        """Тест добавления элемента в таблицу"""
        item = Item(id=1, name="Test Item", category=MagicMock(name="Category"), price=10.0, purchase_date="2023-12-11")
        self.notebook.add_item_to_table(item)
        self.assertEqual(self.notebook.shopping_list.rowCount(), 1, "В таблице должен быть один элемент.")
        self.assertEqual(self.notebook.shopping_list.item(0, 1).text(), "Test Item")

    def test_get_checked_items(self):
        """Тест получения выбранных элементов"""
        db_sess.query = MagicMock(return_value=[Item(id=1), Item(id=2)])
        self.notebook.init_table()
        # Выбираем первый элемент
        checkbox = self.notebook.shopping_list.cellWidget(0, 5).layout().itemAt(0).widget()
        checkbox.setChecked(True)
        checked_items = self.notebook.get_checked_items()
        self.assertEqual(len(checked_items), 1)
        self.assertEqual(checked_items[0].id, 1)

    @patch('openpyxl.Workbook')
    def test_to_get_file(self, mock_workbook):
        """Тест генерации Excel файла"""
        mock_save = MagicMock()
        mock_workbook.return_value.save = mock_save
        self.notebook.to_get_file()
        mock_save.assert_called_once()
        self.assertTrue(mock_save.call_args[0][0].startswith('reports/report_'), "Имя файла должно быть корректным.")

    def test_toggle(self):
        """Тест смены состояния чекбоксов"""
        db_sess.query = MagicMock(return_value=[Item(id=1), Item(id=2)])
        self.notebook.init_table()
        # Изначально все чекбоксы сняты
        self.notebook.toggle()
        for i in range(self.notebook.shopping_list.rowCount()):
            checkbox = self.notebook.shopping_list.cellWidget(i, 5).layout().itemAt(0).widget()
            self.assertTrue(checkbox.isChecked(), "Все чекбоксы должны быть установлены.")

        # Снова вызываем toggle, все чекбоксы должны быть сняты
        self.notebook.toggle()
        for i in range(self.notebook.shopping_list.rowCount()):
            checkbox = self.notebook.shopping_list.cellWidget(i, 5).layout().itemAt(0).widget()
            self.assertFalse(checkbox.isChecked(), "Все чекбоксы должны быть сняты.")

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

if __name__ == "__main__":
    unittest.main()
