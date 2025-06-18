import re
import polars as pl
from datetime import datetime
from MyPackages import JulHelper
from PyQt6.QtCore import pyqtSignal, QObject
from MyPackages.utils import polars_methods as pm
#==============================================================================
### Creating Worker (Execution in second thread)
#==============================================================================
#Creating the Worker class
class Worker(QObject):
    #Creating worker signals
    status = pyqtSignal(pl.DataFrame, object)
    finished = pyqtSignal(pl.DataFrame, object)
    recInLog = pyqtSignal(object)
    inProcess = pyqtSignal(str, dict)
    _stop = False
    
    def __init__(self, queries, params, tab_name, cls, parent):
        super().__init__()
        self.queries = queries
        self.params = params
        self.conn = parent.conn
        self.tab_name = tab_name
        self.cls = cls
        self.fetch = parent.fetch
        self.finished.connect(self.closeCursor)

        #Language
        self.nested = parent.i18n.getNested
        #Headers
        self._status = self.nested("execution", "header", "status")
        self._query = self.nested("execution", "header", "query")
        self._shape = self.nested("execution", "header", "shape")
        self._time = self.nested("execution", "header", "time")
        self._resources = self.nested("execution", "header", "resources")
        self._error = self.nested("execution", "header", "error")
        #States
        self._running = self.nested("execution", "status", "running")
        self._executed = self.nested("execution", "status", "executed")
        self._failed = self.nested("execution", "status", "failed")
        #Msgs
        self._msg0 = self.nested("execution", "msgs", "msg0")
        self._msg1 = self.nested("execution", "msgs", "msg1")
        self._msg2 = self.nested("execution", "msgs", "msg2")
        self._msg3 = self.nested("execution", "msgs", "msg3")
        self._msg4 = self.nested("execution", "msgs", "msg4")
        self._msg5 = self.nested("execution", "msgs", "msg5")
        #Type
        self._msgI = self.nested("execution", "msgs", "msgI")
        self._msgBE = self.nested("execution", "msgs", "msgBE")
        self._msgF = self.nested("execution", "msgs", "msgF")
        self._msgT = self.nested("execution", "msgs", "msgT")
        #Others
        self._type = self.nested("tab-eco", "history", "type")
        self._queryFile = self.nested("sql", "query-file")

    #Long-term ans short-term tasks will be executed here.
    def run(self):
        #Creating the base that will emit the status in different stages
        #Note: This table is larger than what might be shown. Some things still need to be developed
        new_row = pl.DataFrame({
            self._status: pl.Series([], dtype=pl.String),
            self._query: pl.Series([], dtype=pl.String),
            self._shape: pl.Series([], dtype=pl.String),
            self._time: pl.Series([], dtype=pl.String),
            self._resources: pl.Series([], dtype=pl.String),
            self._error: pl.Series([], dtype=pl.String)
        })
        data_status = new_row
        data = None
        #Sending queries to the history table
        self.inProcess.emit(self.queries, self.params)
        #Preparing the query to be able to execute via cursor. Efficient and limited
        try:
            self.queries = JulHelper.cleanQ(self.queries+";", self.params)
        except Exception as exc:
            #Managing general message
            new_row = pl.DataFrame({
                self._status: [self._failed],
                self._query: [self._msg1],
                self._shape: [""],
                self._time: ["NA"],
                self._resources: [""],
                self._error: [str(exc)]
            })
            data_status = new_row
            #Emitting status
            self.finished.emit(data_status, self.tab_name)
            return None

        #Creating list with queries
        queries_list = self.queries.split(';')
        #Delete empty boxes in list
        queries_list = [query.strip() for query in queries_list]
        queries_list = list( filter(None, queries_list) )
        #Conditional to determine whether to execute one or more queries
        if len(queries_list)==0:
            self.finished.emit(data_status, self.tab_name)
            return None
        elif len(queries_list)==1:
            start=datetime.now()
            strNow = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            #Stopping process in case of null query
            if queries_list[0] == '':
                return
            #Executing
            try:
                #Preparing status base
                new_row = pl.DataFrame({
                    self._status: [self._running],
                    self._query: [queries_list[0]],
                    self._shape: [""],
                    self._time: [f"{self._msg2}: "+str(datetime.now().strftime("%H:%M:%S"))],
                    self._resources: [""],
                    self._error: [""]
                })
                data_status = new_row
                #Emitting status
                self.status.emit(data_status, self.tab_name)
                #Download database
                if self.cls == "console":
                    self.cursor = self.conn.cursor()
                    self.cursor.execute(queries_list[0])
                    description = self.cursor.description
                    if description:
                        #Fetching data
                        rows = self.cursor.fetchmany(self.fetch)
                        #Creating DataFrame
                        column_names = [desc[0] for desc in description]
                        columns = zip(*rows)
                        _dict = dict(zip(column_names, columns))
                        data = pl.DataFrame(_dict)
                    else:
                        #Execution time
                        now = datetime.now()
                        delta = now - start
                        delta = str( int(delta.total_seconds()) )+f" {self._msg0}" 
                        #Handling message
                        new_row = pl.DataFrame({
                            self._status: [self._executed],
                            self._query: [queries_list[0]],
                            self._shape: [""],
                            self._time: [delta],
                            self._resources: [""],
                            self._error: [""]
                        })
                        data_status = new_row
                        #Emitting status
                        self.finished.emit(data_status, self.tab_name)
                        self.toLog((self.cursor, strNow, queries_list[0], self.cls, self._executed, "", delta))
                        return None
                elif self.cls=="file":
                    self.cursor = self.conn.cursor()
                    data = pl.read_database(queries_list[0], self.conn)
                    #Execution time
                    now = datetime.now()
                    delta = now - start
                    delta = str( int(delta.total_seconds()) )+f" {self._msg0}"
                    #Handling message
                    new_row = pl.DataFrame({
                        self._status: [self._msg3],
                        self._query: [self._msg4],
                        self._shape: [""],
                        self._time: [delta],
                        self._resources: [""],
                        self._error: [""]
                    })
                    data_status = new_row
                    #Emitting status
                    self.status.emit(data_status, self.tab_name)
                    #Note: this is the only one that does not have a return   
            except TypeError as exc:
                #Execution time
                now = datetime.now()
                delta = now - start
                delta = str( int(delta.total_seconds()) )+f" {self._msg0}"
                #Handling message
                new_row = pl.DataFrame({
                    self._status: [self._executed],
                    self._query: [queries_list[0]],
                    self._shape: [""],
                    self._time: [delta],
                    self._resources: [""],
                    self._error: [""]
                })
                data_status = new_row
                #Emitting status
                self.finished.emit(data_status, self.tab_name)
                self.toLog((self.cursor, strNow, queries_list[0], self.cls, self._executed, "", delta))
                return None
            except Exception as exc:
                #Execution time
                now = datetime.now()
                delta = now - start
                delta = str( int(delta.total_seconds()) )+f" {self._msg0}"
                #Delimiting the error
                if 'AnalysisException' in str(exc):
                    exc = re.search(r'AnalysisException(.*)', str(exc)).group(1).strip()
                    exc = exc[1:][:-27]
                #Handling message
                error_msg = self._msg5 if self._stop else str(exc)
                new_row = pl.DataFrame({
                    self._status: [self._failed],
                    self._query: [queries_list[0]],
                    self._shape: [""],
                    self._time: [delta],
                    self._resources: [""],
                    self._error: [error_msg]
                })
                data_status = new_row
                self.finished.emit(data_status, self.tab_name)
                self.toLog((self.cursor, strNow, queries_list[0], self.cls, self._failed, str(exc), delta))
                return None

            #This else exists to show table in Results or save local file
            else:
                #Execution time
                now = datetime.now()
                delta = now - start
                delta = str( int(delta.total_seconds()) )+f" {self._msg0}"
                #Handling message
                new_row = pl.DataFrame({
                    self._status: [self._executed],
                    self._query: [queries_list[0]],
                    self._shape: [""],
                    self._time: [delta],
                    self._resources: [""],
                    self._error: [""]
                })
                data_status = new_row
                #Emitting status
                self.status.emit(data_status, self.tab_name)
                #Emitting completion signal
                self.finished.emit(data, self.tab_name)
                self.toLog((self.cursor, strNow, queries_list[0], self.cls, self._executed, "", delta))
                return None
        #Executing each query
        elif len(queries_list) > 1:
            #Running queries or queries
            self.cursor = self.conn.cursor()
            count =- 1
            for query in queries_list:
                #Continuing to next query in case of null
                if query =='':
                    continue
                #Executing
                count += 1
                start = datetime.now()
                strNow = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                #Preparing status base
                data_status = pm.replace_row(
                    data_status,
                    count,
                    {   self._status: self._running,
                        self._query: query,
                        self._shape: "",
                        self._time: f"{self._msg2}: "+str(start.strftime("%H:%M:%S")),
                        self._resources: "",
                        self._error: "" }
                )
                #Emitting status
                self.status.emit(data_status, self.tab_name)
                #Flag to end the process
                if self._stop:
                    #Execution time
                    now = datetime.now()
                    delta = now - start
                    delta = str( int(delta.total_seconds()) )+f" {self._msg0}"
                    #Ending message
                    data_status = pm.replace_row(
                        data_status,
                        count,
                        {   self._status: self._failed,
                            self._error: self._msg5  }
                    )
                    #Emitting status
                    self.finished.emit(data_status, self.tab_name)
                    self.toLog((self.cursor, strNow, query, self._msgBE, self._failed, self._msg5, delta))
                    break
                try:
                    self.cursor.execute(query)
                except Exception as exc:
                    if 'AnalysisException' in str(exc):
                        exc = re.search(r'AnalysisException(.*)', str(exc)).group(1).strip()
                        exc = exc[1:][:-27]
                    #Handling the error
                    msg = self._msg5 if self._stop else str(exc)
                    data_status = pm.replace_row(
                        data_status,
                        count,
                        {   self._status: self._failed,
                            self._error: msg  }
                    )
                    #Execution time
                    now = datetime.now()
                    delta = now - start
                    delta = str( int(delta.total_seconds()) )+f" {self._msg0}"
                    #Ending message
                    self.finished.emit(data_status, self.tab_name)
                    self.toLog((self.cursor, strNow, query, self._msgBE, self._failed, msg, delta))
                    return
                else:
                    #Execution time
                    now = datetime.now()
                    delta = now - start
                    delta = str( int(delta.total_seconds()) )+f" {self._msg0}"
                    #Managing state
                    data_status = pm.replace_row(
                        data_status,
                        count,
                        {   self._status: self._executed,
                            self._time: delta  }
                    )
                    self.toLog((self.cursor, strNow, query, self._msgBE, self._executed, "", delta))
            self.finished.emit(data_status, self.tab_name)
            return
   
    #Function to terminate the process, whether in block or not.    
    def killProcess(self):
        self._stop = True
        self.cursor.cancel()
    
    #Function to close the cursor after finishing
    def closeCursor(self):
        #Finishing cursor
        self.cursor.close()
    
    #Function to prepare and send information to the registry
    def toLog(self, tuple):
        #Formatting
        query = "    " + tuple[2].replace("\n", "\n    ")
        error = "    " + tuple[5].replace("\n", "\n    ")
        if tuple[3] == "file":
            _type = self._msgF
        elif tuple[3] == "console":
            _type = self._msgI
        else:
            _type = tuple[3]
        #Query info
        cursor = tuple[1]

        #Creating a log entry
        log_entry = f"\n[{tuple[1]}]\n  [{self._query.upper()}]: \n{query}" + \
                f"\n  [{self._type.upper()}]: {_type}\n  [{self._status.upper()}]: {tuple[4]}"
        if tuple[4] == self._failed:
            log_entry = log_entry + f"\n  [{self._error.upper()}]:\n{error}"
        log_entry = log_entry + f"\n  [{self._msgT.upper()}]: {tuple[6]}"
        
        #Sending Message
        self.recInLog.emit(log_entry)
