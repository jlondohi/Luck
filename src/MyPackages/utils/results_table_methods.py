#Importing native packages
from PyQt6.QtGui import QFont

#================================================================== =======================
#Creating Functions related to results tabs
#================================================================== =======================    
#Function to change the size of the results font
def changeFontSizeResult(self, delta):
    #Running if tab is active
    if self.tabWidget:
        self.current_result.changeFontSize(delta)

#Function to apply formatting according to source
def applyFontResult(self):
    action = self.sender()
    #Verifying that the action is not null and getting its text
    if action is not None:
        font = self.cfg_session.index.get("prede_font")
        font["result-font"] = action.text()
        #Applying changes to each result widget
        for result_widget in self.list_QTable:
            result_widget.setFont( QFont(font["result-font"], font["result-size"]) )