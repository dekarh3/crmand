# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crmand_win.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(504, 868)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.frame = QtWidgets.QFrame(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.leFIO = QtWidgets.QLineEdit(self.frame)
        self.leFIO.setMinimumSize(QtCore.QSize(0, 0))
        self.leFIO.setStatusTip("")
        self.leFIO.setAccessibleDescription("")
        self.leFIO.setObjectName("leFIO")
        self.horizontalLayout_3.addWidget(self.leFIO)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.leNote = QtWidgets.QLineEdit(self.frame)
        self.leNote.setToolTip("")
        self.leNote.setAccessibleName("")
        self.leNote.setAccessibleDescription("")
        self.leNote.setObjectName("leNote")
        self.horizontalLayout_3.addWidget(self.leNote)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.lePhone = QtWidgets.QLineEdit(self.frame)
        self.lePhone.setWhatsThis("")
        self.lePhone.setAccessibleDescription("")
        self.lePhone.setObjectName("lePhone")
        self.horizontalLayout_3.addWidget(self.lePhone)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.cbStageFrom = QtWidgets.QComboBox(self.frame)
        self.cbStageFrom.setMinimumSize(QtCore.QSize(130, 0))
        self.cbStageFrom.setObjectName("cbStageFrom")
        self.horizontalLayout_2.addWidget(self.cbStageFrom)
        self.label_2 = QtWidgets.QLabel(self.frame)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.pbPeopleFilter = QtWidgets.QPushButton(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pbPeopleFilter.sizePolicy().hasHeightForWidth())
        self.pbPeopleFilter.setSizePolicy(sizePolicy)
        self.pbPeopleFilter.setMinimumSize(QtCore.QSize(110, 0))
        self.pbPeopleFilter.setObjectName("pbPeopleFilter")
        self.horizontalLayout_2.addWidget(self.pbPeopleFilter)
        self.label = QtWidgets.QLabel(self.frame)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.cbStageTo = QtWidgets.QComboBox(self.frame)
        self.cbStageTo.setMinimumSize(QtCore.QSize(130, 0))
        self.cbStageTo.setObjectName("cbStageTo")
        self.horizontalLayout_2.addWidget(self.cbStageTo)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_4.addWidget(self.frame)
        self.frame_3 = QtWidgets.QFrame(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy)
        self.frame_3.setMinimumSize(QtCore.QSize(0, 200))
        self.frame_3.setMaximumSize(QtCore.QSize(16777215, 380))
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.frame_3)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.twGroups = QtWidgets.QTableWidget(self.frame_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.twGroups.sizePolicy().hasHeightForWidth())
        self.twGroups.setSizePolicy(sizePolicy)
        self.twGroups.setMinimumSize(QtCore.QSize(0, 200))
        self.twGroups.setMaximumSize(QtCore.QSize(170, 16777215))
        self.twGroups.setObjectName("twGroups")
        self.twGroups.setColumnCount(0)
        self.twGroups.setRowCount(0)
        self.horizontalLayout_6.addWidget(self.twGroups)
        self.twFIO = QtWidgets.QTableWidget(self.frame_3)
        self.twFIO.setObjectName("twFIO")
        self.twFIO.setColumnCount(0)
        self.twFIO.setRowCount(0)
        self.horizontalLayout_6.addWidget(self.twFIO)
        self.verticalLayout_4.addWidget(self.frame_3)
        self.frame_2 = QtWidgets.QFrame(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.pbRedo = QtWidgets.QPushButton(self.frame_2)
        self.pbRedo.setMinimumSize(QtCore.QSize(100, 0))
        self.pbRedo.setObjectName("pbRedo")
        self.horizontalLayout_4.addWidget(self.pbRedo)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem2)
        self.cbStage = QtWidgets.QComboBox(self.frame_2)
        self.cbStage.setMinimumSize(QtCore.QSize(130, 0))
        self.cbStage.setObjectName("cbStage")
        self.horizontalLayout_4.addWidget(self.cbStage)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem3)
        self.pbSave = QtWidgets.QPushButton(self.frame_2)
        self.pbSave.setMinimumSize(QtCore.QSize(100, 0))
        self.pbSave.setObjectName("pbSave")
        self.horizontalLayout_4.addWidget(self.pbSave)
        self.verticalLayout_4.addWidget(self.frame_2)
        self.twCalls = QtWidgets.QTableWidget(Form)
        self.twCalls.setMaximumSize(QtCore.QSize(16777215, 45))
        self.twCalls.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.twCalls.setObjectName("twCalls")
        self.twCalls.setColumnCount(0)
        self.twCalls.setRowCount(0)
        self.twCalls.horizontalHeader().setVisible(False)
        self.twCalls.verticalHeader().setVisible(False)
        self.verticalLayout_4.addWidget(self.twCalls)
        self.frame_5 = QtWidgets.QFrame(Form)
        self.frame_5.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_5.setObjectName("frame_5")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.frame_5)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.leIOF = QtWidgets.QLineEdit(self.frame_5)
        self.leIOF.setObjectName("leIOF")
        self.horizontalLayout_5.addWidget(self.leIOF)
        self.leUrls = QtWidgets.QLineEdit(self.frame_5)
        self.leUrls.setObjectName("leUrls")
        self.horizontalLayout_5.addWidget(self.leUrls)
        self.verticalLayout_4.addWidget(self.frame_5)
        self.frame_6 = QtWidgets.QFrame(Form)
        self.frame_6.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_6.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_6.setObjectName("frame_6")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.frame_6)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.lePhones = QtWidgets.QLineEdit(self.frame_6)
        self.lePhones.setObjectName("lePhones")
        self.horizontalLayout_7.addWidget(self.lePhones)
        self.chbHasPhone = QtWidgets.QCheckBox(self.frame_6)
        self.chbHasPhone.setChecked(True)
        self.chbHasPhone.setTristate(False)
        self.chbHasPhone.setObjectName("chbHasPhone")
        self.horizontalLayout_7.addWidget(self.chbHasPhone)
        self.verticalLayout_4.addWidget(self.frame_6)
        self.frame_4 = QtWidgets.QFrame(Form)
        self.frame_4.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_4.setObjectName("frame_4")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame_4)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.leTown = QtWidgets.QLineEdit(self.frame_4)
        self.leTown.setMaximumSize(QtCore.QSize(130, 16777215))
        self.leTown.setObjectName("leTown")
        self.horizontalLayout.addWidget(self.leTown)
        self.leEmail = QtWidgets.QLineEdit(self.frame_4)
        self.leEmail.setObjectName("leEmail")
        self.horizontalLayout.addWidget(self.leEmail)
        self.verticalLayout_4.addWidget(self.frame_4)
        self.teNote = QtWidgets.QTextEdit(Form)
        self.teNote.setObjectName("teNote")
        self.verticalLayout_4.addWidget(self.teNote)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_2.setText(_translate("Form", "<-ОТ"))
        self.pbPeopleFilter.setText(_translate("Form", "Фильтровать"))
        self.label.setText(_translate("Form", "ДО->"))
        self.pbRedo.setText(_translate("Form", "Восстановить"))
        self.pbSave.setText(_translate("Form", "Сохранить"))
        self.chbHasPhone.setText(_translate("Form", "Тел"))

