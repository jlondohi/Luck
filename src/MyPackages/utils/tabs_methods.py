import os
#Importing PyQt6 packages
from PyQt6.QtWidgets import QMessageBox
from MyPackages import YamlHandler
#=============================================
#Creating functions related to tabs in general
#=============================================
def closeTab(self, tab_index, *args):
    #Getting the name of the tab
    tab_name = self.tabWidget.widget(tab_index).objectName 
    #The tab is not closable if it is 'Log' or 'Ecosystem'
    tab_text = self.tabWidget.tabText(tab_index)
    if ( tab_text.startswith('Log') or
        tab_text == self.i18nNes('tab-eco', 'eco') ):
        return None

    #Check for unsaved changes
    if self.unsavedChanges(tab_name):
        answer = self.showDialogSavingChanges()
        #Answer 'Save'
        if answer == QMessageBox.StandardButton.Save:
            #Saving changes and closing the tab
            save = self.savingChanges(tab_name)
            if save:
                self.tabInfo.pop(tab_name, None)
                self.tabWidget.removeTab(tab_index)
                #Saving session
                self.actualSession.saveSession(self.tabInfo)
                return None
            else:
                #Saving session
                self.actualSession.saveSession(self.tabInfo)
                return None
        #Answer 'Discard'
        elif answer == QMessageBox.StandardButton.Discard:
            #Discarding the changes and closing the tab
            self.tabInfo.pop(tab_name, None)
            self.tabWidget.removeTab(tab_index)
            #Save session
            self.actualSession.saveSession(self.tabInfo)
            return None
    else:
        #Close the tab without asking
        self.tabInfo.pop(tab_name, None)
        self.tabWidget.removeTab(tab_index)
        #Save session
        self.actualSession.saveSession(self.tabInfo)
        return None

#Function to determine unsaved changes        
def unsavedChanges(self, tab_name, *args):
    tab_data = self.tabInfo.get(tab_name)
    #If the Script is completely blank, it is allowed to continue
    if tab_data['text_editor'].toPlainText().strip() in ['', ' ']:
        return False
    #There are three conditions for which you must ask if you want to save
    ##1. Blank source or script changes
    if tab_data['origin'] == '':
        return True
    #2. Source not blank but local file nonexistent
    elif tab_data['origin'] != '' and not os.path.exists(tab_data['origin']):
        tab_data['origin'] = ''
        return True
    #3. Source not blank but existing local file
    elif tab_data['origin'] != '' and os.path.exists(tab_data['origin']):
        script_edit = tab_data['text_editor'].toPlainText()
        try:
            file = open(tab_data['origin'], 'r' , encoding='utf-8')
            script_org = file.read()
            file.close()
        except Exception as exc:
            script_org = ''
        if script_org != script_edit:
            return True
        else:
            return False

#Function to display dialog box, save changes?
def showDialogSavingChanges(self, *args): 
    dialogo = QMessageBox()
    dialogo.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
    dialogo.setWindowIcon(self.icon)
    dialogo.setIcon(QMessageBox.Icon.Question)
    dialogo.setWindowTitle(self.i18nNes('save-files', 'saveE1'))
    dialogo.setText(self.i18nNes('save-files', 'saveE2'))
    dialogo.setStandardButtons(QMessageBox.StandardButton.Save 
                               | QMessageBox.StandardButton.Discard 
                               | QMessageBox.StandardButton.Cancel)
    dialogo.setDefaultButton(QMessageBox.StandardButton.Save)
    answer = dialogo.exec()
    return answer

#Saving script changes
def savingChanges(self, tab_name = '', cls = 'save', *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None

    #Asking where to get the tab_data
    if tab_name == '':
        tab_name = self.tabWidget.currentWidget().objectName

    tab_data = self.tabInfo.get(tab_name)
    #Asking the save type
    if cls == 'save' and tab_data['origin'] != '':
        try:
            file = open(tab_data['origin'], 'w' , encoding = 'utf-8')
            file.write(tab_data['text_editor'].toPlainText() )
            file.close()
        except Exception as exc:
            tab_data['saved'] = False
            #Updating tab icons
            self.updateTabIcons()
            #Creating a QMessageBox instance to display the error message
            msg = QMessageBox()
            msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
            msg.setWindowIcon(self.icon)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle(self.i18nNes('execution', 'msgs', 'msgE'))
            msg.setText(str(exc))
            msg.exec()
            return False
        else:
            #Changing saved status
            tab_data['saved'] = True
            #Updating tab toolTips
            self.updateTabTooltips()
            #Updating tab icons
            self.updateTabIcons()
            return True
    if (cls == 'saveAs') or (tab_data['origin'] == ''):
        origin = self.saveFileAs()
        if origin == '':
            return False
        else: 
            try:
                file = open(origin, 'w', encoding = 'utf-8')
                file.write(tab_data['text_editor'].toPlainText())
                file.close()
            except:
                return False
            else:
                tab_data['origin'] = origin
                #Changing the tab name
                name = origin.rsplit('/', 1)[-1]
                index = self.tabWidget.currentIndex()
                self.tabWidget.setTabText(index, name)
                #Changing saved status
                tab_data['saved'] = True
                #Updating tab toolTips
                self.updateTabTooltips()
                #Updating tab icons
                self.updateTabIcons()
                return True

#Saving parameter changes
def savingChangesP(self, tab_name = '', cls = 'save', *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    #Asking where to get the tab_data
    if tab_name == '':
        tab_name = self.tabWidget.currentWidget().objectName

    tab_data = self.tabInfo.get(tab_name)
    #Asking the save type
    if cls == 'save' and tab_data['origin_param'] != '':
        origin = tab_data['origin_param']
        params = YamlHandler(origin)
        params.index = tab_data['dict_paramsEtl']
        return params.save()
    if (cls == 'saveAs') or (tab_data['origin_param']==''):
        origin = self.saveFilePAs()
        if origin == '':
            return False
        else:
            params = YamlHandler(origin)
            params.index = tab_data['dict_paramsEtl']
            tab_data['origin_param'] = origin
            return params.save()

#Function to move to previous tab
def goPreviousTab(self, *args):
    current_index = self.tabWidget.currentIndex()
    previous_index = (current_index - 1) % self.tabWidget.count()
    self.tabWidget.setCurrentIndex(previous_index)

#Function to move to next tab
def goNextTab(self, *args):
    current_index = self.tabWidget.currentIndex()
    next_index = (current_index + 1) % self.tabWidget.count()
    self.tabWidget.setCurrentIndex(next_index)