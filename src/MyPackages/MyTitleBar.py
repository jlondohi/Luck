import ctypes
from functools import partial
from PyQt6.QtWidgets import (QFrame, QHBoxLayout
    , QPushButton, QSpacerItem, QSizePolicy, QLabel)
from PyQt6.QtCore import Qt, QSize, QEvent
from PyQt6.QtGui import (QGuiApplication, QIcon
    , QPixmap)

#==================================================================
### Creating a custom QFrame class to serve as a title bar
#==================================================================
#Directed class to create custom window manipulation buttons
class TitleWindowButton(QPushButton):
    """
    Custom QPushButton for window manipulation (minimize, maximize, close, etc.).

    Attributes:
        None (inherits QPushButton attributes).

    Methods:
        __init__(self, text='', iconPath=None, parent=None): Initializes the button with optional text and icon.
    """
    def __init__(self, text='', iconPath=None, parent=None):
        """
        Initializes the window button with optional text and icon.

        Args:
            text (str, optional): Button text. Defaults to ''.
            iconPath (str, optional): Path to the icon. Defaults to None.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(text, parent)
        self.setMinimumSize(30, 30)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.adjustSize()
        self.setIconSize(QSize(25, 25))

        if iconPath:
            self.setIcon(QIcon(iconPath))

#Directed class to create custom menu buttons
class TitleMenuButton(QPushButton):
    """
    Custom QPushButton for menu actions in the title bar.

    Attributes:
        None (inherits QPushButton attributes).

    Methods:
        __init__(self, text='', iconPath=None, parent=None): Initializes the button with optional text and icon.
    """
    def __init__(self, text='', iconPath=None, parent=None):
        """
        Initializes the menu button with optional text and icon.

        Args:
            text (str, optional): Button text. Defaults to ''.
            iconPath (str, optional): Path to the icon. Defaults to None.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(text, parent)
        self.setMinimumSize(30, 30)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.adjustSize()
        self.setIconSize(QSize(25, 25))

        if iconPath:
            self.setIcon(QIcon(iconPath))

#Directed class to create separator bars
class Bar(QLabel):
    """
    Custom QLabel used as a separator bar in the title bar.

    Attributes:
        None (inherits QLabel attributes).

    Methods:
        __init__(self, parent=None): Initializes the separator bar.
    """
    def __init__(self, parent=None):
        """
        Initializes the separator bar with a fixed size and icon.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setMaximumSize(20, 30)
        self.setScaledContents(True)
        self.setPixmap(QPixmap('Guis/Resources/divider.png'))

#Directed class to create the title bar
class MyTitleBar(QFrame):
    """
    Custom QFrame that serves as a window title bar with custom buttons and menu actions.

    Attributes:
        parent (QWidget): Parent widget.
        i18nNes (callable): Internationalization function.
        shc (callable): Shortcut configuration getter.
        parentWindow (QWidget): Reference to the parent window.
        dragPosition (QPoint or None): Position for window dragging.
        gui (QGuiApplication): Reference to the application instance.
        layout (QHBoxLayout): Layout for the title bar.
        lbl_title (QLabel): Icon label in the title bar.
        bt_file, bt_edit, bt_select, bt_view, bt_go, bt_sql, bt_ai, bt_help (TitleMenuButton): Menu buttons.
        bt_downloads, bt_baseSetter, bt_light, bt_dark, bt_panelize, bt_expand, bt_minimize, bt_normalize, bt_maximize, bt_close (TitleWindowButton): Window control buttons.

    Methods:
        __init__(self, parent=None, menus=True): Initializes the title bar and its buttons.
        mousePressEvent(self, event): Handles mouse press events for dragging or showing the system menu.
        showSystemMenu(self, pos): Shows the Windows system menu at the given position.
        mouseDoubleClickEvent(self, event): Handles double-click events for maximizing/restoring the window.
        mouseMoveEvent(self, event): Handles mouse movement for dragging the window.
        updateMaximizeRestoreButtons(self, *args): Updates the visibility of maximize/restore buttons.
        minimizeWindow(self, *args): Minimizes the window.
        restoreWindow(self, *args): Restores the window from maximized state.
        maximizeWindow(self, *args): Maximizes the window.
        event(self, event, *args): Handles native gesture and mouse events for native bar behavior.
        nativeEvent(self, eventType, message, *args): Handles native Windows events for the title bar.
        creatingBottons(self, menus, *args): Creates and arranges the title bar buttons and menus.
    """
    def __init__(self, parent=None, menus=True):
        """
        Initializes the custom title bar, sets up buttons, menus, and window flags.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
            menus (bool, optional): Whether to include menu buttons. Defaults to True.
        """
        super().__init__(parent)
        self.parent = parent
        self.i18nNes = self.parent.i18nNes
        self.shc = self.parent.cfg_shortcut.getNested
        self.parentWindow = self.window()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMouseTracking(True)
        self.setFixedHeight(30)
        self.creatingBottons(menus)
        self.dragPosition = None
        self.gui = QGuiApplication.instance()
        #Restoring windows (default)
        self.updateMaximizeRestoreButtons()   
        
    #Function to capture the mouse click
    def mousePressEvent(self, event):
        """
        Handles mouse press events for dragging the window or showing the system menu.

        Args:
            event (QMouseEvent): The mouse press event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPosition = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # Mostrar el menú del sistema de Windows
            self.showSystemMenu(event.globalPosition().toPoint())
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def showSystemMenu(self, pos):
        """
        Shows the Windows system menu at the given position.

        Args:
            pos (QPoint): The position to show the system menu.
        """
        #It only works in Windows
        if hasattr(ctypes, 'windll'):
            hwnd = int(self.parent.winId())
            # 0x313 is the command to show the system menu
            ctypes.windll.user32.PostMessageW(hwnd, 0x313, 0, (pos.y() << 16) | pos.x())

    #Function to capture the double mouse click
    def mouseDoubleClickEvent(self, event):
        """
        Handles double-click events to maximize or restore the window.

        Args:
            event (QMouseEvent): The mouse double-click event.
        """
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
        """
        Handles mouse movement for dragging the window.

        Args:
            event (QMouseEvent): The mouse move event.
        """
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self.parentWindow.isMaximized():
                #Restoring the window to its normal size
                self.parentWindow.showNormal()
                return

            if self.dragPosition:
                self.parent.move(event.globalPosition().toPoint() - self.dragPosition)
                event.accept()

    #Function to handle the bar buttons
    def updateMaximizeRestoreButtons(self, *args):
        """
        Updates the visibility of maximize and restore buttons based on window state.

        Args:
            *args: Additional arguments (unused).
        """
        if self.parentWindow.isMaximized():
            self.bt_normalize.show()
            self.bt_maximize.hide()
        else:
            self.bt_normalize.hide()
            self.bt_maximize.show()     
    
    #Function that minimizes the window
    def minimizeWindow(self, *args):
        """
        Minimizes the parent window.

        Args:
            *args: Additional arguments (unused).
        """
        self.parent.showMinimized()
    
    #Function to restore the window (from maximized to normal size)
    def restoreWindow(self, *args):
        """
        Restores the parent window from maximized to normal size.

        Args:
            *args: Additional arguments (unused).
        """
        self.parentWindow.showNormal()
        self.updateMaximizeRestoreButtons()
    
    # #Function that maximazes the window   
    def maximizeWindow(self, *args):
        """
        Maximizes the parent window.

        Args:
            *args: Additional arguments (unused).
        """
        self.parentWindow.showMaximized()
        self.updateMaximizeRestoreButtons()
    
    #PENDING - It is sought that the bar behaves like the native
    def event(self, event, *args):
        """
        Handles native gesture and mouse events for native bar behavior.

        Args:
            event (QEvent): The event to handle.
            *args: Additional arguments (unused).

        Returns:
            bool: True if handled, otherwise calls the superclass event.
        """
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
    def nativeEvent(self, eventType, message, *args):
        """
        Handles native Windows events for the title bar.

        Args:
            eventType (str): The type of the native event.
            message: The native message object.
            *args: Additional arguments (unused).

        Returns:
            tuple: (bool, int) indicating if the event was handled and the result code.
        """
        # Solo funciona en Windows
        if eventType == 'windows_generic_MSG':
            from ctypes import windll, byref, c_long
            msg = message.__int__()
            # 0x84 = WM_NCHITTEST
            if msg.message == 0x84:
                # 0x2 = HTCAPTION
                return True, 0x2
        return False, 0    
    
    #Function to create taskbar menus and buttons
    def creatingBottons(self, menus, *args):
        """
        Creates and arranges the title bar buttons and menus.

        Args:
            menus (bool): Whether to include menu buttons.
            *args: Additional arguments (unused).
        """
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
        self.lbl_title.setPixmap(QPixmap('Guis/Resources/icon.png'))
        self.lbl_title.setToolTip(self.i18nNes('tooltips', 'tb10'))

        #Creating bottons
        #----------------
        self.bt_file = TitleMenuButton(self.i18nNes('header', 'file'))
        self.layout.addWidget(self.bt_file)
        
        if menus:
            self.bt_edit = TitleMenuButton(self.i18nNes('header', 'edit'))
            self.layout.addWidget(self.bt_edit)
            self.bt_select = TitleMenuButton(self.i18nNes('header', 'select'))
            self.layout.addWidget(self.bt_select)
            self.bt_view = TitleMenuButton(self.i18nNes('header', 'view'))
            self.layout.addWidget(self.bt_view)
            self.bt_go = TitleMenuButton(self.i18nNes('header', 'go'))
            self.layout.addWidget(self.bt_go)
            self.bt_sql = TitleMenuButton(self.i18nNes('header', 'sql'))
            self.layout.addWidget(self.bt_sql)
            self.bt_ai = TitleMenuButton(self.i18nNes('header', 'ai'))
            self.bt_ai.setEnabled(False) #At some point, It'll be true.
            self.layout.addWidget(self.bt_ai)
            self.bt_help = TitleMenuButton(self.i18nNes('header', 'help'))
            self.layout.addWidget(self.bt_help)
        
        self.layout.addSpacerItem(spacer1)
        self.layout.addWidget(self.lbl_title)
        self.layout.addSpacerItem(spacer2)
  
        if menus:
            #Button
            self.layout.addWidget(Bar())
            self.bt_downloads = TitleWindowButton('', 'Guis/Resources/folder.png')
            self.bt_downloads.setObjectName('bt_downloads')
            self.bt_downloads.clicked.connect(self.parent.openDownloadsFolder)
            self.layout.addWidget(self.bt_downloads)
            #Tooltip
            tootip = self.i18nNes('tooltips', 'tb9')
            sc = self.shc('buttons', 'downloads')
            tootip = tootip if not sc else tootip + f' ({sc})'
            self.bt_downloads.setToolTip(tootip)
            
            self.layout.addWidget(Bar())
            
            #Button
            self.bt_baseSetter = TitleWindowButton('', 'Guis/Resources/baseSetter.png')
            self.bt_baseSetter.setObjectName('bt_baseSetter')
            self.bt_baseSetter.setProperty('baseSetter', False)
            self.bt_baseSetter.clicked.connect(self.parent.baseSetter)
            self.layout.addWidget(self.bt_baseSetter)
            #Tooltip
            tootip = self.i18nNes('tooltips', 'tb7')
            sc = self.shc('buttons', 'styler')
            tootip = tootip if not sc else tootip + f' ({sc})'
            self.bt_baseSetter.setToolTip(tootip)
            
            #Button
            self.bt_light = TitleWindowButton('', 'Guis/Resources/light.png')
            self.bt_light.setObjectName('bt_light')
            self.bt_light.clicked.connect(self.parent.lightenFrame)
            self.layout.addWidget(self.bt_light)
            #Tooltip
            tootip = self.i18nNes('tooltips', 'tb5')
            sc = self.shc('buttons', 'lighter')
            tootip = tootip if not sc else tootip + f' ({sc})'
            self.bt_light.setToolTip(tootip)
            
            #Button
            self.bt_dark = TitleWindowButton('', 'Guis/Resources/dark.png')
            self.bt_dark.setObjectName('bt_dark')
            self.bt_dark.hide()
            self.bt_dark.clicked.connect(self.parent.darkenFrame)
            self.layout.addWidget(self.bt_dark)
            #Tooltip
            tootip = self.i18nNes('tooltips', 'tb6')
            sc = self.shc('buttons', 'darker')
            tootip = tootip if not sc else tootip + f' ({sc})'
            self.bt_dark.setToolTip(tootip)
            
            #Button
            self.layout.addWidget(Bar())
            self.bt_panelize = TitleWindowButton('', 'Guis/Resources/panelize.png')
            self.bt_panelize.setObjectName('bt_panelize')
            self.bt_panelize.clicked.connect(self.parent.panelizeFrame)
            self.layout.addWidget(self.bt_panelize)
            self.bt_panelize.hide()
            #Tooltip
            tootip = self.i18nNes('tooltips', 'tb3')
            sc = self.shc('buttons', 'panelize')
            tootip = tootip if not sc else tootip + f' ({sc})'
            self.bt_panelize.setToolTip(tootip)
            
            #Button
            self.bt_expand = TitleWindowButton('', 'Guis/Resources/expand.png')
            self.bt_expand.clicked.connect(self.parent.expandFrame)
            self.layout.addWidget(self.bt_expand)
            #Tooltip
            tootip = self.i18nNes('tooltips', 'tb4')
            sc = self.shc('buttons', 'expand')
            tootip = tootip if not sc else tootip + f' ({sc})'
            self.bt_expand.setToolTip(tootip)
        
        self.layout.addWidget(Bar())
        self.bt_minimize = TitleWindowButton('', 'Guis/Resources/minimize.png')
        self.bt_minimize.setObjectName('bt_minimize')
        self.bt_minimize.setToolTip(self.i18nNes('tooltips', 'tb2'))
        self.bt_minimize.clicked.connect(self.minimizeWindow)
        self.layout.addWidget(self.bt_minimize)

        self.bt_normalize= TitleWindowButton('', 'Guis/Resources/normal.png')
        self.bt_normalize.setObjectName('bt_normalize')
        self.bt_normalize.clicked.connect(self.restoreWindow)
        self.layout.addWidget(self.bt_normalize)
        self.bt_normalize.hide()
        
        self.bt_maximize = TitleWindowButton('', 'Guis/Resources/maximize.png')
        self.bt_maximize.setObjectName('bt_maximize')
        self.bt_maximize.clicked.connect(self.maximizeWindow)
        self.layout.addWidget(self.bt_maximize)
        
        self.bt_close = TitleWindowButton('', 'Guis/Resources/close.png')
        self.bt_close.setObjectName('bt_close')
        self.bt_close.setToolTip(self.i18nNes('tooltips', 'tb1'))
        self.bt_close.clicked.connect(partial(self.parent.close))
        self.layout.addWidget(self.bt_close)

        if not menus:
            self.bt_maximize.setEnabled(False)