from PyQt6.QtWidgets import QFrame, QHBoxLayout \
    , QPushButton, QSpacerItem, QSizePolicy, QLabel
from PyQt6.QtCore import Qt, QSize
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
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMouseTracking(True)
        self.setFixedHeight(30)
        
        self.creatingBottons(menus)
        self.drag_position = None
        self.gui = QGuiApplication.instance()
        self.parentWindow = self.parent.parentWindow

    #Function to capture the mouse click
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()

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

    #Function that minimizes the window
    def minimizeWindow(self):
        self.parent.showMinimized()
    
    #Function to restore the window (from maximized to normal size)
    def restoreWindow(self):
        if not self.parentWindow.isMaximized():
            return
        self.parentWindow.showNormal()
        #Updating title bar buttons

        self.bt_normalize.hide()
        self.bt_maximize.show()
    
    #Function that maximazes the window
    def maximizeWindow(self):
        if self.parentWindow.isMaximized():
            return
        self.parentWindow.showMaximized()
        self.bt_normalize.show()
        self.bt_maximize.hide()
    
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
        lgg = self.parent.lgg

        self.bt_file = TitleMenuButton(nested(lgg, "header", "file"))
        self.layout.addWidget(self.bt_file)
        
        if menus:
            self.bt_edit = TitleMenuButton(nested(lgg, "header", "edit"))
            self.layout.addWidget(self.bt_edit)
            self.bt_select = TitleMenuButton(nested(lgg, "header", "select"))
            self.layout.addWidget(self.bt_select)
            self.bt_view = TitleMenuButton(nested(lgg, "header", "view"))
            self.layout.addWidget(self.bt_view)
            self.bt_sql = TitleMenuButton(nested(lgg, "header", "sql"))
            self.layout.addWidget(self.bt_sql)
            self.bt_ai = TitleMenuButton(nested(lgg, "header", "ai"))
            self.bt_ai.setEnabled(False) #At some point, It'll be true.
            self.layout.addWidget(self.bt_ai)
            self.bt_help = TitleMenuButton(nested(lgg, "header", "help"))
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
            self.bt_light.setToolTip(nested(lgg, "tooltips", "ttp1"))
            self.bt_light.setShortcut("F12")
            self.bt_light.clicked.connect(self.parent.lightenFrame)
            self.layout.addWidget(self.bt_light)
            
            self.bt_dark = TitleWindowButton("", "Guis/Resources/dark.png")
            self.bt_dark.setToolTip(nested(lgg, "tooltips", "ttp2"))
            self.bt_dark.setShortcut("F12")
            self.bt_dark.hide()
            self.bt_dark.clicked.connect(self.parent.darkenFrame)
            self.layout.addWidget(self.bt_dark)
            
            self.layout.addWidget(Bar())
            self.bt_panelize = TitleWindowButton("", "Guis/Resources/panelize.png")
            self.bt_panelize.setToolTip(nested(lgg, "tooltips", "ttp3"))
            self.bt_panelize.setShortcut("F11")
            self.bt_panelize.clicked.connect(self.parent.panelizeFrame)
            self.layout.addWidget(self.bt_panelize)
            self.bt_panelize.hide()
            
            self.bt_expand = TitleWindowButton("", "Guis/Resources/expand.png")
            self.bt_expand.setToolTip(nested(lgg, "tooltips", "ttp4"))
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
        self.bt_close.clicked.connect(lambda: self.parent.close())
        self.bt_close.setObjectName("bt_close")
        self.layout.addWidget(self.bt_close)

        if not menus:
            self.bt_maximize.setEnabled(False)

        

        
        
        
        
        
        
        
        
        
        
        
        
