# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/msg_form.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MessageForm(object):
    """Интерфейс сообщения"""
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(200, 100)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.error_msg = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(10)
        self.error_msg.setFont(font)
        self.error_msg.setText("")
        self.error_msg.setAlignment(QtCore.Qt.AlignCenter)
        self.error_msg.setObjectName("error_msg")
        self.verticalLayout.addWidget(self.error_msg)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
