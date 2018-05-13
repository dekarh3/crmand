# -*- coding: utf-8 -*-
__author__ = 'Denis'

import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem, QComboBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDate

from crmand_slots import MainWindowSlots



class MainWindow(MainWindowSlots):

    # При инициализации класса нам необходимо выполнить некоторые операции
    def __init__(self, form):
        # Сконфигурировать интерфейс методом из базового класса Ui_Form
        self.setupUi(form)
        # Подключить созданные нами слоты к виджетам
        self.connect_slots()

    # Подключаем слоты к виджетам (для каждого действия, которое надо обработать - свой слот)
    def connect_slots(self):
        self.tableWidget.clicked.connect(self.click_tableWidget)
        self.cbLinkFrom.activated[str].connect(self.click_cbLinkFrom)
        self.cbLinkTo.activated[str].connect(self.click_cbLinkTo)
        self.cbStatus.activated[str].connect(self.click_cbStatus)
        self.cbPeopleFrom.activated[str].connect(self.click_cbPeopleFrom)
        self.cbPeopleTo.activated[str].connect(self.click_cbPeopleTo)
        self.cbLink.activated[str].connect(self.click_cbLink)
        self.cbPeople.activated[str].connect(self.click_cbPeople)
        self.pbPeopleFilter.clicked.connect(self.click_pbPeopleFilter)
        self.pbReLogin.clicked.connect(self.click_pbReLogin)
        self.pbRefresh.clicked.connect(self.click_pbRefresh)
#        self.pbRefresh.clicked.connect(self.refreshing)
        self.pbScan.clicked.connect(self.click_pbScan)
        self.pbToAnketa.clicked.connect(self.click_pbToAnketa)
        self.pbToMessage.clicked.connect(self.click_pbToMessage)
        self.pbGetHTML.clicked.connect(self.click_pbGetHTML)
        self.cbHTML.activated[str].connect(self.click_cbHTML)
        self.myTimer.timeout.connect(self.refreshing)
        self.tableFotos.clicked.connect(self.click_tableFotos)
        self.tableFotos.customContextMenuRequested.connect(self.click_label_3)
#        self.label_3.mouseDoubleClickEvent.connect(self.click_label_3)
        return None

if __name__ == '__main__':
    # Создаём экземпляр приложения
    app = QApplication(sys.argv)
    # Создаём базовое окно, в котором будет отображаться наш UI
    window = QWidget()
    # Создаём экземпляр нашего UI
    ui = MainWindow(window)
    # Отображаем окно
    window.show()
    # Обрабатываем нажатие на кнопку окна "Закрыть"
    sys.exit(app.exec_())




