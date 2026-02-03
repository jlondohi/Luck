#Importing PyQt6 packages
from PyQt6.QtWidgets import (QMainWindow, QApplication
    , QLabel, QVBoxLayout, QWidget)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer
#Importing own PyQt6 packages
from MyPackages.MainWindow import MainWindow

class MySplashScreen(QMainWindow):
    """
    Custom splash screen window for displaying a startup image before loading the main application window.

    Attributes:
        app (QApplication): Reference to the QApplication instance.
        _width (int): Width of the splash screen window.
        _height (int): Height of the splash screen window.
        settings (object): Placeholder for settings (unused).
        icon (QIcon): Window icon.
        loadingTimer (QTimer): Timer for transitioning to the main window.

    Methods:
        __init__(self): Initializes the splash screen and UI.
        initUI(self, *args): Sets up the splash screen UI and starts the loading timer.
        showMainWindow(self, *args): Stops the timer and shows the main application window.
    """
    def __init__(self):
        """
        Initializes the splash screen and sets up the UI.
        """
        super().__init__()
        self.app = QApplication.instance()
        #Defining default size
        self._width   = 350
        self._height  = 350
        self.settings = None
        #Initiating
        self.initUI()

    def initUI(self, *args):
        """
        Sets up the splash screen UI, including the image, layout, and timer.

        Args:
            *args: Additional arguments (unused).
        """
        #Window configuration
        self.icon = QIcon('Guis/Resources/icon0.ico')
        self.setWindowIcon(self.icon)
        self.setWindowTitle('Splash Screen')
        self.resize(self._width, self._height)
        #Getting screen geometry
        size = self.geometry()
        center_x = (self.screen().size().width() - size.width()) // 2
        center_y = (self.screen().size().height() - size.height()) // 2
        self.move(center_x, center_y)

        #Setting the window to transparent
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        #Setting the center widget as a QLabel for the image
        pixmap = QPixmap('Guis/Resources/start.png')
        scaled_pixmap = pixmap.scaledToWidth(self._width - 1, Qt.TransformationMode.SmoothTransformation)
        label = QLabel(self)
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #Adding widgets to the layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container = QWidget(self)
        container.setLayout(layout)
        container.setStyleSheet('background-color: transparent;')
        self.setCentralWidget(container)

        #Requesting to load main window
        self.loadingTimer = QTimer(self)
        self.loadingTimer.timeout.connect(self.showMainWindow)
        self.loadingTimer.start(1000)

    #Loading main window
    def showMainWindow(self, *args):
        """
        Stops the loading timer and shows the main application window.

        Args:
            *args: Additional arguments (unused).
        """
        self.loadingTimer.stop()
        #Loading main window
        ventana = MainWindow()
        ventana.show()
        self.close()