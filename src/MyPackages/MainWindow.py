#Importing native packages
import os, sys, getpass, ctypes, shutil, subprocess
import polars as pl
from datetime import datetime
from pathlib import Path
#Importing log packages
import logging
from logging.handlers import RotatingFileHandler
#Importing PyQt6 packages
from PyQt6 import uic
from PyQt6.QtWidgets import (QMainWindow, QApplication
    , QMenu, QSystemTrayIcon, QFrame)
from PyQt6.QtGui import (QAction, QIcon, QGuiApplication)
from PyQt6.QtCore import (Qt , QPoint, QTimer, pyqtSignal
                          , QEvent, QThread)
#Importing custom classes and methods
from MyPackages import (YamlHandler, SessionHandler, AsyncExecute
    , AsyncConnectionManager, MyTitleBar, CssHandler
    , AsynTree, AsyncEditor) #SQLAnalyzer
from MyPackages.utils import (ai_methods, create_menus, set_shortcuts
    , ecosystem_methods, execute_methods, plain_text_edit_methods
    , results_table_methods, tabs_methods, window_methods)

#===========================================
### Main (Execution in first thread)
#===========================================
class MainWindow(QMainWindow):
    """
    Main application window for the Luck SQL editor, managing tabs, themes, sessions, and database connections.

    Signals:
        firstConexionSignal (): Emitted when the first connection is established.
        splitHChanged (int): Emitted when the horizontal splitter changes.
        splitVChanged (int): Emitted when the vertical splitter changes.
        sendTextEditor (object, str): Emitted to send the text editor and its content.

    Attributes:
        updating_splits (bool): Flag for updating splitters.
        updating_paramsParentheses (bool): Flag for updating parameter parentheses.
        tabInfo (dict): Information about each tab.
        current_tabName (str): Name of the current tab.
        current_etlEditor (object): Reference to the current text editor.
        current_pManager (object): Reference to the current parameter manager.
        current_paramsEtl (dict): Current ETL parameters.
        current_result (object): Current result object.
        current_fetched (bool): Whether the current result is fetched.
        dict_MySearchWidget (dict): Dictionary of search widgets.
        lgg (str): Current language code.
        theme (str): Current theme name.
        internalProfile (str): Current profile name.
        dict_languages (dict): Loaded language dictionaries.
        dict_profiles (dict): Loaded profile dictionaries.
        dict_themeSheets (dict): Loaded theme CSS handlers.
        dict_styleSheets (dict): Loaded widget style sheets.
        dict_styledSheets (dict): Formatted style sheets.
        dict_paths (dict): Various file paths.
        re_parameters (str): Regex for parameters.
        user (str): Current username.
        app (QApplication): Application instance.
        gui (QGuiApplication): GUI application instance.
        parentWindow (QWidget): Reference to the parent window.
        version (YamlHandler): Version configuration handler.
        cfg_app (YamlHandler): App configuration handler.
        cfg_session (YamlHandler): Session configuration handler.
        cfg_shortcut (YamlHandler): Shortcut configuration handler.
        syntaxList (YamlHandler): Syntax list handler.
        list_assist (YamlHandler): Assistant list handler.
        list_tmplts (YamlHandler): Templates list handler.
        autoCompleteList (YamlHandler): Autocomplete list handler.
        i18nNes (callable): Internationalization function.
        shc (callable): Shortcut getter.
        prepareFramework (callable): Framework preparation method.
        actualSession (SessionHandler): Session handler.
        icon, icon1, icon2, icon3 (QIcon): Application icons.
        excWorkerIcon1, excWorkerIcon2 (QIcon): Execution worker icons.
        recIcon1, recIcon2 (QIcon): Recording icons.
        baseSetterIcon, baseUnSetterIcon (QIcon): Base setter icons.
        unsavedTab (QIcon): Unsaved tab icon.
        globalTheme (str): Name of the global theme.
        original_stdout (object): Original stdout for redirection.
        num_Stab (int): Counter for editor tabs.
        num_Rtab (int): Counter for result tabs.
        cursorIsWorking (bool): Flag for cursor working state.
        fetch (int): Fetch limit for queries.
        draggable (bool): Window draggable flag.
        dragPosition (QPoint): Position for dragging.
        onResizing (bool): Window resizing flag.
        resizing_edge (object): Edge for resizing.
        iconTimer (QTimer): Timer for restoring icon.
        timerDsn (QTimer): Timer for DSN reconnection.
        timerDsgs (QTimer): Timer for disguise frame off.
        animationTimer (QTimer): Timer for execution worker animation.
        animationW_state (bool): State for execution worker animation.
        timerRec (QTimer): Timer for recording animation.
        animationR_state (bool): State for recording animation.
        recordingLog (bool): Flag for recording log.
        trayIcon (QSystemTrayIcon): System tray icon.
        fm_title (MyTitleBar): Custom title bar.
        clickLabelCount (int): Counter for title label clicks.

    Methods:
        __init__(self): Initializes the main window, loads settings, themes, and sets up the UI.
        restartApp(self): Restarts the application.
        tabChanged(self, index:int=0): Updates references and status bar when the tab changes.
        changeEvent(self, event): Handles window state changes.
        ... (many methods are dynamically bound at the end of the file)
    """

    #Paths
    #--------------------------
    baseDir        = None
    UserDataDir    = None
    guisPath       = None
    i18nPath       = None
    stylesPath     = None

    #LogFile
    #---------------------------
    log_file       = None
        
    #Signals
    #--------------------------
    firstConexionSignal = pyqtSignal()
    splitHChanged  = pyqtSignal(int)
    splitVChanged  = pyqtSignal(int)
    sendTextEditor = pyqtSignal(object, str)

    #Flags
    #--------------------------
    updating_splits = False
    updating_paramsParentheses = False

    #Slots
    #--------------------------
    #Metadata of all taps
    tabInfoTemplate = {
          'text_editor'    : None #Widget reference
        , 'params_manager' : None #Widget reference
        , 'result'         : None #Widget reference
        , 'saved'          : True
        , 'dict_paramsEtl' : {}
        , 'origin'         : ''
        , 'origin_param'   : ''
        , 'result_data'    : {}
        , 'rType'          : 'base' #('base', 'status', 'results')
        , 'fetched'        : False
    }
    tabInfo = {}

    #Reference current tab
    current_tabName   = None
    current_etlEditor = None
    current_pManager  = None
    current_paramsEtl = {}
    current_result    = {}
    current_fetched   = False

    #secont thread functions
    #-------------------------

    #List of object styleables
    dict_MySearchWidget = {}
    
    #Languages, styles or themes
    lgg               = None
    theme             = None
    internalProfile   = None
    dict_languages    = {}
    dict_profiles     = {}
    dict_themeSheets  = {}
    dict_styleSheets  = {} #Original
    dict_styledSheets = {} #Formated with styler()

    #Paths
    dict_paths        = {}

    #Definitions
    #--------------------------
    re_parameters = r'\{([^\n{}]*)\}'

    #Launch a new process with the same arguments
    def restartApp(self):
        subprocess.Popen([sys.executable] + sys.argv)
        QApplication.exit(0)
    
    #Binding Current Tab
    def bindCurrentTab(self):
        tab_name = self.tabWidget.currentWidget().objectName
        tab_data = self.tabInfo.get(tab_name)
        if not tab_data:
            return

        self.current_tabName   = tab_name
        self.current_etlEditor = tab_data['text_editor']
        self.current_pManager  = tab_data['params_manager']
        self.current_paramsEtl = tab_data['dict_paramsEtl']
        self.current_result    = tab_data['result']
        self.current_rType     = tab_data['rType']
        self.current_fetched   = tab_data['fetched']
      
    #Function to update current references
    def tabChanged(self, index:int=0):
        #Terminating process if there is no active tab
        if not self.tabWidget:
            return None

        #Default value
        tl_1, tl_2, tl_3 = self.profile['result-trafficlight']
        
        #Binding Current Tab
        self.bindCurrentTab()
        #Updating tab icons
        self.updateTabIcons()
        
        #Modifying status bar
        #--------------------------
        #Status bar
        self.lbl_status.setText(self.i18nNes('status-bar', 'end'))
        #Fetch info
        if self.current_fetched:
            self.bt_fetch.setText(self.i18nNes('status-bar', 'fetched'))
        else:
            self.bt_fetch.setText(self.i18nNes('status-bar', 'no-fetched'))
        #Result info
        result = self.current_result
        _rows, _cols = self.i18nNes('status-bar', 'rows-cols')
        rows, cols = result.model.ResultDF.shape if result else (0, 0)
        rows = f'>{rows:,}' if self.current_fetched else f'{rows:,}'
        rowsCols = f'{_rows}: {rows}, {_cols}: {cols:,}'
        self.bt_rowsCols.setText(rowsCols)
        #Spaces
        label = f"{self.i18nNes('status-bar', 'spaces')}: {int(self.cfg_session.index.get('tab-spaces')):,}"
        self.bt_spaces.setText(label)

        if self.current_etlEditor:
            #Total lines
            _lines = self.i18nNes('status-bar', 'lines')
            count = self.current_etlEditor.blockCount()
            self.bt_totalLines.setText(f'{_lines}: {count:,}')
            #Lines and blocks
            _line, _block = self.i18nNes('status-bar', 'line-block')
            self.bt_lineBlock.setText(
                f'{_line}: {self.current_etlEditor.textCursor().blockNumber()+1}, {_block}: {self.current_etlEditor.textCursor().columnNumber()+1}'
            )
        
        #Emphasizing the fetch
        if self.current_fetched:
            self.bt_fetch.setStyleSheet(f'QPushButton{{ background-color: {tl_2}; }}')
        else:
            self.bt_fetch.setStyleSheet(f'QPushButton{{ background-color: transparent; }}')

    #System function that is activated when there is a change in the window
    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            if hasattr(self, 'MyTitleBar'):
                self.MyTitleBar.updateMaximizeRestoreButtons()
        
    def __init__(self, baseDir, UserDataDir):
        super().__init__()
        self.user = getpass.getuser()
        self.app  = QApplication.instance()
        self.gui  = QGuiApplication.instance()
        self.parentWindow   = self.window()

        #Defining initial paths
        self.baseDir        = baseDir
        self.UserDataDir    = UserDataDir
        self.guisPath       = self.baseDir / 'Guis'
        self.i18nPath       = self.baseDir / 'i18n'
        self.stylesPath     = self.baseDir / 'Styles'
        
        #Initial message
        logging.info(f"Main workspace window initializing")

        #Loading Settings
        #----------------
        self.version          = YamlHandler(str(self.UserDataDir / 'Settings' / 'version.yaml'))
        self.cfg_app          = YamlHandler(str(self.UserDataDir / 'Settings' / 'config_app.yaml'))
        self.cfg_session      = YamlHandler(str(self.UserDataDir / 'Settings' / 'config_session.yaml'))
        self.cfg_shortcut     = YamlHandler(str(self.UserDataDir / 'Settings' / 'config_shortcut.yaml'))
        self.syntaxList       = YamlHandler(str(self.UserDataDir / 'Settings' / 'config_syntax_list.yaml'))
        self.list_assist      = YamlHandler(str(self.UserDataDir / 'Settings' / 'config_assistant.yaml'))
        self.list_tmplts      = YamlHandler(str(self.UserDataDir / 'Settings' / 'config_templates.yaml'))
        self.autoCompleteList = YamlHandler(str(self.UserDataDir / 'Settings' / 'config_autocomplete_list.yaml'))

        #Adding resource path to cfg_app dictionary
        self.cfg_app.index['resourcesPath'] = str(self.guisPath / 'Resources').replace('\\', '/')

        #Loading language
        for filename in os.listdir(str(self.baseDir / 'i18n')):
            if filename.endswith('.yaml'):
                #Getting file name without extension
                key = os.path.splitext(filename)[0]
                #Reading file content
                self.dict_languages[key] = YamlHandler(str(self.baseDir / 'i18n' / filename)).index
        
        #Loading profiles
        for filename in os.listdir(str(self.baseDir / 'Styles' / 'profiles')):
            if filename.endswith('.yaml'):
                #Getting file name without extension
                key = os.path.splitext(filename)[0]
                #Reading file content
                self.dict_profiles[key] = YamlHandler(str(self.baseDir / 'Styles' / 'profiles' / filename)).index
        
        #Preparing language
        self.lgg = self.cfg_session.index.get('language', 'en-US')
        i18n = YamlHandler(str(self.baseDir / 'i18n' / f'{self.lgg}.yaml'))
        self.i18nNes = i18n.getNested
        #Preparing shurtcuts
        self.shc = self.cfg_shortcut.getNested
        self.prepareFramework()
        self.actualSession    = SessionHandler(self)
        self.icon             = QIcon(str(self.guisPath / 'Resources' / 'icon0.ico'))
        self.icon1            = QIcon(str(self.guisPath / 'Resources' / 'icon1.ico'))
        self.icon2            = QIcon(str(self.guisPath / 'Resources' / 'icon2.ico'))
        self.icon3            = QIcon(str(self.guisPath / 'Resources' / 'icon3.ico'))
        self.excWorkerIcon1   = QIcon(str(self.guisPath / 'Resources' / 'working-1.png'))
        self.excWorkerIcon2   = QIcon(str(self.guisPath / 'Resources' / 'working-2.png'))
        self.recIcon1         = QIcon(str(self.guisPath / 'Resources' / 'log1.png'))
        self.recIcon2         = QIcon(str(self.guisPath / 'Resources' / 'log2.png'))
        self.baseSetterIcon   = QIcon(str(self.guisPath / 'Resources' / 'baseSetter.png'))
        self.baseUnSetterIcon = QIcon(str(self.guisPath / 'Resources' / 'baseUnSetter.png'))
        self.unsavedTab       = QIcon(str(self.guisPath / 'Resources' / 'close-tab5.png'))
        self.setWindowIcon(self.icon)

        #Loading themes
        ##In each theme comes a set of css variables
        for filename in os.listdir(str(self.stylesPath / 'themes')):
            if filename.endswith('.css'):
                #Getting file name without extension
                key = os.path.splitext(filename)[0]
                #Reading file content
                path = str(self.stylesPath / 'themes' / filename)
                self.dict_themeSheets[key] = CssHandler(path, **self.cfg_app.index)
        
        #Loading the variables of the predetermined theme to apply on widgets
        self.globalTheme = self.cfg_session.index.get('global_theme', 'dark')
        cssVariables = self.dict_themeSheets[self.globalTheme].variables

        #Loading styleSheets
        for filename in os.listdir(str(self.stylesPath / 'widgets')):
            if filename.endswith('.css'):
                #Getting file name without extension
                key = os.path.splitext(filename)[0]
                #Establishing definitive path
                path = str(self.stylesPath / 'widgets' / filename)
                #Loading raw css
                css = CssHandler(path)
                #Loading predefined variables
                css.variables = cssVariables
                #Reading file content
                css.render()
                #Keeping the rendering CSS
                self.dict_styleSheets[key] = css.rendered
        
        #Defining variables and functions of the entire environment
        #---------------------------------------------------
        self.original_stdout = sys.stdout
        self.num_Stab = -1  #Class variable to identify editor tabs
        self.num_Rtab = 0   #Class variable to identify the results tabs

        self.cursorIsWorking = False
        self.fetch = self.cfg_session.index.get('fetch-limit', 1000)
        
        #Rescaling Settings
        self.draggable     = False
        self.dragPosition  = QPoint()
        self.onResizing    = False
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
        #Setting excWorker animation timer
        self.animationTimer = QTimer(self)
        self.animationTimer.setInterval(250)
        self.animationTimer.timeout.connect(self.animationExcWorker)
        self.animationW_state = False
        #Setting Rec animation timer
        self.timerRec = QTimer(self)
        self.timerRec.setInterval(700)
        self.timerRec.timeout.connect(self.animationRec)
        self.animationR_state = False
        self.recordingLog = False

        #==================================================================
        #Settings to create menu and system tray icon
        #==================================================================
        #Loading icon
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.icon)
        #Creating system tray menu
        trayMenu = QMenu()
        #Adding actions to menu
        stopExec   = QAction(self.i18nNes('sql', 'stop-run'), self)
        quitAction = QAction(self.i18nNes('file', 'close'), self)
        trayMenu.addAction(stopExec)
        trayMenu.addAction(quitAction)
        ##Connect actions to corresponding methods
        stopExec.triggered.connect(self.stopExcWorker)
        quitAction.triggered.connect(self.close)
        ##Set menu to system tray icon
        self.trayIcon.setContextMenu(trayMenu)
        ##Show icon in system tray
        self.trayIcon.show()

        #=================
        #Loading interface
        #=================
        #Loading GUI template
        uic.loadUi(str(self.guisPath / 'MainWindow.ui'), self)
        #Loading user default style
        self.internalProfile = self.cfg_session.index.get('internal_profile')
        self.profile         = self.dict_profiles[self.internalProfile]
        self.styler(self.internalProfile)

        #Overriding internal general style (From users)
        self.tabWidget.setStyleSheet( self.dict_styledSheets['QTabWidget'] )
        self.tabWidget.setElideMode(Qt.TextElideMode.ElideMiddle)
        #Indicating the version
        version = 'V' + str(self.version.index.get('version')) + ' '*2
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
        self.dragPosition = QPoint()
        self.onResizing = False
        self.grip_size = 8

        #----------------------------
        #Second thread connections
        #----------------------------
        #connection with excute worker
        self.conn = None
        self.asyncExecute = AsyncExecute(None, self)
        self.asyncExecute.status.connect(self.reportData)
        self.asyncExecute.inProcess.connect(self.processHistory)
        self.asyncExecute.recInLog.connect(self.reportLog)
        self.asyncExecute.finished.connect(self.endAsyncExecute)
        self.asyncExecute.toFile.connect(self.toFile)
    
        #Connection with data source
        self.asyncConnMan = AsyncConnectionManager(self)
        self.asyncConnMan.conManWorking.connect(self.connectingDSN)
        self.asyncConnMan.conManFinished.connect(self.connectedDSN)
        self.firstConexionSignal.connect(self.downloadTree)
        
        #Connecting with tree updater
        self.asynTree = AsynTree(self)
        self.asynTree.asynTreeFinished.connect(self.endAsynTree)
        
        #Connection with analyzer


        #Second thread for editor
        #---------------------------
        self.editorThread = QThread()
        self.asyncEditor = AsyncEditor(self)
        self.asyncEditor.moveToThread(self.editorThread)
        
        #Connections
        self.sendTextEditor.connect(self.asyncEditor.processTextEditor)
        self.asyncEditor.finished.connect(self.paintParentheses)
        self.editorThread.start()

        #==================================================
        #Setting up my new title bar
        #==================================================
        #Replacing title bar
        original_fm = self.findChild(QFrame, 'fm_title')
        self.fm_title = MyTitleBar(self, menus=True)
        self.fm_title.setObjectName('fm_title')
        layout = original_fm.parentWidget().layout()
        layout.replaceWidget(original_fm, self.fm_title)      
        original_fm.deleteLater()
        #Creating menus and submenus
        self.createPMenu()
        #Setting shortcuts
        self.setShortcuts()


        self.fm_bar.setMouseTracking(True)
        self.fm_bar.mouseMoveEvent = self.mouseMoveEvent_fmBarra
        self.fm_principal.setMouseTracking(True)
        self.fm_principal.mouseMoveEvent = self.mouseMoveEvent_fmPrincipal

        self.clickLabelCount = 0
        self.fm_title.lbl_title.mousePressEvent = self.labelTitleClicked

        #==================================================
        #Setting up my status bar
        #==================================================
        #Setting the various tooltips of the status bar
        #Conectar reconectar
        self.bt_connect.setToolTip(self.i18nNes('tooltips', 'sb1'))
        self.bt_working.setToolTip(self.i18nNes('tooltips', 'sb2'))
        self.bt_log.setToolTip(self.i18nNes('tooltips', 'sb3'))
        self.lbl_status.setToolTip(self.i18nNes('tooltips', 'sb5'))
        self.bt_totalLines.setToolTip(self.i18nNes('tooltips', 'sb6'))
        self.bt_lineBlock.setToolTip(self.i18nNes('tooltips', 'sb7'))
        self.bt_spaces.setToolTip(self.i18nNes('tooltips', 'sb8'))
        self.bt_rowsCols.setToolTip(self.i18nNes('tooltips', 'sb9'))
        self.bt_fetch.setToolTip(self.i18nNes('tooltips', 'sb10'))
        self.lbl_version.setToolTip(self.i18nNes('tooltips', 'sb11'))
        
        #=================================
        #Setting Qtabwidget
        #=================================
        #Setting Drops
        self.tabWidget.setAcceptDrops(True)
        self.tabWidget.dragEnterEvent = self.dragEnterEvent
        self.tabWidget.dropEvent = self.dropEvent

        #-----------------------------------
        #Various connections and definitions
        #-----------------------------------
        #Connection to close the tab
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.tabWidget.currentChanged.connect(self.tabChanged)
        #Bottons
        self.bt_connect.clicked.connect(self.asyncConnMan.start)
        self.bt_working.clicked.connect(self.stopExcWorker)
        self.bt_log.clicked.connect(self.recLog)
        self.bt_lineBlock.clicked.connect(self.goToLineBlock)
        self.bt_spaces.clicked.connect(self.changeSpacePerTab)
        self.bt_fetch.clicked.connect(self.changeFetch)

        #Applying general styles
        self.setStyleSheet( self.dict_themeSheets[self.globalTheme].rendered )       
        
        #-----------------------------------------------------------
        # Trying to restore the previous session or create a new one
        #-----------------------------------------------------------
        #Adding the ecosystem tab
        self.disguisiFrame()
        self.ecosystemTab()
        lag = self.tabWidget.count()
        #Adding previous session
        if self.actualSession.sessionExists:
            #Creating all tabs from the previous session without info yet
            for key in self.actualSession.session.keys():
                #Omitting the 'version' key
                if key == 'version':
                    continue
                #Creating tab
                self.newScriptTab()

            #Loading information to the tab
            ##Moving in each of the created tabs
            for count, widgetName in enumerate(self.tabInfo.keys()):
                tab_data = self.tabInfo[widgetName]
                session_data = self.actualSession.session.get(count)
        
                ##Moving inside each key of its corresponding tabdata
                for key in tab_data.keys():
                    #Exceptions because they are references to current widgets
                    #1. They are references to widgets or redundants.
                    if key in ('params_manager'):
                        None
                    
                    #2. Loading the text in the editor reference
                    elif key == 'text_editor':
                        tab_data[key].setPlainText(session_data[key])
                    
                    #3. Cargando resultados en memoria
                    elif key == 'result':
                        _result = pl.DataFrame(session_data['result_data'])
                        _rType  = session_data['rType']
                        tab_data[key].loadData(_result, _rType)

                    #4. Loading all data that shares the same key and does not need special treatment
                    else:
                        #Restore all other values
                        tab_data[key] = session_data[key]

                #Updating current references
                self.bindCurrentTab()

                #Updating tab toolTips
                self.updateTabTooltips()
                #Updating tab icons
                self.updateTabIcons()

                #Updating the parameter manager
                self.updatePManager()
                #Change the tab name if applicable
                origin = tab_data['origin']
                if origin:
                    name = origin.rsplit('/', 1)[-1]
                    self.tabWidget.setTabText(count + lag, name)
                  
            #If the size is 1 then there are no tabs, only the version info
            if len(self.actualSession.session.keys()) == 1:
                self.newScriptTab()
        else:
            self.newScriptTab()
        
        #Restoring last state of Basetter
        if self.cfg_session.index.get('baseSetter', False):
            self.baseSetter(None)
        
        #---------------------------------
        #Showing window to the world
        #---------------------------------
        #Open window
        self.show()
        self.tabChanged()
        logging.info(f"Main workspace window initialized successfully.")
        #Starting connection with data source
        self.asyncConnMan.start()

#==================================================================
#Binding related functions to the main window
#==================================================================
MainWindow.createCustomCloseButton = window_methods.createCustomCloseButton
MainWindow.updateTabTooltips = window_methods.updateTabTooltips
MainWindow.updateTabIcons = window_methods.updateTabIcons
MainWindow.onTabCloseClicked = window_methods.onTabCloseClicked

MainWindow.buildTabTooltip = window_methods.buildTabTooltip
MainWindow.applySelectedLanguage = window_methods.applySelectedLanguage
MainWindow.styler = window_methods.styler
MainWindow.captureProfileFormat = window_methods.captureProfileFormat
MainWindow.applyProfileFormat = window_methods.applyProfileFormat

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
MainWindow.syncSplitterH = window_methods.syncSplitterH
MainWindow.syncSplitterV = window_methods.syncSplitterV
MainWindow.saveEcoSplittersSizes = window_methods.saveEcoSplittersSizes
MainWindow.panelizeFrame = window_methods.panelizeFrame
MainWindow.expandFrame = window_methods.expandFrame
MainWindow.darkenFrame = window_methods.darkenFrame
MainWindow.baseSetter = window_methods.baseSetter
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
MainWindow.saveFileAs = window_methods.saveFileAs
MainWindow.saveFilePAs = window_methods.saveFilePAs
MainWindow.showAcercaDe = window_methods.showAcercaDe
MainWindow.startUpdate = window_methods.startUpdate
MainWindow.labelTitleClicked = window_methods.labelTitleClicked
MainWindow.createPMenu = create_menus.createPMenu
MainWindow.setShortcuts = set_shortcuts.setShortcuts

#==================================================================
#Binding functions related to the database structure
#==================================================================
MainWindow.downloadTree = ecosystem_methods.downloadTree
MainWindow.ecosystemTab = ecosystem_methods.ecosystemTab
MainWindow.endAsynTree = ecosystem_methods.endAsynTree

#==================================================================
#Binding functions related to tabs in general
#==================================================================
MainWindow.closeTab = tabs_methods.closeTab
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
MainWindow.addParamToManager = plain_text_edit_methods.addParamToManager
MainWindow.applyFontSize = plain_text_edit_methods.applyFontSize
MainWindow.applyEditorFont = plain_text_edit_methods.applyEditorFont
MainWindow.changeEtlFontSize = plain_text_edit_methods.changeEtlFontSize
MainWindow.changeSpacePerTab = plain_text_edit_methods.changeSpacePerTab
MainWindow.goToLineBlock = plain_text_edit_methods.goToLineBlock
MainWindow.findSpecialEntries = plain_text_edit_methods.findSpecialEntries
MainWindow.paintParentheses = plain_text_edit_methods.paintParentheses
MainWindow.paramSearcher = plain_text_edit_methods.paramSearcher
MainWindow.paramDefiner = plain_text_edit_methods.paramDefiner
MainWindow.updatePManager = plain_text_edit_methods.updatePManager
MainWindow.findSearched = plain_text_edit_methods.findSearched
MainWindow.replaceOne = plain_text_edit_methods.replaceOne
MainWindow.replaceAll = plain_text_edit_methods.replaceAll
MainWindow.searchText = plain_text_edit_methods.searchText
MainWindow.moveMySearchWidget = plain_text_edit_methods.moveMySearchWidget
MainWindow.closeMySearchWidget = plain_text_edit_methods.closeMySearchWidget
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
MainWindow.changeFetch = results_table_methods.changeFetch

#==================================================================   
#Linking functions focused on the execution of one or several queries
#==================================================================
MainWindow.getFullUsername = execute_methods.getFullUsername
MainWindow.applySelectedDSN = execute_methods.applySelectedDSN
MainWindow.connectingDSN = execute_methods.connectingDSN
MainWindow.connectedDSN = execute_methods.connectedDSN
MainWindow.reconnectDsn = execute_methods.reconnectDsn
MainWindow.endAsyncExecute = execute_methods.endAsyncExecute

MainWindow.changeWordWrap = execute_methods.changeWordWrap
MainWindow.verifyConn = execute_methods.verifyConn
MainWindow.animationExcWorker = execute_methods.animationExcWorker
MainWindow.animationRec = execute_methods.animationRec
MainWindow.cleanQ = execute_methods.cleanQ
MainWindow.verifyFilterParams = execute_methods.verifyFilterParams
MainWindow.identifyQuery = execute_methods.identifyQuery
MainWindow.identifyTable = execute_methods.identifyTable
MainWindow.runShortTask = execute_methods.runShortTask
MainWindow.runLongTask = execute_methods.runLongTask
MainWindow.runLongTaskSelected = execute_methods.runLongTaskSelected
MainWindow.runLongTaskAbove = execute_methods.runLongTaskAbove
MainWindow.runLongTaskBelow = execute_methods.runLongTaskBelow
MainWindow.runQueries = execute_methods.runQueries
MainWindow.stopExcWorker = execute_methods.stopExcWorker
MainWindow.runAssist = execute_methods.runAssist
MainWindow.runTemplate = execute_methods.runTemplate
MainWindow.processHistory = execute_methods.processHistory
MainWindow.saveResult = execute_methods.saveResult
MainWindow.saveResultAs = execute_methods.saveResultAs
MainWindow.runFile_to_lz = execute_methods.runFile_to_lz
MainWindow.reportData = execute_methods.reportData
MainWindow.reportLog = execute_methods.reportLog
MainWindow.toFile = execute_methods.toFile
MainWindow.toFile_save = execute_methods.toFile_save
MainWindow.toFile_excelError = execute_methods.toFile_excelError
MainWindow.toFile_defaultSave = execute_methods.toFile_defaultSave
MainWindow.recLog = execute_methods.recLog

#================================================
#Linking AI-focused features
#================================================
