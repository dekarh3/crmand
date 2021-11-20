# -*- coding: utf-8 -*-
__author__ = 'Denis'

import sys
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem, QComboBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from crm_slots import MainWindowSlots

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
        self.clbRedo.clicked.connect(self.click_clbRedo)
        self.clbSave.clicked.connect(self.click_clbSave)
        self.clbAvito.clicked.connect(self.click_clbAvito)
        self.clbBack.clicked.connect(self.clickBack)
        self.clbNewAdd.clicked.connect(self.click_clbNewAdd)
        self.clbTrash.clicked.connect(self.click_clbTrash)
        self.clbCheckPhone.clicked.connect(self.click_clbCheckPhone)
        self.twGroups.clicked.connect(self.click_twGroups)
        self.twFIO.clicked.connect(self.click_twFIO)
        self.twCalls.clicked.connect(self.click_twCalls)
#        self.cbStage.activated[str].connect(self.click_cbStage)
        self.clbGoURL1.clicked.connect(self.click_clbGoURL1)
        self.clbGoUser.clicked.connect(self.click_clbGoUser)
        self.clbAddDate.clicked.connect(self.click_clbAddDate)
        self.clbStageRefresh.clicked.connect(self.click_clbStageRefresh)
        self.leIOF.textChanged[str].connect(self.leIOF_changed)
        self.preview.loadFinished.connect(self.preview_loaded)
        self.preview.loadProgress.connect(self.preview_loading)
        self.clbPreviewLoading.clicked.connect(self.preview_loaded)
#        self.clbPreviewLoading.clicked.connect(self.click_clbPreviewLoading)
#        self.deCalendar.dateChanged.connect(self.change_deCalendar)
#        self.twCalls.customContextMenuRequested.connect(self.click_label_3)
        return None


class MyQWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.previewPlusKeys = 0
        self.previewMinusKeys = 0

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_Plus:
            if int(datetime.now().timestamp()) == self.previewPlusKeys:
                ui.preview.setZoomFactor(ui.preview.zoomFactor() + 0.1)
                self.previewPlusKeys = int(datetime.now().timestamp()) - 1
            else:
                self.previewPlusKeys = -int(datetime.now().timestamp())
        elif e.key() == Qt.Key_Minus:
            if int(datetime.now().timestamp()) == self.previewMinusKeys:
                ui.preview.setZoomFactor(ui.preview.zoomFactor() - 0.1)
                self.previewMinusKeys = int(datetime.now().timestamp()) - 1
            else:
                self.previewMinusKeys = -int(datetime.now().timestamp())
        elif e.key() == Qt.Key_Control:
            if int(datetime.now().timestamp()) == -self.previewPlusKeys:
                ui.preview.setZoomFactor(ui.preview.zoomFactor() + 0.1)
                self.previewPlusKeys = int(datetime.now().timestamp()) - 1
            else:
                self.previewPlusKeys = int(datetime.now().timestamp())
            if int(datetime.now().timestamp()) == -self.previewMinusKeys:
                ui.preview.setZoomFactor(ui.preview.zoomFactor() - 0.1)
                self.previewMinusKeys = int(datetime.now().timestamp()) - 1
            else:
                self.previewMinusKeys = int(datetime.now().timestamp())


if __name__ == '__main__':
    # Создаём экземпляр приложения
    app = QApplication(sys.argv)
    # Создаём базовое окно, в котором будет отображаться наш UI
    window = MyQWidget()
    window.setWindowIcon(QIcon('avito1.png'))
    # Создаём экземпляр нашего UI
    ui = MainWindow(window)
    # Отображаем окно
    window.show()
    # Обрабатываем нажатие на кнопку окна "Закрыть"
    sys.exit(app.exec_())




