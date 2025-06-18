#Importing native packages
import re, os, sys, time, platform \
    , ctypes, ctypes.wintypes
#Trying to import pwd only on Linux
if sys.platform != "win32":
    import pwd
else:
    pwd = None

import polars as pl
from datetime import datetime
#Importing PyQt6 packages
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QThread, Qt
from PyQt6.QtGui import QTextCursor
#Importing custom classes and methods
from MyPackages import UploadDBWidget, Worker

#============================================================   
#Functions focused on the execution of one or several queries
#============================================================
#SQL Menu Functions
#-------------------------
#Function to establish DSN
def applySelectedDSN(self):
    self.dsn = self.sender().text()
    self.cfg_session.index["prede_dsn"] = self.dsn
    #Requesting connection
    self.ConMan.start()
    #Requesting the tree of the dsn

#Function in process of connection with DSN
def connectingDSN(self):
    #Instantiating language
    nested = self.i18n.getNested
    _sc_db = nested("status-bar", "sc-db")
    self.dsn = self.cfg_session.index["prede_dsn"]

    self.lbl_status.setText(_sc_db.format(self.dsn))
    self.bt_connect.setStyleSheet("background-color:#e81123;")

#DSN function connected
def connectedDSN(self, conn):
    #Language
    nested = self.i18n.getNested
    _c_db = nested("status-bar", "c-db")
    _nc_db = nested("status-bar", "nc-db")
    _dsnC = nested("log-messages", "dsn-changed")
    self.dsn = self.cfg_session.index["prede_dsn"]

    if conn:
        self.conn = conn
        self.lbl_status.setText(_c_db.format(self.dsn))
        self.bt_connect.setStyleSheet("background-color:#16825d;")
        self.firstConexionSignal.emit()

        #Bringing new connection to the log
        if self.recordingLog:
            print(f"\n[{_dsnC.upper()}]: {self.dsn}")
    else:
        self.lbl_status.setText(_nc_db.format(self.dsn))
        self.bt_connect.setStyleSheet("background-color:#e81123;")

#Function to reconnect DSN
def reconnectDsn(self):
    #Resetting timer
    self.timerDsn.stop()
    self.timerDsn.start()
    #Reconnect if the cursor is not working
    if not self.cursorIsWorking:
        self.ConMan.start()
        return None

#Function to change the state of word wrap
def changeWordWrap(self, event):
    #Applying changes to each plain text widget
    for text_widget in self.list_Qtexts:
        text_widget.changeWrapMode(event)
    self.cfg_session.index["worldWrap"] = event

#Function to verify connection, used before executing one or more 
##queries.
def verifyConn(self):
    #Checking if there is a connection
    try:
        conn = self.conn
        return True
    except AttributeError:
        #Creating a QMessageBox instance to display the error message
        msg = QMessageBox()
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(self.i18n.getNested("execution", "msgs", "msgE"))
        msg.setText(self.i18n.getNested("execution", "msgs", "msg6"))
        msg.exec()
        return None

#Function focused on executing the query(s), this is the last instance
##before executing in a second thread. Use worker to execute
def runQueries(self, queries, cls="console"):
    #Language
    nested = self.i18n.getNested
    #Headers
    _status = nested("execution", "header", "status")
    _query = nested("execution", "header", "query")
    _shape = nested("execution", "header", "shape")
    _time = nested("execution", "header", "time")
    _resources = nested("execution", "header", "resources")
    _error = nested("execution", "header", "error")
    
    #States
    _running = nested("execution", "status", "running")
    _executed = nested("execution", "status", "executed")
    _failed = nested("execution", "status", "failed")
    #Msgs
    _msg7 = nested("execution", "msgs", "msg7")
    _msg8 = nested("execution", "msgs", "msg8")

    #First verifying that it contains at least one text
    if not bool(re.search(r'[a-zA-Z]', queries)):
        return None
     
    #Terminating if there is no active tab
    if not self.tabWidget:
        return None
    
    ##Creating the DataFrame with the specified dtypes   
    new_row = pl.DataFrame({
        _status: pl.Series([], dtype=pl.String),
        _query: pl.Series([], dtype=pl.String),
        _shape: pl.Series([], dtype=pl.String),
        _time: pl.Series([], dtype=pl.String),
        _resources: pl.Series([], dtype=pl.String),
        _error: pl.Series([], dtype=pl.String)
    })
    data_status = new_row
    
    #Taking the parameters
    #----------------------
    ##Get the name of the active tab
    tab_name = self.tabWidget.currentWidget().objectName
    ##Get the QPlainTextEdit object corresponding to the active tab
    text_params = self.tab_info[tab_name]['text_params']
    ##Take the text from the QPlainTextEdit
    try:
        text_params = eval( "{"+text_params.toPlainText()+"}" )
    except Exception as exc:
        #Handling message
        new_row = pl.DataFrame({
            _status: [_failed],
            _query: [_msg7],
            _shape: [""],
            _time: ["NA"],
            _resources: [""],
            _error: [str(exc)]
        })
        data_status = new_row
        #Reporting the error
        self.reportData(data_status, tab_name)
        return None
    
    #Checking that all the parameters are resolved
    list_ = []
    set_revisar = set(re.findall(r'\{([^{}]*)\}', queries))
    for key in set_revisar:
        value = text_params.get(f"{{{key}}}", None)
        if value is None:
            list_ += [f"{{{key}}}"]
    if len(list_) > 0:
        #Handling message
        data_status = pl.DataFrame({
            _status: [_failed],
            _query: [_msg7],
            _shape: [""],
            _time: ["NA"],
            _resources: [""],
            _error: [f"{_msg8}: {list_}"]
        })
        #Reporting the error
        self.reportData(data_status, tab_name)
        return None

    #Taking the query to the worker
    #---------------------------
    #Multithreading Step 1: Creating a QThread Object
    self.thread = QThread()
    #Multithreading Step 2: Creating a worker object
    ##This must contain the queries and parameters
    self.worker = Worker(queries, text_params, tab_name, cls, self)
    self.worker.fetch = self.cfg_user.index.get("fetch-limit")
    #Multithreading Step 3: Moving Worker to Thread
    self.worker.moveToThread(self.thread)
    #Multithreading Step 4: Connecting Signals and Slots
    self.thread.started.connect(self.worker.run)
    self.worker.status.connect(self.reportData)
    self.worker.inProcess.connect(self.processHistory)
    self.worker.recInLog.connect(self.reportLog)
    self.worker.finished.connect(self.thread.quit)
    self.worker.finished.connect(self.workerFinished)
    
    if cls == "console":
        self.worker.finished.connect(self.reportData)
    elif cls == "file":
        self.worker.finished.connect(self.toFile)
    #Multithreading Step 5: Starting the Thread
    self.thread.start()
    #Marking the system as working
    self.cursorIsWorking = True
    self.lbl_status.setText(_running)
    #Starting working animation
    self.animationW_state = True
    self.animationTimer.start()
    self.updateTrayIcon("running")
    #Defining traffic light colors
    self.internal_theme = self.cfg_session.index.get("internal_theme")
    self.theme = self.cfg_app.index.get("list_thems")[self.internal_theme]
    _, self.tl_2, _ = self.theme["result-trafficlight"]
    self.bt_working.setStyleSheet(f"background-color: {self.tl_2};")
    
#Function to handle the animation of the worker button
def animationWorker(self):
    #Exchanging icon according to status
    if self.animationW_state:
        self.bt_working.setIcon(self.workerIcon2)
    else:
        self.bt_working.setIcon(self.workerIcon1)
    self.animationTimer.start()
    self.animationW_state = not self.animationW_state

#Function to indicate that the worker has finished
def workerFinished(self, df):
    #Language
    nested = self.i18n.getNested
    #Headers
    _status = nested("execution", "header", "status")
    _query = nested("execution", "header", "query")
    _shape = nested("execution", "header", "shape")
    _time = nested("execution", "header", "time")
    _resources = nested("execution", "header", "resources")
    _error = nested("execution", "header", "error")

    self.cursorIsWorking = False
    self.lbl_status.setText(nested("status-bar", "end"))
    #Finishing the working animation
    self.animationTimer.stop()
    self.bt_working.setIcon(self.workerIcon1)
    self.bt_working.setStyleSheet("background-color: None;")
    #Determining the type of completion
    if df.columns == [_status, _query, _shape, _time, _resources, _error]:
        status = "1"
        # status = df.item(-1, _status)
        self.updateTrayIcon(status)
    else:
        self.updateTrayIcon("executed")
    #Resetting reconnectDsn timer
    self.timerDsn.stop()
    self.timerDsn.start()

#Identifying the query (query between ";") running
def identifyQuery(self):
    #Running if tab is active
    if self.tabWidget:
        #Getting the current cursor
        cursor = self.current_etl.textCursor()
        cursor_position = cursor.position()
        etl_text = self.current_etl.toPlainText()
        
        #Finding the index of the semicolon ";" closest before and after the cursor
        left_index = etl_text.rfind(';', 0, cursor_position) + 1 if cursor_position > 0 else 0
        right_index = etl_text.find(';', cursor_position)

        #If ";" is not found on the right, the right boundary is the end of the text
        if right_index == -1:
            right_index = len(etl_text)
            
        #Get the text to the left and right of the cursor
        text_left = etl_text[left_index:cursor_position]
        text_right = etl_text[cursor_position:right_index]
        query = text_left + text_right

        #Select text in text_editor widget
        cursor.setPosition(left_index)
        cursor.setPosition(right_index, QTextCursor.MoveMode.KeepAnchor)
        return query
    else:
        return ""

#Identifying table
def identifyTable(self):
    #Running if tab is active
    if self.tabWidget:
        #Getting the current cursor
        cursor = self.current_etl.textCursor()
        cursor_position = cursor.position()
        etl_text = self.current_etl.toPlainText()
        #Getting the index of the end of the block
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        end_block = cursor.position()
        #Find the index of the closest character before and after the cursor
        left = []
        right = []
        for item in [' ', ';', '\n']:
            #Searching for mark to the left
            value = etl_text.rfind(item, 0, cursor_position) + 1
            left += [value] if value > 0 else [0]
            #Searching mark to the right
            value = etl_text.find(item, cursor_position)
            right += [value] if value > 0 else right
    
        left_index = 0 if len(left) == 0 else max(left)
        right_index = end_block if len(right) == 0 else min(right)

        #Get the text to the left and right of the cursor
        text_left = etl_text[left_index:cursor_position]
        text_right = etl_text[cursor_position:right_index]
        query = text_left + text_right

        #Select text in text_editor widget
        cursor.setPosition(left_index)
        cursor.setPosition(right_index, QTextCursor.MoveMode.KeepAnchor)
        return query
    else:
        return False
        
#Function linked directly to execute.
##Find the inputs to run query between ";"
def runShortTask(self):
    #Saving session
    self.actualSession.saveSession(self.tab_info)
    #Verifying connection
    if not self.cursorIsWorking:
        msg = self.verifyConn()
        if msg == None:
            return None
        #Taking the board
        query = self.identifyQuery()
        if query == "":
            return None
        #Sending to execution
        self.runQueries(query)
    
#Function linked directly to run all.
def runLongTask(self):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None

    #Save session
    self.actualSession.saveSession(self.tab_info)

    if not self.cursorIsWorking:
        #Verifying connection
        msg = self.verifyConn()
        if msg == None:
            return None

        #Taking all the queries
        #----------------
        ##Get the name of the active tab
        tab_name = self.tabWidget.currentWidget().objectName
        ##Get the QPlainTextEdit object corresponding to the active tab
        text_editor = self.tab_info[tab_name]['text_editor']
        ##Take the text from the QPlainTextEdit
        text_editor = text_editor.toPlainText()
        ##Verifying that it is not blank
        if text_editor == "":
            return None
        
        #Asking the user if they are sure
        msg = QMessageBox(self)
        msg.setWindowIcon(self.icon)
        msg.setWindowTitle(self.i18n.getNested("execution", "msgs", "msgBE"))
        msg.setText(self.i18n.getNested("execution", "msgs", "msg9"))
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        answer = msg.exec()
        if answer == QMessageBox.StandardButton.Yes:
            #Sending to execution
            self.runQueries(text_editor)
        else:
            return None

#Function to stop the worker from executing
def stopWorker(self):
    if self.cursorIsWorking:
        self.worker.killProcess()

#Function linked directly to execute.
##Find the inputs to run query between ";"
def runAssist(self):
    #Terminating if there is no active tab
    if not self.tabWidget:
        return None
    
    #Terminating if the worker is working
    if self.cursorIsWorking:
        return None
    
    #Verifying connection
    msg = self.verifyConn()
    if msg == None:
        return None
    
    action = self.sender()
    #Verify that the action is not null and get its text
    if action is not None:
        #Identifying if it is the explain
        if action.text() == "Explain":
            query = self.identifyQuery()
            query = "explain "+ query
        else:
            table = self.identifyTable()
            if table == False:
                return None
            #Taking the query corresponding to the actionMenu
            query = self.list_assist.index[action.text()]
            query = query.replace("{table}", table)

        #Performing a check if it is count by ingestion
        if action.text() == "Count by ingestion":
            try:
                ingestions = pl.read_database("DESCRIBE {};".format(table), self.conn)
            except Exception as exc:
                return None
            else:
                #Getting the intakes
                allowed_elements = ['ingestion_year', 'ingestion_month', 'ingestion_day']
                filtered_list = [element for element in ingestions["name"].to_list() if element in allowed_elements]
                #Modifying the final list
                ingestions = sorted(filtered_list, reverse=True)
            if len(ingestions)>0:
                nums1 = [str(x+1) for x in range(len(ingestions))]
                nums2 = [str(x+1)+" DESC" for x in range(len(ingestions))]
                query = "SELECT {}, COUNT(*) FROM {} GROUP BY {} ORDER BY {}".format(", ".join(ingestions), table, ", ".join(nums1), ", ".join(nums2))
            else:
                return None
        #Sending to execution
        self.runQueries(query)
        return None

#Function to process and store query history
def processHistory(self, queries, params):
    #Language
    nested = self.i18n.getNested
    #Headers
    _type = nested("tab-eco", "history", "type")
    _typeU = nested("tab-eco", "history", "type-u")
    _typeB = nested("tab-eco", "history", "type-b")
    _query = nested("tab-eco", "history", "query")
    _time = nested("tab-eco", "history", "time")
    _param = nested("tab-eco", "history", "param")

    #Creating history structure if it does not exist
    if not self.actualSession.sessionHistoryExists:
        prev = pl.DataFrame({
            _type: pl.Series([], dtype=pl.String),
            _time: pl.Series([], dtype=pl.String),
            _query: pl.Series([], dtype=pl.String),
            _param: pl.Series([], dtype=pl.String)
        })
    else:
        prev = self.actualSession.history
    #Defining type
    cls = _typeB if len(queries.split(';')) > 1 else _typeU
    #Defining time
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #Creating the new row
    new_row = pl.DataFrame({
        _type: [cls],
        _time: [now],
        _query: [str(queries)],
        _param: [str(params)]
    })
    #Concatenate the new record and the previous ones, and limit 100 rows
    historial = new_row.vstack(prev.slice(0, 99))
    self.actualSession.history = historial
    #Watching
    self.actualSession.saveSessionHistory()
    #Showing
    self.hitoricResult.loadData(historial)

#Function to add the template to the text
def runTemplate(self):
    #Terminating if there is no active tab
    if not self.tabWidget:
        return None
    
    action = self.sender()
    if action is not None:
        #Get the name of the active tab
        tab_name = self.tabWidget.currentWidget().objectName
        #Get the QPlainTextEdit object corresponding to the active tab
        text_editor = self.tab_info[tab_name]['text_editor']
        #Adding the info
        plantilla = self.list_tmplts.index[action.text()]
        cursor = text_editor.textCursor()
        cursor.insertText( plantilla )

#Function linked to the query to file menu
def runQuery_to_file(self):
    #Verifying connection
    msg = self.verifyConn()
    if msg == None:
        return None
    #Taking the query
    query = self.identifyQuery()
    if query == "":
        return None
    #Sending to execution
    self.runQueries(query, cls="file")

#Function to open the dialog box that uploads file to lZ
def runFile_to_lz(self):
    #Verifying connection
    msg = self.verifyConn()
    if msg == None:
        return None
    #starting window
    self.subirLz = UploadDBWidget(self)
    self.subirLz.show()

#Function to report info in the log file
def reportLog(self, data):
    #Reporting in the log
    if not self.recordingLog:
        return
    time.sleep(0.5)
    print(data)
    return

#Function to report progress
def reportData(self, data, tab_name):
    #Getting info from the specific tab
    tab_data = self.tab_info.get(tab_name)
    #Reporting message to results table
    if tab_data:
        tab_data['result_data'] = data
        result = tab_data['result']
        result.loadData(data)

#Function to save the file (csv or xlsx)
def toFile(self, data: pl.DataFrame):
    #Language
    nested = self.i18n.getNested
    #Labels
    _toFile1 = nested("save-files", "toFile1")
    _toFile2 = nested("save-files", "toFile2")
    _toFile3 = nested("save-files", "toFile3")
    _toFile4 = nested("save-files", "toFile4")
    _save2 = nested("save-files", "save2")
    _saveM3 = nested("save-files", "saveM3")

    #Getting current date and time
    now = datetime.now()
    formatted_date = now.strftime("%Y%m%d-%H%M%S")
    download_folder = os.path.join( self.cfg_user.index.get("ruta_data"), f"{formatted_date}.csv" )
    
    #Defining file type dictionary
    dic_clss = {
        f"{_toFile1} (*.csv)": ",",
        f"{_toFile2} (*.csv)": ";",
        f"{_toFile3} (*.csv)": "|",
        f"{_toFile4} (*.xlsx)": ""
    }
    
    #Opening save as window
    initial_dir = self.cfg_user.index.get("ruta_data")
    file_filter = ';;'.join(dic_clss.keys())
    fileName, cls = QFileDialog.getSaveFileName(self, _save2, initial_dir, file_filter)
    
    if not fileName:
        #Saving to download path if no file is selected
        self.toFile_defaultSave(data, download_folder, _saveM3)
        return
    
    if cls == f"{_toFile4} (*.xlsx)":
        if data.height > 999995: #Excel does not support more than a million rows
            self.toFile_excelError(data, fileName, download_folder)
        else:
            self.toFile_save(data, fileName, download_folder, file_type='excel')
    else:
        self.toFile_save(data, fileName, download_folder, file_type='csv', sep=dic_clss[cls])
    

#toFile auxiliary function
def toFile_save(self, data, fileName, download_folder, file_type='csv', sep=","):
    #Language
    nested = self.i18n.getNested
    #Labels
    _save1 = nested("save-files", "save1")
    _saveM4 = nested("save-files", "saveM4")
    _saveM4 = nested("save-files", "saveM4")
    
    try:
        #Changing mouse pointer to standby state
        self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        if file_type == 'excel':
            data = data.to_pandas()
            data.to_excel(fileName, index=False, engine='xlsxwriter')
        else:
            data.to_csv(fileName, sep=sep, index=False, encoding="utf-8")
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        #Showing message
        msg = QMessageBox()
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(_save1)
        msg.setText(_saveM4)
        msg.exec()
    except PermissionError:
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        self.toFile_defaultSave(data, download_folder, _saveM4)

#toFile auxiliary function
def toFile_excelError(self, data, fileName, download_folder):
    #Language
    nested = self.i18n.getNested
    #Labels
    _saveM1 = nested("save-files", "saveM1")
    _error1 = nested("save-files", "error1")
    _error3 = nested("save-files", "error3")

    try:
        #Changing mouse pointer to standby state
        self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        data.to_csv(fileName[:-5] + ".csv", sep=",", index=False, encoding="utf-8")
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        msg = QMessageBox()
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(_saveM1)
        msg.setText(f"{_error3}:")
        msg.setInformativeText(str(fileName[:-5] + '.csv'))
        msg.exec()
    except PermissionError:
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        self.toFile_defaultSave(data, download_folder, _error1)

#toFile auxiliary function
def toFile_defaultSave(self, data, download_folder, msg_text):
    #Language
    nested = self.i18n.getNested
    #Labels
    _saveM2 = nested("save-files", "saveM2")
    _error2 = nested("save-files", "error2")
    _error4 = nested("save-files", "error4")

    try:
        #Changing mouse pointer to standby state
        self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        data.to_csv(download_folder, sep=",", index=False, encoding="utf-8")
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        msg = QMessageBox()
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(msg_text)
        msg.setText(f"{_saveM2}:")
        msg.setInformativeText(str(download_folder))
        msg.exec()
    except Exception as exc:
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        msg = QMessageBox()
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(_error2)
        msg.setText(f"{_error4}:")
        msg.setInformativeText(f"{exc}")
        msg.exec()

#Function to obtain the user's full name
def getFullUsername(self):
    #Detecting the operating system   
    if platform.system() == "Windows":
        #Defining the buffer and its maximum size
        buffer = ctypes.create_unicode_buffer(1024)
        size = ctypes.wintypes.DWORD(len(buffer))
        #Calling the Windows function to get the user's full name
        if ctypes.windll.secur32.GetUserNameExW(3, buffer, ctypes.byref(size)):
            return buffer.value
        else:
            return None

    elif platform.system() in ["Linux", "Darwin"]:  #Darwin is the identifier for macOS
        try:
            #Gets the current username
            username = os.getlogin()
            #Use the pwd module to find user information
            user_info = pwd.getpwnam(username)
            #Returns the full name field
            return user_info.pw_gecos.split(',')[0]
        except KeyError:
            return None
    else:
        return None

#Function to record or log recording
def recLog(self):
    #Language
    nested = self.i18n.getNested
    #Labels
    _toFile5 = nested("save-files", "toFile5")
    _save2 = nested("save-files", "save2")
    _logStarted = nested("log-messages", "log-started")
    _logEnd = nested("log-messages", "log-end")
    _user = nested("log-messages", "user")
        
    now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    #Starting rec animation
    if not self.recordingLog:
        #Starting recording file
        filepath = os.path.join(self.cfg_user.index.get("ruta_data"), f'Luck Log-{now}')
        fileName, _ = QFileDialog.getSaveFileName(self, _save2, filepath, f'{_toFile5} (*.log)')
        if not fileName:
            return
        #Redirecting the console
        ##Open the file to write logs
        self.log_file = open(fileName, 'w', encoding='utf-8')

        #Redirect standard output to log file
        sys.stdout = self.log_file
        msg = f"{_logStarted} {now}"
        leng = len(msg)
        print("="*leng, msg, "="*leng, sep="\n")

        #Indicating user
        print(f"[{_user.upper()}]: ({self.user}) {self.getFullUsername()}")
        #Indicating the DSN
        print(f"[DSN]: {self.dsn}")
        
        #Various modifications to the ecosystem
        self.animationR_state = True
        self.recordingLog = True
        self.timerRec.start()
        self.bt_log.setToolTip(nested("tooltips", "ttp6"))
        self.actionRecLog.setText(nested("sql", "end-log"))
    else:
        #Looking at the Log
        msg = f"{_logEnd} {now}"
        leng = len(msg)
        print("="*leng, msg, "="*leng, sep="\n")
        self.log_file.close()

        #Restoring various configurations
        sys.stdout = self.original_stdout
        
        self.recordingLog = False
        self.animationR_state = False
        
        self.timerRec.stop()
        self.bt_log.setIcon(self.recIcon1)
        self.lbl_status.setText(nested("status-bar", "log-end"))
        self.bt_log.setToolTip(nested("tooltips", "ttp5"))
        self.actionRecLog.setText(nested("sql", "start-log"))

#Function to handle rec button animation
def animationRec(self):
    #Language
    nested = self.i18n.getNested
    #Indicating the start of recording
    self.lbl_status.setText(nested("status-bar", "log-started"))
    #Exchanging icon according to status
    if self.animationR_state:
        self.bt_log.setIcon(self.recIcon2)
    else:
        self.bt_log.setIcon(self.recIcon1)
    self.timerRec.start()
    self.animationR_state = not self.animationR_state