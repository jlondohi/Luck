from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt, pyqtSignal

#==================================================================
###Find and replace widget
#==================================================================
class SearchWidget(QMainWindow):
    #Defining signals
    endSearching = pyqtSignal()
    textoBuscar = pyqtSignal(str)
    returnKeyF = pyqtSignal()
    upBoton = pyqtSignal()
    downBoton = pyqtSignal()
    reemOne = pyqtSignal()
    reemAll = pyqtSignal()
    
    def __init__(self, text_editor):
        super().__init__()
        self.textWidget = text_editor
        uic.loadUi('Guis/Search.ui', self)
        self.setWindowFlags(Qt.WindowType.Tool)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(0.7)
        self.initWindow()
        self.bt_close.clicked.connect(self.close)
        self.bt_arriba.clicked.connect(self.upBoton.emit)
        self.bt_abajo.clicked.connect(self.downBoton.emit)
        self.bt_showReem.clicked.connect(self.showReem)
        self.bt_reemplazarO.clicked.connect(self.reemOne.emit)
        self.bt_reemplazarA.clicked.connect(self.reemAll.emit)
        self.qle_textBuscar.textChanged.connect(self.emitSearchText)
        self.qle_textBuscar.setStyleSheet("background-color: #4e4e4e; border-radius:0;")
        self.qle_textBuscar.returnPressed.connect(self.returnKeyF.emit)
        self.qle_textReem.returnPressed.connect(self.reemOne.emit)
        self.qle_textReem.setStyleSheet("background-color: #4e4e4e; border-radius:0;")
        self.setStyleSheet("QFrame { border: none; }")
        
    def initWindow(self):
        self.fm_reemplazar.hide()
        self.bt_showReem.setEnabled(True)
        self.setGeometry(self.geometry().x(), self.geometry().y(), 220, 35)
        self.setWindowTitle('Buscador')

    def showReem(self):
        self.fm_reemplazar.show()
        self.bt_showReem.setEnabled(False)
        self.setGeometry(self.geometry().x(), self.geometry().y(), 220, 70)

    def setEditor(self, textWidget):
        self.textWidget = textWidget
        self.initWindow()
    
    def closeEvent(self, event):
        self.textWidget.Searched_word = None
        self.endSearching.emit()
        super().closeEvent(event)
    
    def emitSearchText(self):               
        #Disabling multicursor mode
        self.textWidget.setCursorWidth(1)
        self.textWidget.multiCursor_list.clear()
        self.textWidget.multiCursorEnabled = False
        #Changing the search text
        self.textWidget.Searched_word = self.qle_textBuscar.text()

    def myShow(self):
        if self.textWidget and self.textWidget.isVisible():
            self.myMove(self.textWidget)
            self.show()
    
    def myMove(self, textWidget):
        top_right = textWidget.rect().topRight()
        new_x = top_right.x() - self.width() - 2
        self.move(new_x, top_right.y())
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            #Capturing the Enter event and preventing it from propagating
            event.accept()  
        else:
            super().keyPressEvent(event)