import re, os, pyodbc
import pandas as pd
from datetime import datetime
from MyPackages import JulHelper
from PyQt6.QtCore import QThread, pyqtSignal, QObject

#=============================================================
### Creating a connection manager (Execution in second thread)
#=============================================================
class ConnectionManager(QThread):
    #Creating signals for correct execution
    conManFinished = pyqtSignal(object)
    conManWorking = pyqtSignal()
    
    def __init__(self, cfg_session):
        super().__init__()
        self.cfg_session = cfg_session
        self.dsn = self.cfg_session.index.get("prede_dsn")

    #Long-term functions are executed here.
    def run(self):
        self.conManWorking.emit()
        try:
            conn = pyodbc.connect(f'DSN={self.dsn}', autocommit = True)
        except:
            self.conManFinished.emit(None)
        else:
            self.conManFinished.emit(conn)
        return