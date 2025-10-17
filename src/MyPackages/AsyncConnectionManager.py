import pyodbc
from PyQt6.QtCore import QThread, pyqtSignal

#=============================================================
### Creating a connection manager (Execution in second thread)
#=============================================================
#Try to open the connection (only validation)  
class AsyncConnectionManager(QThread):
    """
    Manages asynchronous database connection attempts in a separate thread.

    Inherits From:
        QThread

    Signals:
        conManFinished (object): Emitted when the connection attempt finishes. Emits the connection object or None on failure.
        conManWorking (): Emitted when the connection attempt starts.

    Attributes:
        parent (QObject): The parent object, expected to have a `cfg_session` attribute.

    Methods:
        __init__(self, parent):
            Initializes the AsyncConnectionManager with the given parent.

        run(self, *args):
            Attempts to connect to the database using the DSN from the parent configuration.
            Emits signals to indicate progress and result.

        dsn_exists(self, dsn: str) -> bool:
            Checks if the given DSN exists in the system.
    """

    conManFinished = pyqtSignal(object)
    conManWorking = pyqtSignal()

    def __init__(self, parent):
        """
        Initializes the AsyncConnectionManager.

        Args:
            parent (QObject): The parent object, expected to have a `cfg_session` attribute.
        """
        super().__init__()
        self.parent = parent

    def run(self, *args):
        """
        Attempts to establish a database connection using the DSN from the parent configuration.

        Emits:
            conManWorking: When the connection attempt starts.
            conManFinished: With the connection object on success, or None on failure.

        Args:
            *args: Additional arguments (unused).
        """
        dsn = self.parent.cfg_session.index.get("prede_dsn")
        self.conManWorking.emit()

        #Early Exit if the DSN does not exist
        if not self.dsn_exists(dsn):
            self.conManFinished.emit(None)
            return

        #Try to open connection directly in this thread
        try:
            conn = pyodbc.connect(
                f"DSN={dsn}",
                autocommit=True
            )
        except Exception as e:
            #Failure when connecting
            print(f"[DEBUG] Error in connection: {e}")
            self.conManFinished.emit(None)
        else:
            #Success: return connection
            self.conManFinished.emit(conn)

    def dsn_exists(self, dsn: str) -> bool:
        """
        Checks if the given DSN exists in the system.

        Args:
            dsn (str): The Data Source Name to check.

        Returns:
            bool: True if the DSN exists, False otherwise.
        """
        return dsn in pyodbc.dataSources()