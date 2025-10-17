#Importing native packages
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

#=============================================================
### Creating an update for Ecosystem Tree Tree
#=============================================================
class AsynTree(QThread):
    """
    Asynchronous worker for updating and retrieving the ecosystem tree structure from a database.

    Inherits from:
        QThread

    Signals:
        asynTreeFinished (dict): Emitted when the tree retrieval is finished, passing the local tree dictionary.

    Attributes:
        parent (QObject): Parent object.

    Methods:
        __init__(self, parent): Initializes the AsynTree worker.
        run(self, *args): Executes the process to retrieve the tree structure and emits the result.
    """
    asynTreeFinished = pyqtSignal(dict)

    def __init__(self, parent):
        """
        Initializes the AsynTree worker.

        Args:
            parent (QObject): The parent QObject.
        """
        super().__init__()
        self.parent = parent

    def run(self, *args):
        """
        Executes the process to retrieve the ecosystem tree structure from the database.

        Args:
            *args: Additional arguments (unused).

        Emits:
            asynTreeFinished (dict): When the tree retrieval is complete.
        """
        #Creating cursor for queries
        cursor = self.parent.conn.cursor()

        #Downloading the databases
        try:
            cursor.execute('SHOW DATABASES;')
            databases = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.parent.lbl_status.setText(self.i18nNes('status-bar', 'unex-error'))
            self.asynTreeFinished.emit(None)
            return

        #Creating objects to save locally
        tree = {}
        expanded_tree = {}

        #Downloading tables per database
        for database in databases:
            try:
                cursor.execute(f'SHOW TABLES IN {database};')
                tables = [row[0] for row in cursor.fetchall()]
            except Exception as e:
                tables = []
            else:
                tree[database] = tables

        #Downloading statistics by table
        for database, tables in tree.items():
            if not tables:
                continue
            for table in tables:
                try:
                    result = None
                    if result:
                        rows = result[0][1]  #Rows
                        size = result[0][2]  #Size
                    else:
                        rows, size = None, None
                except Exception as e:
                    rows, size = None, None
                finally:
                    if database not in expanded_tree:
                        expanded_tree[database] = {}
                    expanded_tree[database][table] = [rows, size]

        #Save the tree locally
        now = datetime.now().date()
        localTree = {
            'date': now.strftime('%Y-%m-%d'),
            'tree': expanded_tree,
        }
        #Emitting
        self.asynTreeFinished.emit(localTree)

