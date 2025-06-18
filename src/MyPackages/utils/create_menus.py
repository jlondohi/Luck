import pyodbc
from functools import partial
#Importing PyQt6 packages
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence

#===========================================================
#Creating menus and submenus of the main window
#===========================================================
def createPMenu(self):
    #Instantiating language
    nested = self.i18n.getNested

    #1. Creating all actions
    #-----------------------
    #File menu actions
    self.actionNew = QAction(nested("file", "new"), self)
    self.actionOpen = QAction(nested("file", "open"), self)
    self.actionOpenBlock = QAction(nested("file", "open-block"), self)
    self.actionReload = QAction(nested("file", "reload"), self)
    self.actionSave = QAction(nested("file", "save"), self)
    self.actionSaveAs = QAction(nested("file", "save-as"), self)
    self.actionOpenP = QAction(nested("file", "open-param"), self)
    self.actionOpenBlockP = QAction(nested("file", "open-param-block"), self)
    self.actionSaveP = QAction(nested("file", "save-param"), self)
    self.actionSaveAsP = QAction(nested("file", "save-param-as"), self)
    
    #Edit Menu Actions
    self.actionSearch = QAction(nested("edit", "search"), self)
    self.actionReplace = QAction(nested("edit", "replace"), self)
    self.actionComment  = QAction(nested("edit", "comment"), self)
    self.actionSuperComment  = QAction(nested("edit", "super-com"), self)
    
    #Select menu actions
    self.actionGoStartDocument = QAction(nested("select", "go-ini"), self)
    self.actionGoEndDocument = QAction(nested("select", "go-end"), self)
    self.actionPrevQuery = QAction(nested("select", "prev-q"), self)
    self.actionNextQuery = QAction(nested("select", "next-q"), self)
    self.actionSelectToPrevQuery = QAction(nested("select", "stpq"), self)
    self.actionSelectToNextQuery = QAction(nested("select", "stnq"), self)
    self.actionPrevBlock = QAction(nested("select", "prev-block"), self)
    self.actionNextBlock = QAction(nested("select", "next-block"), self)
    self.actionSelNextOcurrence = QAction(nested("select", "snexo"), self)
    self.actionAddCursorToLinesEnd = QAction(nested("select", "acel"), self)
    self.actionAddCursorToLinesStart = QAction(nested("select", "acsl"), self)
    self.actionAddCursorAbove = QAction(nested("select", "ac-above"), self)
    self.actionAddCursorBelow= QAction(nested("select", "ac-below"), self)

    #View menu actions
    self.actionSizeEditor_up = QAction(nested("view", "ifse"), self)
    self.actionSizeEditor_down = QAction(nested("view", "lfse"), self)
    self.actionSizeResult_up = QAction(nested("view", "ifsr"), self)
    self.actionSizeResult_down = QAction(nested("view", "lfsr"), self)
    self.actionPreviousTab = QAction(nested("view", "pt"), self)
    self.actionNextTab = QAction(nested("view", "nt"), self)
    self.actionWordWrap = QAction(nested("view", "ww"), self)
    self.actionWordWrap.setCheckable(True)

    #SQL Menu Actions
    self.actionConnectDSN = QAction(nested("sql", "con-dsn"), self)
    self.actionStopRun = QAction(nested("sql", "stop-run"), self)
    self.actionRun = QAction(nested("sql", "run-query"), self)
    self.actionRunAll = QAction(nested("sql", "run-all"), self)
    self.actionQuery_to_file = QAction(nested("sql", "query-file"), self)
    self.actionFile_to_lz = QAction(nested("sql", "ufftlz"), self)
    self.actionRecLog = QAction(nested("sql", "start-log"), self)

    #AI Menu Actions
    self.actionAnalize = QAction(nested("ai", "analize-query1"), self)
    self.actionFluffAnalize = QAction(nested("ai", "analize-query2"), self)
    
    #Help menu actions
    self.actionAbout = QAction(nested("help", "about"), self)
    self.actionUpdate = QAction(nested("help", "update"), self)
    
    #2. Creating their respective shortCut
    #---------------------------------
    self.actionNew.setShortcut("Ctrl+N")
    self.actionOpen.setShortcut("Ctrl+O")
    self.actionOpenBlock.setShortcut("Ctrl+Shift+O")
    self.actionReload.setShortcut("Ctrl+R")
    self.actionSave.setShortcut("Ctrl+S")
    self.actionSaveAs.setShortcut("Ctrl+Shift+S")
    self.actionOpenP.setShortcut("Alt+O")
    self.actionOpenBlockP.setShortcut("Alt+Shift+O")
    self.actionSaveP.setShortcut("Alt+S")
    self.actionSaveAsP.setShortcut("Alt+Shift+S")
    self.actionSearch.setShortcut("Ctrl+F")
    self.actionReplace.setShortcut("Ctrl+H")
    self.actionRun.setShortcut("F9")
    self.actionRunAll.setShortcut("F10")
    self.actionQuery_to_file.setShortcut("F5")
    self.actionFile_to_lz.setShortcut("F6")
    self.actionAbout.setShortcut("Ctrl+J")
    self.actionComment .setShortcut("Ctrl+}")
    self.actionGoStartDocument.setShortcut("Ctrl+Home")
    self.actionGoEndDocument.setShortcut("Ctrl+End")
    self.actionPrevQuery.setShortcut("Ctrl+Up")
    self.actionNextQuery.setShortcut("Ctrl+Down")
    self.actionSelectToPrevQuery.setShortcut("Ctrl+Shift+Up")
    self.actionSelectToNextQuery.setShortcut("Ctrl+Shift+Down")
    self.actionPrevBlock.setShortcut("Ctrl+q")
    self.actionNextBlock.setShortcut("Ctrl+w")
    self.actionSelNextOcurrence.setShortcut("Ctrl+D")
    self.actionAddCursorToLinesEnd.setShortcut("Ctrl+I")
    self.actionAddCursorToLinesStart.setShortcut("Ctrl+Shift+I")
    self.actionAddCursorAbove.setShortcut("Ctrl+Alt+Up")
    self.actionAddCursorBelow.setShortcut("Ctrl+Alt+Down")
    self.actionSizeEditor_up.setShortcut("Ctrl++")
    self.actionSizeEditor_down.setShortcut("Ctrl+-")
    self.actionSizeResult_up.setShortcut("Ctrl+Shift++")
    self.actionSizeResult_down.setShortcut("Ctrl+Shift+-")
    self.actionWordWrap.setShortcut("Alt+Z")
    
    #Remember that for shortcuts to work
    ##it must be added to a visible widget
    self.centralwidget.addAction(self.actionNew)
    self.centralwidget.addAction(self.actionOpen)
    self.centralwidget.addAction(self.actionOpenBlock)
    self.centralwidget.addAction(self.actionReload)
    self.centralwidget.addAction(self.actionSave)
    self.centralwidget.addAction(self.actionSaveAs)
    self.centralwidget.addAction(self.actionOpenP)
    self.centralwidget.addAction(self.actionOpenBlockP)
    self.centralwidget.addAction(self.actionSaveP)
    self.centralwidget.addAction(self.actionSaveAsP)
    self.centralwidget.addAction(self.actionRun)
    self.centralwidget.addAction(self.actionRunAll)
    self.centralwidget.addAction(self.actionQuery_to_file)
    self.centralwidget.addAction(self.actionAbout)
    self.centralwidget.addAction(self.actionSearch)
    self.centralwidget.addAction(self.actionReplace)
    self.centralwidget.addAction(self.actionComment )
    self.centralwidget.addAction(self.actionPrevQuery)
    self.centralwidget.addAction(self.actionNextQuery)
    self.centralwidget.addAction(self.actionSelectToPrevQuery)
    self.centralwidget.addAction(self.actionSelectToNextQuery)
    self.centralwidget.addAction(self.actionPrevBlock)
    self.centralwidget.addAction(self.actionNextBlock)
    self.centralwidget.addAction(self.actionGoStartDocument)
    self.centralwidget.addAction(self.actionGoEndDocument)
    self.centralwidget.addAction(self.actionSelNextOcurrence)
    self.centralwidget.addAction(self.actionAddCursorToLinesEnd)
    self.centralwidget.addAction(self.actionAddCursorToLinesStart)
    self.centralwidget.addAction(self.actionAddCursorAbove)
    self.centralwidget.addAction(self.actionAddCursorBelow)
    self.centralwidget.addAction(self.actionSizeEditor_up)
    self.centralwidget.addAction(self.actionSizeEditor_down)
    self.centralwidget.addAction(self.actionPreviousTab)
    self.centralwidget.addAction(self.actionNextTab)
    self.centralwidget.addAction(self.actionWordWrap)
    self.centralwidget.addAction(self.actionFile_to_lz)

    #3. Creating menus and adding their actions
    #-----------------------------------------
    self.menuFile = QMenu(self)
    self.menuFile.addAction(self.actionNew)
    self.menuFile.addSeparator()
    self.menuFile.addAction(self.actionOpen)
    self.menuFile.addAction(self.actionOpenBlock)
    self.menuFile.addAction(self.actionReload)
    self.menuFile.addSeparator()
    self.menuFile.addAction(self.actionSave)
    self.menuFile.addAction(self.actionSaveAs)
    self.menuFile.addSeparator()
    self.menuFile.addAction(self.actionOpenP)
    self.menuFile.addAction(self.actionOpenBlockP)
    self.menuFile.addSeparator()
    self.menuFile.addAction(self.actionSaveP)
    self.menuFile.addAction(self.actionSaveAsP)

    self.menuEdit = QMenu(self)
    self.menuEdit.addAction(self.actionSearch)
    self.menuEdit.addAction(self.actionReplace)
    self.menuEdit.addSeparator()
    self.menuEdit.addAction(self.actionComment )
    self.menuEdit.addAction(self.actionSuperComment )
    self.menuEdit.addSeparator()

    self.menuSelect = QMenu(self)
    self.menuSelect.addAction(self.actionGoStartDocument)
    self.menuSelect.addAction(self.actionGoEndDocument)
    self.menuSelect.addSeparator()
    self.menuSelect.addAction(self.actionPrevQuery)
    self.menuSelect.addAction(self.actionNextQuery)
    self.menuSelect.addSeparator()
    self.menuSelect.addAction(self.actionSelectToPrevQuery)
    self.menuSelect.addAction(self.actionSelectToNextQuery)
    self.menuSelect.addSeparator()
    self.menuSelect.addAction(self.actionPrevBlock)
    self.menuSelect.addAction(self.actionNextBlock)
    self.menuSelect.addSeparator()
    self.menuSelect.addAction(self.actionSelNextOcurrence)
    self.menuSelect.addSeparator()
    self.menuSelect.addAction(self.actionAddCursorToLinesEnd)
    self.menuSelect.addAction(self.actionAddCursorToLinesStart)
    self.menuSelect.addSeparator()
    self.menuSelect.addAction(self.actionAddCursorAbove)
    self.menuSelect.addAction(self.actionAddCursorBelow)
    self.menuSelect.addSeparator()
    
    self.menuView = QMenu(self)
    self.menuTheme = QMenu(nested("view", "theme"), self)
    self.menuFont = QMenu(nested("view", "font", "main"), self)
    self.menuFontEditor = QMenu(nested("view", "font", "font-editor"), self)
    self.menuFontResult = QMenu(nested("view", "font", "font-result"), self)
    self.menuView.addMenu(self.menuTheme)
    self.menuView.addMenu(self.menuFont)
    self.menuFont.addMenu(self.menuFontEditor)
    self.menuFont.addMenu(self.menuFontResult)
    self.menuView.addSeparator()
    self.menuView.addAction(self.actionSizeEditor_up)
    self.menuView.addAction(self.actionSizeEditor_down)
    self.menuView.addSeparator()
    self.menuView.addAction(self.actionSizeResult_up)
    self.menuView.addAction(self.actionSizeResult_down)
    self.menuView.addSeparator()
    self.menuView.addAction(self.actionPreviousTab)
    self.menuView.addAction(self.actionNextTab)
    self.menuView.addSeparator()
    self.menuView.addAction(self.actionWordWrap)
    
    self.menuSQL = QMenu(self)
    self.menuSelectDSN = QMenu(nested("sql", "sel-dsn"), self)
    self.menuAssistant = QMenu(nested("sql", "assistant"), self)
    self.menuPlantillas = QMenu(nested("sql", "tmplts"), self)
    self.menuSQL.addMenu(self.menuSelectDSN)
    self.menuSQL.addAction(self.actionConnectDSN)
    self.menuSQL.addSeparator()
    self.menuSQL.addAction(self.actionStopRun)
    self.menuSQL.addAction(self.actionRun)
    self.menuSQL.addAction(self.actionRunAll)
    self.menuSQL.addSeparator()
    self.menuSQL.addAction(self.actionQuery_to_file)
    self.menuSQL.addAction(self.actionFile_to_lz)
    self.menuSQL.addSeparator()
    self.menuSQL.addMenu(self.menuPlantillas)
    self.menuSQL.addMenu(self.menuAssistant)
    self.menuSQL.addSeparator()
    self.menuSQL.addAction(self.actionRecLog)

    self.menuAI = QMenu(self)
    self.menuAI.addAction(self.actionAnalize)
    self.menuAI.addAction(self.actionFluffAnalize)
    
    self.menuHelp= QMenu(self)
    self.menuHelp.addAction(self.actionAbout)
    self.menuHelp.addAction(self.actionUpdate)

    #4. Create custom actions per user
    #----------------------------------------------
    #Creating submenus to select dsn
    try:
        dict_dsn = pyodbc.dataSources()
    except:
        dict_dsn = {"None":nested("msgs", "msg1")}
    
    dsnGroup = QActionGroup(self)
    dsnGroup.setExclusive(True)
    count = 0
    for _dsn in sorted(dict_dsn.keys()):
        count += 1
        action_dsn = QAction(_dsn, self)
        action_dsn.setCheckable(True)
        action_dsn.setToolTip(dict_dsn.get(_dsn, ""))
        dsnGroup.addAction(action_dsn)
        action_dsn.triggered.connect(self.applySelectedDSN)
        self.menuSelectDSN.addAction(action_dsn)
        if count % 4 == 0:
            self.menuSelectDSN.addSeparator()

    #Creating the submenus for view\font and view\theme
    list_fonts = self.cfg_app.index.get("list_fonts")['font']
    list_thems = list(self.cfg_app.index.get("list_thems"))
    list_assist = self.list_assist.index
    list_tmplts = self.list_tmplts.index
    
    #Creating actions for Editor fonts
    group_fontEditor = QActionGroup(self)
    group_fontEditor.setExclusive(True)
    group_fontResult = QActionGroup(self)
    group_fontResult.setExclusive(True)
    count = 10
    for font in sorted(list_fonts):
        count += 1
        #font for Editor and Parameters
        action_fontEditor = QAction(font, self)
        action_fontEditor.setCheckable(True)
        group_fontEditor.addAction(action_fontEditor)
        action_fontEditor.triggered.connect(self.applyEditorFont)
        self.menuFontEditor.addAction(action_fontEditor)
        #font for Results
        accion_fontResult = QAction(font, self)
        accion_fontResult.setCheckable(True)
        group_fontResult.addAction(accion_fontResult)
        accion_fontResult.triggered.connect(self.applyFontResult)
        self.menuFontResult.addAction(accion_fontResult)
        if count % 4 == 0:
            self.menuFontEditor.addSeparator()
            self.menuFontResult.addSeparator()
    #Creating actions for themes
    group_theme = QActionGroup(self)
    group_theme.setExclusive(True)
    count = 10
    for theme in sorted(list_thems):
        count += 1
        accion_theme = QAction(theme, self)
        accion_theme.setCheckable(True)
        group_theme.addAction(accion_theme)
        accion_theme.triggered.connect(self.captureThemeFormat)
        self.menuTheme.addAction(accion_theme)
        self.menuTheme.addSeparator() if count % 4 == 0 else None
    #Creating actions for assistance
    self.menuAssistant.addAction(self.actionRun)
    self.menuAssistant.addAction(self.actionRunAll)
    self.menuAssistant.addSeparator()
    count = 10
    for assist in list_assist.keys():
        count += 1
        shortcut = "Alt+A,{}".format(",".join(list(str(count))))
        accion_assist = QAction(assist, self)
        accion_assist.triggered.connect(self.runAssist)
        accion_assist.setShortcut(QKeySequence(shortcut))
        self.menuAssistant.addAction(accion_assist)
        self.centralwidget.addAction(accion_assist)
        self.menuAssistant.addSeparator() if count % 4 == 0 else None
    #Creating actions for templates
    count = 10
    for plantilla in list_tmplts.keys():
        count += 1
        shortcut = "Alt+P,{}".format(",".join(list(str(count))))
        plantilla_assist = QAction(plantilla, self)
        plantilla_assist.setShortcut(QKeySequence(str(count)))
        plantilla_assist.triggered.connect(self.runTemplate)
        plantilla_assist.setShortcut(QKeySequence(shortcut))
        self.menuPlantillas.addAction(plantilla_assist)
        self.centralwidget.addAction(plantilla_assist)
        self.menuPlantillas.addSeparator() if count % 4 == 0 else None
    #Creating the shortcuts for these custom functions
    self.actionShowAsistente = QAction("Show assistant", self)
    self.actionShowPlantillas = QAction("Show tmplts", self)
    self.actionShowAsistente.setShortcut("F8")
    self.actionShowPlantillas.setShortcut("F7")
    self.centralwidget.addAction(self.actionShowAsistente)
    self.centralwidget.addAction(self.actionShowPlantillas)
    self.actionShowAsistente.triggered.connect(partial(self.showMenu, "assistant"))
    self.actionShowPlantillas.triggered.connect(partial(self.showMenu, "tmplts"))
    
    #5. Linking buttons, menus and actions
    #-----------------------------------------
    self.fm_title.bt_file.clicked.connect(partial(self.showMenu, "file"))
    self.fm_title.bt_edit.clicked.connect(partial(self.showMenu, "edit"))
    self.fm_title.bt_select.clicked.connect(partial(self.showMenu, "select"))
    self.fm_title.bt_view.clicked.connect(partial(self.showMenu, "view"))
    self.fm_title.bt_sql.clicked.connect(partial(self.showMenu, "sql"))
    self.fm_title.bt_ai.clicked.connect(partial(self.showMenu, "ai"))
    self.fm_title.bt_help.clicked.connect(partial(self.showMenu, "help"))

    #MenuFile Actions
    self.actionNew.triggered.connect(partial(self.newScriptTab, ""))
    self.actionReload.triggered.connect(self.reloadETL)
    self.actionOpen.triggered.connect(partial(self.openFile, True))
    self.actionOpenBlock.triggered.connect(partial(self.openBlockFiles, True))
    self.actionSave.triggered.connect(partial(self.savingChanges, "", "save"))
    self.actionSaveAs.triggered.connect(partial(self.savingChanges, "", "saveAs"))
    self.actionOpenP.triggered.connect(partial(self.openFileP, True))
    self.actionOpenBlockP.triggered.connect(partial(self.openBlockFilesP, True))
    self.actionSaveP.triggered.connect(partial(self.savingChangesP, "", "save"))
    self.actionSaveAsP.triggered.connect(partial(self.savingChangesP, "", "saveAs"))

    #Edit actions
    self.actionSearch.triggered.connect(self.searchText)
    self.actionReplace.triggered.connect(self.replaceText)
    self.actionComment .triggered.connect(self.commentText)
    self.actionSuperComment .triggered.connect(self.insertSuperComment)

    #Select actions
    self.actionGoStartDocument.triggered.connect(self.goToStartOfDocument)
    self.actionGoEndDocument.triggered.connect(self.goToEndOfDocument)
    self.actionPrevQuery.triggered.connect(partial(self.specialFind, ";", False))
    self.actionNextQuery.triggered.connect(partial(self.specialFind, ";", True))
    self.actionSelectToNextQuery.triggered.connect(self.selectUpToNextQuery)
    self.actionSelectToPrevQuery.triggered.connect(self.selectUpToPreviousQuery)
    self.actionPrevBlock.triggered.connect(partial(self.specialFind, "--#-", False))
    self.actionNextBlock.triggered.connect(partial(self.specialFind, "--#-", True))
    self.actionSelNextOcurrence.triggered.connect(self.addNextOccurrence)
    self.actionAddCursorToLinesEnd.triggered.connect(partial(self.addCursorsToLineBorders, _start=False))
    self.actionAddCursorToLinesStart.triggered.connect(partial(self.addCursorsToLineBorders, _start=True))
    self.actionAddCursorAbove.triggered.connect(partial(self.addCursorToAboveBelow, _above=True))
    self.actionAddCursorBelow.triggered.connect(partial(self.addCursorToAboveBelow, _above=False))

    #View
    self.actionWordWrap.triggered.connect(self.changeWordWrap)
    self.actionSizeEditor_up.triggered.connect(partial(self.changeEtlFontSize, 1))
    self.actionSizeEditor_down.triggered.connect(partial(self.changeEtlFontSize, -1))
    self.actionSizeResult_up.triggered.connect(partial(self.changeFontSizeResult, 1))
    self.actionSizeResult_down.triggered.connect(partial(self.changeFontSizeResult, -1))

    #menuSQL actions
    self.actionConnectDSN.triggered.connect(self.ConMan.start)
    self.actionRun.triggered.connect(self.runShortTask)
    self.actionRunAll.triggered.connect(self.runLongTask)
    self.actionQuery_to_file.triggered.connect(self.runQuery_to_file)
    self.actionFile_to_lz.triggered.connect(self.runFile_to_lz)
    self.actionStopRun.triggered.connect(self.stopWorker)
    self.actionRecLog.triggered.connect(self.recLog)
    
    self.actionFile_to_lz.setDisabled(True)
    
    #AI Menu Actions
    self.actionAnalize.triggered.connect(self.aiQueryAnalizer)
    self.actionFluffAnalize.triggered.connect(self.sqlfluffAnalizer)

    #Menu ActionsHelp
    self.actionAbout.triggered.connect(self.showAcercaDe)
    self.actionUpdate.triggered.connect(self.startUpdate)

    #5. Modifying styles
    #-----------------------
    #Debugged code

    #6. Checking in Menus the actions previously defined by the user
    #--------------------------------------------------------------------
    #DSN
    dsn = self.cfg_session.index.get("prede_dsn")
    for action in self.menuSelectDSN.actions():
        action.setChecked(action.text() == dsn)
    #Editor font
    font = self.cfg_session.index.get("prede_font")
    for action in self.menuFontEditor.actions():
        action.setChecked(action.text() == font["editor-font"])
    #Result font
    for action in self.menuFontResult.actions():
        action.setChecked(action.text() == font["result-font"])
    internal_theme = self.cfg_session.index.get("internal_theme")

    internal_theme = self.cfg_session.index.get("internal_theme")
    for action in self.menuTheme.actions():
        action.setChecked(action.text() == internal_theme)
    #Word Wrap
    self.actionWordWrap.setChecked(self.cfg_session.index.get("worldWrap"))