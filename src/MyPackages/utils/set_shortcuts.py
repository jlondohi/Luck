#Importing PyQt6 packages
from PyQt6.QtGui import (QKeySequence, QShortcut, QCursor)

#===========================================================
#Setting all Shortcuts
#===========================================================
def setShortcuts(self, *args):
    #-------------------------------------
    #1. Creating their respective shortCut
    #-------------------------------------
    
    #MENUS
    #----------------------------------------------
    #menu New
    self.actionNew.setShortcut(self.shc('file', 'new'))
    self.actionOpen.setShortcut(self.shc('file', 'open'))
    self.actionOpenBlock.setShortcut(self.shc('file', 'open-block'))
    self.actionReload.setShortcut(self.shc('file', 'reload'))
    self.actionSave.setShortcut(self.shc('file', 'save'))
    self.actionSaveAs.setShortcut(self.shc('file', 'save-as'))
    self.actionOpenP.setShortcut(self.shc('file', 'open-param'))
    self.actionOpenBlockP.setShortcut(self.shc('file', 'open-param-block'))
    self.actionSaveP.setShortcut(self.shc('file', 'save-param'))
    self.actionSaveAsP.setShortcut(self.shc('file', 'save-param-as'))
    self.actionClose.setShortcut(self.shc('file', 'close'))
    #Menu Edit
    self.actionSearch.setShortcut(self.shc('edit', 'search'))
    self.actionReplace.setShortcut(self.shc('edit', 'replace'))
    self.actionComment.setShortcut(self.shc('edit', 'comment'))
    self.actionSuperComment.setShortcut(self.shc('edit', 'super-com'))
    #Menu Select
    self.actionSelectToPrevQuery.setShortcut(self.shc('select', 'stpq'))
    self.actionSelectToNextQuery.setShortcut(self.shc('select', 'stnq'))
    self.actionSelNextOcurrence.setShortcut(self.shc('select', 'snexo'))
    self.actionAddCursorToLinesEnd.setShortcut(self.shc('select', 'acel'))
    self.actionAddCursorToLinesStart.setShortcut(self.shc('select', 'acsl'))
    self.actionAddCursorAbove.setShortcut(self.shc('select', 'ac-above'))
    self.actionAddCursorBelow.setShortcut(self.shc('select', 'ac-below'))
    #Menu View
    QShortcut(QKeySequence(self.shc('view', 'profile')), self, 
        activated=lambda: self.menuProfile.popup(QCursor.pos()))
    QShortcut(QKeySequence(self.shc('view', 'font')), self, 
        activated=lambda: self.menuFont.popup(QCursor.pos()))
    self.actionSizeEditor_up.setShortcut(self.shc('view', 'ifse'))
    self.actionSizeEditor_down.setShortcut(self.shc('view', 'lfse'))
    self.actionSizeResult_up.setShortcut(self.shc('view', 'ifsr'))
    self.actionSizeResult_down.setShortcut(self.shc('view', 'lfsr'))
    self.actionTabSpace.setShortcut(self.shc('view', 'tab-space'))
    self.actionResultFetch.setShortcut(self.shc('view', 'result-fetch'))
    self.actionWordWrap.setShortcut(self.shc('view', 'ww'))
    #Menu Go
    self.actionGoStartDocument.setShortcut('Ctrl+Home')
    self.actionGoEndDocument.setShortcut('Ctrl+End')
    self.actionGoToLineBlock.setShortcut(self.shc('go', 'goto'))
    self.actionPrevQuery.setShortcut(self.shc('go', 'prev-q'))
    self.actionNextQuery.setShortcut(self.shc('go', 'next-q'))
    self.actionPrevBlock.setShortcut(self.shc('go', 'prev-block'))
    self.actionNextBlock.setShortcut(self.shc('go', 'next-block'))
    self.actionNextTab.setShortcut(self.shc('go', 'pt'))
    self.actionPreviousTab.setShortcut(self.shc('go', 'nt'))
    #Menu SQL
    QShortcut(QKeySequence(self.shc('sql', 'sel-dsn')), self, 
        activated=lambda: self.menuSelectDSN.popup(QCursor.pos()))
    self.actionConnectDSN.setShortcut(self.shc('sql', 'con-dsn'))
    self.actionStopRun.setShortcut(self.shc('sql', 'stop-run'))
    self.actionRun.setShortcut(self.shc('sql', 'run-query'))
    self.actionRunAll.setShortcut(self.shc('sql', 'run-all'))
    self.actionSaveResult.setShortcut(self.shc('sql', 'save-result'))
    self.actionSaveResultAs.setShortcut(self.shc('sql', 'save-result-as'))
    self.actionFile_to_lz.setShortcut(self.shc('sql', 'ufftlz'))
    self.actionShowTemplates.setShortcut(self.shc('sql', 'tmplts'))
    self.actionShowAssistant.setShortcut(self.shc('sql', 'assistant'))
    self.actionRecLog.setShortcut(self.shc('sql', 'start/end-log'))
    #Menu Help
    self.actionAbout.setShortcut(self.shc('help', 'about'))
    self.actionUpdate.setShortcut(self.shc('help', 'update'))

    #BUTTONS
    #----------------------------------------------
    #Note: These shurtcut do not need to be added to the centralwidget
    self.fm_title.bt_downloads.setShortcut(self.shc('buttons', 'downloads'))
    self.fm_title.bt_baseSetter.setShortcut(self.shc('buttons', 'styler'))
    self.fm_title.bt_light.setShortcut(self.shc('buttons', 'lighter'))
    self.fm_title.bt_dark.setShortcut(self.shc('buttons', 'darker'))
    self.fm_title.bt_panelize.setShortcut(self.shc('buttons', 'panelize'))
    self.fm_title.bt_expand.setShortcut(self.shc('buttons', 'expand'))

    #--------------------------
    #2. Adding to centralwidget
    #--------------------------
    #Actions File
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
    self.centralwidget.addAction(self.actionClose)
    #Actions Edit
    self.centralwidget.addAction(self.actionSearch)
    self.centralwidget.addAction(self.actionReplace)
    self.centralwidget.addAction(self.actionComment)
    self.centralwidget.addAction(self.actionSuperComment)
    #Actions Select
    self.centralwidget.addAction(self.actionSelectToPrevQuery)
    self.centralwidget.addAction(self.actionSelectToNextQuery)
    self.centralwidget.addAction(self.actionPrevBlock)
    self.centralwidget.addAction(self.actionNextBlock)
    self.centralwidget.addAction(self.actionSelNextOcurrence)
    self.centralwidget.addAction(self.actionAddCursorToLinesEnd)
    self.centralwidget.addAction(self.actionAddCursorToLinesStart)
    self.centralwidget.addAction(self.actionAddCursorAbove)
    self.centralwidget.addAction(self.actionAddCursorBelow)
    #Actions Go
    self.centralwidget.addAction(self.actionGoToLineBlock)
    self.centralwidget.addAction(self.actionPrevQuery)
    self.centralwidget.addAction(self.actionNextQuery)
    self.centralwidget.addAction(self.actionNextTab)
    #Actions View
    self.centralwidget.addAction(self.actionSizeEditor_up)
    self.centralwidget.addAction(self.actionSizeEditor_down)
    self.centralwidget.addAction(self.actionSizeResult_up)
    self.centralwidget.addAction(self.actionSizeResult_down)
    self.centralwidget.addAction(self.actionPreviousTab)
    self.centralwidget.addAction(self.actionTabSpace)
    self.centralwidget.addAction(self.actionResultFetch)
    self.centralwidget.addAction(self.actionWordWrap)
    #Actions SQL
    self.centralwidget.addAction(self.actionConnectDSN)
    self.centralwidget.addAction(self.actionStopRun)
    self.centralwidget.addAction(self.actionRun)
    self.centralwidget.addAction(self.actionRunAll)
    self.centralwidget.addAction(self.actionFile_to_lz)
    self.centralwidget.addAction(self.actionSaveResult)
    self.centralwidget.addAction(self.actionSaveResultAs)
    self.centralwidget.addAction(self.actionShowTemplates)
    self.centralwidget.addAction(self.actionShowAssistant)
    self.centralwidget.addAction(self.actionRecLog)
    #Actions Help
    self.centralwidget.addAction(self.actionAbout)
    self.centralwidget.addAction(self.actionUpdate)
    