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
    """
    Custom QMainWindow for displaying and managing tooltips with advanced features like blinking, copy, and pin.

    Signals:
        returnKeyF (): Emitted when a return key event is triggered.

    Attributes:
        app (QApplication): Reference to the QApplication instance.
        i18nNes (callable): Internationalization function.
        showTimer (QTimer): Timer for auto-hiding the tooltip.
        blinkTimer (QTimer): Timer for blinking the copy button.
        blinkTimes (int): Counter for blink cycles.
        blinkerColor (str): Color used for blinking effect.
        originalStyle (str): Original style sheet of the copy button.
        iconCerrar (QIcon): Icon for the close button.
        stateClose (bool): Indicates if the tooltip is pinned.
        text (str): The current text displayed in the tooltip.
        clickPosition (QPoint): Last mouse click position for moving the window.

    Methods:
        __init__(self, parent): Initializes the tooltip window and its UI.
        initWindow(self, *args): Initializes window geometry and title.
        myShow(self, cell_rect, *args): Shows the tooltip at the specified cell rectangle.
        setText(self, text, *args): Sets and formats the tooltip text.
        toClipBoard(self, *args): Copies the tooltip text to the clipboard.
        leaveEvent(self, event, *args): Handles the event when the mouse leaves the tooltip.
        enterEvent(self, event, *args): Handles the event when the mouse enters the tooltip.
        keyPressEvent(self, event, *args): Handles key press events (e.g., Escape to close).
        blinker(self, *args): Handles the blinking effect for the copy button.
        toFix(self, *args): Pins or unpins the tooltip window.
        mousePressEvent(self, event, *args): Captures the mouse position for moving the window.
        mouseMoveEvent_fm(self, event, *args): Moves the window based on mouse movement.
    """

    #Defining signals
    returnKeyF = pyqtSignal()

    def __init__(self, parent):
        """
        Initializes the tooltip window, loads the UI, and sets up signals, timers, and styles.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__()
        self.app = QApplication.instance()
        
        #Language
        self.i18nNes = parent.i18nNes
        
        uic.loadUi(str(parent.parent.guisPath / 'Tooltip.ui'), self)
        self.setWindowFlags(Qt.WindowType.Tool)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(1)
        self.initWindow()
        self.bt_copiar.clicked.connect(self.toClipBoard)
        self.bt_copiar.setToolTip(self.i18nNes('tooltips', 'ttp1'))
        self.bt_fijar.clicked.connect(self.toFix)
        self.bt_fijar.setToolTip(self.i18nNes('tooltips', 'ttp2'))
        self.fm_tooltip.mouseMoveEvent = self.mouseMoveEvent_fm
        #Creating a timer to alert you about the error message
        self.showTimer = QTimer()
        self.showTimer.setInterval(5000)
        self.showTimer.timeout.connect(partial(self.leaveEvent, None))
        #Creating a timer to flash and attract attention
        self.blinkTimer = QTimer()
        self.blinkTimer.setInterval(400)
        self.blinkTimer.timeout.connect(self.blinker)
        self.blinkTimes = 0
        self.blinkerColor = parent.tl_3
        self.originalStyle = self.bt_copiar.styleSheet()
        #Loading second icon
        self.iconCerrar = QIcon(str(parent.parent.guisPath / 'Resources' /'close.png'))
        self.stateClose = False
    
    def initWindow(self, *args):
        """
        Initializes the window geometry and title.

        Args:
            *args: Additional arguments (unused).
        """
        self.setGeometry(self.geometry().x(), self.geometry().y(), 500, 400)
        self.setWindowTitle('Tooltip')
    
    def myShow(self, cell_rect, *args):
        """
        Shows the tooltip at the specified cell rectangle, centering it over the parent if available.

        Args:
            cell_rect (QRect): The rectangle to center the tooltip on.
            *args: Additional arguments (unused).
        """
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
    def setText(self, text, *args):
        """
        Sets and formats the tooltip text, adjusting the window size accordingly.

        Args:
            text (str): The text to display.
            *args: Additional arguments (unused).
        """
        self.text = text.replace('\n', '<br>')
        self.textContent.setHtml(f"<div pre-wrap;'>{self.text}</div>")
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
    def toClipBoard(self, *args):
        """
        Copies the current tooltip text to the clipboard.

        Args:
            *args: Additional arguments (unused).
        """
        clipboard = self.app.clipboard()
        clipboard.setText(self.text)
    
    #Widget's own function (when the mouse leaves focus)
    def leaveEvent(self, event, *args):
        """
        Handles the event when the mouse leaves the tooltip.

        Args:
            event (QEvent): The leave event.
            *args: Additional arguments (unused).
        """
        if self.stateClose:
            self.showTimer.stop()
        else:
            self.showTimer.stop()
            self.close()
    
    #Widget's own function, (when mouse focus input)
    def enterEvent(self, event, *args):
        """
        Handles the event when the mouse enters the tooltip.

        Args:
            event (QEvent): The enter event.
            *args: Additional arguments (unused).
        """
        self.bt_copiar.setStyleSheet(self.originalStyle)
        self.blinkTimer.stop()
        self.showTimer.stop()

    #Function to capture key events
    def keyPressEvent(self, event, *args):
        """
        Handles key press events, such as Escape to close the tooltip.

        Args:
            event (QKeyEvent): The key event.
            *args: Additional arguments (unused).
        """
        if event.key() == Qt.Key.Key_Escape:
            self.showTimer.stop()
            self.close()
    
    #Function to attract user attention
    def blinker(self, *args):
        """
        Handles the blinking effect for the copy button to attract user attention.

        Args:
            *args: Additional arguments (unused).
        """
        self.blinkTimes += 1
        if self.blinkTimes < 6:
            if self.blinkTimes % 2 == 1:
                self.bt_copiar.setStyleSheet(f'QPushButton{{ background-color: {self.blinkerColor}; }}')
            else:
                self.bt_copiar.setStyleSheet(self.originalStyle)
            self.blinkTimer.start()
        else:
            self.bt_copiar.setStyleSheet(self.originalStyle)
            self.blinkTimer.stop()
            self.showTimer.start()
    
    #Function to fix the message
    def toFix(self, *args):
        """
        Pins or unpins the tooltip window, toggling its close state.

        Args:
            *args: Additional arguments (unused).
        """
        if self.stateClose:
            self.close()
        else:
            self.stateClose = True
            self.bt_fijar.setIcon(self.iconCerrar)
            self.showTimer.stop()
    
    #Functions to move the window
    #-------------------------------
    #Click position grabber
    def mousePressEvent(self, event, *args):
        """
        Captures the mouse position for moving the tooltip window.

        Args:
            event (QMouseEvent): The mouse press event.
            *args: Additional arguments (unused).
        """
        #Capturing the mouse position. Globally
        self.clickPosition = event.globalPosition().toPoint()
    
    #Move window
    def mouseMoveEvent_fm(self, event, *args):
        """
        Moves the tooltip window based on mouse movement.

        Args:
            event (QMouseEvent): The mouse move event.
            *args: Additional arguments (unused).
        """
        #Moving screen
        if self.clickPosition:
            self.move(self.pos() + event.globalPosition().toPoint() - self.clickPosition)
            self.clickPosition = event.globalPosition().toPoint()
