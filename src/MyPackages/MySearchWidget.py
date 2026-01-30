from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt, pyqtSignal

#==================================================================
###Find and replace widget
#==================================================================
class MySearchWidget(QMainWindow):
    """
    Find and replace widget for text editors, supporting search, replace, and navigation.

    Signals:
        endSearching (): Emitted when the search widget is closed.
        textSearch (str): Emitted when the search text changes.
        returnKeyF (): Emitted when the return key is pressed in the search field.
        upBoton (): Emitted when the up button is pressed.
        downBoton (): Emitted when the down button is pressed.
        reemOne (): Emitted when the replace-one button is pressed.
        reemAll (): Emitted when the replace-all button is pressed.

    Attributes:
        textWidget (QWidget): Reference to the associated text editor widget.
        _width (int): Width of the search widget.
        _high (int): Height of the search widget.

    Methods:
        __init__(self, textEditor): Initializes the search widget.
        initWindow(self, *args): Sets up the widget geometry and initial state.
        showReem(self, *args): Shows the replace UI.
        setEditor(self, textWidget, *args): Sets the associated text editor.
        closeEvent(self, event, *args): Handles the close event and emits endSearching.
        emitSearchText(self, *args): Updates the searched word in the text editor.
        myShow(self, *args): Shows and positions the search widget.
        myMove(self, *args): Moves the widget relative to the text editor.
        keyPressEvent(self, event, *args): Handles key press events, especially Enter/Return.
    """
    #Defining signals
    endSearching = pyqtSignal()
    textSearch  = pyqtSignal(str)
    returnKeyF   = pyqtSignal()
    upBoton      = pyqtSignal()
    downBoton    = pyqtSignal()
    reemOne      = pyqtSignal()
    reemAll      = pyqtSignal()
    
    def __init__(self, textEditor):
        """
        Initializes the search widget and connects signals.

        Args:
            textEditor (QWidget): The text editor to associate with this search widget.
        """
        super().__init__()
        self.textWidget = textEditor
        uic.loadUi('Guis/Search.ui', self)
        self.setWindowFlags(Qt.WindowType.Tool)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(0.7)
        self.initWindow()
        self.bt_close.clicked.connect(self.close)
        self.bt_up.clicked.connect(self.upBoton.emit)
        self.bt_down.clicked.connect(self.downBoton.emit)
        self.bt_showReplace.clicked.connect(self.showReem)
        self.bt_replaceO.clicked.connect(self.reemOne.emit)
        self.bt_replaceA.clicked.connect(self.reemAll.emit)
        self.qle_textSearch.textChanged.connect(self.emitSearchText)
        self.qle_textSearch.returnPressed.connect(self.returnKeyF.emit)
        self.qle_textReplace.returnPressed.connect(self.reemOne.emit)
        
    def initWindow(self, *args):
        """
        Sets up the widget geometry, initial state, and UI properties.

        Args:
            *args: Additional arguments (unused).
        """
        #Defining the total widget geometry
        self._width = 300
        self._high  = 70
        self.centralWidget().setMaximumSize(self._width, self._high)
        self.fm_replace.hide()
        self.bt_showReplace.setEnabled(True)
        self.fm_search.setProperty('search', True)
        #Defining position in search mode
        self.setGeometry(self.geometry().x(), self.geometry().y(), self._width, int(self._high/2))
        self.setWindowTitle('searcher')

    def showReem(self, *args):
        """
        Shows the replace UI and updates the widget geometry and style.

        Args:
            *args: Additional arguments (unused).
        """
        self.fm_replace.show()
        self.bt_showReplace.setEnabled(False)
        self.fm_search.setProperty('search', False)
        #Defining position in replace mode
        self.setGeometry(self.geometry().x(), self.geometry().y(), self._width, self._high)
        #Modifying the style
        self.fm_search.style().unpolish(self.fm_search)
        self.fm_search.style().polish(self.fm_search)

    def setEditor(self, textWidget, *args):
        """
        Sets the associated text editor and re-initializes the window.

        Args:
            textWidget (QWidget): The text editor to associate.
            *args: Additional arguments (unused).
        """
        self.textWidget = textWidget
        self.initWindow()
    
    def closeEvent(self, event, *args):
        """
        Handles the close event, resets search state, and emits endSearching.

        Args:
            event (QCloseEvent): The close event.
            *args: Additional arguments (unused).
        """
        self.textWidget.searchedWord = None
        self.endSearching.emit()
        self.textWidget.viewport().update()
        super().closeEvent(event)
    
    def emitSearchText(self, *args):
        """
        Updates the searched word in the text editor and refreshes the viewport.

        Args:
            *args: Additional arguments (unused).
        """
        #Changing the search text
        self.textWidget.searchedWord = self.qle_textSearch.text()
        self.textWidget.viewport().update()

    def myShow(self, *args):
        """
        Shows and positions the search widget if the text editor is visible.

        Args:
            *args: Additional arguments (unused).
        """
        if self.textWidget and self.textWidget.isVisible():
            self.myMove()
            self.show()
    
    def myMove(self, *args):
        """
        Moves the search widget relative to the top-right of the text editor.

        Args:
            *args: Additional arguments (unused).
        """
        top_right = self.textWidget.rect().topRight()
        new_x = top_right.x() - self.width() - 15
        self.move(new_x, top_right.y())
        
    def keyPressEvent(self, event, *args):
        """
        Handles key press events, capturing Enter/Return to prevent propagation.

        Args:
            event (QKeyEvent): The key event.
            *args: Additional arguments (unused).
        """
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            #Capturing the Enter event and preventing it from propagating
            event.accept()
        else:
            super().keyPressEvent(event)