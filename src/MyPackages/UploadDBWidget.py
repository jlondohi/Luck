
try:
    from sparky_bc import Sparky
except:
    Sparky = None

import os, sys, getpass
from PyQt6 import uic
from PyQt6.QtWidgets import (QMainWindow, QFileDialog
    , QLineEdit, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

from MyPackages.MyTitleBar import MyTitleBar
#=======================
### Upload to LZ widget
#=======================
#Helper class to run sparky in a separate thread
class UploadDB(QThread):
    update_status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__()
        self.file_path = parent.file_path
        self.tabla = parent.tabla
        self.mode = parent.mode
        #---
        self.username = parent.username
        self.psw = parent.psw
        self.dsn = parent.dsn
        self.hostname = parent.hostname
        self.logger = {}
        self.sp = None
        self.sp_created = False
        #---
        self.original_stdout = sys.stdout

        #cultating and Instanciando Sparky
        sys.stdout = open(os.devnull, 'w')
        try:
            self.sp = Sparky(username = self.username, dsn = self.dsn
                , password = self.psw, hostname = self.hostname
                , logger = self.logger)
        except:
            self.sp_created = False
        else:
            self.sp_created = True
        finally:
            sys.stdout.close()
            sys.stdout = self.original_stdout

    def run(self):
        #Redirecting sys.stdout to os.devnull
        sys.stdout = open(os.devnull, 'w')
        for path in self.file_path:
            try:
                self.sp.subir_csv(path=path, table_name=self.tabla, modo=self.mode)
            except:
                self.error.emit()
            else:
                self.finished.emit()
            finally:
                #Restoring sys.stdout to its original value
                sys.stdout.close()
                sys.stdout = self.original_stdout
         
#Main class, contains window and functionalities
class UploadDBWidget(QMainWindow):
    #Defining signals
    closeSignal   = pyqtSignal()
    finishSignal  = pyqtSignal()
    prosessSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        uic.loadUi(str(self.parent.guisPath / 'UploadLZ.ui'), self)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(1)
        self.bt_abrir.clicked.connect(self.openFile)
        self.bt_ver.clicked.connect(self.seePass)
        self.bt_nover.clicked.connect(self.unseePass)
        self.bt_subir.clicked.connect(self.toDB)

        #Replacing title bar
        self.parentWindow = parent.parentWindow
        original_fm = self.findChild(QFrame, 'fm_title')
        self.fm_title = MyTitleBar(self, menus=False)
        self.fm_title.setObjectName('fm_title')
        layout = original_fm.parentWidget().layout()
        layout.replaceWidget(original_fm, self.fm_title)
        original_fm.deleteLater()
        self.fm_title.setStyleSheet( parent.dict_themeSheets[parent.globalTheme] )
        
        #Global variables
        self.file_path = ''
        self.logger = {}
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateStatus)

        #Language
        self.i18nNes = parent.i18nNes
        #Headers
        self._header = self.i18nNes('upload-to-db', 'header')
        #Cls
        self._option1 = self.i18nNes('upload-to-db', 'option1')
        self._option2 = self.i18nNes('upload-to-db', 'option2')
        self._option3 = self.i18nNes('upload-to-db', 'option3')
        #others
        self._starting = self.i18nNes('status-bar', 'starting')
        self._open     = self.i18nNes('open-file', 'open2')
        self._allowed  = self.i18nNes('open-file', 'open4')
        self._end      = self.i18nNes('status-bar', 'end')
        self._endE     = self.i18nNes('status-bar', 'end-e')
        self._cmic     = self.i18nNes('status-bar', 'cmic')
        self._state    = self.i18nNes('upload-to-db', 'state')
        self._time     = self.i18nNes('upload-to-db', 'time')

        #Starting window
        self.initWindow()

    #Function to load some initial definitions
    def initWindow(self, *args):
        self.bt_nover.hide()
        #Add options to the QComboBox
        self.default_opciones = [self._option1, self._option2, self._option3]
        self.comboBox.addItems(self.default_opciones)
        self.setWindowTitle(self._header)

        #Get the geometry of the main window
        main_window_geo    = self.parent.geometry()
        main_window_x      = main_window_geo.x()
        main_window_y      = main_window_geo.y()
        main_window_width  = main_window_geo.width()
        main_window_height = main_window_geo.height()

        #Calculate position for child window
        width = 400
        height = 200
        new_x = main_window_x + (main_window_width - width) // 2
        new_y = main_window_y + 90

        #Set the geometry of the secondary window
        self.setGeometry(new_x, new_y, width, height)
        self.show()
    
    #Function to close the window
    def myclose(self, *args):
        self.finishSignal.emit()
        self.close()
    
    #Function to open select file dialog box
    def openFile(self, *args):
        fileNames, _ = QFileDialog.getOpenFileNames(self, self._open, '', f'{self._allowed} (*.csv *.xlsx)')
        if fileNames:
            self.file_path = fileNames
            #Modifying options in multiple selection mode
            if len(fileNames)>1:
                opciones = [self._option3]
            else:
                opciones = self.default_opciones
            self.comboBox.clear()
            self.comboBox.addItems(opciones)
    
    #Function to view the password
    def seePass(self, *args):
        self.bt_nover.show()
        self.bt_ver.hide()
        self.qle_password.setEchoMode(QLineEdit.EchoMode.Normal) 
    
    #Function to stop seeing the password
    def unseePass(self, *args):
        self.bt_ver.show()
        self.bt_nover.hide()
        self.qle_password.setEchoMode(QLineEdit.EchoMode.Password)
    
    #Upload to DB
    def toDB(self, *args):
        #Interrupting if null
        if not self.file_path:
            return

        #Getting the values ​​of each widget
        self.tabla = self.qle_tabla.text()
        self.username = getpass.getuser()
        self.psw = self.qle_password.text()
        self.dsn = self.parent.cfg_session.index.get('prede_dsn')
        self.hostname = self.parent.cfg_app.index.get('hostname')

        #Confirming that the route is valid as well as the table
        if os.path.exists(self.file_path[0]) and len(self.tabla) > 3 and '.' in self.tabla and len(self.psw)>=6:
            #Translating the comboBox
            combo_text = self.comboBox.currentText()
            if combo_text == self._option1:
                self.mode = 'overwrite'
            elif combo_text == self._option2:
                self.mode = 'error'
            elif combo_text == self._option3:
                self.mode = 'append'
            else:
                self.mode = 'ignore'

            #Running upload
            self.lbl_estado.setText(self._starting)
            self.uploadDB = UploadDB(self)
            self.uploadDB.update_status.connect(self.updateStatus)
            self.uploadDB.finished.connect(self.onFinished)
            self.uploadDB.error.connect(self.onError)
            self.uploadDB.start()
            self.timer.start(500)
        else:
            self.lbl_estado.setText(self._cmic)
    
    def onError(self, *args):
        self.timer.stop()
        self.lbl_estado.setText(self._endE)
        self.quit()
        self.deleteLater()
    
    def onFinished(self, *args):
        self.timer.stop()
        self.lbl_estado.setText(self._end)
        self.quit()
        self.deleteLater()
        
    def updateStatus(self, *args):
        if self.uploadDB.sp_created:
            if hasattr(self.uploadDB.sp.logger, 'df'):
                logger = self.uploadDB.sp.logger
                last_row = logger.df.iloc[-1][['i', self._state, self._time]].to_list() if not logger.df.empty else ['No data']
                self.lbl_estado.setText(', '.join(map(str, last_row)))

    #Click position grabber, this is global
    def mousePressEvent(self, event, *args):
        if event.button() == Qt.MouseButton.LeftButton:
            #Capturing the mouse position. Globally
            self.clickPosition = event.globalPosition().toPoint()
            #Identifying if there is a click
            if event.button() == Qt.MouseButton.LeftButton:
                    self.draggable = True
                    self.dragPosition = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)
        
        