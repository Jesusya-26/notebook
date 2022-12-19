import datetime
import sys
import traceback
import json
import openpyxl

from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QCheckBox, QStyledItemDelegate
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QDoubleSpinBox, QDateEdit
from PyQt5.QtCore import Qt
from ui.main_window import Ui_MainWindow
from ui.item_action import Ui_ItemAction
from ui.filter_form import Ui_FilterForm
from ui.msg_form import Ui_MessageForm
from ui.price_error import Ui_PriceErrorForm
from data import db_session
from data.items import Item
from data.catergories import Category

with open('settings.json') as file:
    settings = json.load(file)  # выгружаем настройки из json-файла


class AlignDelegate(QStyledItemDelegate):
    """Вспомогательный класс для выравнивания стоблцов таблицы по центру"""

    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter


class Notebook(QMainWindow, Ui_MainWindow):
    """Класс главного окна приложения (обработка действий пользователя)"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init_buttons()
        self.shopping_list.horizontalHeader().sectionClicked.connect(
            self.toggle)  # смена состояния всех записей при нажатии на заголовки таблицы
        delegate = AlignDelegate(self.shopping_list)
        self.shopping_list.setItemDelegateForColumn(0, delegate)
        self.shopping_list.setItemDelegateForColumn(2, delegate)
        self.init_table()

    def init_table(self, key=None, reverse=False, mode=None) -> None:
        """Инициализация таблицы"""
        for i in range(self.shopping_list.rowCount()):
            self.shopping_list.removeRow(0)  # очищаем таблицу
        items = db_sess.query(Item)
        if mode == 'sort':  # если указан модификатор "сортировка"
            items = sorted(items, key=key, reverse=reverse)
        elif mode == 'filter':  # если указан модификатор "фильтр"
            items = list(filter(key, items))
        for item in items:
            self.add_item_to_table(item)  # добавляем каждый элемент

    def init_buttons(self) -> None:
        """Инициализация кнопок (привязываем к каждой кнопке функцию)"""
        self.search.clicked.connect(self.to_search)
        self.add_item.clicked.connect(self.to_add_item)
        self.delete_item.clicked.connect(self.to_delete_item)
        self.edit_item.clicked.connect(self.to_edit_item)
        self.filter.clicked.connect(self.to_filter)
        self.get_file.clicked.connect(self.to_get_file)

    def to_search(self) -> None:
        """Поиск по названию"""
        self.init_table(key=lambda x: self.search_bar.text().lower() in str(x.name).lower(), mode='filter')

    def to_add_item(self) -> None:
        """Добавление записи"""
        self.new_window = ItemAction(self, 'add')  # открытие интерфейса для добавления записи
        self.new_window.show()

    def to_delete_item(self) -> None:
        """Удаление выбранных записей"""
        item_list = self.get_checked_items()
        if len(item_list) == 0:  # если записи не выбраны, то выкидываем ошибку
            self.error_window = MessageForm(self, 'Выберите хотя бы один элемент!')
            self.error_window.show()
            return
        for item in item_list:
            db_sess.delete(item)  # удаляем запись из базы данных
            db_sess.commit()
        self.init_table()

    def to_edit_item(self) -> None:
        """Изменение выбранных записей"""
        item_list = self.get_checked_items()
        if len(item_list) > 1 or len(item_list) == 0:  # если запись не выбрана или выбрано больше одной записи
            self.error_window = MessageForm(self, 'Выберите один элемент!')  # выкидываем ошибку
            self.error_window.show()
        elif len(item_list) == 1:
            self.new_window = ItemAction(self, 'edit', item_list[0])  # открытие интерфейса для изменения записи
            self.new_window.show()

    def to_filter(self) -> None:
        """Открытие окна с выбором фильтров"""
        self.new_window = FilterForm(self)
        self.new_window.show()

    def to_get_file(self) -> None:
        """Формирование excel файла"""
        wb = openpyxl.Workbook()  # создание книги
        list = wb.active  # выбор листа
        list.title = 'Отчёт'
        items, labels = [], []
        for i in db_sess.query(Item):
            items.append(tuple([i.name, i.category.name, i.price, i.purchase_date, i.about]))
        for i in range(1, self.shopping_list.columnCount() - 1):
            labels.append(self.shopping_list.horizontalHeaderItem(i).text())
        labels.append('Описание')
        list.append(tuple(labels))
        for item in items:
            list.append(item)  # добавляем на лист все записи
        list["G1"] = 'ПРОГРАММА ДЛЯ КОНТРОЛЯ ДЕНЕЖНЫХ СРЕДСТВ'
        list["G2"] = f'ОТЧЁТ ОТ {datetime.datetime.today().strftime("%H:%M %d.%m.%Y")}'
        wb.save(f'reports/report_{datetime.datetime.today().strftime("%H_%M_%d_%m_%Y")}.xlsx')  # сохраняем файл
        self.message = MessageForm(self, 'Файл успешно сформирован! (см. папку reports)', label='Сообщение')
        self.message.show()  # выкидываем сообщение, что всё сформировано успешно

    def get_checked_items(self) -> list:
        """Получение выбранных записей"""
        items = db_sess.query(Item)
        checked_list = []
        for i in range(self.shopping_list.rowCount()):
            box = self.shopping_list.cellWidget(i, 5).layout().itemAt(0).widget()
            if box.isChecked():  # проверка состояния чекбокса
                item = items.filter(Item.id == int(self.shopping_list.item(i, 0).text())).first()  # ищем запись по id
                checked_list.append(item)  # добавляем запись в список
        return checked_list

    def add_item_to_table(self, item) -> None:
        """Добавление записи в таблицу"""
        self.shopping_list.insertRow(0)  # всегда добавляем запись в начало
        self.shopping_list.setItem(0, 0, QTableWidgetItem(str(item.id)))  # id
        self.shopping_list.item(0, 0).setFlags(Qt.ItemIsEnabled)  # блокируем
        self.shopping_list.setItem(0, 1, QTableWidgetItem(item.name))  # название покупки
        self.shopping_list.item(0, 1).setFlags(Qt.ItemIsEnabled)
        self.shopping_list.setItem(0, 2, QTableWidgetItem(item.category.name))  # категория покупки
        self.shopping_list.item(0, 2).setFlags(Qt.ItemIsEnabled)
        cell_widget, price = QWidget(), QDoubleSpinBox()
        price.setMinimum(0)
        price.setMaximum(10 ** 10)
        price.setValue(item.price)
        lay_out = QHBoxLayout(cell_widget)
        lay_out.addWidget(price)
        lay_out.setAlignment(Qt.AlignCenter)
        lay_out.setContentsMargins(0, 0, 0, 0)
        cell_widget.setLayout(lay_out)
        self.shopping_list.setCellWidget(0, 3, cell_widget)  # цена
        self.shopping_list.cellWidget(0, 3).setEnabled(False)  # блокируем
        cell_widget, date = QWidget(), QDateEdit()
        date.setMinimumDate(datetime.date(2022, 1, 1))
        date.setMaximumDate(datetime.date.today())
        date.setDate(item.purchase_date)
        lay_out = QHBoxLayout(cell_widget)
        lay_out.addWidget(date)
        lay_out.setAlignment(Qt.AlignCenter)
        lay_out.setContentsMargins(0, 0, 0, 0)
        cell_widget.setLayout(lay_out)
        self.shopping_list.setCellWidget(0, 4, cell_widget)  # дата
        self.shopping_list.cellWidget(0, 4).setEnabled(False)
        cell_widget, ch_box = QWidget(), QCheckBox()
        lay_out = QHBoxLayout(cell_widget)
        lay_out.addWidget(ch_box)
        lay_out.setAlignment(Qt.AlignCenter)
        lay_out.setContentsMargins(0, 0, 0, 0)
        cell_widget.setLayout(lay_out)
        self.shopping_list.setCellWidget(0, 5, cell_widget)  # чекбокс

    def toggle(self) -> None:
        """Меняем состояние записей"""
        if self.shopping_list.cellWidget(0, 5).layout().itemAt(0).widget().checkState():  # если первая выбрана
            for i in range(self.shopping_list.rowCount()):  # выбираем ни одну
                self.shopping_list.cellWidget(i, 5).layout().itemAt(0).widget().setCheckState(False)
        else:
            for i in range(self.shopping_list.rowCount()):  # выбираем все
                self.shopping_list.cellWidget(i, 5).layout().itemAt(0).widget().setCheckState(True)


class ItemAction(QWidget, Ui_ItemAction):
    """Класс для обработки создания и редактирования записей"""
    def __init__(self, main_window, mode, item=None):
        super().__init__()
        self.setupUi(self)
        self.main_window, self.item = main_window, item  # главное окно и запись
        self.buttonBox.buttons()[1].clicked.connect(self.close)
        if mode == 'add':
            self.setWindowTitle('Добавление записи')
            self.title.setText('Добавление записи')
            self.buttonBox.buttons()[0].clicked.connect(self.add_item)
        elif mode == 'edit':
            self.setWindowTitle('Редактирование записи')
            self.title.setText('Редактирование записи')
            self.name_line.setText(self.item.name)  # при редактировании устанавливаем в поля значения переданной записи
            self.category_line.setText(self.item.category.name)
            self.about_line.setText(self.item.about)
            self.price_line.setValue(self.item.price)
            self.date_line.setDate(self.item.purchase_date)
            self.buttonBox.buttons()[0].clicked.connect(self.edit_item)

    def add_item(self) -> None:
        """Добавление записи"""
        if self.check_item():  # если данные некорректны, то выходим
            return
        category = None
        for i in db_sess.query(Category):  # проверка, существует ли уже данная категория
            if i.name.lower() == self.category_line.text().strip().lower():
                category = i
        if not category:  # если нет, создаем новую
            category = Category(name=self.category_line.text().strip())
            db_sess.add(category)  # добавляем в базу данных
            db_sess.commit()
        item = Item(
            name=self.name_line.text().strip(),
            price=self.price_line.value(),
            about=self.about_line.toPlainText().strip(),
            purchase_date=self.date_line.date().toPyDate()
        )  # создание новой записи
        category.items.append(item)  # добавляем в категорию запись
        db_sess.merge(category)  # сохраняе изменения категории
        db_sess.commit()
        self.main_window.init_table()
        self.close()

    def edit_item(self) -> None:
        """Изменение записи"""
        if self.check_item():
            return
        category = None
        for i in db_sess.query(Category):
            if i.name.lower() == self.category_line.text().strip().lower():
                category = i
        if category and category.name.lower() != self.item.category.name.lower():  # если категория изменилась на сущ.
            prev_category = self.item.category
            prev_category.items.remove(self.item)  # удаляем запись из прошлой категории
            db_sess.merge(prev_category)
            category.items.append(self.item)  # и добавляем в новую
            db_sess.merge(category)
            db_sess.commit()
        elif not category:  # если новой категории не существует, то создаём её
            category = Category(name=self.category_line.text().strip())
            db_sess.add(category)
            db_sess.commit()
            prev_category = self.item.category
            self.item.category_id = category.id
            db_sess.merge(prev_category)
            db_sess.merge(category)
            db_sess.commit()
        self.item.name = self.name_line.text().strip()  # меняем все данные записи
        self.item.price = self.price_line.value()
        self.item.about = self.about_line.toPlainText().strip()
        self.item.purchase_date = self.date_line.date().toPyDate()
        db_sess.commit()
        self.main_window.init_table()
        self.close()

    def check_item(self) -> bool:
        """Проверка корректности данных"""
        if len(self.name_line.text().strip()) < 3:  # если название короче 3 символов, выкидываем ошибку
            self.error_window = MessageForm(self.main_window, 'Слишком короткое название покупки!')
            self.error_window.show()
            return True
        if len(self.category_line.text().strip()) < 3:  # если категория короче 3 символов, выкидываем ошибку
            self.error_window = MessageForm(self.main_window, 'Слишком короткое название категории!')
            self.error_window.show()
            return True
        if self.price_line.value() > 10 ** 8 and settings['ABRAMOVICH'] == -1:  # если цена слишком высокая, спрашиваем
            self.error_window = PriceErrorForm(self.main_window, self)  # является ли пользователь Абрамовичем
            self.error_window.show()
            return True
        if self.price_line.value() > 10 ** 8 and settings['ABRAMOVICH'] == 0:  # если не является, то выкидываем ошибку
            self.error_window = MessageForm(self.main_window, 'Слишком дорогая покупка! '
                                                              'Смиритесь, у вас нет столько денег...')
            self.error_window.show()
            return True
        return False


class FilterForm(QWidget, Ui_FilterForm):
    """Класс для обработки установленных фильтров"""
    def __init__(self, main_window):
        super().__init__()
        self.setupUi(self)
        self.main_window = main_window
        for category in db_sess.query(Category):  # добавляем все категории
            self.category_box.addItem(category.name)
        self.buttonBox.buttons()[0].clicked.connect(self.add_filter)
        self.buttonBox.buttons()[1].clicked.connect(self.close)

    def add_filter(self) -> None:
        """Добавляем выбранный фильтр"""
        if self.for_category.isChecked():  # если выбрано "по категории"
            category = self.category_box.currentText()
            self.main_window.init_table(key=lambda x: x.category.name == category, mode='filter')
        elif self.for_price.isChecked():  # если выбрано "по цене"
            d = {'по возрастанию': True, 'по убыванию': False}
            self.main_window.init_table(key=lambda x: x.price, reverse=d[self.price_box.currentText()], mode='sort')
        elif self.for_date.isChecked():  # если выбрано по дате
            d = {'сначала старые': True, 'сначала новые': False}
            self.main_window.init_table(key=lambda x: x.purchase_date, reverse=d[self.date_box.currentText()],
                                        mode='sort')
        elif self.for_period.isChecked():  # если выбрано по периоду
            start_date, end_date = self.start_date.date().toPyDate(), self.end_date.date().toPyDate()
            dt = end_date - start_date
            self.main_window.init_table(key=lambda x: x.purchase_date - start_date <= dt, mode='filter')
        self.close()


class MessageForm(QWidget, Ui_MessageForm):
    """Класс для отображения сообщений в окне"""
    def __init__(self, main_window, text, label='Ошибка'):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(label)
        self.error_msg.setText(text)  # устанавливаем текст сообщения


class PriceErrorForm(QWidget, Ui_PriceErrorForm):
    """Класс для обработки вывода вопроса про Абрамовича"""
    def __init__(self, main_window, widget):
        super().__init__()
        self.setupUi(self)
        self.main_window = main_window
        self.main_wigdet = widget
        self.buttonBox.buttons()[0].clicked.connect(self.yes)
        self.buttonBox.buttons()[1].clicked.connect(self.no)

    def yes(self) -> None:
        """Если пользователь является Абрамовичем"""
        global settings
        settings['ABRAMOVICH'] = 1  # меняем настройки
        with open('settings.json', mode='w') as file:
            json.dump(settings, file)  # и загружаем в json-файл
        self.main_wigdet.add_item()  # добавляем запись
        self.close()

    def no(self) -> None:
        """Если пользователь не является Абрамовичем"""
        global settings
        settings['ABRAMOVICH'] = 0
        with open('settings.json', mode='w') as file:
            json.dump(settings, file)
        self.error_window = MessageForm(self.main_window, 'Слишком дорогая покупка! '
                                                          'Смиритесь, у вас нет столько денег...')
        self.error_window.show()  # выкидываем ошибку
        self.close()


def excepthook(exc_type, exc_value, exc_tb):
    """Обработчик ошибок (т.к. PyQT не выбрасывает ошибки)"""
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    QApplication.quit()
    # or QtWidgets.QApplication.exit(0)


if __name__ == '__main__':
    sys.excepthook = excepthook  # устанавливаем хук на ошибки
    db_session.global_init('db/notebook.db')  # инициализируем базу данных
    db_sess = db_session.create_session()  # создаем сессию
    app = QApplication(sys.argv)  # создаем приложение
    ex = Notebook()
    ex.show()
    sys.exit(app.exec())
