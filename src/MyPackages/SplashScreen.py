from PyQt6.QtWidgets import QMainWindow, QApplication \
    , QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer

#Importing own PyQt6 packages
from MyPackages.MainWindow import MainWindow

class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app = QApplication.instance()
        #Defining default size
        self._width = 350
        self._height = 350
        self.settings = None
        #Initiating
        self.initUI()

    def initUI(self):
        #Window configuration
        self.icon = QIcon('Guis/Resources/icon0.ico')
        self.setWindowIcon(self.icon)
        self.setWindowTitle("Splash Screen")
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
        container.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.setCentralWidget(container)
        
        #Requesting to load main window
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.showMainWindow)
        self.loading_timer.start(1000)

    #Loading main window
    def showMainWindow(self):
        self.loading_timer.stop()
        #Loading main window
        ventana = MainWindow()
        ventana.show()
        self.close()