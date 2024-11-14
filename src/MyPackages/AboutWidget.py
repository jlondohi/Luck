from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QFrame
from PyQt6.QtCore import Qt
from MyPackages.MyTitleBar import MyTitleBar

#=============================
### Creating AboutWidget class
#=============================
class AboutWidget(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        version = parent.version
        self.cfg_session = parent.cfg_session
        self.i18n = parent.i18n
        self.lgg = parent.lgg
        
        self.parentWindow = self.window()
        #Loading GUI
        uic.loadUi('Guis/About.ui', self)

        #Replacing title bar
        original_fm = self.findChild(QFrame, 'fm_title')
        self.fm_title = MyTitleBar(self, menus=False)
        self.fm_title.setObjectName("fm_title")
        layout = original_fm.parentWidget().layout()
        layout.replaceWidget(original_fm, self.fm_title)      
        original_fm.deleteLater()

        #Setting StyleSheet
        self.fm_title.setStyleSheet(parent.dict_styleSheets["dark_theme"])

        #Modifying key data
        metadata = version.index.get("metadata")
        _version = version.index.get("version")
        _fecha = version.index.get('release_date')
        _autor = metadata['developer']
        self.lbl_autor.setText(f"<b>Author:</b> {_autor}")
        self.lbl_fecha.setText(f"<b>Date:</b> {_fecha}")
        self.lbl_version.setText(f"<b>Version:</b> {_version}")
        self.lbl_status.setText(f"<b>Version:</b> {_version}")
        self.initWindow()
        #Opening GUI without the windows native title bar
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint |
                           Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(1)
    
    #Function to initialize the window harmoniously with the monitor
    def initWindow(self):
        self.setWindowTitle('Luck')
        #Loading geometry
        geometria = self.cfg_session.index.get('prede_geo')
        #Get main monitor geometry
        self.screen_width = self.screen().size().width()
        self.screen_height = self.screen().size().height()
        #Set the initial window size relative to the monitor size
        x = int(self.screen_width * geometria[0] + 100)
        y = int(self.screen_height * geometria[1] + 100)
        self.setGeometry(x, y, 400, 200)