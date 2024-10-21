#Importing native packages
import os, sys
import warnings, getpass
import pandas as pd

#Disabling pandas related warnings and untested DBAPI2 connection
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")
#Importing PyQt6 packages
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QApplication \
    , QMenu, QSystemTrayIcon, QFrame
from PyQt6.QtGui import QAction, QIcon, QKeySequence \
    , QShortcut, QGuiApplication
from PyQt6.QtCore import Qt , QPoint, QTimer, pyqtSignal
#Importing custom classes and methods
from MyPackages import YamlHandler, SessionHandler, ConnectionManager \
    , SQLAnalyzer, MyTitleBar
from MyPackages.utils import ai_methods, create_menus, ecosystem_methods \
    , execute_methods, plain_text_edit_methods, results_table_methods \
    , tabs_methods, window_methods

#===========================================
### Main (Execution in first thread)
#===========================================
class MainWindow(QMainWindow):
    #Signals
    firstConexionSignal = pyqtSignal()

    def tabChanged(self):
        #Terminating process if there is no active tab
        if not self.tabWidget:
            return None
        
        #Getting the name of the current tab
        tab_name = self.tabWidget.currentWidget().objectName
        tab_data = self.tab_info.get(tab_name)
        if tab_data:
            self.current_etl = tab_data['text_editor']
            self.current_param = tab_data['text_params']
            self.current_result = tab_data['result']

    def __init__(self):
        super().__init__()
        self.user = getpass.getuser()
        self.app = QApplication.instance()
        self.gui = QGuiApplication.instance()
        self.parentWindow = self.window()

        #Loading Settings
        #-----------------     
        self.version = YamlHandler("Settings/version.yaml")
        self.cfg_user = YamlHandler("Settings/config_user.yaml")
        self.cfg_app = YamlHandler("Settings/config_app.yaml")
        self.cfg_session = YamlHandler("Settings/config_session.yaml")
        self.syntax_list = YamlHandler("Settings/config_syntax_list.yaml")
        self.list_assist = YamlHandler("Settings/config_assistant.yaml")
        self.list_tmplts = YamlHandler("Settings/config_templates.yaml")
        self.autoComplete_list = YamlHandler("Settings/config_autocomplete_list.yaml")

        #Preparing language
        self.i18n = YamlHandler("Settings/config_i18n.yaml")
        self.lgg = "es"

        self.dict_styleSheets  = {}
        self.dict_styledSheets = {}
        self.prepareFramework()
        self.actualSession = SessionHandler(self)
        self.icon = QIcon('Guis/Resources/icon0.ico')
        self.icon1 = QIcon('Guis/Resources/icon1.ico')
        self.icon2 = QIcon('Guis/Resources/icon2.ico')
        self.icon3 = QIcon('Guis/Resources/icon3.ico')
        self.workerIcon1 = QIcon("Guis/Resources/working_1.png")
        self.workerIcon2 = QIcon("Guis/Resources/working_2.png")
        self.recIcon1 = QIcon("Guis/Resources/log1.png")
        self.recIcon2 = QIcon("Guis/Resources/log2.png")
        self.setWindowIcon(self.icon)

        #Loading styleSheets
        style_sheets_dir = 'Settings/StyleSheets'
        for filename in os.listdir(style_sheets_dir):
            if filename.endswith(".css"):
                #Getting file name without extension
                key = os.path.splitext(filename)[0]
                #Reading file content
                with open( os.path.join(style_sheets_dir, filename), 'r' ) as file:
                    self.dict_styleSheets[key] = file.read()

        #Defining variables and functions of the entire environment
        #---------------------------------------------------
        self.original_stdout = sys.stdout
        self.num_Stab = -1  #Class variable to identify editor tabs
        self.num_Rtab = 0  #Class variable to identify the results tabs

        self.result_tab_name = None
        self.syntax_highlighter_dict = {}
        self.list_Qtexts = []
        self.list_QTable = []
        self.dict_splitters = {'h':[] , 'v':[] }

        self.tab_info = {}
        self.searchWidget_dict = {}
        self.cursorIsWorking = False
        self.fetch = self.cfg_user.index.get("Fetch limit")

        #Rescaling Settings
        self.draggable = False
        self.drag_position = QPoint()
        self.onResizing = False
        self.resizing_edge = None

        #Setting timers
        #-------------------------------
        ##Setting the icon restore timer
        self.iconTimer = QTimer()
        self.iconTimer.setInterval(3000)
        self.iconTimer.timeout.connect(self.stopIconTimer)
        #Setting reconnection timer
        self.timerDsn = QTimer(self)
        self.timerDsn.timeout.connect(self.reconnectDsn)
        self.timerDsn.setInterval(1795*1000) #Value in milliseconds

        self.timerDsn.start()
        self.timerDsgs = QTimer(self)
        self.timerDsgs.timeout.connect(self.disguiseFrameOff)
        self.timerDsgs.setInterval(3000)
        #Setting worker animation timer
        self.animationTimer = QTimer(self)
        self.animationTimer.setInterval(250)
        self.animationTimer.timeout.connect(self.animationWorker)
        self.animationW_state = False
        #Setting Rec animation timer
        self.timerRec = QTimer(self)
        self.timerRec.setInterval(700)
        self.timerRec.timeout.connect(self.animationWorker)
        self.animationR_state = False
        self.recordingLog = False

        #================================================================== =============
        #Settings to create menu and system tray icon
        #================================================================== =============
        #Loading icon
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.icon)
        #Creating system tray menu
        trayMenu = QMenu()
        #Adding actions to menu
        stopEjec = QAction(self.i18n.getNested(self.lgg, "sql", "stop-run"), self)
        quitAction = QAction(self.i18n.getNested(self.lgg, "file", "close"), self)
        trayMenu.addAction(stopEjec)
        trayMenu.addAction(quitAction)
        ##Connect actions to corresponding methods
        stopEjec.triggered.connect(self.stopWorker)
        quitAction.triggered.connect(self.close)
        ##Set menu to system tray icon
        self.trayIcon.setContextMenu(trayMenu)
        ##Show icon in system tray
        self.trayIcon.show()

        #=================
        #Loading interface
        #=================
        #Loading GUI template
        uic.loadUi('Guis/MainWindow.ui', self)
        #Loading user default style
        internal_theme = self.cfg_session.index.get("internal_theme")
        self.styler(internal_theme)
        #Overriding internal general style (From users)
        self.tabWidget.setStyleSheet( self.dict_styledSheets["tab_styler"] )
        #Indicating the version
        version = "V" + str(self.version.index.get("version")) + " "*2
        self.lbl_version.setText(version)
        self.disguisiFrame()
        
        self.initWindow()
        #Opening GUI without the windows title bar
        self.setWindowFlags(Qt.WindowType.Window | 
                    Qt.WindowType.FramelessWindowHint | 
                    Qt.WindowType.WindowSystemMenuHint | 
                    Qt.WindowType.WindowMinMaxButtonsHint)
        self.setWindowOpacity(1)
        #Setting the resize option
        self.draggable = False
        self.drag_position = QPoint()
        self.onResizing = False
        self.grip_size = 8

        #----------------------------
        #Second thread connections
        #----------------------------
        #Connection with data source
        self.ConMan = ConnectionManager(self.cfg_session)
        self.ConMan.conManWorking.connect(self.connectingDSN)
        self.ConMan.conManFinished.connect(self.connectedDSN)
        self.firstConexionSignal.connect(self.downloadTree)
        #Connection with analyzer
        self.fluffAnalizer = SQLAnalyzer()
        self.fluffAnalizer.finished.connect(lambda: print("..."))
        #Connection with the worker
        ##Moved to executeM due to large

        #==================================================
        #Setting up my new title bar
        #==================================================
        #Replacing title bar
        original_fm = self.findChild(QFrame, 'fm_title')
        self.fm_title = MyTitleBar(self, menus=True)
        self.fm_title.setObjectName("fm_title")
        layout = original_fm.parentWidget().layout()
        layout.replaceWidget(original_fm, self.fm_title)      
        original_fm.deleteLater()
        #Creating menus and submenus
        self.createPMenu()

        self.fm_bar.setMouseTracking(True)
        self.fm_bar.mouseMoveEvent = self.mouseMoveEvent_fmBarra
        self.fm_principal.setMouseTracking(True)
        self.fm_principal.mouseMoveEvent = self.mouseMoveEvent_fmPrincipal

        self.click_label_count = 0
        self.fm_title.lbl_title.mousePressEvent = self.labelTitleClicked
             
        #=================================
        #Setting Qtabwidget
        #=================================
        #Setting Drops
        self.tabWidget.setAcceptDrops(True)
        self.tabWidget.dragEnterEvent = self.dragEnterEvent
        self.tabWidget.dropEvent = self.dropEvent
        #Setting movements between tabs
        self.scPreviousTab = QShortcut(QKeySequence("Ctrl+PageUp"), self)
        self.scPreviousTab.activated.connect(self.goPreviousTab)
        self.scNextTab = QShortcut(QKeySequence("Ctrl+PageDown"), self)
        self.scNextTab.activated.connect(self.goNextTab)

        #-----------------------------------
        #Various connections and definitions
        #-----------------------------------
        #Connection to close the tab
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.bt_connect.clicked.connect(self.ConMan.start)
        self.bt_working.clicked.connect(self.stopWorker)
        self.bt_log.clicked.connect(self.recLog)
        self.current_etl = None
        self.current_param = None
        self.current_result = None
        #Connections to detect screen changes
        self.app.screenRemoved.connect(self.onScreenRemoved)
        #Applying general styles
        self.setStyleSheet( self.dict_styleSheets["dark_theme"] )
        
        #-----------------------------------------------------------
        # Trying to restore the previous session or create a new one
        #-----------------------------------------------------------
        #Adding the ecosystem tab
        self.disguisiFrame()
        self.ecosystemTab()
  
        #Adding previous session
        if self.actualSession.sessionExists:
            cont = 0
            #Creating all tabs from the previous session
            for key in self.actualSession.session.keys():
                #Creating tab
                self.newScriptTab()
            #Loading information to the tab
            for key in self.tab_info.keys():
                #Obtaining the values ​​of the open session
                text_editor = self.actualSession.session.get(cont)["text_editor"]
                text_params = self.actualSession.session.get(cont)["text_params"]
                dict_paramsEtl = self.actualSession.session.get(cont)["dict_paramsEtl"]
                origin = self.actualSession.session.get(cont)['origin']
                data = self.actualSession.session.get(cont)["result_data"]
                #Adding values ​​in the newly created session
                self.tab_info.get(key)["text_editor"].setPlainText(text_editor)
                self.tab_info.get(key)["text_params"].setPlainText(text_params)
                self.tab_info.get(key)["dict_paramsEtl"] = dict_paramsEtl
                self.tab_info.get(key)['origin'] = origin
                self.tab_info.get(key)["result_data"] = data
                self.tab_info.get(key)["result"].loadData(pd.DataFrame(data))
                #Changing the tab name
                if origin != "":
                    nombre = origin.rsplit('/', 1)[-1]
                    self.tabWidget.setTabText(cont, nombre)
                #Following
                cont += 1
        else:
            self.newScriptTab()
        
        #---------------------------------
        #Showing window to the world
        #---------------------------------
        #Starting connection with data source
        self.ConMan.start()
        #Open window
        self.show()

        #------------------------------------------------
        #Connections related to the operating system
        #------------------------------------------------
        #Connecting the application screen change
        self.windowHandle().screenChanged.connect(self.onScreenChanged)
        self.actual_dpi = self.windowHandle().screen().physicalDotsPerInch()
        #Connecting application state change
        self.app.applicationStateChanged.connect(self.stateChanged)

#==================================================================
#Binding related functions to the main window
#==================================================================
MainWindow.updateTrayIcon = window_methods.updateTrayIcon
MainWindow.stopIconTimer = window_methods.stopIconTimer
MainWindow.dropEventParam = window_methods.dropEventParam

MainWindow.dragEnterEvent = window_methods.dragEnterEvent
MainWindow.dropEvent = window_methods.dropEvent
MainWindow.mousePressEvent = window_methods.mousePressEvent
MainWindow.mouseReleaseEvent = window_methods.mouseReleaseEvent
MainWindow.closeEvent = window_methods.closeEvent
MainWindow.leaveEvent = window_methods.leaveEvent

MainWindow.prepareFramework = window_methods.prepareFramework
MainWindow.prepareUrlsDrop = window_methods.prepareUrlsDrop
MainWindow.initWindow = window_methods.initWindow
MainWindow.onScreenChanged = window_methods.onScreenChanged
MainWindow.stateChanged = window_methods.stateChanged
MainWindow.panelizeFrame = window_methods.panelizeFrame
MainWindow.expandFrame = window_methods.expandFrame
MainWindow.darkenFrame = window_methods.darkenFrame
MainWindow.disguiseFrame = window_methods.disguiseFrame
MainWindow.disguisiFrame = window_methods.disguisiFrame
MainWindow.disguiseFrameOff = window_methods.disguiseFrameOff
MainWindow.lightenFrame = window_methods.lightenFrame
MainWindow.openDownloadsFolder = window_methods.openDownloadsFolder
MainWindow.getResizingEdge = window_methods.getResizingEdge
MainWindow.changeSizeWindow = window_methods.changeSizeWindow
MainWindow.mouseMoveEvent_fmBarra = window_methods.mouseMoveEvent_fmBarra
MainWindow.mouseMoveEvent_fmPrincipal = window_methods.mouseMoveEvent_fmPrincipal
MainWindow.showMenu = window_methods.showMenu
MainWindow.openFile = window_methods.openFile
MainWindow.openFileP = window_methods.openFileP
MainWindow.openBlockFiles = window_methods.openBlockFiles
MainWindow.openBlockFilesP = window_methods.openBlockFilesP
MainWindow.reloadETL = window_methods.reloadETL
MainWindow.saveFileAS = window_methods.saveFileAS
MainWindow.saveFilePAS = window_methods.saveFilePAS
MainWindow.showAcercaDe = window_methods.showAcercaDe
MainWindow.startUpdate = window_methods.startUpdate
MainWindow.labelTitleClicked = window_methods.labelTitleClicked
MainWindow.createPMenu = create_menus.createPMenu

MainWindow.onScreenRemoved = window_methods.onScreenRemoved

#==================================================================
#Binding functions related to the database structure
#==================================================================
MainWindow.downloadTree = ecosystem_methods.downloadTree
MainWindow.ecosystemTab = ecosystem_methods.ecosystemTab

#==================================================================
#Binding functions related to tabs in general
#==================================================================
MainWindow.closeTab = tabs_methods.closeTab
MainWindow.removeTabWidgets = tabs_methods.removeTabWidgets
MainWindow.removeWidgetsText = tabs_methods.removeWidgetsText
MainWindow.unsavedChanges = tabs_methods.unsavedChanges
MainWindow.showDialogSavingChanges = tabs_methods.showDialogSavingChanges
MainWindow.savingChanges = tabs_methods.savingChanges
MainWindow.savingChangesP = tabs_methods.savingChangesP
MainWindow.goPreviousTab = tabs_methods.goPreviousTab
MainWindow.goNextTab = tabs_methods.goNextTab

#==================================================================
#Binding functions related to the Scripts tabs (Editor and Param)
#==================================================================
MainWindow.newScriptTab = plain_text_edit_methods.newScriptTab
MainWindow.addParmScriptTab = plain_text_edit_methods.addParmScriptTab
MainWindow.styler = plain_text_edit_methods.styler
MainWindow.applyFontSize = plain_text_edit_methods.applyFontSize
MainWindow.applyEditorFont = plain_text_edit_methods.applyEditorFont
MainWindow.changeEtlFontSize = plain_text_edit_methods.changeEtlFontSize
MainWindow.captureThemeFormat = plain_text_edit_methods.captureThemeFormat
MainWindow.applyThemeFormat = plain_text_edit_methods.applyThemeFormat
MainWindow.applySplitH = plain_text_edit_methods.applySplitH
MainWindow.applySplitV = plain_text_edit_methods.applySplitV
MainWindow.paramSearcher = plain_text_edit_methods.paramSearcher
MainWindow.paramDefiner = plain_text_edit_methods.paramDefiner
MainWindow.updateTextParm = plain_text_edit_methods.updateTextParm
MainWindow.findSearched = plain_text_edit_methods.findSearched
MainWindow.replaceOne = plain_text_edit_methods.replaceOne
MainWindow.replaceAll = plain_text_edit_methods.replaceAll
MainWindow.searchText = plain_text_edit_methods.searchText
MainWindow.moveSearchWidget = plain_text_edit_methods.moveSearchWidget
MainWindow.closeSearchWidget = plain_text_edit_methods.closeSearchWidget
MainWindow.replaceText = plain_text_edit_methods.replaceText
MainWindow.commentText = plain_text_edit_methods.commentText
MainWindow.insertSuperComment = plain_text_edit_methods.insertSuperComment
MainWindow.specialFind = plain_text_edit_methods.specialFind
MainWindow.selectUpToPreviousQuery = plain_text_edit_methods.selectUpToPreviousQuery
MainWindow.selectUpToNextQuery = plain_text_edit_methods.selectUpToNextQuery
MainWindow.goToStartOfDocument = plain_text_edit_methods.goToStartOfDocument
MainWindow.goToEndOfDocument = plain_text_edit_methods.goToEndOfDocument
MainWindow.addNextOccurrence = plain_text_edit_methods.addNextOccurrence
MainWindow.addCursorsToLineBorders = plain_text_edit_methods.addCursorsToLineBorders
MainWindow.addCursorToAboveBelow = plain_text_edit_methods.addCursorToAboveBelow

#==================================================================
#Binding related functions to results tabs
#==================================================================
MainWindow.applyFontResult = results_table_methods.applyFontResult
MainWindow.changeFontSizeResult = results_table_methods.changeFontSizeResult

#==================================================================   
#Linking functions focused on the execution of one or several queries
#==================================================================
MainWindow.applySelectedDSN = execute_methods.applySelectedDSN
MainWindow.connectingDSN = execute_methods.connectingDSN
MainWindow.connectedDSN = execute_methods.connectedDSN
MainWindow.reconnectDsn = execute_methods.reconnectDsn

MainWindow.changeWordWrap = execute_methods.changeWordWrap
MainWindow.verifyConn = execute_methods.verifyConn
MainWindow.runQueries = execute_methods.runQueries
MainWindow.animationWorker = execute_methods.animationWorker
MainWindow.workerFinished = execute_methods.workerFinished
MainWindow.identifyQuery = execute_methods.identifyQuery
MainWindow.identifyTable = execute_methods.identifyTable
MainWindow.runShortTask = execute_methods.runShortTask
MainWindow.runLongTask = execute_methods.runLongTask
MainWindow.stopWorker = execute_methods.stopWorker
MainWindow.runAssist = execute_methods.runAssist
MainWindow.runTemplate = execute_methods.runTemplate
MainWindow.processHistory = execute_methods.processHistory
MainWindow.runQuery_to_file = execute_methods.runQuery_to_file
MainWindow.runFile_to_lz = execute_methods.runFile_to_lz
MainWindow.reportData = execute_methods.reportData
MainWindow.toFile = execute_methods.toFile
MainWindow.toFile_save = execute_methods.toFile_save
MainWindow.toFile_excelError = execute_methods.toFile_excelError
MainWindow.toFile_defaultSave = execute_methods.toFile_defaultSave
MainWindow.recLog = execute_methods.recLog

#================================================
#Linking AI-focused features
#================================================
MainWindow.aiQueryAnalizer = ai_methods.aiQueryAnalizer
MainWindow.sqlfluffAnalizer = ai_methods.sqlfluffAnalizer

