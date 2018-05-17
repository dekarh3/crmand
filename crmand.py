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
        self.pbPeopleFilter.clicked.connect(self.click_pbPeopleFilter)
        self.pbRedo.clicked.connect(self.click_pbRedo)
        self.twGroups.clicked.connect(self.click_twGroups)
        self.twFIO.clicked.connect(self.click_twFIO)
        self.twCalls.clicked.connect(self.click_twCalls)
        self.cbStage.activated[str].connect(self.click_cbStage)
        self.pbRedo.clicked.connect(self.click_pbRedo)
#        self.twCalls.customContextMenuRequested.connect(self.click_label_3)

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



