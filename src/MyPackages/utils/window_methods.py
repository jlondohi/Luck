
#Importing native packages
import os, sys, platform, subprocess, tempfile, winreg \
    , string, random, base64, getpass, socket
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from functools import partial
#Importing PyQt6 packages
from PyQt6.QtWidgets import (QFileDialog, QMessageBox, QTabBar, QToolButton)
from PyQt6.QtGui import (QCursor, QDragEnterEvent, QDropEvent, QIcon, QDesktopServices)
from PyQt6.QtCore import (Qt, QUrl)
#Importing custom classes and methods
from MyPackages import (AboutWidget, Updater, YamlHandler
    , MyResultTable, MyPlainTextEdit, MyParamsManager
    , MyTooltip, MySearchWidget)

#==================================================================
#Creating functions related to the main window
#==================================================================
#Function to create custom buttons for tabs
def createCustomCloseButton(self, tabIndex):
    tabWidget = self.tabWidget
    tabBar = tabWidget.tabBar()
    tab_name = tabWidget.widget(tabIndex).objectName
    btn = QToolButton(tabBar)
    btn.setObjectName("tabCloser")
    btn.setAutoRaise(True)
    btn.setCursor(Qt.CursorShape.ArrowCursor)
    btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    #Setting button
    tabBar.setTabButton(
        tabIndex,
        QTabBar.ButtonPosition.RightSide,
        btn
    )
    #Connecting the new button with the custom close
    btn.clicked.connect(partial(self.onTabCloseClicked, tab_name))

#Function to close the tab to which the close button belongs
def onTabCloseClicked(self, tab_name):
    #Searching among all the tabs which index corresponds to the name
    for i in range(self.tabWidget.count()):
        w = self.tabWidget.widget(i)
        if w and w.objectName == tab_name:
            self.closeTab(i)

#Function to update the tabBar toolTips
def updateTabTooltips(self):
    tabBar = self.tabWidget.tabBar()
    for tab_index in range(self.tabWidget.count()):
        tab_name = self.tabWidget.widget(tab_index).objectName
        tab_data = self.tabInfo.get(tab_name)
        if not tab_data:
            tabBar.setTabToolTip(tab_index, '')
            continue

        tooltip = self.buildTabTooltip(tab_data)
        tabBar.setTabToolTip(tab_index, tooltip)

#Function to update the tabBar icons
def updateTabIcons(self):
    tabBar = self.tabWidget.tabBar()
    currentIndex = self.tabWidget.currentIndex()
    #Going through each of the tabs
    for tab_index in range(self.tabWidget.count()):
        tab_name = self.tabWidget.widget(tab_index).objectName
        tab_data = self.tabInfo.get(tab_name)
        #Early release condition
        if not tab_data:
            continue
        #Early release condition
        btn = tabBar.tabButton(tab_index, QTabBar.ButtonPosition.RightSide)
        if not btn:
            continue

        #Setting final state ONCE
        if tab_data['saved']==False:
            newType = 'unsaved'
        elif tab_index == currentIndex:
            newType = 'active'
        elif tab_data['saved']==True:
            newType = 'saved'

        #Avoid unnecessary repainting
        if btn.property('type') == newType:
            continue

        btn.setProperty('type', newType)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

#Function to build the toolTips
def buildTabTooltip(self, tab_data: dict) -> str:
    #Pre-loading i18nNes
    _name       = self.i18nNes('tab-tooltips', 'name')
    _path       = self.i18nNes('tab-tooltips', 'path')
    _saved       = self.i18nNes('tab-tooltips', 'saved')
    _fetched    = self.i18nNes('tab-tooltips', 'fetched')
    _no_fetched = self.i18nNes('tab-tooltips', 'no-fetched')
    #Creating list of lines
    lines = []
    #Creating lines
    origin = tab_data['origin']
    origin = origin.replace('\\', '/')
    name = origin.rsplit('/', 1)[-1]
    if name:
        lines.append(f'{_name}: {name}')
        lines.append(f'{_path}: {origin}')
        lines.append(f"{_saved}: {tab_data['saved']}")
    if tab_data['rType'] == 'results':
        if tab_data['fetched']:
            lines.append(f'Resultado: {_fetched}')
        else:
            lines.append(f'Resultado: {_no_fetched}')
    return '\n'.join(lines)


#Function to establish language
def applySelectedLanguage(self, *args):
    self.lgg = self.sender().text()
    self.cfg_session.index['language'] = self.lgg
    #Saving the session
    self.cfg_session.save()
    #Restarting
    self.restartApp()

#Function that captures user topic selection
def captureProfileFormat(self, *args):
    sender = self.sender()
    #Verifying that the sender is not null and getting its text
    if not sender:
        return

    #Modifying default profile in cfg
    profileName = sender.text()
    self.cfg_session.index['internal_profile'] = profileName
    self.cfg_session.save()
    self.applyProfileFormat(profileName)

#Creating a function that is responsible for filling the styledSheets
def styler(self, profileName, *args):
    #Bringing all the information on the selected topic
    self.profile = self.dict_profiles[profileName]
    color1  = self.profile['editor-color_text']
    color2  = self.profile['editor-background-color']
    
    color3  = self.profile['editor-selection-bg-color']
    color4  = self.profile['editor-line-highlight']
    
    color5  = self.profile['result-color_text']
    color6  = self.profile['result-background-color']
    color7  = self.profile['result-alternate-background-color']
    color8  = self.profile['result-gridline-color']
    color9  = self.profile['result-highlight']
    color10 = self.profile['result-header-color']

    temp = self.profile['other_colors']
    color11 = temp['parameter_format'][0]

    color12 = self.profile['result-trafficlight'][2]

    #Modifying styleSheets templates
    format_args = {
        'QTabWidget':       [color10, color1, color2],
        'MyPlainTextEdit':  [color1, color2, color3],
        'MyParamsManager':  [color1, color2, color11, color12],
        'MyResultTable':    [color5, color6, color7, color8, color9, color10],
        'MyTooltip':        [color1, color2, color5, color6],
        'MyTreeView':       [color5, color6, color9],
        'QMessageBox':      [color1, color2],
        'MySearchWidget':   [color1, color2, color5, color6]
    }
    for key, args in format_args.items():
        self.dict_styledSheets[key] = self.dict_styleSheets[key].format(*args)
    return None
                    
#Function that applies profile as needed
def applyProfileFormat(self, profileName, cls = 'all', *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    self.styler(profileName)
    if cls == 'all':
        #Applying format to the widget
        self.tabWidget.setStyleSheet( self.dict_styledSheets['QTabWidget'] )
        
        #Applying changes to each plain text widget
        for editor in self.centralWidget().findChildren(MyPlainTextEdit):
            #Applying change to window
            editor.setStyleSheet( self.dict_styledSheets['MyPlainTextEdit'] )
            editor.updateSettings()
            #Applying change to each highlighter
            editor.highlighter.updateSettings(profileName)
            editor.highlighter.rehighlight()
            editor.highlightCurrentLine(True)
        
        #Applying changes to each param manager
        for manager in self.centralWidget().findChildren(MyParamsManager):
            #Applying change to window
            manager.setStyleSheet( self.dict_styledSheets['MyParamsManager'] )
            
        #Applying change to each result widget
        for result in self.centralWidget().findChildren(MyResultTable):
            result.setStyleSheet( self.dict_styledSheets['MyResultTable'] )
            result.delegate.updatePaint(profileName)
        
        #Applying changes to all MyTooltip
        for tootip in self.centralWidget().findChildren(MyTooltip):
            tootip.setStyleSheet( self.dict_styledSheets['MyTooltip'] )

        #Applying changes to the single tree
        self.dataBaseTree.setStyleSheet( self.dict_styledSheets['MyTreeView'] )

        #Applying changes to all QMessageBox
        for msg in self.centralWidget().findChildren(QMessageBox):
            msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )

        #Applying changes to all MySearchWidget
        for searcher in self.centralWidget().findChildren(MySearchWidget):
            searcher.setStyleSheet( self.dict_styledSheets['MySearchWidget'] )

    elif cls == 'result':
        #Applying format to the widget
        self.tabWidget.setStyleSheet( self.dict_styledSheets['QTabWidget'] )
        #Applying change to each result widget
        for result in self.centralWidget().findChildren(MyResultTable):
            result.setStyleSheet( self.dict_styledSheets['MyResultTable'] )
            result.delegate.updatePaint(profileName)
        
        #Applying changes to all MyTooltip
        for tootip in self.centralWidget().findChildren(MyTooltip):
            tootip.setStyleSheet( self.dict_styledSheets['MyTooltip'] )
        
        #Applying changes to the single tree
        self.dataBaseTree.setStyleSheet( self.dict_styledSheets['MyTreeView'] )

#Function to update the system icon V2
def updateTrayIcon(self, status=None, *args):
    #Status
    _running = self.i18nNes('execution', 'status', 'running')
    _executed = self.i18nNes('execution', 'status', 'executed')
    _failed = self.i18nNes('execution', 'status', 'failed')
    #Default value
    tl_1, tl_2, tl_3 = self.profile['result-trafficlight']
    #Defining the icon to display
    if status == _executed:
        #The value of executed is temporary
        icono = self.icon1
        self.iconTimer.start()
        self.bt_working.setStyleSheet(f'QPushButton{{ background-color: {tl_1};}}')
    elif status == _running:
        icono = self.icon2
        self.bt_working.setStyleSheet(f'QPushButton{{ background-color: {tl_2}; }}')
    elif status == _failed:
        icono = self.icon3
        self.bt_working.setStyleSheet(f'QPushButton{{ background-color: {tl_3}; }}')
    else:
        icono = self.icon
        self.bt_working.setStyleSheet(f'QPushButton{{ background-color: None; }}')
    #Updating the system icon
    self.trayIcon.setIcon(icono)
    self.setWindowIcon(icono)

#Function linked to QTimer iconTimer
def stopIconTimer(self, *args):
    self.iconTimer.stop()
    self.updateTrayIcon(None)

#Preparing frameworks
def prepareFramework(self, *args):
    #On most modern operating systems (Win, macOS, Linux),
    ##expanduser('~') is the safest and most standardized way to obtain the user profile.
    try:
        #This works on Windows, macOS and Linux without accessing the registry
        download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        #Additional validation for Windows: sometimes the folder is called 'Downloads' in the file system
        ##although internally 'Downloads' is usually a valid alias.
        if not os.path.exists(download_folder) and platform.system() == 'Windows':
            #Try to get it via environment variable if expanduser fails
            user_profile = os.getenv('USERPROFILE')
            if user_profile:
                download_folder = os.path.join(user_profile, 'Downloads')

        #If for some reason it does not exist (the custom system), it creates it
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
            
    except Exception as e:
        #Universal fallback in case of permissions or route error
        download_folder = os.getcwd() 

    self.cfg_app.index['dataPath'] = download_folder


#Function to initialize the window harmoniously with the monitor
def initWindow(self, *args):
    self.setWindowTitle('Luck')
    geometria = self.cfg_session.index.get('prede_geo')
    #Getting the geometry of the main monitor
    self.screen_width = self.screen().size().width()
    self.screen_height = self.screen().size().height()
    
    #Defining the initial window size relative to the monitor size
    x = int(self.screen_width * geometria[0])
    y = int(self.screen_height * geometria[1])
    ventana_width = int(self.screen_width * geometria[2])
    ventana_height = int(self.screen_height * geometria[3])
    #Adjusting x
    x = x if int(self.screen_width * geometria[0]) > 0 else 50
    self.setGeometry(x, y , ventana_width, ventana_height)
    self.normalGeo = self.normalGeometry()

#Function linked to dragEvent of the QTabWidget
#Determines if the dragged file is valid
def dragEnterEvent(self, event: QDragEnterEvent, *args):
    if event.mimeData().hasUrls():
        event.acceptProposedAction()
    else:
        event.ignore()

#Function linked to dropEvent of the QTabWidget
def dropEvent(self, event:QDropEvent, *args):
    data = event.mimeData()
    final_list = self.prepareUrlsDrop(data, '.sql')

    #Checking opening flow
    if len(final_list) == 1:
        try:
            self.newScriptTab(final_list[0])
            event.acceptProposedAction()
        except ValueError:
            msg = QMessageBox()
            msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
            msg.setWindowIcon(self.icon)
            msg.setIcon(QMessageBox.Icon.Critical)  
            msg.setWindowTitle(self.i18nNes('msgs', 'msg2'))
            msg.setText(self.i18nNes('msgs', 'msg3'))
            msg.exec()
        return None
    elif len(final_list) > 1:
        msg = QMessageBox(self)
        msg.setWindowIcon(self.icon)
        msg.setWindowTitle(self.i18nNes('open-file', 'open1'))
        msg.setText(self.i18nNes('open-file', 'open3'))
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        answer = msg.exec()
        #Dilemma according to answer from the previous message
        if answer == QMessageBox.StandardButton.Yes:
            self.openBlockFiles(False, final_list)
        else:
            self.openFile(False, final_list)
        event.acceptProposedAction()
    else:
        event.ignore()

#Function linked to dropEvent of the parameters
def dropEventParam(self, event:QDropEvent, *args):
    data = event.mimeData()
    final_list = self.prepareUrlsDrop(data, ('.sqlp', '.txt'))

    #Checking opening flow
    if len(final_list)==1:
        try:
            self.addParmScriptTab(final_list[0])
            event.acceptProposedAction()
        except ValueError:
            msg = QMessageBox()
            msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
            msg.setWindowIcon(self.icon)
            msg.setIcon(QMessageBox.Icon.Critical)  
            msg.setWindowTitle(self.i18nNes('msgs', 'msg2'))  
            msg.setText(self.i18nNes('msgs', 'msg3'))
            msg.exec()
        return None
    elif len(final_list)>1:
        msg = QMessageBox(self)
        msg.setWindowIcon(self.icon)
        msg.setWindowTitle(self.i18nNes('open-file', 'openP1'))
        msg.setText(self.i18nNes('open-file', 'openP2'))
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        answer = msg.exec()
        #Dilemma according to answer from the previous message
        if answer == QMessageBox.StandardButton.Yes:
            self.openBlockFilesP(False, final_list)
        else:
            self.openFileP(False, final_list)
        event.acceptProposedAction()
    else:
        event.ignore()

#Function to prepare the list of urls contributed in the drag and drop event
def prepareUrlsDrop(self, data, types:str, *args):
    #Creating a valid list of URLS
    urls = data.urls()
    other_urls = data.text().split('file:///')
    ##File explorer URLS have priority
    if len(urls)>0:
        final_list = []
        for url in list( data.urls() ):
            file_path = url.toLocalFile()
            if file_path.endswith(types):
                final_list += [file_path]
    elif len(other_urls)>0:
        final_list = []
        for _list in other_urls:
            full_url = _list.split('\n')
            for url in full_url:
                if url.lower().endswith(types) and os.path.exists(url):
                    final_list += [url]
    return final_list

#Functions to save the splitter sizes from ecosystem tab
def saveEcoSplittersSizes(self, pos, index, *args):
    sizes = self.splitter_eco.sizes()
    total = sum(sizes)
    if total == 0:
        return
    geo = [round(s / total, 4) for s in sizes]
    self.cfg_session.index['splitter_geo_eco'] = geo

#Functions to apply the new sizes within the ETL editors tab
##Horizontal
def syncSplitterH(self, pos, *args):      
    #Avoiding recursion
    if self.updating_splits:
        return
    #Raising flag to avoid recursion
    self.updating_splits = True
    #Emiting signal to update the splitter
    self.splitHChanged.emit(pos)
    #Calculating the new geometry
    ref = self.size().width() - 39
    geo = round(pos / ref, 4)
    #Avoiding save full screens results
    if geo >= 0.2:
        self.cfg_session.index['splitter_geo'][0] = abs(geo)  
    #Going down the recursion flag
    self.updating_splits = False

#Functions to apply the new sizes within the ETL editors tab  
##Vertical
def syncSplitterV(self, pos, *args):
    if self.updating_splits:
        return
    #Raising flag to avoid recursion
    self.updating_splits = True
    #Emiting signal to update the splitter
    self.splitVChanged.emit(pos)
    #Calculating the new geometry
    ref = self.size().height() - 131
    geo = round(pos / ref, 4)
    self.cfg_session.index.get('splitter_geo')[1] = abs(geo)
    #Going down the recursion flag
    self.updating_splits = False

#Function to restore etl and result panels
def panelizeFrame(self, event, *args):
    self.fm_title.bt_panelize.hide()
    self.fm_title.bt_expand.show()
    #Returning to default values
    ref = self.size().width()-39
    geo = self.cfg_session.index.get('splitter_geo')[0]
    pos = int(geo*ref)
    self.syncSplitterH(pos)

#Function to expand results to 100% of the window
def expandFrame(self, event, *args):
    self.fm_title.bt_panelize.show()
    self.fm_title.bt_expand.hide()
    self.syncSplitterH(0)

#Function to restore user default profile
def darkenFrame(self, event, *args):
    self.fm_title.bt_light.show()
    self.fm_title.bt_dark.hide()
    #Applying default profile
    profileName = self.cfg_session.index.get('internal_profile')
    self.applyProfileFormat(profileName, 'result')
    #Applying other changes to each result widget
    for result in self.centralWidget().findChildren(MyResultTable):
        result.delegate.rType = result.rType
    
#Function to momentarily illuminate the frames
def lightenFrame(self, event, *args):
    self.fm_title.bt_light.hide()
    self.fm_title.bt_dark.show()
    #Applying classic profile
    profileName = 'Clasico'
    self.applyProfileFormat(profileName, 'result')
    #Applying other changes to each result widget
    for result in self.centralWidget().findChildren(MyResultTable):
        result.delegate.rType = 'base'

#Function to set the base setter
def baseSetter(self, event, *args):
    if self.fm_title.bt_baseSetter.property('baseSetter') == False:
        #Changing the icon and name to set
        self.fm_title.bt_baseSetter.setIcon(self.baseUnSetterIcon)
        #Changin the object name to set
        self.fm_title.bt_baseSetter.setProperty('baseSetter', True)
        self.cfg_session.index['baseSetter'] = True
        self.cfg_session.save()
        #Tooltip
        tootip = self.i18nNes('tooltips', 'tb8')
        sc = self.shc('buttons', 'styler')
        tootip = tootip if not sc else tootip + f' ({sc})'
        self.fm_title.bt_baseSetter.setToolTip(tootip)
        self.current_result.viewport().update()

    elif self.fm_title.bt_baseSetter.property('baseSetter') == True:
        #Changing the icon and name to unset
        self.fm_title.bt_baseSetter.setIcon(self.baseSetterIcon)
        #Changin the object name to unset
        self.fm_title.bt_baseSetter.setProperty('baseSetter', False)
        self.cfg_session.index['baseSetter'] = False
        self.cfg_session.save()
        #Tooltip
        tootip = self.i18nNes('tooltips', 'tb7')
        sc = self.shc('buttons', 'styler')
        tootip = tootip if not sc else tootip + f' ({sc})'
        self.fm_title.bt_baseSetter.setToolTip(tootip)
        self.current_result.viewport().update()

#Function to open the downloads folder
def openDownloadsFolder(self, *args):
    path = self.cfg_app.index['dataPath']
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin': #MacOS
        subprocess.run(['open', path])
    else:  #Linux and others
        subprocess.run(['xdg-open', path])

#Function to show menus
def showMenu(self, cls, *args):
    if cls == 'file':
        self.menuFile.exec(self.fm_title.bt_file.mapToGlobal(self.fm_title.bt_file.rect().bottomLeft()))
    elif cls == 'edit':
        self.menuEdit.exec(self.fm_title.bt_edit.mapToGlobal(self.fm_title.bt_edit.rect().bottomLeft()))
    elif cls == 'select':
        self.menuSelect.exec(self.fm_title.bt_select.mapToGlobal(self.fm_title.bt_select.rect().bottomLeft()))
    elif cls == 'view':
        self.menuView.exec(self.fm_title.bt_view.mapToGlobal(self.fm_title.bt_view.rect().bottomLeft()))
    elif cls == 'go':
        self.menuGo.exec(self.fm_title.bt_go.mapToGlobal(self.fm_title.bt_go.rect().bottomLeft()))
    elif cls == 'sql':
        self.menuSQL.exec(self.fm_title.bt_sql.mapToGlobal(self.fm_title.bt_sql.rect().bottomLeft()))
    elif cls == 'help':
        self.menuHelp.exec(self.fm_title.bt_help.mapToGlobal(self.fm_title.bt_help.rect().bottomLeft()))
    elif cls == 'assistant':
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        self.menuAssistant.exec(self.mapToGlobal(cursor_pos))
    elif cls == 'tmplts':
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        self.manuTemplates.exec(self.mapToGlobal(cursor_pos))
    elif cls == 'ai':
        self.menuAI.exec(self.fm_title.bt_ai.mapToGlobal(self.fm_title.bt_ai.rect().bottomLeft()))

#Defining what to do when closing the window
def closeEvent(self, event, *args):
    #Saving settings when closing the window
    self.cfg_session.save()
    #Saving session
    self.actualSession.saveSession(self.tabInfo)
    #Saving log
    if self.recordingLog:
        self.recLog()
    #Closing
    print(f"Luck ended well {datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')}")
    
    #Closing second thread
    #---------------------
    self.editorThread.quit()
    self.editorThread.deleteLater
    self.asyncExecute.quit()
    self.asyncExecute.deleteLater
    self.asyncConnMan.quit()
    self.asyncConnMan.deleteLater()

    #Closing
    event.accept()

#Function to open SQL files
def openFile(self, dialog=True, fileNames=[], *args):
    if dialog:
        fileNames, _ = QFileDialog.getOpenFileNames(
            self, self.i18nNes('open-file', 'open2')
            , '', f"{self.i18nNes('open-file', 'openSQL')} (*.sql)")
    if fileNames:
        for fileName in fileNames:
            self.newScriptTab(fileName)

#Function to open parameter files
def openFileP(self, dialog=True, fileName='', *args):
    if dialog:
        fileName, _ = QFileDialog.getOpenFileName(
            self, self.i18nNes('open-file', 'open2')
            , '', f"{self.i18nNes('open-file', 'openP3')} (*.sqlp)")
    if fileName:
        self.addParmScriptTab(fileName)

#Function to open files in SQL blocks
def openBlockFiles(self, dialog=True, fileNames=[], *args):
    if dialog:
        fileNames, _ = QFileDialog.getOpenFileNames(
            self, self.i18nNes('open-file', 'open2')
            , '', f"{self.i18nNes('open-file', 'openSQL')} (*.sql)")
    if fileNames:
        #Changing mouse pointer to standby state
        self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        combined_content = ''
        #Opening files in order
        count = 0
        for fileName in fileNames:
            count += 1
            with open(fileName, 'r', encoding='utf-8') as file:
                content = file.read()
                combined_content += \
                    '--'+'#'*40 + '\n' \
                    + '--#- Bloque {}: {}'.format(count, str(fileName).rsplit('/', 1)[-1]) \
                    + '\n' + '--'+'#'*40 + '\n'*2 \
                    + content \
                    + '\n'*2
        
        #Saving combined content to a file in downloads
        temp_file = os.path.join(self.cfg_app.index.get('dataPath'), 'combined_script.sql')
        #Checking which file does not exist
        count = 1
        while os.path.exists(temp_file):
            temp_file = os.path.join(self.cfg_app.index.get('dataPath'), f'combined_script ({count}).sql')
            count += 1
        #Saving file
        with open(temp_file, 'w', encoding='utf-8') as temp:
            temp.write(combined_content)
        #Changing mouse pointer to default state
        self.app.restoreOverrideCursor()
        #Concatenated loading
        self.newScriptTab(temp_file)

#Function to open bulk SQL parameter files
def openBlockFilesP(self, dialog=True, fileNames=[], *args):
    if dialog:
        fileNames, _ = QFileDialog.getOpenFileNames(
            self, self.i18nNes('open-file', 'open2')
            , '', f"{self.i18nNes('open-file', 'openSQL')} (*.sqlp *.txt)")
    if fileNames:
        #Changing mouse pointer to standby state
        self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        combined_params = {}
        #Opening files in order
        count = 0
        for fileName in fileNames:
            count += 1
            param = YamlHandler(fileName).index
            combined_params = {**combined_params, **param}
        
        #Checking that the target file does not exist
        count = 1
        temp_file = os.path.join(self.cfg_app.index.get('dataPath'), 'combined_params.sqlp')
        while os.path.exists(temp_file):
            temp_file = os.path.join(self.cfg_app.index.get('dataPath'), f'combined_params ({count}).sqlp')
            count += 1
        #Saving the parameters combined in a file in downloads
        final_params = YamlHandler(temp_file)
        final_params.index = combined_params
        final_params.save()
        
        #Changing mouse pointer to default state
        self.app.restoreOverrideCursor()
        #Concatenated loading
        self.addParmScriptTab(temp_file)
        self.updatePManager()

#Function to reload the ETL
def reloadETL(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    #Getting the name of the tab
    tab_name = self.tabWidget.currentWidget().objectName
    tab_data = self.tabInfo.get(tab_name)
    if tab_data['origin'] != '':
        #Loading the ETL again
        origin = tab_data['origin'] 
        textEditor = tab_data['text_editor']
        file = open(origin, 'r' , encoding='utf-8')
        textEditor.setPlainText( file.read() )
        file.close()
        #Save session
        self.actualSession.saveSession(self.tabInfo)

#Function to save SQL files
def saveFileAs(self, *args):
    fileName, _ = QFileDialog.getSaveFileName(
        self, self.i18nNes('save-files', 'save2')
        , '', f"{self.i18nNes('save-files', 'toFile6')} (*.sql)")
    if fileName:
        return fileName
    else: 
        return ''

#Function to save parameter files
def saveFilePAs(self, *args):
    fileName, _ = QFileDialog.getSaveFileName(
        self, self.i18nNes('save-files', 'save2')
        , '', f"{self.i18nNes('save-files', 'toFile7')} (*.sqlp)")
    if fileName:
        return fileName
    else: 
        return ''

#About window
def showAcercaDe(self, *args):
    self.aboutOfWindow = AboutWidget(self)
    self.aboutOfWindow.setStyleSheet( self.dict_themeSheets[self.globalTheme].rendered )
    self.aboutOfWindow.show()

#Decompose version
def decomposeVersion(version:str, *args):
    #Closing early
    if not version:
        return
    #Eliminating V from the version, if applied
    version = version.lower()
    if version.startswith('v'):
        version = version[1:]
    #Transforming the version entered
    major, minor, patch = map(int, version.split('.'))
    return major, minor, patch

#Function to compare versions
#True if the current version is lower
def compareVersion(WebVersion, currentVersion, *args):
    majorW, minorW, pathW = decomposeVersion(WebVersion)
    majorC, minorC, pathC = decomposeVersion(currentVersion)
    versionW = majorW*10000 + minorW*100 + pathW
    versionC = majorC*10000 + minorC*100 + pathC
    #Comparing
    return True if versionW > versionC else False

#Software update
def startUpdate(self, silent=False, *args):
    error = False
    #Microsoft Store update
    #----------------------
    #Identifying if the execution is in an MSIX environment
    #In these environments the update is done through the application store
    if "APPX_PACKAGE_FAMILY_NAME" in os.environ:
        #Creating informative message and allowing the user to be redirected to the app page
        msg = QMessageBox()
        msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
        msg.setWindowIcon(self.icon)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(self.i18nNes('update-app', 'title4'))
        msg.setText(self.i18nNes('update-app', 'msix-info'))
        answer = msg.exec()
        if answer == QMessageBox.StandardButton.Ok:
            url = self.version.index.get('msix_url')
            QDesktopServices.openUrl(QUrl(url))
        return
    
    #GitHub update
    #--------------
    #Instantiating updater
    updater = Updater(self)
    updater.server_url = self.version.index.get('github_url')
    current_version = self.version.index.get('version')
    
    #Requesting official version in repo (web)
    try:
        web_version = updater.checkForUpdate()
    except:
        error = True
    else:
        if web_version.startswith('error'):
            error = True
    
    if error:
        msg = QMessageBox()
        msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
        msg.setWindowIcon(self.icon)
        # msg.setIcon(QMessageBox.Icon.Information)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(self.i18nNes('update-app', 'title3'))
        msg.setText(self.i18nNes('update-app', 'connection-error')) 
        answer = msg.exec()
        return

    #Comparing versions
    outdated = compareVersion(web_version, current_version)
    #Ending early
    if silent and not outdated:
            return

    #Creating message according to the case
    if outdated:
        msg = QMessageBox()
        msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
        msg.setWindowIcon(self.icon)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(self.i18nNes('update-app', 'title2'))
        msg.setText(f'{web_version}')
        msg.setText(f"{self.i18nNes('update-app', 'outdated')}: {web_version}")
        answer = msg.exec()
        #Downloading or discarding
        if answer == QMessageBox.StandardButton.Yes:
            #Downloading the update
            web_version = updater.downloadUpdate()
        elif answer == QMessageBox.StandardButton.No:
            return
    else:
        msg = QMessageBox()
        msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(self.i18nNes('update-app', 'title1'))
        msg.setText(f'{web_version}')
        msg.setText(f"{self.i18nNes('update-app', 'update')}: {current_version}")
        msg.exec()

def disguiseFrame(self, *args):
    info2    = 'KP5wSd9foRj+c9puxDUr8JKuH0l4hnDnRlMDceF7wybYLKOTsqHZBPcri94nHTup1Gns3mOx3jgHpiUXBdxtRqZOCpWFzFyTSUzrAJLkMvHE0eeA7c/MUCAoMtKTt/VP1qb3+zcidaYp4XsUkxwc1euqPPVavMpbfZX8HOgQSHislTG8dogfPnKnOLbeL6BzWqNypjo0KWywOYyCLgcbs8m6P6dWpPKoaewRfcDkmRPtE33XPnMjI5bXiG8hkiJTVXHStkesCcI2ftu8BmrQ54+JLlgtJ6QxA2en3r8OlgG13yHZIvOCKPCZkqVEbk+pA7weyiwP1UE3sY1zQumwvQOIyPvPYX4s4NLtyjOnJtTUs3Z7nhs5uisAB1PYAfEA/La8d6gUdZcGOYndpSaHARdkO9C8UkJ8sUoKJzZ2CII9SOYg7uwPegOT4w/KKNLwM4iPkDBKLLEpC+soXsPT+u2Td43fA/H3uvnofult/IaXgV6KCFa9lP3tuZ1mocCp9qAlAJEOeyES9vcwCANo1Z+fhFCcAowrL4/iDqprXfgBdqk58IdfLJstkzNJ/hQCkvy9DUbOhddTHNIYBhHGxugob08lyNH8CpMUWYDQ+QApK5oEwEWJ/vujY5GwAppJ//Ntqi3z+TLt943LyC0E762U877IVkRSx2FE3bZExhjfDEsFiTn5jO4X0Z4RPogFtFe7kPb0y66gbRK/0TPDUCYSV7wfcgUM8VQNkKyvcpCpJIGDoaLVQZsp03TF8PHaVVgurKbJJonyqraw2enzIozfB6kpdGlgfBGAnoBfHwQ='
    msg_comp = base64.b64decode(info2)
    iv       = msg_comp[:16]
    msg_cif  = msg_comp[16:]
    cipher   = AES.new(b'wa8P4bbhboiKKCRe', AES.MODE_CBC, iv=iv)
    msg_org  = unpad(cipher.decrypt(msg_cif), AES.block_size).decode()
    rnn      = ''.join(random.choice( string.ascii_lowercase ) for _ in range(3))
    path     = os.path.join(tempfile.gettempdir(), 'Luck', f'{rnn}.sql')
    arcv     = open( path, 'w' , encoding='utf-8')
    arcv.write( msg_org )
    arcv.close()
    self.newScriptTab(path)
    os.remove(path)

def disguiseFrameOff(self, *args):
    self.clickLabelCount = 0

def labelTitleClicked(self, event, *args):
    if event.button() == Qt.MouseButton.RightButton and event.modifiers() == Qt.KeyboardModifier.AltModifier:
        self.clickLabelCount += 1
        if self.clickLabelCount == 3:
            self.timerDsgs.start()
            self.disguiseFrame()
            self.clickLabelCount = 0
    else:
        self.mousePressEvent(event)

#-------------------------------------------------
# Functions focused on moving or rescaling window
#-------------------------------------------------
#Click position grabber
def mousePressEvent(self, event, *args):
    #Capturing the mouse position. Globally
    self.clickPosition = event.globalPosition().toPoint()
    #Identifying if there is a click
    if event.button() == Qt.MouseButton.LeftButton:
        #Wondering if we're on the edge
        edge, _ = self.getResizingEdge(event.pos())
        if edge:
            #activating window resizing
            self.onResizing = True
            self.resizing_edge = edge
        else:
            self.draggable = True
            self.dragPosition = event.globalPosition().toPoint() - self.pos()
    super(self.__class__, self).mousePressEvent(event)

#Resetting variables when the click is released when changing size
def mouseReleaseEvent(self, event, *args):
    self.draggable = False
    self.onResizing = False
    if not self.parentWindow.isMaximized():
        #Getting current window position
        x = self.geometry().x()/self.screen_width
        y = self.geometry().y()/self.screen_height
        #Getting current window size
        width = self.geometry().width()/self.screen_width
        height = self.geometry().height()/self.screen_height
        #Saving the geometry in the session config
        #It is important to respect the limits
        self.cfg_session.index.get('prede_geo')[0] = min(abs(round(x, 4)), 0.3)
        self.cfg_session.index.get('prede_geo')[1] = min(abs(round(y, 4)), 0.3)
        self.cfg_session.index.get('prede_geo')[2] = min(abs(round(width, 4)), 0.7)
        self.cfg_session.index.get('prede_geo')[3] = min(abs(round(height, 4)), 0.7)
    super(self.__class__, self).mouseReleaseEvent(event)

#Function to identify the edge of an object
def getResizingEdge(self, pos, *args):
    grip_size = 5
    rect = self.rect()

    left = pos.x() <= grip_size
    right = pos.x() >= rect.width() - grip_size
    top = pos.y() <= grip_size
    bottom = pos.y() >= rect.height() - grip_size

    if left and top:
        #return Qt.TopLeftCorner, Qt.SizeFDiagCursor
        return None, Qt.CursorShape.ArrowCursor
    elif left and bottom:
        #return Qt.BottomLeftCorner, Qt.SizeBDiagCursor
        return None, Qt.CursorShape.ArrowCursor
    elif right and top:
        #return Qt.TopRightCorner, Qt.SizeBDiagCursor
        return None, Qt.CursorShape.ArrowCursor
    elif right and bottom:
        return Qt.Corner.BottomRightCorner, Qt.CursorShape.SizeFDiagCursor
    elif left:
        return Qt.Edge.LeftEdge, Qt.CursorShape.SizeHorCursor
    elif right:
        return Qt.Edge.RightEdge, Qt.CursorShape.SizeHorCursor
    elif top:
        return Qt.Edge.TopEdge, Qt.CursorShape.SizeVerCursor
    elif bottom:
        return Qt.Edge.BottomEdge, Qt.CursorShape.SizeVerCursor
    else:
        return None, Qt.CursorShape.ArrowCursor

def disguisiFrame(self, *args):
    #PENDING
    None

#Function to change the size of the main window
def changeSizeWindow(self, global_pos, *args):
    rect = self.geometry()
    #Simple movements: left, right, up, down
    if self.resizing_edge == Qt.Edge.LeftEdge:
        rect.setLeft(global_pos.x())
    elif self.resizing_edge == Qt.Edge.RightEdge:
        rect.setRight(global_pos.x())
    elif self.resizing_edge == Qt.Edge.TopEdge:
        rect.setTop(global_pos.y())
    elif self.resizing_edge == Qt.Edge.BottomEdge:
        rect.setBottom(global_pos.y())
    
    #Combined movements
    elif self.resizing_edge == Qt.Corner.TopLeftCorner:
        rect.setTopLeft(global_pos)
    elif self.resizing_edge == Qt.Corner.TopRightCorner:
        rect.setTopRight(global_pos)
    elif self.resizing_edge == Qt.Corner.BottomLeftCorner:
        rect.setBottomLeft(global_pos)
    elif self.resizing_edge == Qt.Corner.BottomRightCorner:
        rect.setBottomRight(global_pos)
    self.setGeometry(rect)

#Overriding system stop event
def focusOutEvent(self, event, *args):
    self.setCursor(Qt.CursorShape.ArrowCursor)
    super(self.__class__, self).focusOutEvent(event)

#Overriding system focus exit event
def leaveEvent(self, event, *args):
    self.setCursor(Qt.CursorShape.ArrowCursor)
    super(self.__class__, self).leaveEvent(event)

#Function to move or stop when the window is moved (fmBar)
def mouseMoveEvent_fmBarra(self, event, *args):
    if event.buttons() == Qt.MouseButton.NoButton:
        #Wondering if we're on the edge
        window_pos = self.mapFromGlobal( event.globalPosition().toPoint() )
        edge, cursor_shape = self.getResizingEdge(window_pos)
        self.setCursor(cursor_shape)
    #We only activate the move when the left click is pressed
    elif event.buttons() & Qt.MouseButton.LeftButton:
        #Resizing window in case of edge event
        if self.onResizing:
            self.changeSizeWindow(event.globalPosition().toPoint())
            return

#Function to move or stop when the window is moved (fmBar)
def mouseMoveEvent_fmPrincipal(self, event, *args):
    if event.buttons() == Qt.MouseButton.NoButton:
        #Wondering if we're on the edge
        window_pos = self.mapFromGlobal(event.globalPosition().toPoint())
        edge, cursor_shape = self.getResizingEdge(window_pos)
        self.setCursor(cursor_shape)
    #We only activate the move when the left click is pressed
    elif event.buttons() & Qt.MouseButton.LeftButton:
        #Resizing window in case of edge event
        if self.onResizing:
            self.changeSizeWindow(event.globalPosition().toPoint())
            return

