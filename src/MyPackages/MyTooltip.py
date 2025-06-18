#Importing PyQt6 packages
import math
from functools import partial
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtGui import QFontMetrics, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

#========================================================
### Creating the classes to handle ToolTips -For results
#========================================================
class MyTooltip(QMainWindow):
    #Defining signals
    returnKeyF = pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self.app = QApplication.instance()

        #Language
        self.nested = parent.i18n.getNested

        uic.loadUi('Guis/Tooltip.ui', self)
        self.setWindowFlags(Qt.WindowType.Tool)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(1)
        self.initWindow()
        self.bt_copiar.clicked.connect(self.toClipBoard)
        self.bt_copiar.setToolTip(self.nested("tooltips", "ttp7"))
        self.bt_fijar.clicked.connect(self.toFix)
        self.bt_fijar.setToolTip(self.nested("tooltips", "ttp8"))
        self.fm_tooltip.mouseMoveEvent = self.mouseMoveEvent_fm
        #Creating a timer to alert you about the error message
        self.showTimer = QTimer()
        self.showTimer.setInterval(5000)
        self.showTimer.timeout.connect(partial(self.leaveEvent, None))
        #Creating a timer to flash and attract attention
        self.blinkTimer = QTimer()
        self.blinkTimer.setInterval(400)
        self.blinkTimer.timeout.connect(self.blinker)
        self.blink_times = 0
        self.blinkerColor = parent.tl_3
        self.original_style = self.bt_copiar.styleSheet()
        #Taking text color
        self.text_color = parent.theme["result-color_text"]
        #Loading second icon
        self.iconCerrar = QIcon('Guis/Resources/close.png')
        self.stateClose = False
    
    def initWindow(self):
        self.setGeometry(self.geometry().x(), self.geometry().y(), 500, 400)
        self.setWindowTitle('Tooltip')
    
    def myShow(self, cell_rect):
        geo = cell_rect.center()
        self.move(geo.x(), geo.y())
        if self.parent():
            #Getting the geometry of the parent
            parent_geometry = self.parent().geometry()
            #Getting the child window rectangle
            window_geometry = self.frameGeometry()
            #Calculating the position of the center of the parent
            parent_center = parent_geometry.center()
            #Moving the child window rectangle to the center of the parent
            window_geometry.moveCenter(parent_center)
            #Moving the child window to the new position
            self.move(window_geometry.topLeft())

        self.blinkTimer.start()
        self.show()

    #Function to enter and format text within the tooltip
    def setText(self, text):
        self.text = text.replace("\n", "<br>")
        self.textContent.setHtml(f"<div style='white-space: pre-wrap; color: {self.text_color};'>{self.text}</div>")
        #Calculating text size and adjusting the window
        fm = QFontMetrics(self.textContent.font())
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()
        if text_width > 600:
            factor = math.ceil(text_width/700)
            text_width = 600
            y_plus = 100
        else:
            factor = 1
            text_width = text_width+100
            y_plus = 60
        #Avoiding excessive size
        value_y = int(factor*text_height+y_plus)
        value_y = 800 if value_y > 800 else value_y
        self.resize(text_width, value_y)
        self.myShow(self.geometry())

    #Function to copy to clipboard    
    def toClipBoard(self):
        clipboard = self.app.clipboard()
        clipboard.setText(self.text)
    
    #Widget's own function (when the mouse leaves focus)
    def leaveEvent(self, event):
        if self.stateClose:
            self.showTimer.stop()
        else:
            self.showTimer.stop()
            self.close()
    
    #Widget's own function, (when mouse focus input)
    def enterEvent(self, event):
        self.bt_copiar.setStyleSheet(self.original_style)
        self.blinkTimer.stop()
        self.showTimer.stop()

    #Function to capture key events
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.showTimer.stop()
            self.close()
    
    #Function to attract user attention
    def blinker(self):
        self.blink_times += 1
        if self.blink_times < 6:
            if self.blink_times % 2 == 1:
                self.bt_copiar.setStyleSheet(f'background-color: {self.blinkerColor};')
            else:
                self.bt_copiar.setStyleSheet(self.original_style)
            self.blinkTimer.start()
        else:
            self.bt_copiar.setStyleSheet(self.original_style)
            self.blinkTimer.stop()
            self.showTimer.start()
    
    #Function to fix the message
    def toFix(self):
        if self.stateClose:
            self.close()
        else:
            self.stateClose = True
            self.bt_fijar.setIcon(self.iconCerrar)
            self.showTimer.stop()
    
    #Functions to move the window
    #-------------------------------
    #Click position grabber
    def mousePressEvent(self, event):
        #Capturing the mouse position. Globally
        self.click_position = event.globalPosition().toPoint()
    
    #Move window
    def mouseMoveEvent_fm(self, event):
        #Moving screen
        if self.click_position:
            self.move(self.pos() + event.globalPosition().toPoint() - self.click_position)
            self.click_position = event.globalPosition().toPoint()
