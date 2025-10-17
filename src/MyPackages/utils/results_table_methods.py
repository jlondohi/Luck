#Importing native packages
from PyQt6.QtGui import QFont
from MyPackages import MyResultTable
from PyQt6.QtWidgets import QInputDialog, QLineEdit
#==================================================================
#Creating Functions related to results tabs
#==================================================================    
#Function to change the size of the results font
def changeFontSizeResult(self, delta, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    self.current_result.changeFontSize(delta)

#Function to apply formatting according to source
def applyFontResult(self, *args):
    action = self.sender()
    #Verifying that the action is not null and getting its text
    if action is not None:
        font = self.cfg_session.index.get('prede_font')
        font['result-font'] = action.text()
        #Applying changes to each result widget
        for result in self.centralWidget().findChildren(MyResultTable):
            result.setFont( QFont(font['result-font'], font['result-size']) )

#Function to change the fetch of the system
def changeFetch(self, *args):
    current_fetch = self.cfg_session.index.get('fetch-limit')
    #Getting text of msg
    _input_title = self.i18nNes('status-bar', 'fetch-title')
    _input_msg   = self.i18nNes('status-bar', 'fetch-msg')
    #Showing the message
    value, ok = QInputDialog.getText(self, _input_title, _input_msg, QLineEdit.EchoMode.Normal, str(current_fetch))
    try:    
        value = int(value)
    except:
        return
    #Making changes
    if ok and isinstance(value, int):
        #Changing system value
        self.cfg_session.index['fetch-limit'] = value
        self.cfg_session.save()
        self.fetch = value
        