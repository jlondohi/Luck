#Importing native packages
import re, os
import pandas as pd
from datetime import datetime, timedelta

#Importing PyQt6 packages
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QTreeView, QMenu
from PyQt6.QtCore import Qt, QSortFilterProxyModel, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QAction, QActionGroup  \
    , QKeySequence, QStandardItemModel, QStandardItem
#Importing custom classes and methods
from MyPackages import MyPlainTextEdit, ResultTable \
    , MySyntaxHighlighter
#=================================================
#Creating database tree and exploratory functions
#=================================================

class MyTreeView(QTreeView):
    #Defining signals
    describeReady = pyqtSignal(pd.DataFrame)

    def __init__(self, parent):
        super().__init__()
        self.app = QApplication.instance()

        self.parent = parent
        #Creating the data model
        self.tree = None
        self.treeModel = QStandardItemModel()
        self.treeModel.setHorizontalHeaderLabels([''])
        self.header().setVisible(False)
        self.setModel(self.treeModel)
        #Defining the proxy model
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.treeModel)
        self.proxyModel.setRecursiveFilteringEnabled(True) 
        self.proxyModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        #Setting the model
        self.setModel(self.proxyModel)
        #Loading Icon
        self.icon0 = QIcon('Guis/Resources/database0.png')
        self.icon1 = QIcon('Guis/Resources/database1.png')
        self.icon2 = QIcon('Guis/Resources/database2.png')
        self.icon3 = QIcon('Guis/Resources/database3.png')
        #Connecting the signals
        self.expanded.connect(self.onItemExpanded)
        self.collapsed.connect(self.onItemCollapsed)
        #Various settings
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.onItemClicked)
        self.expansion_state = {}
        
        #Language
        self.nested = parent.i18n.getNested
        self.lgg = parent.lgg
        #Headers
        self._status = self.nested(self.lgg, "execution", "header", "status")
        self._error = self.nested(self.lgg, "execution", "header", "error")
        self._table = self.nested(self.lgg, "execution", "header", "table")
        #States
        self._running = self.nested(self.lgg, "execution", "status", "running")
        self._failed = self.nested(self.lgg, "execution", "status", "failed")
        #Msgs
        self._msg6 = self.nested(self.lgg, "execution", "msgs", "msg6")

        #Tree
        self._copy = self.nested(self.lgg, "tab-eco", "tree", "copy")
        self._update = self.nested(self.lgg, "tab-eco", "tree", "update")
        self._updateAll = self.nested(self.lgg, "tab-eco", "tree", "update-all")

    #Function to apply the search filter to the tree
    def filterTree(self, text):
        if not text:
            self.restoreState()
            self.expansion_state.clear()
        else:
            self.saveState()
            self.proxyModel.setFilterFixedString(text)
            self.expandFilteredItems(text)
    
    #Expanding filtered items
    def expandFilteredItems(self, text):
        #Cycle through all the elements visible in the proxy and expand the ones that contain the text

        for row in range(self.proxyModel.rowCount()):
            index = self.proxyModel.index(row, 0)
            self.expand(index)

    #Function to save state prior to filtering
    def saveState(self):
        if not self.expansion_state:
            for row in range(self.proxyModel.rowCount()):
                index = self.proxyModel.index(row, 0)
                self.expansion_state[index] = self.isExpanded(index)
    
    #Function to restore the state before filtering
    def restoreState(self):
        for index in self.expansion_state.keys():
            status = self.expansion_state[index]
            self.expand(index) if status else self.collapse(index)

    #Function to load data to the tree
    def loadData(self, sessionTree:dict):
        #Deleting previous model
        self.treeModel.clear()

        #Copying info
        self.sessionTree = sessionTree
        tree = self.sessionTree.get("tree")

        #Going through each key
        for database, tables in tree.items():
            #Defining the corresponding icon
            icon = self.icon1 if tables else self.icon0

            #Creating an element for the key
            database_item = QStandardItem(database)
            database_item.setIcon(icon)
            self.treeModel.appendRow(database_item)
            
            #Add each table as a child of the key
            for table, stats in tables.items():
                table_item = QStandardItem(table)
                #Setting icon
                table_item.setIcon(self.icon3)
                #Adding the item to the tree
                database_item.appendRow(table_item)

        #Fit columns to content
        self.resizeColumnToContents(0)
        
    #Function to expand the show describe
    def onItemClicked(self, index):
        source_index = self.proxyModel.mapToSource(index)
        item = self.treeModel.itemFromIndex(source_index)
        if not item:
            return
        #Checking if it is a parent or child item
        if item.hasChildren():
            #Expand or collapse if parent
            if self.isExpanded(index):
                self.collapse(index)
                item.setIcon(self.icon1)
            else:
                self.expand(index)
                item.setIcon(self.icon2)
        #If it is a son, your description will be searched.
        else:
            parent_item = item.parent()
            if parent_item is not None:
                table = f"{parent_item.text()}.{item.text()}"
                self.describeOfTree(table)
    
    #Function to change the icon when expanding from the arrow
    def onItemExpanded(self, index):
        source_index = self.proxyModel.mapToSource(index)
        item = self.treeModel.itemFromIndex(source_index)
        if item and item.hasChildren():
            item.setIcon(self.icon2)

    #Function to change the icon when collapsing from the arrow
    def onItemCollapsed(self, index):
        source_index = self.proxyModel.mapToSource(index)
        item = self.treeModel.itemFromIndex(source_index)
        if item and item.hasChildren():
            item.setIcon(self.icon1)

    #Requesting the describe
    def describeOfTree(self, table):
        if table:
            #Changing mouse pointer to standby state
            self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
            #Creating a temporary Dataframe while the end arrives
            temp = pd.DataFrame({
                    self._status: pd.Series(dtype=str),
                    self._table: pd.Series(dtype=str),
                    self._error: pd.Series(dtype=str)
                                })
            #Managing general message
            temp.loc[0, self._status] = self._running
            temp.loc[0, self._table] = table
            temp.loc[0, self._error] = ""

            self.describeReady.emit(temp)
            
            #Verifying connection
            if not self.parent.cursorIsWorking:
                msg = self.parent.verifyConn()
                if msg == None:
                    temp.loc[0, self._status] = self._failed
                    temp.loc[0, self._error] = self._msg6
                    self.describeReady.emit(temp)
                    self.app.restoreOverrideCursor()
                    return None
                
                #Taking the board
                query = f"describe {table};"
                self.parent.tableDescribed.setText(f"{self._table}: {table}")
                try:
                    temp2 = pd.read_sql(query, self.parent.conn)
                    self.describeReady.emit(temp2)
                except Exception as exc:
                    temp.loc[0, self._status] = self._failed
                    temp.loc[0, self._error] = exc
                    self.describeReady.emit(temp)
            #Changing mouse pointer to default state
            self.app.restoreOverrideCursor()
    
    #Function to detect request of context menú 
    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return

        source_index = self.proxyModel.mapToSource(index)
        item = self.treeModel.itemFromIndex(source_index)

        if item:
            #Create the context menu
            menu = QMenu(self)
            #Validating if it is a son or father
            if item.hasChildren():
                #Upadate a DB
                update = QAction(self._update, self)
                update.triggered.connect(lambda: self.updateTables(item.text()))
                #Upadate tree
                updateAll = QAction(self._updateAll, self)
                updateAll.triggered.connect(self.updateAllTree)

                #Populating menu
                menu.addAction(update)
                menu.addSeparator()
                menu.addAction(updateAll)
            else:
                #Table
                copy_action = QAction(self._copy, self)
                copy_action.triggered.connect(lambda: self.copyTableName(item))
                menu.addAction(copy_action)

            #Show the context menu
            menu.exec(event.globalPos())
    
    #Function to update DB
    def updateTables(self, databaseName):
        #Do not execute if the worker is working
        if self.parent.cursorIsWorking:
            return
        
        #Veryfying connection
        msg = self.parent.verifyConn()
        if msg == None:
            return None

        #Requesting information from the DB
        cursor = self.parent.conn.cursor()
        self.parent.lbl_status.setText(self.nested(self.lgg, "status-bar", "update-db"))
        #Downloading tables of database
        try:
            cursor.execute(f"SHOW TABLES IN {databaseName};")
            tables = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            tables = []

        #Populating the rest of the information
        for table in tables:
            self.sessionTree['tree'][databaseName][table] = [None, None]
        
        #Save the tree locally
        self.parent.actualSession.saveSessionTree(self.sessionTree)
        #Send the data to the visual tree
        self.loadData(self.sessionTree)
        self.parent.lbl_status.setText(self.nested(self.lgg, "status-bar", "updated-db"))
    
    #Function to update tree (All DB)
    def updateAllTree(self):
        self.parent.downloadTree(force=True)

    #Function to copy table with DB
    def copyTableName(self, item):
        parent_item = item.parent()
        if parent_item:
            table_name = f"{parent_item.text()}.{item.text()}"
            clipboard = QApplication.clipboard()
            clipboard.setText(table_name)

    #Function to execute functions depending on the keys pressed
    def keyPressEvent(self, event):
        #Detecting Ctrl+C
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            index = self.currentIndex()
            if not index.isValid():
                return

            source_index = self.proxyModel.mapToSource(index)
            item = self.treeModel.itemFromIndex(source_index)
            
            #Only activated if it is a table
            if item and not item.hasChildren():
                self.copyTableName(item)
        else:
            #Allow default handling for other keys
            super().keyPressEvent(event)



            
