import re, time
import pandas as pd
from datetime import datetime
from MyPackages import JulHelper
from PyQt6.QtCore import pyqtSignal, QObject

#==============================================================================
### Creating Worker (Execution in second thread)
#==============================================================================
#Creating the Worker class
class Worker(QObject):
    #Creating worker signals
    status = pyqtSignal(pd.DataFrame, object)
    finished = pyqtSignal(pd.DataFrame, object)
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
        self.lgg = parent.lgg
        #Headers
        self._status = self.nested(self.lgg, "execution", "header", "status")
        self._query = self.nested(self.lgg, "execution", "header", "query")
        self._time = self.nested(self.lgg, "execution", "header", "time")
        self._error = self.nested(self.lgg, "execution", "header", "error")
        #States
        self._running = self.nested(self.lgg, "execution", "status", "running")
        self._executed = self.nested(self.lgg, "execution", "status", "executed")
        self._failed = self.nested(self.lgg, "execution", "status", "failed")
        #Msgs
        self._msg0 = self.nested(self.lgg, "execution", "msgs", "msg0")
        self._msg1 = self.nested(self.lgg, "execution", "msgs", "msg1")
        self._msg2 = self.nested(self.lgg, "execution", "msgs", "msg2")
        self._msg3 = self.nested(self.lgg, "execution", "msgs", "msg3")
        self._msg4 = self.nested(self.lgg, "execution", "msgs", "msg4")
        self._msg5 = self.nested(self.lgg, "execution", "msgs", "msg5")

    #Long-term tasks will be executed here. 
    def run(self):
        #Creating the base that will emit the status in different stages
        data_status = pd.DataFrame({
                        self._status: pd.Series(dtype=str),
                        self._query: pd.Series(dtype=str),
                        self._time: pd.Series(dtype=str),
                        self._error: pd.Series(dtype=str)
                                })
        data = None
        #Sending queries to the history table
        self.inProcess.emit(self.queries, self.params)
        #Preparing the query to be able to execute via cursor. efficient and limited
        try:
            self.queries = JulHelper.cleanQ(self.queries+";", self.params)
        except Exception as exc:
            #Managing general message
            data_status.loc[0, self._status] = self._failed
            data_status.loc[0, self._query] = self._msg1
            data_status.loc[0, self._time] = "NA"
            data_status.loc[0, self._error] = str(exc)
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
            if queries_list[0] !='':
                try:
                    #Preparing status base
                    data_status.loc[0, self._status] = self._running
                    data_status.loc[0, self._query] = queries_list[0]
                    data_status.loc[0, self._time] = f"{self._msg2}: "+str(datetime.now().strftime("%H:%M:%S"))
                    data_status.loc[0, self._error] = ""
                    self.status.emit(data_status, self.tab_name)
                    #Download database
                    if self.cls == "console":
                        self.cursor = self.conn.cursor()
                        self.cursor.execute(queries_list[0])
                        description = self.cursor.description
                        if description:
                            rows = self.cursor.fetchmany(self.fetch)
                            data = pd.DataFrame.from_records(rows, columns=[desc[0] for desc in description])
                        else:                    
                            #Execution time
                            now = datetime.now()
                            delta = now - start
                            #Handling message
                            data_status.loc[0, self._status] = self._executed
                            data_status.loc[0, self._query] = queries_list[0]
                            data_status.loc[0, self._time] = str(int( delta.total_seconds()) )+f" {self._msg0}"   
                            data_status.loc[0, self._error] = ""
                            self.finished.emit(data_status, self.tab_name)
                            return None
                    elif self.cls=="file":
                        self.cursor = self.conn.cursor()
                        data = pd.read_sql(queries_list[0], self.conn)
                        #Execution time
                        now = datetime.now()
                        delta = now - start
                        #Handling message
                        data_status.loc[0, self._status] = self._msg3
                        data_status.loc[0, self._query] = self._msg4
                        data_status.loc[0, self._time] = str(int( delta.total_seconds()) )+f" {self._msg0}"   
                        data_status.loc[0, self._error] = ""
                        self.status.emit(data_status, self.tab_name)
                        #Note: this is the only one that does not have a return   
                except TypeError as exc:
                    #Execution time
                    now = datetime.now()
                    delta = now - start
                    #Handling message
                    data_status.loc[0, self._status] = self._executed
                    data_status.loc[0, self._query] = queries_list[0]
                    data_status.loc[0, self._time] = str(int( delta.total_seconds()) )+f" {self._msg0}"   
                    data_status.loc[0, self._error] = ""
                    self.finished.emit(data_status, self.tab_name)
                    return None
                except Exception as exc:
                    #Delimiting the error
                    if 'AnalysisException' in str(exc):
                        exc = re.search(r'AnalysisException(.*)', str(exc)).group(1).strip()
                        exc = exc[1:][:-27]
                    #Handling message
                    data_status.loc[0, self._status] = self._failed
                    data_status.loc[0, self._query] = queries_list[0]
                    data_status.loc[0, self._time] = "NA"
                    #Replacing error message in case of stop by the user
                    if self._stop:
                        data_status.loc[0, self._error] = self._msg5
                    else:
                        data_status.loc[0, self._error] = str(exc)
                    self.finished.emit(data_status, self.tab_name)
                    return None
                
                #This else exists to save to file ("file")
                else:
                    #Execution time
                    now = datetime.now()
                    delta = now - start
                    #Handling message
                    data_status.loc[0, self._status] = self._executed
                    data_status.loc[0, self._query] = queries_list[0]
                    data_status.loc[0, self._time] = str(int( delta.total_seconds()) )+f" {self._msg0}"   
                    data_status.loc[0, self._error] = ""
                    self.status.emit(data_status, self.tab_name)
                    #Emitting completion signal
                    time.sleep(1)
                    self.finished.emit(data, self.tab_name)
                    return None
        #Executing each query
        elif len(queries_list)>1:
            #Running queries or queries
            self.cursor = self.conn.cursor()
            cont =- 1
            for query in queries_list:
                if query !='':
                    cont += 1
                    start=datetime.now()
                    #Preparing status base
                    data_status.loc[cont, self._status] = self._running
                    data_status.loc[cont, self._query] = query
                    data_status.loc[cont, self._time] = f"{self._msg2}: "+str(start.strftime("%H:%M:%S"))
                    data_status.loc[cont, self._error] = ""
                    self.status.emit(data_status, self.tab_name)
                    #Flag to end the process
                    if self._stop:
                        data_status.loc[cont, self._status] = self._failed
                        data_status.loc[cont, self._error] = self._msg5
                        self.finished.emit(data_status, self.tab_name)
                        break

                    try:
                        self.cursor.execute(query)
                    except Exception as exc:
                        if 'AnalysisException' in str(exc):
                            exc = re.search(r'AnalysisException(.*)', str(exc)).group(1).strip()
                            exc = exc[1:][:-27]
                        #Handling the error
                        data_status.loc[cont, self._status] = self._failed
                        #Replacing error message in case of stop by the user
                        if self._stop:
                            data_status.loc[cont, self._error] = self._msg5
                        else:
                            data_status.loc[cont, self._error] = str(exc)
                        
                        self.finished.emit(data_status, self.tab_name)
                        return None
                    else:
                        #Execution time
                        now = datetime.now()
                        delta = now - start
                        #Managing state
                        data_status.loc[cont, self._status] = self._executed
                        data_status.loc[cont, self._time] = str(int( delta.total_seconds()) )+f" {self._msg0}"       
                        self.status.emit(data_status, self.tab_name)
            
            self.finished.emit(data_status, self.tab_name)            
            return None

    #Function to terminate the process, whether in block or not.    
    def killProcess(self):
        self._stop = True
        self.cursor.cancel()
    
    #Function to close the cursor after finishing
    def closeCursor(self):
        #Finishing cursor
        self.cursor.close()
