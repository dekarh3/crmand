import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QToolTip, QPushButton, QMessageBox)
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon, QFont

class mainWindow(QWidget):

    def __init__(self, screenWidth, screenHeight, windowWidth=400, windowHeight=400):
        super().__init__()
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight
        self.windowWidth = windowWidth
        self.windowHeight = windowHeight
        self.initUI()


    def initUI(self):
        QToolTip.setFont(QFont('SansSerif', 10))
        self.setToolTip('ToolTip Widget')

        exitButton = QPushButton('Exit', self)
        exitButton.setToolTip("<b>Wish to Exit?</b>")
        exitButton.resize(exitButton.sizeHint())
        exitButton.move(100, 100)
        exitButton.clicked.connect(QCoreApplication.instance().quit)

        infoButton = QPushButton('Info', self) # Button that calls infoDialogue()
        infoButton.setToolTip('<b>ToolTip</b>')
        infoButton.resize(infoButton.sizeHint())
        infoButton.move(100, 200)
        infoButton.clicked.connect(self.infoDialogue)

        positionX = (self.screenWidth - self.windowWidth) / 2
        positionY = (self.screenHeight - self.windowHeight) / 2
        self.setGeometry(positionX, positionY, self.windowWidth, self.windowHeight)

        self.setWindowTitle('Window Title')
        #self.setWindowIcon(QIcon('./icon.png'))

        self.show()


    def infoDialogue(self): ## Method to open a message box
        infoBox = QMessageBox() ##Message Box that doesn't run
        print("Im here")
        infoBox.setIcon(QMessageBox.Information)
        infoBox.setText("Informações Adicionais")
        infoBox.setInformativeText("Informative Text")
        infoBox.setWindowTitle("Window Title")
        infoBox.setDetailedText("Detailed Text")
        infoBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        infoBox.setEscapeButton(QMessageBox.Close)
        infoBox.exec_()


    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Exit', "Are you sure you want to exit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    screenResolution = app.desktop().screenGeometry()
    screenWidth = screenResolution.width()
    screenHeight = screenResolution.height()
    example = mainWindow(screenWidth, screenHeight)
    sys.exit(app.exec_())