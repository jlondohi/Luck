import os
#Importing PyQt6 packages
from PyQt6.QtWidgets import QMessageBox
#=============================================
#Creating functions related to tabs in general
#=============================================
def closeTab(self, tab_index):
    #Getting the name of the tab
    tab_name = self.tabWidget.widget(tab_index).objectName 
    #The tab is not closable if it is "Log" or "Ecosystem"
    tab_text = self.tabWidget.tabText(tab_index)
    if ( tab_text.startswith("Log") or
        tab_text == self.i18n.getNested("tab-eco", "eco") ):
        return None

    #Check for unsaved changes
    if self.unsavedChanges(tab_name):
        answer = self.showDialogSavingChanges()
        #Answer "Save"
        if answer == QMessageBox.StandardButton.Save:
            #Saving changes and closing the tab
            save = self.savingChanges(tab_name)
            if save:
                self.removeTabWidgets(tab_name)
                self.tabWidget.removeTab(tab_index)
                #Saving session
                self.actualSession.saveSession(self.tab_info)
                return None
            else:
                #Saving session
                self.actualSession.saveSession(self.tab_info)
                return None
        #Answer "Discard"
        elif answer == QMessageBox.StandardButton.Discard:
            #Discarding the changes and closing the tab
            self.removeTabWidgets(tab_name)
            self.tabWidget.removeTab(tab_index)
            #Save session
            self.actualSession.saveSession(self.tab_info)
            return None
    else:
        #Close the tab without asking
        self.removeTabWidgets(tab_name)
        self.tabWidget.removeTab(tab_index)
        #Save session
        self.actualSession.saveSession(self.tab_info)
        return None

#Function to remove tabs from the list
def removeTabWidgets(self, tab_name):
    tab_data = self.tab_info.pop(tab_name, None)
    if tab_data:
        #Remove text widgets from the list
        self.list_Qtexts.remove(tab_data['text_editor'])
        self.list_Qtexts.remove(tab_data['text_params'])
        self.list_QTable.remove(tab_data['result'])

#Function to remove Qtexts from the list
def removeWidgetsText(self, tab_name):
    tab_data = self.tab_info.get(tab_name)
    if tab_data:
        #Removing text widgets from the list
        self.list_Qtexts.remove(tab_data['text_editor'])
        self.list_Qtexts.remove(tab_data['text_params'])
        self.list_QTable.remove(tab_data['result'])

#Function to determine unsaved changes        
def unsavedChanges(self, tab_name):
    tab_data = self.tab_info.get(tab_name)
    #If the Script is completely blank, it is allowed to continue
    if tab_data['text_editor'].toPlainText().strip() in ["", " "]:
        return False
    #There are three conditions for which you must ask if you want to save
    ##1. Blank source or script changes
    if tab_data['origin'] == "":
        return True
    #2. Source not blank but local file nonexistent
    elif tab_data['origin'] != "" and not os.path.exists(tab_data['origin']):
        tab_data['origin'] = ""
        return True
    #3. Source not blank but existing local file
    elif tab_data['origin'] != "" and os.path.exists(tab_data['origin']):
        script_edit = tab_data['text_editor'].toPlainText()
        try:
            archivo = open(tab_data['origin'], "r" , encoding='utf-8')
            script_org = archivo.read()
            archivo.close()
        except Exception as exc:
            script_org = ""
        if script_org != script_edit:
            return True
        else:
            return False

#Function to display dialog box, save changes?
def showDialogSavingChanges(self): 
    #Instantiating language
    nested = self.i18n.getNested

    dialogo = QMessageBox()
    dialogo.setWindowIcon(self.icon)
    dialogo.setIcon(QMessageBox.Icon.Question)
    dialogo.setWindowTitle(nested("save-files", "saveE1"))
    dialogo.setText(nested("save-files", "saveE2"))
    dialogo.setStandardButtons(QMessageBox.StandardButton.Save 
                               | QMessageBox.StandardButton.Discard 
                               | QMessageBox.StandardButton.Cancel)
    dialogo.setDefaultButton(QMessageBox.StandardButton.Save)
    answer = dialogo.exec()
    return answer

#Saving script changes
def savingChanges(self, tab_name = "", cls = "save"):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None

    #Asking where to get the tab_data
    if tab_name == "":
        tab_name = self.tabWidget.currentWidget().objectName

    tab_data = self.tab_info.get(tab_name)
    #Asking the save type
    if cls == "save" and tab_data['origin'] != "":
        archivo = open(tab_data['origin'], "w" , encoding = 'utf-8')
        archivo.write(tab_data['text_editor'].toPlainText() )
        archivo.close()
        return True
    if (cls == "saveAs") or (tab_data['origin'] == ""):
        origin = self.saveFileAS()
        if origin == "":
            return False
        else: 
            try:
                archivo = open(origin, "w", encoding = 'utf-8')
                archivo.write(tab_data['text_editor'].toPlainText())
                archivo.close()
            except:
                return False
            else:
                tab_data['origin'] = origin
                #Changing the tab name
                nombre = origin.rsplit('/', 1)[-1]
                index = self.tabWidget.currentIndex()
                self.tabWidget.setTabText(index, nombre)
                return True

#Saving parameter changes
def savingChangesP(self, tab_name = "", cls = "save"):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    #Asking where to get the tab_data
    if tab_name == "":
        tab_name = self.tabWidget.currentWidget().objectName

    tab_data = self.tab_info.get(tab_name)
    #Asking the save type
    if cls == "save" and tab_data['origin_param'] != "":
        archivo = open(tab_data['origin_param'], "w" , encoding='utf-8')
        archivo.write(tab_data['text_params'].toPlainText() )
        archivo.close()
        return True
    if (cls == "saveAs") or (tab_data['origin_param']==""):
        origin = self.saveFilePAS()
        if origin == "":
            return False
        else: 
            try:
                archivo = open(origin, "w" , encoding='utf-8')
                archivo.write(tab_data['text_params'].toPlainText())
                archivo.close()
            except:
                return False
            else:
                tab_data['origin_param'] = origin
                return True

#Function to move to previous tab
def goPreviousTab(self):
    current_index = self.tabWidget.currentIndex()
    previous_index = (current_index - 1) % self.tabWidget.count()
    self.tabWidget.setCurrentIndex(previous_index)

#Function to move to next tab
def goNextTab(self):
    current_index = self.tabWidget.currentIndex()
    next_index = (current_index + 1) % self.tabWidget.count()
    self.tabWidget.setCurrentIndex(next_index)