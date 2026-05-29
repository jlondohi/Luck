import pyodbc
from functools import partial
#Importing PyQt6 packages
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import (QAction, QActionGroup, QKeySequence)

#===========================================================
#Creating menus and submenus of the main window
#===========================================================
def createPMenu(self, *args):
    #1. Creating all actions
    #-----------------------
    #File menu actions
    self.actionNew          = QAction(self.i18nNes('file', 'new'), self)
    self.actionOpen         = QAction(self.i18nNes('file', 'open'), self)
    self.actionOpenBlock    = QAction(self.i18nNes('file', 'open-block'), self)
    self.actionReload       = QAction(self.i18nNes('file', 'reload'), self)
    self.actionSave         = QAction(self.i18nNes('file', 'save'), self)
    self.actionSaveAs       = QAction(self.i18nNes('file', 'save-as'), self)
    self.actionOpenP        = QAction(self.i18nNes('file', 'open-param'), self)
    self.actionOpenBlockP   = QAction(self.i18nNes('file', 'open-param-block'), self)
    self.actionSaveP        = QAction(self.i18nNes('file', 'save-param'), self)
    self.actionSaveAsP      = QAction(self.i18nNes('file', 'save-param-as'), self)
    self.actionClose        = QAction(self.i18nNes('file', 'close'), self)
    
    #Edit Menu Actions
    self.actionSearch       = QAction(self.i18nNes('edit', 'search'), self)
    self.actionReplace      = QAction(self.i18nNes('edit', 'replace'), self)
    self.actionComment      = QAction(self.i18nNes('edit', 'comment'), self)
    self.actionSuperComment = QAction(self.i18nNes('edit', 'super-com'), self)
    
    #Select menu actions
    self.actionSelectToPrevQuery = QAction(self.i18nNes('select', 'stpq'), self)
    self.actionSelectToNextQuery = QAction(self.i18nNes('select', 'stnq'), self)
    self.actionSelNextOcurrence = QAction(self.i18nNes('select', 'snexo'), self)
    self.actionAddCursorToLinesEnd  = QAction(self.i18nNes('select', 'acel'), self)
    self.actionAddCursorToLinesStart = QAction(self.i18nNes('select', 'acsl'), self)
    self.actionAddCursorAbove       = QAction(self.i18nNes('select', 'ac-above'), self)
    self.actionAddCursorBelow   = QAction(self.i18nNes('select', 'ac-below'), self)

    #View menu actions
    self.actionSizeEditor_up    = QAction(self.i18nNes('view', 'ifse'), self)
    self.actionSizeEditor_down  = QAction(self.i18nNes('view', 'lfse'), self)
    self.actionSizeResult_up    = QAction(self.i18nNes('view', 'ifsr'), self)
    self.actionSizeResult_down  = QAction(self.i18nNes('view', 'lfsr'), self)
    self.actionTabSpace         = QAction(self.i18nNes('view', 'tab-space'), self)
    self.actionResultFetch      = QAction(self.i18nNes('view', 'result-fetch'), self)
    self.actionWordWrap         = QAction(self.i18nNes('view', 'ww'), self)
    self.actionWordWrap.setCheckable(True)

    #Go menu actions
    self.actionGoStartDocument  = QAction(self.i18nNes('go', 'go-ini'), self)
    self.actionGoEndDocument    = QAction(self.i18nNes('go', 'go-end'), self)
    self.actionGoToLineBlock    = QAction(self.i18nNes('go', 'goto'), self)
    self.actionPrevQuery        = QAction(self.i18nNes('go', 'prev-q'), self)
    self.actionNextQuery        = QAction(self.i18nNes('go', 'next-q'), self)
    self.actionPrevBlock        = QAction(self.i18nNes('go', 'prev-block'), self)
    self.actionNextBlock        = QAction(self.i18nNes('go', 'next-block'), self)
    self.actionPreviousTab      = QAction(self.i18nNes('go', 'pt'), self)
    self.actionNextTab          = QAction(self.i18nNes('go', 'nt'), self)

    #SQL Menu Actions
    self.actionConnectDSN   = QAction(self.i18nNes('sql', 'con-dsn'), self)
    self.actionStopRun      = QAction(self.i18nNes('sql', 'stop-run'), self)
    self.actionRun          = QAction(self.i18nNes('sql', 'run-query'), self)
    self.actionRunAll       = QAction(self.i18nNes('sql', 'run-all'), self)
    self.actionRunAbove     = QAction(self.i18nNes('sql', 'run-above'), self)
    self.actionRunBelow     = QAction(self.i18nNes('sql', 'run-below'), self)
    self.actionSaveResult   = QAction(self.i18nNes('sql', 'save-result'), self)
    self.actionSaveResultAs = QAction(self.i18nNes('sql', 'save-result-as'), self)
    self.actionFile_to_lz   = QAction(self.i18nNes('sql', 'ufftlz'), self)
    self.actionRecLog       = QAction(self.i18nNes('sql', 'start-log'), self)

    #AI Menu Actions
    self.actionAnalize      = QAction(self.i18nNes('ai', 'analize-query1'), self)
    self.actionFluffAnalize = QAction(self.i18nNes('ai', 'analize-query2'), self)
    
    #Help menu actions
    self.actionAbout    = QAction(self.i18nNes('help', 'about'), self)
    self.actionUpdate   = QAction(self.i18nNes('help', 'update'), self)
    
    #2. Creating menus and adding their actions
    #-----------------------------------------
    self.menuFile   = QMenu(self)
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
    self.menuFile.addSeparator()
    self.menuFile.addAction(self.actionClose)

    self.menuEdit   = QMenu(self)
    self.menuEdit.addAction(self.actionSearch)
    self.menuEdit.addAction(self.actionReplace)
    self.menuEdit.addSeparator()
    self.menuEdit.addAction(self.actionComment)
    self.menuEdit.addAction(self.actionSuperComment)
    self.menuEdit.addSeparator()

    self.menuSelect = QMenu(self)
    self.menuSelect.addAction(self.actionSelectToPrevQuery)
    self.menuSelect.addAction(self.actionSelectToNextQuery)
    self.menuSelect.addSeparator()
    self.menuSelect.addAction(self.actionSelNextOcurrence)
    self.menuSelect.addSeparator()
    self.menuSelect.addAction(self.actionAddCursorToLinesEnd)
    self.menuSelect.addAction(self.actionAddCursorToLinesStart)
    self.menuSelect.addSeparator()
    self.menuSelect.addAction(self.actionAddCursorAbove)
    self.menuSelect.addAction(self.actionAddCursorBelow)
    self.menuSelect.addSeparator()
    
    self.menuView       = QMenu(self)
    self.menuLanguage   = QMenu(self.i18nNes('view', 'language'), self)
    self.menuProfile    = QMenu(self.i18nNes('view', 'profile'), self)
    self.menuFont       = QMenu(self.i18nNes('view', 'font', 'main'), self)
    self.menuFontEditor = QMenu(self.i18nNes('view', 'font', 'font-editor'), self)
    self.menuFontResult = QMenu(self.i18nNes('view', 'font', 'font-result'), self)
    self.menuView.addMenu(self.menuLanguage)
    self.menuView.addMenu(self.menuProfile)
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
    self.menuView.addAction(self.actionTabSpace)
    self.menuView.addAction(self.actionResultFetch)
    self.menuView.addSeparator()
    self.menuView.addAction(self.actionWordWrap)
    
    self.menuGo         = QMenu(self)
    self.menuGo.addAction(self.actionGoStartDocument)
    self.menuGo.addAction(self.actionGoEndDocument)
    self.menuGo.addSeparator()
    self.menuGo.addAction(self.actionGoToLineBlock)
    self.menuGo.addSeparator()
    self.menuGo.addAction(self.actionPrevQuery)
    self.menuGo.addAction(self.actionNextQuery)
    self.menuGo.addSeparator()
    self.menuGo.addAction(self.actionPrevBlock)
    self.menuGo.addAction(self.actionNextBlock)
    self.menuGo.addSeparator()
    self.menuGo.addAction(self.actionPreviousTab)
    self.menuGo.addAction(self.actionNextTab)

    self.menuSQL        = QMenu(self)
    self.menuSelectDSN  = QMenu(self.i18nNes('sql', 'sel-dsn'), self)
    self.menuAssistant  = QMenu(self.i18nNes('sql', 'assistant'), self)
    self.manuTemplates  = QMenu(self.i18nNes('sql', 'tmplts'), self)
    self.menuSQL.addMenu(self.menuSelectDSN)
    self.menuSQL.addAction(self.actionConnectDSN)
    self.menuSQL.addSeparator()
    self.menuSQL.addAction(self.actionStopRun)
    self.menuSQL.addAction(self.actionRun)
    self.menuSQL.addAction(self.actionRunAll)
    self.menuSQL.addAction(self.actionRunAbove)
    self.menuSQL.addAction(self.actionRunBelow)
    self.menuSQL.addSeparator()
    self.menuSQL.addAction(self.actionSaveResult)
    self.menuSQL.addAction(self.actionSaveResultAs)
    self.menuSQL.addAction(self.actionFile_to_lz)
    self.menuSQL.addSeparator()
    self.menuSQL.addMenu(self.manuTemplates)
    self.menuSQL.addMenu(self.menuAssistant)
    self.menuSQL.addSeparator()
    self.menuSQL.addAction(self.actionRecLog)

    self.menuAI     = QMenu(self)
    self.menuAI.addAction(self.actionAnalize)
    self.menuAI.addAction(self.actionFluffAnalize)
    
    self.menuHelp   = QMenu(self)
    self.menuHelp.addAction(self.actionAbout)
    self.menuHelp.addAction(self.actionUpdate)

    #3. Create custom actions per user
    #----------------------------------------------
    #Creating submenus to select dsn
    try:
        dict_dsn = pyodbc.dataSources()
    except:
        dict_dsn = {'None':self.i18nNes('msgs', 'msg1')}
    
    dsnGroup = QActionGroup(self)
    dsnGroup.setExclusive(True)
    count = 0
    for _dsn in sorted(dict_dsn.keys()):
        count += 1
        action_dsn = QAction(_dsn, self)
        action_dsn.setCheckable(True)
        action_dsn.setToolTip(dict_dsn.get(_dsn, ''))
        dsnGroup.addAction(action_dsn)
        action_dsn.triggered.connect(self.applySelectedDSN)
        self.menuSelectDSN.addAction(action_dsn)
        if count % 4 == 0:
            self.menuSelectDSN.addSeparator()

    #Creating the submenus for view\font and view\profile
    list_fonts = self.cfg_app.index.get('list_fonts')['font']
    list_languages = list(self.dict_languages.keys())
    list_profiles = list(self.dict_profiles.keys())
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
    #Creating actions for Language
    group_language = QActionGroup(self)
    group_language.setExclusive(True)
    count = 10
    for language in sorted(list_languages):
        count += 1
        accion_language = QAction(language, self)
        accion_language.setCheckable(True)
        group_language.addAction(accion_language)
        accion_language.triggered.connect(self.applySelectedLanguage)
        self.menuLanguage.addAction(accion_language)
        self.menuLanguage.addSeparator() if count % 4 == 0 else None
    #Creating actions for profiles
    group_profile = QActionGroup(self)
    group_profile.setExclusive(True)
    count = 10
    for profile in sorted(list_profiles):
        count += 1
        accion_profile = QAction(profile, self)
        accion_profile.setCheckable(True)
        group_profile.addAction(accion_profile)
        accion_profile.triggered.connect(self.captureProfileFormat)
        self.menuProfile.addAction(accion_profile)
        self.menuProfile.addSeparator() if count % 4 == 0 else None
    #Creating actions for assistance
    self.menuAssistant.addAction(self.actionRun)
    self.menuAssistant.addAction(self.actionRunAll)
    self.menuAssistant.addAction(self.actionRunAbove)
    self.menuAssistant.addAction(self.actionRunBelow)
    self.menuAssistant.addSeparator()
    count = 10
    for assist in list_assist.keys():
        count += 1
        shortcut = 'Alt+A,{}'.format(','.join(list(str(count))))
        action_assist = QAction(assist, self)
        action_assist.triggered.connect(self.runAssist)
        action_assist.setShortcut(QKeySequence(shortcut))
        self.menuAssistant.addAction(action_assist)
        self.centralwidget.addAction(action_assist)
        self.menuAssistant.addSeparator() if count % 4 == 0 else None
    #Creating actions for templates
    count = 10
    for template in list_tmplts.keys():
        count += 1
        shortcut = 'Alt+P,{}'.format(','.join(list(str(count))))
        template_assist = QAction(template, self)
        template_assist.setShortcut(QKeySequence(str(count)))
        template_assist.triggered.connect(self.runTemplate)
        template_assist.setShortcut(QKeySequence(shortcut))
        self.manuTemplates.addAction(template_assist)
        self.centralwidget.addAction(template_assist)
        self.manuTemplates.addSeparator() if count % 4 == 0 else None
    #Creating the shortcuts for these custom functions
    self.actionShowAssistant = QAction('Show assistant', self)
    self.actionShowTemplates = QAction('Show tmplts', self)
    self.centralwidget.addAction(self.actionShowAssistant)
    self.centralwidget.addAction(self.actionShowTemplates)
    self.actionShowAssistant.triggered.connect(partial(self.showMenu, 'assistant'))
    self.actionShowTemplates.triggered.connect(partial(self.showMenu, 'tmplts'))
    
    #4. Linking buttons, menus and actions
    #-----------------------------------------
    self.fm_title.bt_file.clicked.connect(partial(self.showMenu, 'file'))
    self.fm_title.bt_edit.clicked.connect(partial(self.showMenu, 'edit'))
    self.fm_title.bt_select.clicked.connect(partial(self.showMenu, 'select'))
    self.fm_title.bt_view.clicked.connect(partial(self.showMenu, 'view'))
    self.fm_title.bt_go.clicked.connect(partial(self.showMenu, 'go'))
    self.fm_title.bt_sql.clicked.connect(partial(self.showMenu, 'sql'))
    self.fm_title.bt_ai.clicked.connect(partial(self.showMenu, 'ai'))
    self.fm_title.bt_help.clicked.connect(partial(self.showMenu, 'help'))

    #MenuFile Actions
    self.actionNew.triggered.connect(partial(self.newScriptTab, ''))
    self.actionReload.triggered.connect(self.reloadETL)
    self.actionOpen.triggered.connect(partial(self.openFile, True))
    self.actionOpenBlock.triggered.connect(partial(self.openBlockFiles, True))
    self.actionSave.triggered.connect(partial(self.savingChanges, '', 'save'))
    self.actionSaveAs.triggered.connect(partial(self.savingChanges, '', 'saveAs'))
    self.actionOpenP.triggered.connect(partial(self.openFileP, True))
    self.actionOpenBlockP.triggered.connect(partial(self.openBlockFilesP, True))
    self.actionSaveP.triggered.connect(partial(self.savingChangesP, '', 'save'))
    self.actionSaveAsP.triggered.connect(partial(self.savingChangesP, '', 'saveAs'))
    self.actionClose.triggered.connect(self.close)

    #Edit actions
    self.actionSearch.triggered.connect(self.searchText)
    self.actionReplace.triggered.connect(self.replaceText)
    self.actionComment.triggered.connect(self.commentText)
    self.actionSuperComment.triggered.connect(self.insertSuperComment)

    #Select actions
    self.actionSelectToNextQuery.triggered.connect(self.selectUpToNextQuery)
    self.actionSelectToPrevQuery.triggered.connect(self.selectUpToPreviousQuery)
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
    self.actionTabSpace.triggered.connect(self.changeSpacePerTab)
    self.actionResultFetch.triggered.connect(self.changeFetch)
   
    #Go
    self.actionGoStartDocument.triggered.connect(self.goToStartOfDocument)
    self.actionGoEndDocument.triggered.connect(self.goToEndOfDocument)
    self.actionGoToLineBlock.triggered.connect(self.goToLineBlock)
    self.actionPrevQuery.triggered.connect(partial(self.specialFind, ';', False))
    self.actionNextQuery.triggered.connect(partial(self.specialFind, ';', True))
    self.actionPrevBlock.triggered.connect(partial(self.specialFind, '--#-', False))
    self.actionNextBlock.triggered.connect(partial(self.specialFind, '--#-', True))
    self.actionPreviousTab.triggered.connect(self.goNextTab)
    self.actionNextTab.triggered.connect(self.goPreviousTab)

    #menuSQL actions
    self.actionConnectDSN.triggered.connect(self.asyncConnMan.start)
    self.actionRun.triggered.connect(self.runShortTask)
    self.actionRunAll.triggered.connect(self.runLongTask)
    self.actionRunAbove.triggered.connect(self.runLongTaskAbove)
    self.actionRunBelow.triggered.connect(self.runLongTaskBelow)
    self.actionSaveResult.triggered.connect(self.saveResult)
    self.actionSaveResultAs.triggered.connect(self.saveResultAs)
    self.actionFile_to_lz.triggered.connect(self.runFile_to_lz)
    self.actionStopRun.triggered.connect(self.stopExcWorker)
    self.actionRecLog.triggered.connect(self.recLog)
    
    self.actionFile_to_lz.setDisabled(True)
    
    #AI Menu Actions

    #Menu ActionsHelp
    self.actionAbout.triggered.connect(self.showAcercaDe)
    self.actionUpdate.triggered.connect(self.startUpdate)

    #5. Checking in Menus the actions previously defined by the user
    #--------------------------------------------------------------------
    #DSN
    dsn = self.cfg_session.index.get('prede_dsn')
    for action in self.menuSelectDSN.actions():
        action.setChecked(action.text() == dsn)
    #Language
    lgg = self.cfg_session.index.get('language', 'en-US')
    for action in self.menuLanguage.actions():
        action.setChecked(action.text() == lgg)
    #Editor font
    font = self.cfg_session.index.get('prede_font')
    for action in self.menuFontEditor.actions():
        action.setChecked(action.text() == font['editor-font'])
    #Result font
    for action in self.menuFontResult.actions():
        action.setChecked(action.text() == font['result-font'])
    internalProfile = self.cfg_session.index.get('internal_profile')

    internalProfile = self.cfg_session.index.get('internal_profile')
    for action in self.menuProfile.actions():
        action.setChecked(action.text() == internalProfile)
    #Word Wrap
    self.actionWordWrap.setChecked(self.cfg_session.index.get('worldWrap'))
    