import ctypes
from functools import partial
from PyQt6.QtWidgets import QFrame, QHBoxLayout \
    , QPushButton, QSpacerItem, QSizePolicy, QLabel
from PyQt6.QtCore import Qt, QSize, QEvent
from PyQt6.QtGui import QGuiApplication, QIcon \
    , QPixmap

#================================================================== ============================
### Creating a custom QFrame class to serve as a title bar
#================================================================== ============================
#Directed class to create custom window manipulation buttons
class TitleWindowButton(QPushButton):
    def __init__(self, text="", icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(30, 30)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.adjustSize()
        self.setIconSize(QSize(25, 25))

        if icon_path:
            self.setIcon(QIcon(icon_path))

#Directed class to create custom menu buttons
class TitleMenuButton(QPushButton):
    def __init__(self, text="", icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(30, 30)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.adjustSize()
        self.setIconSize(QSize(25, 25))

        if icon_path:
            self.setIcon(QIcon(icon_path))

#Directed class to create separator bars
class Bar(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumSize(20, 30)
        self.setScaledContents(True)
        self.setPixmap(QPixmap("Guis/Resources/divider.png"))

#Directed class to create the title bar
class MyTitleBar(QFrame):
    def __init__(self, parent=None, menus=True):
        super().__init__(parent)
        self.parent = parent
        self.parentWindow = self.window()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMouseTracking(True)
        self.setFixedHeight(30)
        self.creatingBottons(menus)
        self.drag_position = None
        self.gui = QGuiApplication.instance()
        #Restoring windows (default)
        self.updateMaximizeRestoreButtons()   
        
    #Function to capture the mouse click
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # Mostrar el menú del sistema de Windows
            self.showSystemMenu(event.globalPosition().toPoint())
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def showSystemMenu(self, pos):
        #It only works in Windows
        if hasattr(ctypes, "windll"):
            hwnd = int(self.parent.winId())
            # 0x313 is the command to show the system menu
            ctypes.windll.user32.PostMessageW(hwnd, 0x313, 0, (pos.y() << 16) | pos.x())

    #Function to capture the double mouse click
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            #We check if the window is maximized
            if self.parentWindow.isMaximized():
                self.restoreWindow()
            else:
                self.maximizeWindow()
        else:
            super().mouseDoubleClickEvent(event)

    #Function to move or stop when the window is moved
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self.parentWindow.isMaximized():
                #Restoring the window to its normal size
                self.parentWindow.showNormal()
                return

            if self.drag_position:
                self.parent.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()

    #Function to handle the bar buttons
    def updateMaximizeRestoreButtons(self, *args):
        if self.parentWindow.isMaximized():
            self.bt_normalize.show()
            self.bt_maximize.hide()
        else:
            self.bt_normalize.hide()
            self.bt_maximize.show()     
    
    #Function that minimizes the window
    def minimizeWindow(self):
        self.parent.showMinimized()
    
    #Function to restore the window (from maximized to normal size)
    def restoreWindow(self):
        self.parentWindow.showNormal()
        self.updateMaximizeRestoreButtons()
    
    # #Function that maximazes the window   
    def maximizeWindow(self):
        self.parentWindow.showMaximized()
        self.updateMaximizeRestoreButtons()
    
    #PENDING - It is sought that the bar behaves like the native
    def event(self, event):
        # Esto permite que Windows reconozca la barra como la barra de título
        if event.type() == QEvent.Type.NativeGesture:
            return super().event(event)
        if event.type() == QEvent.Type.MouseButtonDblClick:
            return super().event(event)
        if event.type() == QEvent.Type.MouseButtonPress:
            return super().event(event)
        if event.type() == QEvent.Type.MouseMove:
            return super().event(event)
        if event.type() == QEvent.Type.HoverMove:
            return super().event(event)
        return super().event(event)

    #PENDING - It is sought that the bar behaves like the native
    def nativeEvent(self, eventType, message):
        # Solo funciona en Windows
        if eventType == "windows_generic_MSG":
            from ctypes import windll, byref, c_long
            msg = message.__int__()
            # 0x84 = WM_NCHITTEST
            if msg.message == 0x84:
                # 0x2 = HTCAPTION
                return True, 0x2
        return False, 0    
    
    #Function to create taskbar menus and buttons
    def creatingBottons(self, menus):
        #Creating the layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10,0,10,0)
        self.layout.setSpacing(1)

        #Spacers
        spacer1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        #Labels
        self.lbl_title = QLabel()
        self.lbl_title.setMaximumSize(30, 30)
        self.lbl_title.setScaledContents(True)
        self.lbl_title.setPixmap(QPixmap("Guis/Resources/icon.png"))

        #Creating bottons
        #----------------
        #Instantiating language
        nested = self.parent.i18n.getNested

        self.bt_file = TitleMenuButton(nested("header", "file"))
        self.layout.addWidget(self.bt_file)
        
        if menus:
            self.bt_edit = TitleMenuButton(nested("header", "edit"))
            self.layout.addWidget(self.bt_edit)
            self.bt_select = TitleMenuButton(nested("header", "select"))
            self.layout.addWidget(self.bt_select)
            self.bt_view = TitleMenuButton(nested("header", "view"))
            self.layout.addWidget(self.bt_view)
            self.bt_sql = TitleMenuButton(nested("header", "sql"))
            self.layout.addWidget(self.bt_sql)
            self.bt_ai = TitleMenuButton(nested("header", "ai"))
            self.bt_ai.setEnabled(False) #At some point, It'll be true.
            self.layout.addWidget(self.bt_ai)
            self.bt_help = TitleMenuButton(nested("header", "help"))
            self.layout.addWidget(self.bt_help)
        
        self.layout.addSpacerItem(spacer1)
        self.layout.addWidget(self.lbl_title)
        self.layout.addSpacerItem(spacer2)
  
        if menus:
            self.layout.addWidget(Bar())
            self.bt_downloads = TitleWindowButton("", "Guis/Resources/folder.png")
            self.bt_downloads.clicked.connect(self.parent.openDownloadsFolder)
            self.layout.addWidget(self.bt_downloads)
            
            self.layout.addWidget(Bar())
            self.bt_light = TitleWindowButton("", "Guis/Resources/light.png")
            self.bt_light.setToolTip(nested("tooltips", "ttp1"))
            self.bt_light.setShortcut("F12")
            self.bt_light.clicked.connect(self.parent.lightenFrame)
            self.layout.addWidget(self.bt_light)
            
            self.bt_dark = TitleWindowButton("", "Guis/Resources/dark.png")
            self.bt_dark.setToolTip(nested("tooltips", "ttp2"))
            self.bt_dark.setShortcut("F12")
            self.bt_dark.hide()
            self.bt_dark.clicked.connect(self.parent.darkenFrame)
            self.layout.addWidget(self.bt_dark)
            
            self.layout.addWidget(Bar())
            self.bt_panelize = TitleWindowButton("", "Guis/Resources/panelize.png")
            self.bt_panelize.setToolTip(nested("tooltips", "ttp3"))
            self.bt_panelize.setShortcut("F11")
            self.bt_panelize.clicked.connect(self.parent.panelizeFrame)
            self.layout.addWidget(self.bt_panelize)
            self.bt_panelize.hide()
            
            self.bt_expand = TitleWindowButton("", "Guis/Resources/expand.png")
            self.bt_expand.setToolTip(nested("tooltips", "ttp4"))
            self.bt_expand.clicked.connect(self.parent.expandFrame)
            self.layout.addWidget(self.bt_expand)
        
        self.layout.addWidget(Bar())
        self.bt_minimize = TitleWindowButton("", "Guis/Resources/minimize.png")
        self.bt_minimize.clicked.connect(self.minimizeWindow)
        self.layout.addWidget(self.bt_minimize)

        self.bt_normalize= TitleWindowButton("", "Guis/Resources/normal.png")
        self.bt_normalize.clicked.connect(self.restoreWindow)
        self.layout.addWidget(self.bt_normalize)
        self.bt_normalize.hide()
        
        self.bt_maximize = TitleWindowButton("", "Guis/Resources/maximize.png")
        self.bt_maximize.clicked.connect(self.maximizeWindow)
        self.layout.addWidget(self.bt_maximize)
        
        self.bt_close = TitleWindowButton("", "Guis/Resources/close.png")
        self.bt_close.clicked.connect(partial(self.parent.close))
        
        self.bt_close.setObjectName("bt_close")
        self.layout.addWidget(self.bt_close)

        if not menus:
            self.bt_maximize.setEnabled(False)

        

        
        
        
        
        
        
        
        
        
        
        
        
