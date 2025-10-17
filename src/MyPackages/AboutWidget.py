from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QFrame
from PyQt6.QtCore import Qt
from MyPackages.MyTitleBar import MyTitleBar

#=============================
### Creating AboutWidget class
#=============================
class AboutWidget(QMainWindow):
    """
    AboutWidget displays the application's About dialog with version and metadata information.

    Inherits from:
        QMainWindow

    Attributes:
        parent (QWidget): The parent widget.
        i18nNes (Any): Internationalization object, inherited from parent.
        cfg_shortcut (Any): Shortcut configuration, inherited from parent.
        parentWindow (QWidget): Reference to the parent window.
        fm_title (MyTitleBar): Custom title bar widget.
    
    Methods:
        __init__(self, parent=None):
            Initializes the AboutWidget, loads the UI, sets up the custom title bar, and displays version info.

        initWindow(self, *args):
            Initializes the window title and (optionally) geometry.
    """
    def __init__(self, parent=None):
        """
        Initializes the AboutWidget.

        Args:
            parent (QWidget, optional): The parent widget. Should provide `i18nNes`, `cfg_shortcut`, and `version` attributes.

        Side Effects:
            - Loads the UI from 'Guis/About.ui'.
            - Loads HTML content into the QTextBrowser.
            - Replaces the default title bar with a custom one.
            - Sets the window to be frameless and always on top.
            - Displays the application version.

        Attributes Set:
            parent, i18nNes, cfg_shortcut, parentWindow, fm_title
        """
        super().__init__()
        self.parent = parent
        self.i18nNes = self.parent.i18nNes
        self.cfg_shortcut = self.parent.cfg_shortcut
        version = parent.version
        
        self.parentWindow = self.window()
        #Loading GUI
        uic.loadUi('Guis/About.ui', self)
        with open("Guis/About.html", "r", encoding="utf-8") as f:
            self.qtb_description.setHtml(f.read())
        self.qtb_description.setOpenExternalLinks(True)

        #Replacing title bar
        original_fm = self.findChild(QFrame, 'fm_title')
        self.fm_title = MyTitleBar(self, menus=False)
        self.fm_title.setObjectName('fm_title')
        layout = original_fm.parentWidget().layout()
        layout.replaceWidget(original_fm, self.fm_title)      
        original_fm.deleteLater()

        #Modifying key data
        metadata = version.index.get('metadata')
        _version = version.index.get('version') 
        self.lbl_status.setText(f'<b>Version:</b> {_version}')
        self.initWindow()
        #Opening GUI without the windows native title bar
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint |
                           Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(1)
    
    #Function to initialize the window harmoniously with the monitor
    def initWindow(self, *args):
        """
        Initializes the window title and geometry.

        Args:
            *args: Additional arguments (unused).

        Side Effects:
            - Sets the window title to 'Luck'.
            - (Commented) Optionally sets geometry and QTextBrowser size based on document and monitor size.
        """
        self.setWindowTitle('Luck')
        # #Loading geometry
        # geometria = self.parent.cfg_session.index.get('prede_geo')
        # #Get main monitor geometry
        # self.screen_width = self.screen().size().width()
        # self.screen_height = self.screen().size().height()
        # #Set the initial window size relative to the monitor size
        # x = int(self.screen_width * geometria[0] + 100)
        # y = int(self.screen_height * geometria[1] + 100)
        
        # #Get the ideal document size
        # doc_size = self.qtb_description.document().size().toSize()
        # #Defines maximums
        # max_width = 500
        # max_height = 300
        # #Calculate limited final size
        # width = min(doc_size.width() + 40, max_width)
        # height = min(doc_size.height() + 40, max_height)
        # #Apply size to QTextBrowser
        # self.qtb_description.setFixedSize(width, height)
        # #Adjust the window to respect this size
        # self.qtb_description.window().adjustSize()
        # # self.setGeometry(x, y, 400, 200)