#Importing native packages
import re, os
import pandas as pd
from datetime import datetime, timedelta

#Importing PyQt6 packages
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QTreeView
from PyQt6.QtCore import Qt, QSortFilterProxyModel, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
#Importing custom classes and methods
from MyPackages import MyPlainTextEdit, ResultTable \
    , MySyntaxHighlighter

from PyQt6.QtGui import QStandardItemModel, QStandardItem
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
    def loadData(self, tree:dict):
        #Deleting previous model
        self.treeModel.clear()

        #Going through each key
        for base in tree.keys():
            #Defining the corresponding icon
            tablas = tree[base]
            if len(tablas) == 0:
                icon = self.icon0
            else:
                icon = self.icon1
            #Creating an element for the key
            base_item = QStandardItem(base)
            base_item.setIcon(icon)
            self.treeModel.appendRow(base_item)
            
            #Add each table as a child of the key
            for tabla in tablas:
                tabla_item = QStandardItem(tabla)
                base_item.appendRow(tabla_item)
                #Setting icon
                tabla_item.setIcon(self.icon3)

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