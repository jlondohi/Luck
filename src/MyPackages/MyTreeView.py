#Importing native packages
import polars as pl
from functools import partial

#Importing PyQt6 packages
from PyQt6.QtWidgets import QApplication, QTreeView, QMenu
from PyQt6.QtCore import (Qt, QSortFilterProxyModel, pyqtSignal)
from PyQt6.QtGui import (QIcon, QAction, QStandardItemModel, QStandardItem)
#Importing local packages
from MyPackages.utils import polars_methods as pm
#=================================================
#Creating database tree and exploratory functions
#=================================================

class MyTreeView(QTreeView):
    """
    Custom QTreeView for displaying and interacting with a database tree, including context menus and filtering.

    Signals:
        describeReady (pl.DataFrame): Emitted when a table description DataFrame is ready.

    Attributes:
        app (QApplication): Reference to the QApplication instance.
        parent (QWidget): Parent widget.
        updating (bool): Indicates if the tree is currently updating.
        tree (object): Data model for the tree (unused in this code).
        treeModel (QStandardItemModel): Model for the tree structure.
        proxyModel (QSortFilterProxyModel): Proxy model for filtering and sorting.
        icon0, icon1, icon2, icon3 (QIcon): Icons for different tree items.
        expansionState (dict): Stores expansion state for tree items.
        i18nNes (callable): Internationalization function.
        _status, _error, _table (str): Localized header strings.
        _running, _failed (str): Localized status strings.
        _msg6 (str): Localized message string.
        _copy, _update, _updateAll, _expand, _expandAll, _collapse, _collapseAll (str): Localized tree action strings.
        menu1 (QMenu): Context menu for parent items (databases).
        menu2 (QMenu): Context menu for child items (tables).
        actionUpdate, actionExpColl, actionCopy, actionCollapse (QAction): Actions for context menus.

    Methods:
        __init__(self, parent): Initializes the tree view and its models, icons, and menus.
        filterTree(self, text, *args): Applies a search filter to the tree.
        expandFilteredItems(self, text, *args): Expands items matching the filter.
        saveState(self, *args): Saves the expansion state of the tree.
        restoreState(self, *args): Restores the expansion state of the tree.
        loadData(self, sessionTree:dict, *args): Loads data into the tree from a session tree dictionary.
        onItemClicked(self, index, *args): Handles item click events for expanding/collapsing or describing tables.
        onItemExpanded(self, index, *args): Changes icon when an item is expanded.
        onItemCollapsed(self, index, *args): Changes icon when an item is collapsed.
        describeOfTree(self, table, *args): Emits a description DataFrame for a table.
        createMenus(self, *args): Creates context menus for parent and child items.
        showMenu(self, position, *args): Shows the appropriate context menu at the given position.
        updateTables(self, databaseName, *args): Updates the tables for a given database.
        updateAllTree(self, *args): Updates all databases in the tree.
        copyTableName(self, item, *args): Copies the full table name to the clipboard.
        keyPressEvent(self, event, *args): Handles key press events for shortcuts like Ctrl+C.
    """

    #Defining signals
    describeReady = pyqtSignal(pl.DataFrame)

    def __init__(self, parent):
        """
        Initializes the MyTreeView, setting up models, icons, context menus, and signals.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__()
        self.app = QApplication.instance()

        self.parent = parent
        self.updating = False
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
        self.icon0 = QIcon(str(self.parent.guisPath / 'Resources' / 'database0.png'))
        self.icon1 = QIcon(str(self.parent.guisPath / 'Resources' / 'database1.png'))
        self.icon2 = QIcon(str(self.parent.guisPath / 'Resources' / 'database2.png'))
        self.icon3 = QIcon(str(self.parent.guisPath / 'Resources' / 'database3.png'))
        #Connecting the signals
        self.expanded.connect(self.onItemExpanded)
        self.collapsed.connect(self.onItemCollapsed)
        #Various settings
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.onItemClicked)
        self.expansionState = {}
        
        #Language
        self.i18nNes = parent.i18nNes
        #Headers
        self._status    = self.i18nNes('execution', 'header', 'status')
        self._error     = self.i18nNes('execution', 'header', 'error')
        self._table     = self.i18nNes('execution', 'header', 'table')
        #States
        self._running   = self.i18nNes('execution', 'status', 'running')
        self._failed    = self.i18nNes('execution', 'status', 'failed')
        #Msgs
        self._msg6      = self.i18nNes('execution', 'msgs', 'msg6')

        #Tree
        self._copy      = self.i18nNes('tab-eco', 'tree', 'copy')
        self._update    = self.i18nNes('tab-eco', 'tree', 'update')
        self._updateAll = self.i18nNes('tab-eco', 'tree', 'update-all')
        self._expand    = self.i18nNes('tab-eco', 'tree', 'expand')
        self._expandAll    = self.i18nNes('tab-eco', 'tree', 'expand-all')
        self._collapse  = self.i18nNes('tab-eco', 'tree', 'collapse')
        self._collapseAll  = self.i18nNes('tab-eco', 'tree', 'collapse-all')
        #Enable the personalized context menu
        self.createMenus()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showMenu)

    #Function to apply the search filter to the tree
    def filterTree(self, text, *args):
        """
        Applies a search filter to the tree and expands matching items.

        Args:
            text (str): The filter text.
            *args: Additional arguments (unused).
        """
        if not text:
            self.restoreState()
            self.expansionState.clear()
        else:
            self.saveState()
            self.proxyModel.setFilterFixedString(text)
            self.expandFilteredItems(text)
    
    #Expanding filtered items
    def expandFilteredItems(self, text, *args):
        """
        Expands all items in the proxy model that match the filter.

        Args:
            text (str): The filter text.
            *args: Additional arguments (unused).
        """
        #Cycle through all the elements visible in the proxy and expand the ones that contain the text

        for row in range(self.proxyModel.rowCount()):
            index = self.proxyModel.index(row, 0)
            self.expand(index)

    #Function to save state prior to filtering
    def saveState(self, *args):
        """
        Saves the current expansion state of the tree.

        Args:
            *args: Additional arguments (unused).
        """
        if not self.expansionState:
            for row in range(self.proxyModel.rowCount()):
                index = self.proxyModel.index(row, 0)
                self.expansionState[index] = self.isExpanded(index)
    
    #Function to restore the state before filtering
    def restoreState(self, *args):
        """
        Restores the expansion state of the tree.

        Args:
            *args: Additional arguments (unused).
        """
        for index in self.expansionState.keys():
            status = self.expansionState[index]
            self.expand(index) if status else self.collapse(index)

    #Function to load data to the tree
    def loadData(self, sessionTree:dict, *args):
        """
        Loads data into the tree from a session tree dictionary.

        Args:
            sessionTree (dict): The session tree data.
            *args: Additional arguments (unused).
        """
        #Deleting previous model
        self.treeModel.clear()

        #Copying info
        self.sessionTree = sessionTree
        tree = self.sessionTree.get('tree')

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
    def onItemClicked(self, index, *args):
        """
        Handles item click events for expanding/collapsing or describing tables.

        Args:
            index (QModelIndex): The clicked item index.
            *args: Additional arguments (unused).
        """
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
                table = f'{parent_item.text()}.{item.text()}'
                self.describeOfTree(table)
    
    #Function to change the icon when expanding from the arrow
    def onItemExpanded(self, index, *args):
        """
        Changes the icon when an item is expanded.

        Args:
            index (QModelIndex): The expanded item index.
            *args: Additional arguments (unused).
        """
        source_index = self.proxyModel.mapToSource(index)
        item = self.treeModel.itemFromIndex(source_index)
        if item and item.hasChildren():
            item.setIcon(self.icon2)

    #Function to change the icon when collapsing from the arrow
    def onItemCollapsed(self, index, *args):
        """
        Changes the icon when an item is collapsed.

        Args:
            index (QModelIndex): The collapsed item index.
            *args: Additional arguments (unused).
        """
        source_index = self.proxyModel.mapToSource(index)
        item = self.treeModel.itemFromIndex(source_index)
        if item and item.hasChildren():
            item.setIcon(self.icon1)

    #Requesting the describe
    def describeOfTree(self, table, *args):
        """
        Emits a description DataFrame for the specified table.

        Args:
            table (str): The table name in 'database.table' format.
            *args: Additional arguments (unused).

        Emits:
            describeReady (pl.DataFrame): When the table description is ready.
        """
        if table:
            #Changing mouse pointer to standby state
            self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
            #Creating a temporary Dataframe while the end arrives
            temp = pl.DataFrame({
                self._status: [self._running],
                self._table: [table],
                self._error: ['']
            })
            self.describeReady.emit(temp)
            
            #Verifying connection
            if not self.parent.cursorIsWorking:
                msg = self.parent.verifyConn()
                if not msg:
                    temp = pm.replace_row(temp, 0, {self._status:self._failed, self._error:self._msg6})
                    self.describeReady.emit(temp)
                    self.app.restoreOverrideCursor()
                    return None
                
                #Taking the board
                query = f'describe {table};'
                self.parent.tableDescribed.setText(f'{self._table}: {table}')
                try:
                    temp2 = pl.read_database(query, self.parent.conn)
                    self.describeReady.emit(temp2)
                except Exception as exc:
                    temp = pm.replace_row(temp, 0, {self._status:self._failed, self._error:str(exc)})
                    self.describeReady.emit(temp)
            #Changing mouse pointer to default state
            self.app.restoreOverrideCursor()
    
    #Function to create contextual menus
    def createMenus(self, *args):
        """
        Creates context menus for parent (database) and child (table) items.

        Args:
            *args: Additional arguments (unused).
        """
        #Menu for parent items (databases)
        self.menu1 = QMenu(self)
        self.actionUpdate = QAction(self._update, self)
        actionUpdateAll = QAction(self._updateAll, self)
        self.actionExpColl = QAction(self._expand, self)
        actionExpandAll = QAction(self._expandAll, self)
        actionCollapseAll = QAction(self._collapseAll, self)

        actionUpdateAll.triggered.connect(self.updateAllTree)
        actionExpandAll.triggered.connect(self.expandAll)
        actionCollapseAll.triggered.connect(self.collapseAll)

        self.menu1.addAction(self.actionUpdate)
        self.menu1.addAction(actionUpdateAll)
        self.menu1.addSeparator()
        self.menu1.addAction(self.actionExpColl)
        self.menu1.addSeparator()
        self.menu1.addAction(actionExpandAll)
        self.menu1.addAction(actionCollapseAll)

        #Menu for child items (tables)
        self.menu2 = QMenu(self)
        self.actionCopy = QAction(self._copy, self)
        actionCopy = QAction(self._copy, self)
        self.actionCollapse = QAction(self._collapse, self)

        self.menu2.addAction(self.actionCopy)
        self.menu2.addSeparator()
        self.menu2.addAction(self.actionCollapse)
        self.menu2.addAction(actionCollapseAll)
        
    #Function to show menues
    def showMenu(self, position, *args):
        """
        Shows the appropriate context menu at the given position.

        Args:
            position (QPoint): The position to show the menu.
            *args: Additional arguments (unused).
        """
        proxy_index = self.indexAt(position)
        if not proxy_index.isValid():
            return
        
        source_index = self.proxyModel.mapToSource(proxy_index)
        item = self.treeModel.itemFromIndex(source_index)

        if not item:
            return
        #There are two menus, choosing which
        if item.hasChildren():
            try:
                self.actionUpdate.triggered.disconnect()
                self.actionExpColl.triggered.disconnect()
            except TypeError:
                pass
            #Connect the action with the current item
            self.actionUpdate.triggered.connect(partial(self.updateTables, item.text()))
            if self.isExpanded(proxy_index):
                self.actionExpColl.triggered.connect(partial(self.collapse, proxy_index))
                self.actionExpColl.setText(self._collapse)
            else:
                self.actionExpColl.triggered.connect(partial(self.expand, proxy_index))
                self.actionExpColl.setText(self._expand)
            self.menu1.exec(self.mapToGlobal(position))
        else:
            try:
                self.actionCopy.triggered.disconnect()
                self.actionCollapse.triggered.disconnect()
            except TypeError:
                pass
            #Connect the action with the current item
            self.actionCopy.triggered.connect(partial(self.copyTableName, item))
            parent_proxy_index = proxy_index.parent()
            self.actionCollapse.triggered.connect(partial(self.collapse, parent_proxy_index))
            self.menu2.exec(self.mapToGlobal(position))
    
    #Function to update DB
    def updateTables(self, databaseName, *args):
        """
        Updates the tables for the specified database.

        Args:
            databaseName (str): The name of the database to update.
            *args: Additional arguments (unused).
        """
        #Do not execute if the asyncExecute is working
        if self.parent.cursorIsWorking or self.updating:
            return
        
        #Veryfying connection
        msg = self.parent.verifyConn()
        if not msg:
            return None

        #Requesting information from the DB
        cursor = self.parent.conn.cursor()
        self.parent.lbl_status.setText(self.i18nNes('status-bar', 'update-db'))
        #Downloading tables of database
        self.updating = True
        try:
            cursor.execute(f'SHOW TABLES IN {databaseName};')
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
        self.parent.lbl_status.setText(self.i18nNes('status-bar', 'updated-db'))
        self.updating = False
    
    #Function to update tree (All DB)
    def updateAllTree(self, *args):
        """
        Updates all databases in the tree.

        Args:
            *args: Additional arguments (unused).
        """
        self.parent.downloadTree(force=True)

    #Function to copy table with DB
    def copyTableName(self, item, *args):
        """
        Copies the full table name (database.table) to the clipboard.

        Args:
            item (QStandardItem): The table item.
            *args: Additional arguments (unused).
        """
        parent_item = item.parent()
        if parent_item:
            table_name = f'{parent_item.text()}.{item.text()}'
            clipboard = QApplication.clipboard()
            clipboard.setText(table_name)

    #Function to execute functions depending on the keys pressed
    def keyPressEvent(self, event, *args):
        """
        Handles key press events for shortcuts like Ctrl+C to copy table names.

        Args:
            event (QKeyEvent): The key event.
            *args: Additional arguments (unused).
        """
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