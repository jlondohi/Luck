import sqlfluff
from PyQt6.QtCore import QThread, pyqtSignal

#=============================================================
### Creating a connection manager (Execution in second thread)
#=============================================================

class SQLAnalyzer(QThread):
    #Creating signals for correct execution
    #finished = pyqtSignal(object)
    def __init__(self):
        super().__init__()
        self.query = ""

    #Long-term functions are executed here.
    def run(self):
        try:
            result = sqlfluff.lint(self.query, config_path = "Settings\\.sqlfluff")
        except Exception as exc:
            print(exc)
        else:
            if result:
                for lint in result:
                    print(f"Code: {lint['code']}. Error: {lint['description']} en línea {lint['start_line_no']}, columna {lint['start_line_pos']}")
        return

