import os, sys, getpass
#from sparky_bc import Sparky

from contextlib import contextmanager
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QLineEdit
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

#=======================
### Upload to LZ widget
#=======================
#Helper class to run sparky in a separate thread
class UploadDBThread(QThread):
    update_status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal()

    def __init__(self, path, tabla, mode, username, psw, dsn, hostname):
        super().__init__()
        self.path = path
        self.tabla = tabla
        self.mode = mode
        #---
        self.username = username
        self.psw = psw
        self.dsn = dsn
        self.hostname = hostname
        self.logger = {}
        self.sp = None
        self.sp_created = False
        #---
        self.original_stdout = sys.stdout
        Sparky = None

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
        for path in self.path:
            try:
                self.sp.subir_csv(path=path, nombre_tabla=self.tabla, modo=self.mode)
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
    closeSignal = pyqtSignal()
    finishSignal = pyqtSignal()
    prosessSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi('Guis/UploadLZ.ui', self)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(1)
        self.bt_abrir.clicked.connect(self.openFile)
        self.bt_ver.clicked.connect(self.seePass)
        self.bt_nover.clicked.connect(self.unseePass)
        self.bt_subir.clicked.connect(self.toLZ)
        #Configuring window buttons
        self.bt_minimize.clicked.connect(lambda: self.showMinimized())
        self.bt_close.clicked.connect(self.myclose)
        self.fm_title.mouseMoveEvent = self.mouseMoveEvent
        self.fm_title.mouseClickEvent = self.mousePressEvent
        #Global variables
        self.file_path = ""
        self.logger = {}
        self.parent = parent
        self.cfg_user = parent.cfg_user
        self.cfg_session = parent.cfg_session

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateStatus)

        #Language
        nested = parent.i18n.getNested
        lgg = parent.lgg
        #Headers
        self._header = nested(lgg, "upload-to-db", "header")
        #Cls
        self._option1 = nested(lgg, "upload-to-db", "option1")
        self._option2 = nested(lgg, "upload-to-db", "option2")
        self._option3 = nested(lgg, "upload-to-db", "option3")
        #others
        self._starting = nested(lgg, "status-bar", "starting")
        self._open = nested(lgg, "open-file", "open2")
        self._allowed = nested(lgg, "open-file", "open4")
        self._end = nested(lgg, "status-bar", "end")
        self._endE = nested(lgg, "status-bar", "end-e")
        self._cmic = nested(lgg, "status-bar", "cmic")
        self._state = nested(lgg, "upload-to-db", "state")
        self._time = nested(lgg, "upload-to-db", "time")

        #Starting window
        self.initWindow()

    #Function to load some initial definitions
    def initWindow(self):
        self.bt_nover.hide()
        #Add options to the QComboBox
        self.default_opciones = [self._option1, self._option2, self._option3]
        self.comboBox.addItems(self.default_opciones)
        self.setWindowTitle(self._header)

        #Get the geometry of the main window
        main_window_geo = self.parent.geometry()
        main_window_x = main_window_geo.x()
        main_window_y = main_window_geo.y()
        main_window_width = main_window_geo.width()
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
    def myclose(self):
        self.finishSignal.emit()
        self.close()
    
    #Function to open select file dialog box
    def openFile(self):
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
    def seePass(self):
        self.bt_nover.show()
        self.bt_ver.hide()
        self.qle_password.setEchoMode(QLineEdit.Normal) 
    
    #Function to stop seeing the password
    def unseePass(self):
        self.bt_ver.show()
        self.bt_nover.hide()
        self.qle_password.setEchoMode(QLineEdit.Password)
    
    #Climb to the LIGHT
    def toLZ(self):
        #Getting the values ​​of each widget
        self.tabla = self.qle_tabla.text()
        self.username = getpass.getuser()
        self.psw = self.qle_password.text()
        self.dsn = self.cfg_session.index.get("prede_dsn")
        self.hostname = self.cfg_user.index.get("HOSTNAME")

        #Confirming that the route is valid as well as the table
        if os.path.exists(self.file_path[0]) and len(self.tabla) > 3 and "." in self.tabla and len(self.psw)>=6:
            #Translating the comboBox
            combo_text = self.comboBox.currentText()
            if combo_text == self._option1:
                self.mode = "overwrite"
            elif combo_text == self._option2:
                self.mode = "error"
            elif combo_text == self._option3:
                self.mode = "append"
            else:
                self.mode = "ignore"

            #Running upload
            self.lbl_estado.setText(self._starting)
            self.thread = UploadDBThread(self.file_path, self.tabla, self.mode
                                        , self.username, self.psw, self.dsn, self.hostname)
            self.thread.update_status.connect(self.updateStatus)
            self.thread.finished.connect(self.onFinished)
            self.thread.error.connect(self.onError)
            self.thread.start()
            self.timer.start(500)
        else:
            self.lbl_estado.setText(self._cmic)
    
    def onError(self):
        self.timer.stop()
        self.lbl_estado.setText(self._endE)
    
    def onFinished(self):
        self.timer.stop()
        self.lbl_estado.setText(self._end)

    def updateStatus(self):
        if self.thread.sp_created:
            if hasattr(self.thread.sp.logger, 'df'):
                logger = self.thread.sp.logger
                last_row = logger.df.iloc[-1][["i", self._state, self._time]].to_list() if not logger.df.empty else ["No data"]
                self.lbl_estado.setText(", ".join(map(str, last_row)))
                #status_text = f"{str(logger.info)}\n{str(logger.warning)}\n{str(logger.error)}\n{str(logger.critical)}"
                #self.lbl_status.setText( self.status_text )

    #Function to move the window
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self.click_position:
                self.move(self.pos() + event.globalPosition().toPoint() - self.click_position)
                self.click_position = event.globalPosition().toPoint()
                event.accept()
        super().mouseMoveEvent(event)

    #Click position grabber, this is global
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            #Capturing the mouse position. Globally
            self.click_position = event.globalPosition().toPoint()
            #Identifying if there is a click
            if event.button() == Qt.MouseButton.LeftButton:
                    self.draggable = True
                    self.drag_position = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)
        
        