#Importing native packages
from datetime import datetime, timedelta

#Importing PyQt6 packages
from PyQt6.QtWidgets import QWidget, QVBoxLayout \
    , QSplitter, QGroupBox, QLineEdit, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
#Importing custom classes and methods
from MyPackages import ResultTable, MyTreeView

#================================================================== ===================
#Creating database tree and exploratory functions
#================================================================== ===================
#Function to update the tree
def downloadTree(self, force = False):
    #Do not execute if the worker is working
    if self.cursorIsWorking:
        return
    
    #Veryfying connection
    msg = self.verifyConn()
    if msg == None:
        return None
        
    #Instantiating language
    nested = self.i18n.getNested

    if not force and self.firstConexionSignal:
        self.firstConexionSignal.disconnect(self.downloadTree)
    
    #Obtaining reference data   
    if self.actualSession.sessionTreeExists:
        _date = self.actualSession.tree.get("date")
    else:
        _date = "2024-03-13"
    last = datetime.strptime(_date, '%Y-%m-%d').date()
    now = datetime.now().date()
    delta = timedelta(days = self.cfg_user.index.get("tree-update-in"))

    #Only runs once every so often, unless forced
    #Check if the current date is greater than one week after the saved date
    if (now > last + delta) or force:
        self.lbl_status.setText(nested("status-bar", "update-tree"))
        
        #Creating cursor for queries
        cursor = self.conn.cursor()
        #Downloading the databases
        try:
            cursor.execute("SHOW DATABASES;")
            databases = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.lbl_status.setText(self.nested("status-bar", "unex-error"))
            return

        #Creating objects to save locally
        tree = {}
        expanded_tree = {}

        #Downloading tables per database
        for database in databases:
            try:
                cursor.execute(f"SHOW TABLES IN {database};")
                tables = [row[0] for row in cursor.fetchall()]
            except Exception as e:
                tables = []
            tree[database] = tables

        #Downloading statistics by table
        for database, tables in tree.items():
            if not tables:
                continue
            for table in tables:
                try:
                    #cursor.execute(f"SHOW TABLE STATS {database}.{table}")
                    #result = cursor.fetchall()
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
        localTree = {
            "date": now.strftime('%Y-%m-%d'),
            "tree": expanded_tree,
        }
        self.actualSession.saveSessionTree(localTree)
        #Send the data to the visual tree
        self.dataBaseTree.loadData(localTree)
        self.lbl_status.setText(nested("status-bar", "updated-tree"))

#Function that creates a new tab in the window
def ecosystemTab(self):
    #Instantiating language
    nested = self.i18n.getNested

    #Changing mouse pointer to standby state
    self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)

    self.num_Stab += 1
    tab_new = QWidget()
    layoutTab = QVBoxLayout()
    layoutTab.setContentsMargins(0, 0, 0, 0)
    tab_new.setLayout(layoutTab)
    
    #Loading default font
    font = self.cfg_session.index.get("prede_font")
    internal_theme = self.cfg_session.index.get("internal_theme")
    self.styler(internal_theme)
    
    #Tree Widget
    #-----------
    groupBoxTree = QGroupBox(nested("tab-eco", "db"))
    treeLayout = QVBoxLayout()
    treeLayout.setContentsMargins(0, 0, 0, 0)
    #Search
    self.treeSearchBar = QLineEdit()
    self.treeSearchBar.setPlaceholderText(nested("tab-eco", "searh-table"))
    treeLayout.addWidget(self.treeSearchBar)
    #Tree
    self.dataBaseTree = MyTreeView(self)
    self.dataBaseTree.setStyleSheet( self.dict_styledSheets["tree_styler"] )
    self.treeSearchBar.textChanged.connect(self.dataBaseTree.filterTree)
    treeLayout.addWidget(self.dataBaseTree)
    groupBoxTree.setLayout(treeLayout)
    #Loading data stored in the system
    if self.actualSession.sessionTreeExists:
        _tree = self.actualSession.tree
        #Sending the data to the tree
        self.dataBaseTree.loadData(_tree)
    
    #Results tab widget
    #--------------------------
    groupBoxResult = QGroupBox(nested("tab-eco", "table-strctr"))
    resultLayout = QVBoxLayout()
    resultLayout.setContentsMargins(0, 0, 0, 0)
    #Title
    self.tableDescribed = QLabel()
    self.tableDescribed.setObjectName("lbl_tableDescribe")
    self.tableDescribed.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
    resultLayout.addWidget(self.tableDescribed)
    #Tabla
    self.dbtResult = ResultTable(self)
    self.dbtResult.setStyleSheet( self.dict_styledSheets["result_styler"] )
    self.dbtResult.setFont( QFont(font["result-font"], font["result-size"]) )
    self.dbtResult.sizeChanged.connect(lambda font: self.applyFontSize(font, "result"))
    
    self.dataBaseTree.describeReady.connect(self.dbtResult.loadData)
    resultLayout.addWidget(self.dbtResult)
    groupBoxResult.setLayout(resultLayout)

    #History Table Widget
    #-------------------------
    groupBoxHistory = QGroupBox(nested("tab-eco", "history", "header"))
    historyLayout = QVBoxLayout()
    historyLayout.setContentsMargins(0, 0, 0, 0)
    self.hitoricResult = ResultTable(self)
    self.hitoricResult.setStyleSheet( self.dict_styledSheets["result_styler"] )
    self.hitoricResult.setFont( QFont(font["result-font"], font["result-size"]) )
    self.hitoricResult.sizeChanged.connect(lambda font: self.applyFontSize(font, "result"))
    
    historyLayout.addWidget(self.hitoricResult)
    groupBoxHistory.setLayout(historyLayout)
    #Loading previous results
    if self.actualSession.sessionHistoryExists:
        self.hitoricResult.loadData(self.actualSession.history)

    #Adding all results to your list
    #--------------------------------------
    self.list_QTable.append(self.dbtResult)
    self.list_QTable.append(self.hitoricResult)

    #Adding objects to splitters
    #-------------------------------------
    splitter_h = QSplitter(Qt.Orientation.Horizontal)
    splitter_h.addWidget(groupBoxTree)
    splitter_h.addWidget(groupBoxResult)
    splitter_h.addWidget(groupBoxHistory)
    layoutTab.addWidget(splitter_h)
            
    #Adding and activating the new tab
    self.tabWidget.addTab(tab_new, nested("tab-eco", "eco"))
    self.tabWidget.setCurrentIndex(0)
    
    #PENDING. Setting splitter sizes
    # geo = self.cfg_session.index.get('splitter_geo')
    # splitter_h.setSizes([int(self.screen_width*geo[0]), int(self.screen_width*geo[1])])

    #Changing mouse pointer to default state
    self.app.restoreOverrideCursor()
        

