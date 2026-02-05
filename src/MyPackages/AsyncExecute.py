import re, yaml, gc, pyodbc
import polars as pl
from datetime import datetime
from PyQt6.QtCore import pyqtSignal, QThread
from MyPackages.utils import polars_methods as pm
#==============================================================================
### Creating AsyncExecute (Execution in second thread)
#==============================================================================
#Creating the AsyncExecute class
class AsyncExecute(QThread):
    """
    Asynchronous executor for running database queries and emitting results in a separate thread.

    Inherits from:
        QThread

    Signals:
        status (pl.DataFrame, object, str): Emitted to update the status of the execution.
        finished (str): Emitted when execution is finished, passing the final status.
        toFile (pl.DataFrame, bool): Emitted when data should be saved to a file.
        recInLog (object): Emitted to record a log entry.
        inProcess (str, dict): Emitted when a query is in process, with its parameters.

    Attributes:
        parent (QObject): Parent object.
        tasks (pl.DataFrame): DataFrame containing the tasks to execute.
        current_task (int): Index of the current task being executed.
        total_task (int): Total number of tasks to execute.
        _stop (bool): Flag to stop execution.
        working (bool): Indicates if the executor is currently working.
        tab_name (str): Name of the tab associated with this execution.
        fetch (int): Number of rows to fetch from the database.
        i18nNes (callable): Internationalization function.
        Various _status, _query, _shape, _time, _resources, _error, _running, _executed, _failed, _msg0-5, _msgI, _msgBE, _msgF, _msgT, _type, _queryFile: Localized strings for UI and logging.

    Methods:
        __init__(self, tab_name, parent): Initializes the AsyncExecute object.
        run(self, *args): Executes all tasks in order.
        prepareTask(self, nextTask, *args): Prepares and updates the tasks to be executed.
        executionConsole(self, query, *args): Executes a query in console mode.
        downloadFetchedResult(self, *args): Downloads the result of a query after execution.
        downloadResult(self, query, *args): Downloads the result of a file-type query.
        killProcess(self, *args): Terminates the execution process.
        closeCursor(self, *args): Closes the database cursor after finishing.
        toLog(self, tuple, *args): Prepares and sends information to the log.
    """

    #Creating AsyncExecute signals
    status      = pyqtSignal(pl.DataFrame, object, str)
    finished    = pyqtSignal(str)
    toFile      = pyqtSignal(pl.DataFrame, bool)
    recInLog    = pyqtSignal(object)
    inProcess   = pyqtSignal(str, dict)

    def __init__(self, tab_name, parent):
        """
        Initializes the AsyncExecute object.

        Args:
            tab_name (str): Name of the tab associated with this execution.
            parent (QObject): The parent QObject.
        """
        super().__init__()
        self.parent = parent
        #Slots
        self.tasks        = None
        self.current_task = None
        self.total_task   = None
        #Flag to stop the AsyncExecute
        self._stop        = False
        self.working      = False
        #---

        self.tab_name = tab_name
        self.fetch    = parent.fetch
        self.finished.connect(self.closeCursor)

        #Language
        self.i18nNes    = parent.i18nNes
        #Headers
        self._status    = self.i18nNes('execution', 'header', 'status')
        self._query     = self.i18nNes('execution', 'header', 'query')
        self._shape     = self.i18nNes('execution', 'header', 'shape')
        self._time      = self.i18nNes('execution', 'header', 'time')
        self._resources = self.i18nNes('execution', 'header', 'resources')
        self._error     = self.i18nNes('execution', 'header', 'error')
        #States
        self._running   = self.i18nNes('execution', 'status', 'running')
        self._executed  = self.i18nNes('execution', 'status', 'executed')
        self._failed    = self.i18nNes('execution', 'status', 'failed')
        #Msgs
        self._msg0  = self.i18nNes('execution', 'msgs', 'msg0')
        self._msg1  = self.i18nNes('execution', 'msgs', 'msg1')
        self._msg2  = self.i18nNes('execution', 'msgs', 'msg2')
        self._msg3  = self.i18nNes('execution', 'msgs', 'msg3')
        self._msg4  = self.i18nNes('execution', 'msgs', 'msg4')
        self._msg5  = self.i18nNes('execution', 'msgs', 'msg5')
        #Type
        self._msgI  = self.i18nNes('execution', 'msgs', 'msgI')
        self._msgBE = self.i18nNes('execution', 'msgs', 'msgBE')
        self._msgF  = self.i18nNes('execution', 'msgs', 'msgF')
        self._msgT  = self.i18nNes('execution', 'msgs', 'msgT')
        #Others
        self._type      = self.i18nNes('tab-eco', 'history', 'type')
        self._queryFile = self.i18nNes('sql', 'query-file')

        #Structure of the DataFrame that will be used to emit the status
        new_row = pl.DataFrame({
            self._status: pl.Series([], dtype=pl.String),
            self._query: pl.Series([], dtype=pl.String),
            self._shape: pl.Series([], dtype=pl.String),
            self._time: pl.Series([], dtype=pl.String),
            self._resources: pl.Series([], dtype=pl.String),
            self._error: pl.Series([], dtype=pl.String)
        })
      
    #Everything in tasks will be executed, in order
    def run(self, *args):
        """
        Executes all tasks in the tasks DataFrame in order.

        Args:
            *args: Additional arguments (unused).

        Emits:
            status (pl.DataFrame, object, str): To update the status.
            finished (str): When execution is complete.
            toFile (pl.DataFrame, bool): When data should be saved to a file.
            inProcess (str, dict): When a query is in process.
        """
        #Starting
        #--------
        self.conn = self.parent.conn
        self.current_task=0
        self.cursor = self.conn.cursor()
        _type = self._msgBE
        
        #Restoring fetch mark
        self.parent.tabInfo[self.tab_name]['fetched'] = False
        #Process every task
        #------------------
        while self.current_task < self.total_task:
            #Raising Flag of Working
            self.working = True

            #Taking query in process
            #-----------------------
            row = self.tasks.row(self.current_task, named=True)
            _query   = row['query']
            _params  = yaml.safe_load(row['params'])
            _cls     = row['cls']
            _saveAs  = row['saveAs']
            
            #Creating the final query to execute
            #-----------------------------------
            final_query = _query
            if len(_params.keys())>0:
                #Compile a regular expression that detects all params to replace
                pattern = re.compile('|'.join(map(re.escape, _params.keys())))
                final_query = pattern.sub(lambda match: str(_params[match.group(0)]), _query)
            #Time marcs
            start = datetime.now()
            #Showing processing message
            now = datetime.now()
            strNow = now.strftime('%Y-%m-%d %H:%M:%S')
            #Showing processing message
            self.tasks = pm.replace_row(self.tasks, self.current_task,
                {'status': self._running,
                'time': f'{self._msg2}: {strNow}'} )
            self.status.emit(self.tasks, self.tab_name, 'status')
            

            #Flag to end the process
            #-----------------------
            if self._stop:
                #Ending message
                state  = False
                status = self._stop
                error  = self._msg5
                self.tasks = pm.replace_row(self.tasks, self.current_task,
                    {'status': status,
                    'time': '',
                    'error': error })
                self.status.emit(self.tasks, self.tab_name, 'status')
                #Going down flags
                self.working = False
                self._stop = False
                break

            #Cleaning memory
            #---------------
            if 'data' in locals():
                del data
                gc.collect()
            
            #Running query
            #-------------
            data = None
            if _cls=='console':
                state, status, error = self.executionConsole(final_query)
                _type = self._msgBE
                if self.total_task == 1 and state:
                    state, status, error, data = self.downloadFetchedResult()
                    _type = self._msgI

            elif _cls=='file':
                state, status, error, data = self.downloadResult(final_query)
                _type = self._msgF
                if self.total_task > 1 and state:
                    _saveAs = False
                if data is not None and not error:
                    self.toFile.emit(data, _saveAs)
                #Prevent data from being displayed in the results
                data = None
 
            #Presenting progress
            #-------------------
            now = datetime.now()
            delta = now - start
            delta = str( int(delta.total_seconds()) )+f' {self._msg0}'
            self.tasks = pm.replace_row(self.tasks, self.current_task,
                {'status': status,
                 'time': delta,
                 'error': error })
            self.status.emit(self.tasks, self.tab_name, 'status')
            self.inProcess.emit(_query, _params)
            self.toLog((self.cursor, strNow, final_query, _type, status, error, delta))
            #Stopping if at least one consultation fails
            if not state:
                break
            #Next task
            self.current_task += 1
        
        #Going down Flag of Working
        self.working = False
        
        #Emmiting the data
        #-----------------
        if isinstance(data, pl.DataFrame):
            self.status.emit(data, self.tab_name, 'result')
        
        #Finishing the work
        self.finished.emit(status)

    #Function to prepare the entrance tasks and update the necessary slots for 
    # the proper functioning of the AsyncExecute
    def prepareTask(self, nextTask, *args):
        """
        Prepares the entrance tasks and updates the necessary slots for AsyncExecute.

        Args:
            nextTask (pl.DataFrame): The next set of tasks to execute.
            *args: Additional arguments (unused).
        """
        if self.working:
            self.tasks = pl.concat([self.tasks, nextTask], how='vertical')
        else:
            self._stop = False
            self.tasks = nextTask
        #Updating other slots
        self.total_task = self.tasks.height
    
    #Running under the typology console without waiting for the result to download
    def executionConsole(self, query, *args):
        """
        Executes a query in console mode without waiting for the result to download.

        Args:
            query (str): The SQL query to execute.
            *args: Additional arguments (unused).

        Returns:
            tuple: (_state (bool), _status (str), _error (str))
        """
        try:
            self.cursor.execute(query)
        except Exception as exc:
            #Handling the error
            if isinstance(exc, pyodbc.Error):
                error = exc.args[1] if len(exc.args) > 1 else str(exc)
            else:
                error = exc
            
            _state  = False
            _status = self._failed
            _error  = str(error)
        else:
            _state  = True
            _status = self._executed
            _error  = ''
        return _state, _status, _error
            
    #Running under the typology console waiting for the result to download
    def downloadFetchedResult(self, *args):
        """
        Downloads the result of a query after execution in console mode.

        Args:
            *args: Additional arguments (unused).

        Returns:
            tuple: (_state (bool), _status (str), _error (str), _data (pl.DataFrame or None))
        """
        _data = None
        columns = None
        columnNames = []
        try:
            description = self.cursor.description
            if not description:
                _state = True
                _status = self._executed
                _error = ''
                _data = None
                return _state, _status, _error, _data
            #Fetching data
            rows = self.cursor.fetchmany(int(self.fetch)+1)
        except Exception as exc:
            #Handling the error
            if isinstance(exc, pyodbc.Error):
                _error = exc.args[1] if len(exc.args) > 1 else str(exc)
            else:
                _error = exc
            
            _state = False
            _status = self._failed
            _data = None
        else:
            #Creating database. IMPORTANT, respecting original data type
            _len = len(rows)
            #Marking as fetched if applied
            if _len > self.fetch:
                rows = rows[:self.fetch]
                self.parent.tabInfo[self.tab_name]['fetched'] = True
            #Creating DataFrame, respecting the types of each column
            columnNames = [desc[0] for desc in description]
            columns = zip(*rows)
            _dict = dict(zip(columnNames, columns))
            #Creating condition for empty zips states
            if not _dict:
                _dict = {col: [] for col in columnNames}
            _data = pl.DataFrame(_dict)
            #Handling the NO error
            _state = True
            _status = self._executed
            _error  = ''
        return _state, _status, _error, _data
            
    #Running under the typology file waiting for the result to download    
    def downloadResult(self, query, *args):
        """
        Downloads the result of a file-type query.

        Args:
            query (str): The SQL query to execute.
            *args: Additional arguments (unused).

        Returns:
            tuple: (_state (bool), _status (str), _error (str), _data (pl.DataFrame or None))
        """
        _data = None
        try:
            _data = pl.read_database(query, self.conn)
        except Exception as exc:
            #Handling the error
            if isinstance(exc, pyodbc.Error):
                _error = exc.args[1] if len(exc.args) > 1 else str(exc)
            else:
                _error = exc
            
            _state = False
            _status = self._failed
            _data = None
        else:
            #Handling the error
            _state = True
            _status = self._executed
            _error  = ''
        return _state, _status, _error, _data
   
    #Function to terminate the process, whether in block or not.    
    def killProcess(self, *args):
        """
        Terminates the execution process and cancels the current cursor.

        Args:
            *args: Additional arguments (unused).
        """
        self._stop = True
        self.working = False
        self.cursor.cancel()
        
    #Function to close the cursor after finishing
    def closeCursor(self, *args):
        """
        Closes the database cursor after finishing execution.

        Args:
            *args: Additional arguments (unused).
        """
        #Finishing cursor
        self.cursor.close()
        self.deleteLater
    
    #Function to prepare and send information to the registry
    def toLog(self, tuple, *args):
        """
        Prepares and sends information to the registry log.

        Args:
            tuple (tuple): Contains cursor, timestamp, query, type, status, error, and delta.
            *args: Additional arguments (unused).

        Emits:
            recInLog (object): With the formatted log entry.
        """
        #Formatting
        query = '    ' + tuple[2].replace('\n', '\n    ')
        error = '    ' + tuple[5].replace('\n', '\n    ')
        if tuple[3] == 'file':
            _type = self._msgF
        elif tuple[3] == 'console':
            _type = self._msgI
        else:
            _type = tuple[3]
        #Query info
        cursor = tuple[1]

        #Creating a log entry
        log_entry = f'\n[{tuple[1]}]\n  [{self._query.upper()}]: \n{query}' + \
                f'\n  [{self._type.upper()}]: {_type}\n  [{self._status.upper()}]: {tuple[4]}'
        if tuple[4] == self._failed:
            log_entry = log_entry + f'\n  [{self._error.upper()}]:\n{error}'
        log_entry = log_entry + f'\n  [{self._msgT.upper()}]: {tuple[6]}'
        
        #Sending Message
        self.recInLog.emit(log_entry)
