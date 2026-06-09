#Importing native packages
import re, os, sys, yaml, time, platform \
    , subprocess , ctypes, ctypes.wintypes, locale \
    , logging
#Trying to import pwd only on Linux
if sys.platform != 'win32':
    import pwd
else:
    pwd = None

import polars as pl
from datetime import datetime
from typing import Literal

#Importing PyQt6 packages
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor
#Importing custom classes and methods
from MyPackages import (UploadDBWidget, MyPlainTextEdit)

#============================================================   
#Functions focused on the execution of one or several queries
#============================================================
#SQL Menu Functions
#------------------
#Function to establish DSN
def applySelectedDSN(self, *args):
    self.dsn = self.sender().text()
    self.cfg_session.index['prede_dsn'] = self.dsn
    #Saving the session
    self.cfg_session.save()
    #Requesting new connection
    self.conn = None
    self.asyncConnMan.start()

#Function to indicate 'in process of connection with DSN'
def connectingDSN(self, *args):
    _sc_db = self.i18nNes('status-bar', 'sc-db')
    self.dsn = self.cfg_session.index.get('prede_dsn')

    self.lbl_status.setText(_sc_db.format(self.dsn))
    self.bt_connect.setProperty('connected', False)
    self.bt_connect.style().unpolish(self.bt_connect)
    self.bt_connect.style().polish(self.bt_connect)

#DSN function connected
def connectedDSN(self, conn, *args):
    _c_db = self.i18nNes('status-bar', 'c-db')
    _nc_db = self.i18nNes('status-bar', 'nc-db')
    _dsnC = self.i18nNes('log-messages', 'dsn-changed')
    self.dsn = self.cfg_session.index.get('prede_dsn')

    if conn:
        self.conn = conn
        self.lbl_status.setText(_c_db.format(self.dsn))
        self.bt_connect.setProperty('connected', True)
        self.bt_connect.style().unpolish(self.bt_connect)
        self.bt_connect.style().polish(self.bt_connect)
        self.firstConexionSignal.emit()

        #Bringing new connection to the log
        if self.recordingLog:
            self.log_file.write(f'\n[{_dsnC.upper()}]: {self.dsn}')
    else:
        self.lbl_status.setText(_nc_db.format(self.dsn))
        self.bt_connect.setProperty('connected', False)
        self.bt_connect.style().unpolish(self.bt_connect)
        self.bt_connect.style().polish(self.bt_connect)

#Function to reconnect DSN
def reconnectDsn(self, *args):
    #Resetting timer
    self.timerDsn.stop()
    self.timerDsn.start()
    #Reconnect if the cursor is not working
    if not self.cursorIsWorking:
        self.asyncConnMan.start()
        return None

#Function to change the state of word wrap
def changeWordWrap(self, event, *args):
    #Applying changes to each plain text widget
    for editor in self.centralWidget().findChildren(MyPlainTextEdit):
        editor.changeWrapMode(event)
    self.cfg_session.index['worldWrap'] = event
    self.cfg_session.save()

#Function to verify connection, used before executing one or more 
##queries.
def verifyConn(self, *args):
    #Checking if there is a connection
    try:
        conn = self.conn
    except AttributeError:
        #Creating a QMessageBox instance to display the error message
        msg = QMessageBox()
        msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(self.i18nNes('execution', 'msgs', 'msgE'))
        msg.setText(self.i18nNes('execution', 'msgs', 'msg6'))
        msg.exec()
        return False
    else:
        if conn:
            return True
        else:
            #Creating a QMessageBox instance to display the error message
            msg = QMessageBox()
            msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
            msg.setWindowIcon(self.icon)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle(self.i18nNes('execution', 'msgs', 'msgE'))
            msg.setText(self.i18nNes('execution', 'msgs', 'msg6'))
            msg.exec()
            return False

#Function focused on executing the query(s). This is the last instance before executing in a second thread. 
# Its purpose is to determine whether to execute it or add it to the current execution list. 
# Use the asyncExecute to execute it.
def runQueries(self, queries, cls: Literal['console', 'file']='console', saveAs=False, *args):
    _wating  = self.i18nNes('execution', 'status', 'wating')
    _running = self.i18nNes('execution', 'status', 'running')
    
    #Save session
    self.actualSession.saveSession(self.tabInfo)
    #Terminating if there is no active tab
    if not self.tabWidget:
        return None
    #Verifying connection
    if not self.cursorIsWorking:
        msg = self.verifyConn()
        if not msg:
            return None

    #Creating a list of formatted queries that will be sent to the asyncExecute
    tasks = [] 
    ##Creating a template row for the Status DataFrame  
    template_row = {
          'status':     ''
        , 'query':      ''
        , 'params':     ''
        , 'shape':      ''
        , 'time':       ''
        , 'resources':  ''
        , 'error':      ''
        #Internal operation columns
        , 'cls':        ''
        , 'saveAs':     False
    }
    
    #Separating Queries and Parameters
    #---------------------------------
    for query in queries.split(';'):
        #Passing the next in case of blank query
        if not query.strip():
            continue
        #Validating and filtering parameters
        state, params = self.verifyFilterParams(query)
        #Giving a more leible format to the parameter dictionary
        params = str(yaml.dump(params, allow_unicode=True))
        params = params.rstrip('\n')
        #Ending if at least one query has missing parameters
        if not state:
            return
        #Adding the new row to the status DataFrame
        new_row = template_row.copy()
        new_row['status'] = _wating
        new_row['query']  = query
        new_row['params'] = params
        new_row['cls']    = cls
        new_row['saveAs'] = saveAs
        tasks += [new_row.copy()]
    
    #Creating the DataFrame with the status
    tasks = pl.DataFrame(tasks)
    #Determining whether to send the block or add it to the existing
    if self.cursorIsWorking:
        #Showing new queries
        all_tasks = pl.concat([self.asyncExecute.tasks, tasks], how='vertical')
        #Do not exceed app limit
        limit = self.cfg_app.index.get('query-queue-limit')
        if limit is not None and isinstance(limit, int) and all_tasks.shape[0] > limit:
            #Creating a QMessageBox instance to display the error message
            msg = QMessageBox()
            msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
            msg.setWindowIcon(self.icon)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle(self.i18nNes('execution', 'status', 'running'))
            msg.setText(self.i18nNes('execution', 'msgs', 'msg11'))
            msg.exec()
            return
        
        result = self.current_result
        rType = result.rType
        result.loadData(all_tasks, rType)
        #Sending new queries
        self.asyncExecute.prepareTask(tasks)
        return None

    #Starting asyncExecute
    #----------------------------------------
    self.asyncExecute.tab_name = self.current_tabName
    self.asyncExecute.prepareTask(tasks)
    self.asyncExecute.fetch = self.fetch
    self.asyncExecute.start()
    
    #Marking the system as working
    self.cursorIsWorking = True
    self.lbl_status.setText(self.i18nNes('status-bar', 'working'))
    #Starting working animation
    self.animationW_state = True
    self.animationTimer.start()
    self.updateTrayIcon(_running)

    
#Function to handle the animation of the asyncExecute button
def animationExcWorker(self, *args):
    #Exchanging icon according to status
    if self.animationW_state:
        self.bt_working.setIcon(self.excWorkerIcon2)
    else:
        self.bt_working.setIcon(self.excWorkerIcon1)
    self.animationTimer.start()
    self.animationW_state = not self.animationW_state

#Function to indicate that the asyncExecute has finished
def endAsyncExecute(self, status, *args):
    #Status bar
    self.cursorIsWorking = False
    self.lbl_status.setText(self.i18nNes('status-bar', 'end'))
    #Finishing the working animation
    self.animationTimer.stop()
    self.updateTrayIcon(status)
    #Resetting reconnectDsn timer
    self.timerDsn.stop()
    self.timerDsn.start()
    #Updating the Information of the Active Tab
    self.tabChanged()

#Identifying the query (query between ';') running
def identifyQuery(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None

    #Getting the current cursor
    cursor = self.current_etlEditor.textCursor()
    cursor_position = cursor.position()
    etl_text = self.current_etlEditor.toPlainText()
    
    #Finding the index of the semicolon ';' closest before and after the cursor
    left_index = etl_text.rfind(';', 0, cursor_position) + 1 if cursor_position > 0 else 0
    right_index = etl_text.find(';', cursor_position)

    #If ';' is not found on the right, the right boundary is the end of the text
    if right_index == -1:
        right_index = len(etl_text)
        
    #Get the text to the left and right of the cursor
    text_left = etl_text[left_index:cursor_position]
    text_right = etl_text[cursor_position:right_index]
    query = text_left + text_right

    #Select text in textEditor widget
    cursor.setPosition(left_index)
    cursor.setPosition(right_index, QTextCursor.MoveMode.KeepAnchor)
    return query, left_index, right_index


#Identifying the table in which right click was clicked
def identifyTable(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    #Getting the current cursor
    cursor = self.current_etlEditor.textCursor()
    cursor_position = cursor.position()
    etl_text = self.current_etlEditor.toPlainText()
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

    #Select text in textEditor widget
    cursor.setPosition(left_index)
    cursor.setPosition(right_index, QTextCursor.MoveMode.KeepAnchor)
    return query

        
#Creating a query without comments to be executed. Remember that
#comments are those that begin with --or /**/
def cleanQ(self, queries, params={}, *args):
    #Removing block comments
    queries = re.sub(r'/\*(.*?)\*/', ' ', queries, flags=re.DOTALL)
    #Removing comment from a line
    queries = re.sub(r'\s*\-\-.*', '', queries)
    #Removing double spaces
    queries = re.sub(r'\s+',' ', queries)
    #Generating output
    return queries

#Function to verify and filter only the parameters of the consultation
def verifyFilterParams(self, queries, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    #Taking the necessary parameters for the Querie
    params = self.current_paramsEtl.copy()
    params_query = {f'{{{match}}}' for match in re.findall(self.re_parameters, queries)}
    filtered_params = {key: params[key] for key in params_query if key in params}
    #If some of the parameters are not defined, then the return is false + the missing ones
    missing = [key for key, value in filtered_params.items() if value == '']
    if missing:
        message = f"{self.i18nNes('execution', 'msgs', 'msg8')}: {', '.join(missing)}"
        #If there are multiple without specifying, the error message changes
        if len(missing) > 5:
            message = self.i18nNes('execution', 'msgs', 'msg9')
        msg = QMessageBox()
        msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(self.i18nNes('execution', 'msgs', 'msg7'))
        msg.setText(message)
        msg.exec()
        #At least a parameter is empty
        return False, missing
    #If everything is fine, return true + the parameters
    return True, filtered_params

#Function linked directly to execute.
##Find the inputs to run query between ';'
def runShortTask(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    #Identifying the query on the cursor
    query, _, _ = self.identifyQuery()
    #Cleaning comments
    query = self.cleanQ(query)
    if query == '':
        return None
    #Sending to execution
    self.runQueries(query, cls='console', saveAs=False)
    
#Function linked directly to run all.
def runLongTask(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None

    #Cleaning comments
    queries = self.current_etlEditor.toPlainText()
    queries = self.cleanQ(queries)
    
    #Asking the user if they are sure
    msg = QMessageBox(self)
    msg.setWindowIcon(self.icon)
    msg.setWindowTitle(self.i18nNes('execution', 'msgs', 'msgBE'))
    msg.setText(self.i18nNes('execution', 'msgs', 'msg10'))
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg.setDefaultButton(QMessageBox.StandardButton.Yes)
    answer = msg.exec()
    if answer == QMessageBox.StandardButton.Yes:
        #Sending to execution
        self.runQueries(queries, cls='console', saveAs=False)
    else:
        return None

#Function linked directly to run Above.
def runLongTaskAbove(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None

    #Identifying previous queries
    _, left_index, _ = self.identifyQuery()
    etl_text = self.current_etlEditor.toPlainText()
    queries = etl_text[0:left_index]
    
    #Cleaning comments
    queries = self.cleanQ(queries)
    if queries == '':
        return None
    
    #Asking the user if they are sure
    msg = QMessageBox(self)
    msg.setWindowIcon(self.icon)
    msg.setWindowTitle(self.i18nNes('execution', 'msgs', 'msgBE'))
    msg.setText(self.i18nNes('execution', 'msgs', 'msg10a'))
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg.setDefaultButton(QMessageBox.StandardButton.Yes)
    answer = msg.exec()
    if answer == QMessageBox.StandardButton.Yes:
        #Sending to execution
        self.runQueries(queries, cls='console', saveAs=False)
    else:
        return None
    
#Function linked directly to run Below.
def runLongTaskBelow(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None

    #Identifying previous queries
    query, left_index, right_index = self.identifyQuery()
    etl_text = self.current_etlEditor.toPlainText()
    
    #Get the text to the left and right of the cursor
    text_right = etl_text[right_index:-1]
    queries = query + ";" + text_right

    #Cleaning comments
    queries = self.cleanQ(queries)
    if queries == '':
        return None
    
    #Asking the user if they are sure
    msg = QMessageBox(self)
    msg.setWindowIcon(self.icon)
    msg.setWindowTitle(self.i18nNes('execution', 'msgs', 'msgBE'))
    msg.setText(self.i18nNes('execution', 'msgs', 'msg10b'))
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg.setDefaultButton(QMessageBox.StandardButton.Yes)
    answer = msg.exec()
    if answer == QMessageBox.StandardButton.Yes:
        #Sending to execution
        self.runQueries(queries, cls='console', saveAs=False)
    else:
        return None

#Function to stop the asyncExecute from executing
def stopExcWorker(self, *args):
    if self.cursorIsWorking:
        self.asyncExecute.killProcess()

#Function linked directly to execute.
##Find the inputs to run query between ';'
def runAssist(self, *args):
    #------------------------------------------------------------
    # Exit conditions
    #------------------------------------------------------------
    #Terminating if there is no active tab
    if not self.tabWidget:
        return None
    
    #Verify that the action is not null and get its text
    action = self.sender()
    if not action:
        return None
    
    #Terminating if the asyncExecute is working
    if self.cursorIsWorking:
        return None
    
    #Verifying connection
    msg = self.verifyConn()
    if not msg:
        return None
    
    #------------------------------------------------------------
    # Real code
    #------------------------------------------------------------
    #Identifying the target table
    table = self.identifyTable()
    #Taking the query corresponding to the actionMenu
    query = self.list_assist.index[action.text()]
    
    #Identifying if it is the explainand and modifying query
    if action.text() == 'Explain':
        query, _, _ = self.identifyQuery()
        query = 'explain '+ query
        table = ' '

    #Other exit conditions -- Checking table name
    if table == False:
        return None

    #Performing a check if it is count by ingestion and modifying query
    if action.text() == 'Count by ingestion':
        try:
            describe = pl.read_database(f'DESCRIBE {table};', self.conn)
        except Exception as exc:
            return None
        else:
            #Getting the ingestions names
            allowed_elements = ['ingestion_year', 'ingestion_month', 'ingestion_day']
            filtered_list = [element for element in describe['name'].to_list() if element in allowed_elements]
            #Modifying the final list
            ingestions = sorted(filtered_list, reverse=True)
            if len(ingestions)>0:
                nums1 = [str(var+1) for var in range(len(ingestions))]
                nums2 = [str(var+1)+' DESC' for var in range(len(ingestions))]
                query = f'SELECT {', '.join(ingestions)}, COUNT(1) FROM {table} GROUP BY {', '.join(nums1)} ORDER BY {', '.join(nums2)}'
            else:
                return None
    elif action.text() == 'Copy columns':
        try:
            describe = pl.read_database(f'DESCRIBE {table};', self.conn)
        except Exception as exc:
            return None
        else:
            _executed  = self.i18nNes('execution', 'status', 'executed')
            clipboard = self.app.clipboard()
            clipboard.setText('\n, '.join( describe['name'].to_list() ))
            template_row = {
                      'status':     _executed
                    , 'query':      'Copy columns'
                    , 'params':     ''
                    , 'shape':      ''
                    , 'time':       ''
                    , 'resources':  ''
                    , 'error':      ''
                    #Internal operation columns
                    , 'cls':        ''
                    , 'saveAs':     False
            }
            df = pl.DataFrame(template_row)
            result = self.current_result
            result.loadData(df, 'status')
            return None

    #EXECUTION
    #---------
    query = query.replace('{table}', table)
    #Sending to execution
    self.runQueries(query)
    return None

#Function to process and store query history
def processHistory(self, queries, params, *args):
    #Headers
    _type  = self.i18nNes('tab-eco', 'history', 'type')
    _typeU = self.i18nNes('tab-eco', 'history', 'type-u')
    _typeB = self.i18nNes('tab-eco', 'history', 'type-b')
    _query = self.i18nNes('tab-eco', 'history', 'query')
    _time  = self.i18nNes('tab-eco', 'history', 'time')
    _param = self.i18nNes('tab-eco', 'history', 'param')

    #Creating history structure if it does not exist
    if not self.actualSession.sessionHistoryExists:
        prev = pl.DataFrame({
            _type:  pl.Series([], dtype=pl.String),
            _time:  pl.Series([], dtype=pl.String),
            _query: pl.Series([], dtype=pl.String),
            _param: pl.Series([], dtype=pl.String)
        })
    else:
        prev = self.actualSession.history
    #Defining type
    cls = _typeB if len(queries.split(';')) > 1 else _typeU
    #Defining time
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #Creating the new row
    new_row = pl.DataFrame({
        _type:  [cls],
        _time:  [now],
        _query: [str(queries)],
        _param: [str(params)]
    })
    #Concatenate the new record and the previous ones, and limit 100 rows
    historial = new_row.vstack(prev.slice(0, 99))
    self.actualSession.history = historial
    #Watching
    self.actualSession.saveSessionHistory()
    #Showing
    self.hitoricResult.loadData(historial, 'base')

#Function to add the template to the text
def runTemplate(self, *args):
    #Terminating if there is no active tab
    if not self.tabWidget:
        return None
    
    action = self.sender()
    if action is not None:
        #Get the name of the active tab
        tab_name = self.tabWidget.currentWidget().objectName
        #Get the QPlainTextEdit object corresponding to the active tab
        textEditor = self.tabInfo[tab_name]['text_editor']
        #Adding the info
        template = self.list_tmplts.index[action.text()]
        cursor = textEditor.textCursor()
        cursor.insertText( template )

#Function linked to the query to file menu
def saveResult(self, *args):
    #Verifying connection
    msg = self.verifyConn()
    if not msg:
        return None
    #Identifying the query on the cursor
    query, _, _ = self.identifyQuery()
    #Cleaning comments
    query = self.cleanQ(query)
    if query == '':
        return None
    #Sending to execution
    self.runQueries(query, cls='file', saveAs=False)

#Function linked to the query to file menu
def saveResultAs(self, *args):
    #Verifying connection
    msg = self.verifyConn()
    if not msg:
        return None
    #Identifying the query on the cursor
    query, _, _ = self.identifyQuery()
    #Cleaning comments
    query = self.cleanQ(query)
    if query == '':
        return None
    #Sending to execution
    self.runQueries(query, cls='file', saveAs=True)

#Function to open the dialog box that uploads file to lZ
def runFile_to_lz(self, *args):
    #Verifying connection
    msg = self.verifyConn()
    if not msg:
        return None
    #starting window
    self.subirLz = UploadDBWidget(self)
    self.subirLz.show()

#Function to report info in the log file
def reportLog(self, data, *args):
    #Reporting in the log
    if not self.recordingLog:
        return
    time.sleep(0.5)
    self.log_file.write(data)
    return

#Function to report progress
def reportData(self, data, tab_name, rType, *args):
    #Getting info from the specific tab
    tab_data = self.tabInfo.get(tab_name)    
    #Reporting message to results table
    if tab_data:
        tab_data['result_data'] = data
        tab_data['rType'] = rType
        result = tab_data['result']
        result.loadData(data, rType)

#Function to save the file (csv or xlsx)
def toFile(self, data:pl.DataFrame, saveAs=False, *args):
    #Labels
    _toFile1 = self.i18nNes('save-files', 'toFile1')
    _toFile2 = self.i18nNes('save-files', 'toFile2')
    _toFile3 = self.i18nNes('save-files', 'toFile3')
    _toFile4 = self.i18nNes('save-files', 'toFile4')
    _save2   = self.i18nNes('save-files', 'save2')
    _saveM3  = self.i18nNes('save-files', 'saveM3')

    #Getting current date and time
    now = datetime.now()
    formatted_date = now.strftime('%Y%m%d-%H%M%S')
    download_folder = os.path.join( self.cfg_app.index.get('dataPath'), f'{formatted_date}.csv' )
    
    if saveAs:
        #Defining file type dictionary
        dic_clss = {
            f'{_toFile3} (*.csv)': ',',
            f'{_toFile1} (*.csv)': ';',
            f'{_toFile2} (*.csv)': '|',
            f'{_toFile4} (*.xlsx)': ''
        }
        
        #Opening save as window
        initial_dir = self.cfg_app.index.get('dataPath')
        file_filter = ';;'.join(dic_clss.keys())
        fileName, cls = QFileDialog.getSaveFileName(self, _save2, initial_dir, file_filter)
        
        if not fileName:
            #Saving to download path if no file is selected
            self.toFile_defaultSave(data, download_folder, _saveM3)
            return
        
        if cls == f'{_toFile4} (*.xlsx)':
            if data.height > 999995: #Excel does not support more than a million rows
                self.toFile_excelError(data, fileName, download_folder)
            else:
                self.toFile_save(data, fileName, download_folder, file_type='excel')
        else:
            self.toFile_save(data, fileName, download_folder, file_type='csv', sep=dic_clss[cls])
    else:
        #Obtaining the separate system by system default
        locale.setlocale(locale.LC_ALL, '')
        conv = locale.localeconv()
        _sep = ',' if conv['decimal_point'] == '.' else ';'
        #Saving to download path
        data.write_csv(file=download_folder, separator=_sep, include_header=True)
        try:
            _system = platform.system()
            if _system == 'Windows':
                os.startfile(download_folder)
            elif _system == 'Darwin':  #macOS
                subprocess.call(['open', download_folder])
            else:  #Linux and other Unix-Like
                subprocess.call(['xdg-open', download_folder])
        except Exception as exc:
            None

#toFile auxiliary function
def toFile_save(self, data, fileName, download_folder, file_type='csv', sep=';', *args):
    #Labels
    _save1 = self.i18nNes('save-files', 'save1')
    _saveM4 = self.i18nNes('save-files', 'saveM4')
    _saveM4 = self.i18nNes('save-files', 'saveM4')
    
    try:
        #Changing mouse pointer to standby state
        self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        if file_type == 'excel':
            data = data.to_pandas()
            data.to_excel(fileName, index=False, engine='xlsxwriter')
        else:
            data.write_csv(file=fileName, separator=sep, include_header=True)
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        #Showing message
        msg = QMessageBox()
        msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
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
def toFile_excelError(self, data, fileName, download_folder, *args):
    #Labels
    _saveM1 = self.i18nNes('save-files', 'saveM1')
    _error1 = self.i18nNes('save-files', 'error1')
    _error3 = self.i18nNes('save-files', 'error3')

    try:
        #Changing mouse pointer to standby state
        self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        data.write_csv(file=fileName[:-5] + '.csv', separator=';', include_header=True)
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        msg = QMessageBox()
        msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(_saveM1)
        msg.setText(f'{_error3}:')
        msg.setInformativeText(str(fileName[:-5] + '.csv'))
        msg.exec()
    except PermissionError:
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        self.toFile_defaultSave(data, download_folder, _error1)

#toFile auxiliary function
def toFile_defaultSave(self, data, download_folder, msg_text, *args):
    #Labels
    _saveM2 = self.i18nNes('save-files', 'saveM2')
    _error2 = self.i18nNes('save-files', 'error2')
    _error4 = self.i18nNes('save-files', 'error4')

    try:
        #Changing mouse pointer to standby state
        self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        data.write_csv(file=download_folder, separator=';', include_header=True)
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        msg = QMessageBox()
        msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(msg_text)
        msg.setText(f'{_saveM2}:')
        msg.setInformativeText(str(download_folder))
        msg.exec()
    except Exception as exc:
        #Restoring mouse cursor image
        self.app.restoreOverrideCursor()
        msg = QMessageBox()
        msg.setStyleSheet( self.dict_styledSheets['QMessageBox'] )
        msg.setWindowIcon(self.icon)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(_error2)
        msg.setText(f'{_error4}:')
        msg.setInformativeText(f'{exc}')
        msg.exec()

#Function to obtain the user's full name
def getFullUsername(self, *args):
    #Detecting the operating system   
    if platform.system() == 'Windows':
        #Defining the buffer and its maximum size
        buffer = ctypes.create_unicode_buffer(1024)
        size = ctypes.wintypes.DWORD(len(buffer))
        #Calling the Windows function to get the user's full name
        if ctypes.windll.secur32.GetUserNameExW(3, buffer, ctypes.byref(size)):
            return buffer.value
        else:
            return None

    elif platform.system() in ['Linux', 'Darwin']:  #Darwin is the identifier for macOS
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
def recLog(self, *args):
    #Labels
    _toFile5 = self.i18nNes('save-files', 'toFile5')
    _save2 = self.i18nNes('save-files', 'save2')
    _logStarted = self.i18nNes('log-messages', 'log-started')
    _logEnd = self.i18nNes('log-messages', 'log-end')
    _user = self.i18nNes('log-messages', 'user')
        
    now = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    #Starting rec animation
    if not self.recordingLog:
        #Starting recording file
        filepath = os.path.join(self.cfg_app.index.get('dataPath'), f'Luck Log-{now}')
        fileName, _ = QFileDialog.getSaveFileName(self, _save2, filepath, f'{_toFile5} (*.log)')
        if not fileName:
            return

        ##Open the file to write logs
        self.log_file = open(fileName, 'w', encoding='utf-8', buffering=1)
        #Writing standard output to log file
        msg = f'{_logStarted} {now}'
        leng = len(msg)
        self.log_file.write(f"{'='*leng}\n{msg}\n{'='*leng}\n")
        #Indicating user
        self.log_file.write(f'[{_user.upper()}]: ({self.user}) {self.getFullUsername()}\n')
        #Indicating the DSN
        self.log_file.write(f'[DSN]: {self.dsn}\n')
        #Flushing
        self.log_file.flush()
        
        #Various modifications to the ecosystem
        self.animationR_state = True
        self.recordingLog = True
        self.timerRec.start()
        self.bt_log.setToolTip(self.i18nNes('tooltips', 'sb4'))
        self.actionRecLog.setText(self.i18nNes('sql', 'end-log'))
    else:
        #Looking at the Log
        msg = f'{_logEnd} {now}'
        leng = len(msg)

        #Witing the closure directly before closing the file
        self.log_file.write(f"{'='*leng}\n{msg}\n{'='*leng}\n")
        self.log_file.close()
        self.log_file = None #Cleaning the reference
        
        self.recordingLog = False
        self.animationR_state = False
        
        self.timerRec.stop()
        self.bt_log.setIcon(self.recIcon1)
        self.lbl_status.setText(self.i18nNes('status-bar', 'log-end'))
        self.bt_log.setToolTip(self.i18nNes('tooltips', 'sb3'))
        self.actionRecLog.setText(self.i18nNes('sql', 'start-log'))

#Function to handle rec button animation
def animationRec(self, *args):
    #Indicating the start of recording
    self.lbl_status.setText(self.i18nNes('status-bar', 'log-started'))
    #Exchanging icon according to status
    if self.animationR_state:
        self.bt_log.setIcon(self.recIcon2)
    else:
        self.bt_log.setIcon(self.recIcon1)
    self.timerRec.start()
    self.animationR_state = not self.animationR_state