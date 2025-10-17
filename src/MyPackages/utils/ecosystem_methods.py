#Importing native packages
from datetime import datetime, timedelta

#Importing PyQt6 packages
from PyQt6.QtWidgets import (QWidget, QVBoxLayout
    , QSplitter, QGroupBox, QLineEdit, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
#Importing custom classes and methods
from MyPackages import (MyResultTable, MyTreeView)

#==================================================================
#Creating database tree and exploratory functions
#==================================================================
#Function to download the tree
def downloadTree(self, force = False, *args):
    #Do not execute if the AsyncTree is working
    if self.asynTree.isRunning():
        return
    #Veryfying connection
    msg = self.verifyConn()
    if not msg:
        return None

    if not force and self.firstConexionSignal:
        self.firstConexionSignal.disconnect(self.downloadTree)
    
    #Obtaining reference data
    if self.actualSession.sessionTreeExists:
        _date = self.actualSession.tree.get('date')
    else:
        _date = '2024-03-13'
    last = datetime.strptime(_date, '%Y-%m-%d').date()
    now = datetime.now().date()
    days = self.cfg_app.index.get('tree-update-in')
    delta = timedelta(days=days)

    #Only runs once every so often, unless forced
    #Check if the current date is greater than one week after the saved date
    if (now > last + delta) or force:
        self.lbl_status.setText(self.i18nNes('status-bar', 'update-tree'))
        self.asynTree.start()

#Function to update the tree
def endAsynTree(self, localTree:dict, *args):
    if not localTree:
        self.lbl_status.setText(self.i18nNes('status-bar', 'update-error'))
        return
    
    self.actualSession.saveSessionTree(localTree)
    #Send the data to the visual tree
    self.dataBaseTree.loadData(localTree)
    self.lbl_status.setText(self.i18nNes('status-bar', 'updated-tree'))
    self.asynTree.quit()
    # self.asynTree.deleteLater()

#Function that creates a new tab in the window
def ecosystemTab(self, *args):
    #Changing mouse pointer to standby state
    self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)

    self.num_Stab += 1
    tab_new = QWidget()
    layoutTab = QVBoxLayout()
    layoutTab.setContentsMargins(0, 0, 0, 0)
    tab_new.setLayout(layoutTab)
    
    #Loading default font
    font = self.cfg_session.index.get('prede_font')
    internalProfile = self.cfg_session.index.get('internal_profile')
    self.styler(internalProfile)
    
    #Tree Widget
    #-----------
    groupBoxTree = QGroupBox(self.i18nNes('tab-eco', 'db'))
    treeLayout = QVBoxLayout()
    treeLayout.setContentsMargins(0, 0, 0, 0)
    #Search
    self.treeSearchBar = QLineEdit()
    self.treeSearchBar.setPlaceholderText(self.i18nNes('tab-eco', 'searh-table'))
    treeLayout.addWidget(self.treeSearchBar)
    #Tree
    self.dataBaseTree = MyTreeView(self)
    self.dataBaseTree.setStyleSheet( self.dict_styledSheets['MyTreeView'] )
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
    groupBoxResult = QGroupBox(self.i18nNes('tab-eco', 'table-strctr'))
    resultLayout = QVBoxLayout()
    resultLayout.setContentsMargins(0, 0, 0, 0)
    #Title
    self.tableDescribed = QLabel()
    self.tableDescribed.setObjectName('lbl_tableDescribe')
    self.tableDescribed.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
    resultLayout.addWidget(self.tableDescribed)
    #Tabla
    self.dbtResult = MyResultTable(self)
    self.dbtResult.setStyleSheet( self.dict_styledSheets['MyResultTable'] )
    self.dbtResult.setFont( QFont(font['result-font'], font['result-size']) )
    self.dbtResult.sizeChanged.connect(lambda font: self.applyFontSize(font, 'result'))
    
    self.dataBaseTree.describeReady.connect(self.dbtResult.loadData)
    resultLayout.addWidget(self.dbtResult)
    groupBoxResult.setLayout(resultLayout)

    #History Table Widget
    #-------------------------
    groupBoxHistory = QGroupBox(self.i18nNes('tab-eco', 'history', 'header'))
    historyLayout = QVBoxLayout()
    historyLayout.setContentsMargins(0, 0, 0, 0)
    self.hitoricResult = MyResultTable(self)
    self.hitoricResult.setStyleSheet( self.dict_styledSheets['MyResultTable'] )
    self.hitoricResult.setFont( QFont(font['result-font'], font['result-size']) )
    self.hitoricResult.sizeChanged.connect(lambda font: self.applyFontSize(font, 'result'))
    self.hitoricResult.columnSizeChanged.connect(
        lambda t: self.cfg_session.getNested('eco', 'history-frame').__setitem__(t[0], t[1])
    )
    
    historyLayout.addWidget(self.hitoricResult)
    groupBoxHistory.setLayout(historyLayout)
    #Loading previous results
    if self.actualSession.sessionHistoryExists:
        self.hitoricResult.loadData(self.actualSession.history, 'base')

        sizes = self.cfg_session.getNested('eco', 'history-frame')
        #Taking the size only of the active columns
        header = self.hitoricResult.horizontalHeader()
        for i in range(header.count()):
            header.resizeSection(i, sizes[i])
        
    #Adding objects to splitters
    #-------------------------------------
    geo = self.cfg_session.getNested('eco', 'splitter_geo_eco')
    ref = self.size().width() - 39
    self.splitter_eco = QSplitter(Qt.Orientation.Horizontal)
    self.splitter_eco.addWidget(groupBoxTree)
    self.splitter_eco.addWidget(groupBoxResult)
    self.splitter_eco.addWidget(groupBoxHistory)
    layoutTab.addWidget(self.splitter_eco)
    self.splitter_eco.splitterMoved.connect(self.saveEcoSplittersSizes)

    self.splitter_eco.setSizes([
        int(ref * geo[0]),
        int(ref * geo[1]),
        int(ref * geo[2])
    ])

    #Setting the splitter handles to hover state
    for i in range(1, self.splitter_eco.count()):
        handle = self.splitter_eco.handle(i)
        handle.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            
    #Adding and activating the new tab
    self.tabWidget.addTab(tab_new, self.i18nNes('tab-eco', 'eco'))
    self.tabWidget.setCurrentIndex(0)
    
    #Changing mouse pointer to default state
    self.app.restoreOverrideCursor()
        

