from operator import index
import polars as pl
from functools import partial
from PyQt6.QtWidgets import (QApplication, QTableView 
    , QMenu, QHeaderView, QInputDialog, QAbstractItemView
    , QStyledItemDelegate)
from PyQt6.QtGui import (QAction, QFont, QColor, QBrush, QPen
    , QPalette)
from PyQt6.QtCore import (Qt, pyqtSignal, QAbstractTableModel
    , QModelIndex)
from MyPackages.MyTooltip import MyTooltip

#========================================
### Creating class to draw results table
#========================================
class CustomDelegate(QStyledItemDelegate):
    """
    Custom delegate for painting table cells in the results table, supporting color profiles and data types.

    Attributes:
        rType (str): Type of result ('base', 'status', 'results').
        tl_1, tl_2, tl_3 (str): Traffic light colors.
        backgroundColor (str): Background color for even rows.
        alterBackgroundColor (str): Background color for odd rows.
        gridlineColor (str): Color for grid lines.
        alignLeft, alignRight, alignCenter (Qt.AlignmentFlag): Alignment options.
        intTypes, floatTypes, catTypes, booleanTypes, stringTypes, dateTypes (list): Supported polars data types.
        i18nNes (callable): Internationalization function.
        _status, _query, _shape, _time, _resources, _error (str): Localized header strings.
        _running, _executed, _failed (str): Localized status strings.
        schema (dict): DataFrame schema.
        columnNames (list): List of column names.
        lengths (dict): Dictionary indicating columns with constant length.

    Methods:
        __init__(self, parent=None): Initializes the delegate and loads language strings.
        updatePaint(self, profileName, *args): Updates color and style settings from the profile.
        paint(self, painter, option, index, *args): Custom paint logic for table cells.
    """
    #Defining Slots
    #--------------
    #Boolean for status or other results
    rType   = 'base' #('base', 'status', 'results')
    #Trafficlight
    tl_1    = 'white'
    tl_2    = 'white'
    tl_3    = 'white'
    #Other attributes
    backgroundColor        = 'white'
    alterBackgroundColor  = 'white'
    gridlineColor          = 'black'

    #Alignment
    alignLeft      = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
    alignRight     = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
    alignCenter    = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter

    #Data types
    intTypes       = [pl.Int8, pl.Int16, pl.Int32, pl.Int64 \
                        , pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64]
    floatTypes     = [pl.Float32, pl.Float64]
    catTypes       = [pl.Categorical]
    booleanTypes   = [pl.Boolean]
    stringTypes    = [pl.Utf8, pl.String, pl.Object]
    dateTypes      = [pl.Date, pl.Datetime, pl.Time, pl.Duration]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent   = parent

        #Language
        self.i18nNes = self.parent.i18nNes
        #Headers
        self._status = self.i18nNes('execution', 'header', 'status')
        self._query = self.i18nNes('execution', 'header', 'query')
        self._shape = self.i18nNes('execution', 'header', 'shape')
        self._time = self.i18nNes('execution', 'header', 'time')
        self._resources = self.i18nNes('execution', 'header', 'resources')
        self._error = self.i18nNes('execution', 'header', 'error')
        #States
        self._running = self.i18nNes('execution', 'status', 'running')
        self._executed = self.i18nNes('execution', 'status', 'executed')
        self._failed = self.i18nNes('execution', 'status', 'failed')
        
        #Table Properties according to data
        self.schema         = {}
        self.columnNames   = []
        self.lengths        = {}

    def updatePaint(self, profileName, *args):
        self.profile = self.parent.dict_profiles[profileName]
        self.tl_1, self.tl_2, self.tl_3 = self.profile['result-trafficlight']
        self.backgroundColor = self.profile['result-background-color']
        self.alterBackgroundColor = self.profile['result-alternate-background-color']
        self.gridlineColor = self.profile['result-gridline-color']

        #Setting colors for different types of data
        self.text_color    = self.profile['result-color_text']
        self.numbers_color = self.profile['result-color_number']
        self.floats_color  = self.profile['result-color_float']
        self.boleans_color = self.profile['result-color_bolean']
        self.strings_color = self.profile['result-color_string']
        self.dates_color   = self.profile['result-color_date']
        self.cats_color    = self.profile['result-color_cat']

    def paint(self, painter, option, index, *args):
        #Early output if there are no data types
        if not index.isValid() or not self.schema:
            return
        
        # -------
        # Default
        # -------
        align = self.alignCenter
        bg_color = option.backgroundBrush
        value = index.data(Qt.ItemDataRole.DisplayRole)
        color = QColor(self.text_color)
        
        #Cell information
        _col = index.column()
        if 0 <= _col < len(self.columnNames):
            _column_name = self.columnNames[_col]
        else:
            _column_name = ''
        _type = self.schema.get(_column_name, pl.Boolean)

        #Aligning floats
        if _type in self.floatTypes:
            align = self.alignLeft
        #Aligning text according to type of data or its lengths
        elif _type in self.stringTypes and not self.lengths.get(_column_name, False):
            align = self.alignLeft
        
        # ------------------------------
        # Modifying cell characteristics
        # ------------------------------
        #1. Alternate background color
        row = index.row()
        bg_color = QBrush(QColor(self.backgroundColor)) if row % 2 == 0 else QBrush(QColor(self.alterBackgroundColor))

        #If it is status, paint the background according to state
        baseSetter = self.parent.cfg_session.index.get('baseSetter')
        if self.rType == 'status':
            #Traffic light
            if value == self._executed:
                bg_color = QBrush(QColor(self.tl_1))
            elif value == self._running:
                bg_color = QBrush(QColor(self.tl_2))
            elif value == self._failed:
                bg_color = QBrush(QColor(self.tl_3))
        elif self.rType == 'result' and not baseSetter:
            #Changing colors
            if _type in self.intTypes:
                color = QColor(self.numbers_color)
            elif _type in self.floatTypes:
                color = QColor(self.floats_color)
            elif _type in self.booleanTypes:
                color = QColor(self.boleans_color)
            elif _type in self.stringTypes:
                color = QColor(self.strings_color)
            elif _type in self.dateTypes:
                color = QColor(self.dates_color)
            elif _type in self.catTypes:
                color = QColor(self.cats_color)
        elif self.rType == 'base' or baseSetter:
            color = QColor(self.text_color)

        #Using the defined color
        option.palette.setColor(QPalette.ColorRole.Text, color)

        #2. Paint cell background
        painter.fillRect(option.rect, bg_color)
        #3. Paint cell edges
        pen = QPen(QColor(self.gridlineColor))
        painter.setPen(pen)
        painter.drawRect(option.rect)
        #4. Call base paint
        option.displayAlignment = align
        option.backgroundBrush  = bg_color
        #5. Paint Nones
        if value == str(None):
            font = option.font
            font.setBold(True)
            option.font = font
        super().paint(painter, option, index)

#This is a class that is used to create a table model from a Polars Dataframe
class PolarsModel(QAbstractTableModel):
    """
    Table model for displaying a Polars DataFrame in a QTableView.

    Attributes:
        ResultDF (pl.DataFrame): The DataFrame being displayed.
        parent (QWidget): Parent widget.
        i18nNes (callable): Internationalization function.
        _trunc (str): Truncation message.
        truncValue (int or None): Maximum cell length before truncation.

    Methods:
        __init__(self, df=pl.DataFrame(), parent=None): Initializes the model.
        rowCount(self, parent=QModelIndex(), *args): Returns the number of rows.
        columnCount(self, parent=QModelIndex(), *args): Returns the number of columns.
        data(self, index, role=Qt.ItemDataRole.DisplayRole, *args): Returns the data for a cell.
        headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole, *args): Returns the header data.
        setDataFrame(self, df, *args): Sets the DataFrame for the model.
    """
    def __init__(self, df=pl.DataFrame(), parent=None):
        super().__init__(parent)
        self.ResultDF = df
        self.parent = parent
        self.i18nNes = self.parent.i18nNes

        #Truncation
        self._trunc = self.i18nNes('tab-result', 'cell', 'truncated')
        truncate_after = self.parent.cfg_app.index.get('truncate-after')
        self.truncValue = int(truncate_after) if truncate_after is not None else None
        
    #Method to count rows
    def rowCount(self, parent=QModelIndex(), *args):
        return self.ResultDF.height

    #Method to count the columns
    def columnCount(self, parent=QModelIndex(), *args):
        return self.ResultDF.width

    #Method to define the value of each cell
    def data(self, index, role=Qt.ItemDataRole.DisplayRole, *args):
        if not index.isValid():
            return None
        #Value to paint
        value = str(self.ResultDF[index.row(), index.column()])
        #Truncating value in cell if the user has defined it
        if role == Qt.ItemDataRole.DisplayRole:
            if self.truncValue and len(value) > self.truncValue:
                return f'{value[:self.truncValue]} {self._trunc}'
            return value
        #Showing the value in case of requested a Tooltip
        if role == Qt.ItemDataRole.ToolTipRole:
            return value
        #If everything else fails
        return None

    #Method to define the header of the table
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole, *args):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self.ResultDF.columns[section])
        else:
            return str(section)

    #Method to set the DataFrame
    def setDataFrame(self, df, *args):
        self.beginResetModel()
        self.ResultDF = df.clone()
        self.endResetModel()

#========================================
### Creating class for results table
#========================================
class MyResultTable(QTableView):
    """
    Custom QTableView for displaying query results with advanced features like filtering, copying, and custom menus.

    Signals:
        columnSorted (int, Qt.SortOrder): Emitted when a column is sorted.
        columnSizeChanged (tuple): Emitted when a column size changes.
        sizeChanged (QFont): Emitted when the font size changes.

    Attributes:
        rType (str): Type of result ('base', 'status', 'result').
        app (QApplication): Application instance.
        parent (QWidget): Parent widget.
        i18nNes (callable): Internationalization function.
        df_bkp (pl.DataFrame or None): Backup DataFrame for restoring.
        _status, _error (str): Localized header strings.
        _running, _executed, _failed (str): Localized status strings.
        menuTexts (dict): Texts for context menu actions.
        filtersTexts (dict): Texts for filter actions.
        numFilterActions (list): List of number filter actions.
        textFilterActions (list): List of text filter actions.
        maxColumnWidth (int): Maximum column width.
        minColumnWidth (int): Minimum column width.
        delegate (CustomDelegate): Custom delegate for painting cells.
        profile (dict): Profile configuration.
        model (PolarsModel): Table model for the results.
        updateTableSizes (bool): Whether to update column sizes.
        headerMenu (QMenu): Context menu for column headers.
        copyColumnAction, sortAscAction, sortDescAction, restoreAction (QAction): Header menu actions.
        numFilterMenu, textFilterMenu (QMenu): Submenus for filters.
        cellMenu (QMenu): Context menu for cells.
        copyAction (QAction): Action for copying with Ctrl+C.

    Methods:
        __init__(self, parent): Initializes the results table and its menus.
        onSelectionChanged(self, selected, deselected, *args): Updates status bar on selection change.
        showCellInfo(self, row, column, *args): Shows a tooltip with cell information.
        applyColumnSizes(self, *args): Applies saved column sizes.
        updateColumnSizes(self, logicalIndex, oldSize, newSize, *args): Updates column sizes in config.
        columnsWithConstantLength(self, df: pl.DataFrame, *args) -> dict[str, bool]: Finds columns with constant length.
        resizeEvent(self, event, *args): Handles resize events.
        loadData(self, df, rType:str=None, drop_bkp=False, *args): Loads data into the table.
        mouseDoubleClickEvent(self, event, *args): Shows cell info on double click.
        wheelEvent(self, event, *args): Handles font size changes with mouse wheel.
        changeFontSize(self, delta, *args): Changes the font size.
        copySelected(self, *args): Returns selected data as a DataFrame.
        copyAsFilter(self, *args): Copies selected data as a filter string.
        controlC(self, *args): Handles Ctrl+C for copying.
        copySelectedValue(self, *args): Copies selected cell values.
        copyWholeTable(self, *args): Copies the entire table.
        restoreTable(self, *args): Restores the table from backup.
        sortByColumn(self, logical_index, order, *args): Sorts the table by a column.
        copySelectedValueH(self, *args): Copies selected values with headers.
        copyWholeColumn(self, col_index, *args): Copies an entire column.
        showNumFilterInput(self, logical_index, filter_type, *args): Shows input dialog for number filters.
        showTxtFilterInput(self, logical_index, filter_type, *args): Shows input dialog for text filters.
        filterNumColumn(self, column_name, filter_type, value, *args): Applies a number filter.
        filterTextColumn(self, column_name, filter_type, value, *args): Applies a text filter.
        copySelectedRow(self, *args): Copies the selected row.
        copySelectedRowWithHeader(self, *args): Copies the selected row with headers.
        cellMenu(self, pos, *args): Shows the cell context menu.
        headerMenuH(self, pos, *args): Shows the column header context menu.
        headerMenuV(self, pos, *args): Shows the row header context menu.
    """
    #Signs
    columnSorted = pyqtSignal(int, Qt.SortOrder)
    columnSizeChanged = pyqtSignal(tuple)
    sizeChanged  = pyqtSignal(QFont)
    
    def __init__(self, parent):
        super().__init__()
        #Slots
        self.rType = 'base'

        self.app = QApplication.instance()
        self.parent = parent
        self.i18nNes = self.parent.i18nNes
        self.df_bkp = None

        #Headers
        self._status = self.i18nNes('execution', 'header', 'status')
        self._error = self.i18nNes('execution', 'header', 'error')
        #States
        self._running = self.i18nNes('execution', 'status', 'running')
        self._executed = self.i18nNes('execution', 'status', 'executed')
        self._failed = self.i18nNes('execution', 'status', 'failed')
        
        #Menus
        self.menuTexts = {
            'copy_column': self.i18nNes('tab-result', 'headerMenuH', 'copy-column'),
            'sort_asc': self.i18nNes('tab-result', 'headerMenuH', 'sort-asc'),
            'sort_des': self.i18nNes('tab-result', 'headerMenuH', 'sort-des'),
            'restore': self.i18nNes('tab-result', 'headerMenuH', 'restore'),
            'numbers_filter': self.i18nNes('tab-result', 'headerMenuH', 'numbers-filter'),
            'texts_filter': self.i18nNes('tab-result', 'headerMenuH', 'texts-filter'),
        }

        #Setting msgs of filters
        self.filtersTexts = {
            #Numerical filters
            'num_equal': self.i18nNes('tab-result', 'filter-value-num', 'num-equal'),
            'num_not_equal': self.i18nNes('tab-result', 'filter-value-num', 'num-not-equal'),
            'greater': self.i18nNes('tab-result', 'filter-value-num', 'greater'),
            'greater_equal': self.i18nNes('tab-result', 'filter-value-num', 'greater-equal'),
            'lesser': self.i18nNes('tab-result', 'filter-value-num', 'lesser'),
            'lesser_equal': self.i18nNes('tab-result', 'filter-value-num', 'lesser-equal'),
            #Text filters
            'txt_equal': self.i18nNes('tab-result', 'filter-value-text', 'txt-equal'),
            'txt_not_equal': self.i18nNes('tab-result', 'filter-value-text', 'txt-not-equal'),
            'start_with': self.i18nNes('tab-result', 'filter-value-text', 'start-with'),
            'end_with': self.i18nNes('tab-result', 'filter-value-text', 'end-with'),
            'contains': self.i18nNes('tab-result', 'filter-value-text', 'contains'),
            'not_contains': self.i18nNes('tab-result', 'filter-value-text', 'not-contains')
        }

        #Defining number filter actions
        self.numFilterActions = [
            (self.filtersTexts.get('num_equal'), 'num_equal'),
            (self.filtersTexts.get('num_not_equal'), 'num_not_equal'),
            (None, None),  #Separator
            (self.filtersTexts.get('greater'), 'greater'),
            (self.filtersTexts.get('greater_equal'), 'greater_equal'),
            (self.filtersTexts.get('lesser'), 'lesser'),
            (self.filtersTexts.get('lesser_equal'), 'lesser_equal'),
            (self.filtersTexts.get('between'), 'between'),
            (None, None),  #Separator
            (self.filtersTexts.get('top_10'), 'top_10'),
            (self.filtersTexts.get('above_avg'), 'above_avg'),
            (self.filtersTexts.get('below_avg'), 'below_avg'),
        ]

        #Defining text filter actions
        self.textFilterActions = [
            (self.filtersTexts.get('txt_equal'), 'txt_equal'),
            (self.filtersTexts.get('txt_not_equal'), 'txt_not_equal'),
            (None, None),  #Separator
            (self.filtersTexts.get('start_with'), 'start_with'),
            (self.filtersTexts.get('end_with'), 'end_with'),
            (None, None),  #Separator
            (self.filtersTexts.get('contains'), 'contains'),
            (self.filtersTexts.get('not_contains'), 'not_contains'),
        ]

        #Defining internal profile
        profileName = self.parent.cfg_session.index.get('internal_profile')
        _max = self.parent.cfg_app.index.get('max-width-result-column')
        _max = str(_max).replace('px','')
        _max = int(_max) if _max.isdigit() else 70
        self.maxColumnWidth = _max

        _min = self.parent.cfg_app.index.get('min-width-result-column')
        _min = str(_min).replace('px','')
        _min = int(_min) if _min.isdigit() else 70
        self.minColumnWidth = _min

        #Defining style delegator
        self.delegate = CustomDelegate(self.parent)
        self.profile = self.parent.dict_profiles[profileName]
        _, _, self.tl_3, = self.profile['result-trafficlight']
        self.delegate.updatePaint(profileName)
        self.setItemDelegate(self.delegate)
        
        #Setting the model
        self.model = PolarsModel(pl.DataFrame(), self.parent)
        self.setModel(self.model)
        #Enabling mouse tracking
        self.setMouseTracking(True)
        #Column properties
        self.horizontalHeader().setDefaultSectionSize(150)
        self.horizontalHeader().setSectionsClickable(True)
        self.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.headerMenuH)
        self.horizontalHeader().sectionResized.connect(self.updateColumnSizes)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        #Row Properties
        self.verticalHeader().setSectionsClickable(True)
        self.verticalHeader().setDefaultSectionSize(30)
        self.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.verticalHeader().customContextMenuRequested.connect(self.headerMenuV)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        
        #Disabling table editability
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sort_order = Qt.SortOrder.AscendingOrder
        #Configuring contextual menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.cellMenu)
        
        #Conectando Ctrl+C a copyAction
        self.copyAction = QAction(self)
        self.copyAction.setShortcut('Ctrl+C')
        self.copyAction.triggered.connect(self.controlC)
        self.addAction(self.copyAction)

        #Connect selection signal
        self.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        #Attribute to determine whether or not to update sizes headers
        self.updateTableSizes = False

        #Creating transverse Menus and actions to the entire results table
        #-------------------------------------------------------
        #Principal menus
        self.headerMenu = QMenu(self)

        #Creating actions for the header menu
        self.copyColumnAction = QAction(self.menuTexts['copy_column'], self)
        self.sortAscAction = QAction(self.menuTexts['sort_asc'], self)
        self.sortDescAction = QAction(self.menuTexts['sort_des'], self)
        self.restoreAction = QAction(self.menuTexts['restore'], self)
        self.numFilterMenu = QMenu(self.menuTexts['numbers_filter'], self)
        self.textFilterMenu = QMenu(self.menuTexts['texts_filter'], self)
       
        #Creatting the cell menu
        #--------------------------------------
        #Names of the menu options
        _copy_value = self.i18nNes('tab-result', 'cell-menu', 'copy-value')
        _copy_value_header = self.i18nNes('tab-result', 'cell-menu', 'copy-value-header')
        _copy_vale_filter = self.i18nNes('tab-result', 'cell-menu', 'copy-vale-filter')
        _copy_table = self.i18nNes('tab-result', 'cell-menu', 'copy-table')
        
        #Creating the context menu
        self.cellMenu = QMenu(self)
        #Action to copy cell value
        copyValueAction = QAction(_copy_value, self)
        copyValueAction.triggered.connect(self.copySelectedValue)
        self.cellMenu.addAction(copyValueAction)
        #Action to copy cell value
        copyValueActionH = QAction(_copy_value_header, self)
        copyValueActionH.triggered.connect(self.copySelectedValueH)
        self.cellMenu.addAction(copyValueActionH)
        #Action to copy as filter
        copyAsFilter = QAction(_copy_vale_filter, self)
        copyAsFilter.triggered.connect(self.copyAsFilter)
        self.cellMenu.addAction(copyAsFilter)
        self.cellMenu.addSeparator()
        #Action to copy the entire table
        copyTableAction = QAction(_copy_table, self)
        copyTableAction.triggered.connect(self.copyWholeTable)
        self.cellMenu.addAction(copyTableAction)
        self.cellMenu.addSeparator()

    #Function to show in status bar information of the selection
    def onSelectionChanged(self, selected, deselected, *args):
        #Current total of selected
        count = len(self.selectionModel().selectedIndexes())
        if count<=1:
            _rows, _cols = self.i18nNes('status-bar', 'rows-cols')
            rows, cols = self.model.ResultDF.shape
            rows = f'>{rows:,}' if self.parent.current_fetched else f'{rows:,}'
            rowsCols = f'{_rows}: {rows}, {_cols}: {cols:,}'
            self.parent.bt_rowsCols.setText(rowsCols)
        else:
            _cells = self.i18nNes('status-bar', 'cells')
            self.parent.bt_rowsCols.setText(f'{_cells}: {count:,}')
    
    #Function to show a window with the cell information
    def showCellInfo(self, row, column, *args):
        if not self.isVisible():
            return
        #Getting cell text
        index = self.model.index(row, column)
        cell_text = str(self.model.ResultDF[index.row(), index.column()])
        #Obtaining global position
        cell_rect = self.visualRect(index)
        #Getting the global position of the top left corner of the cell
        global_pos = self.mapToGlobal(cell_rect.bottomLeft())
        #Showing tooltip with information
        self.tooltip = MyTooltip(self)
        self.tooltip.setStyleSheet( self.parent.dict_styledSheets['MyTooltip'] )
        self.tooltip.setParent(self.parent.tabWidget)
        self.tooltip.setText(cell_text)
        self.tooltip.myShow(cell_rect)
        self.tooltip.textContent.setFocus()
    
    #Function to apply custom size to columns
    def applyColumnSizes(self, *args):
        frame = self.parent.cfg_session.index.get('status_frame')
        #Taking the size only of the active columns
        sizes = [val[1] for key, val in frame.items() if val[0] is True]
        header = self.horizontalHeader()
        for i in range(header.count()):
            header.resizeSection(i, sizes[i])
    
    #Modifying the parameters assigned by the user
    def updateColumnSizes(self, logicalIndex, oldSize, newSize, *args):
        if self.updateTableSizes and self.rType == 'status':
            #Editing the size only of the active columns
            frame = self.parent.cfg_session.index.get('status_frame')
            #Taking the current columns sizes
            header = self.horizontalHeader()
            current_sizes = []
            for i in range(header.count()):
                current_sizes.append(header.sectionSize(i))
            #Keeping the sizes where appropriate
            count = 0
            for key, val in frame.items():
                if val[0] is True:
                    frame[key][1] = current_sizes[count]
                    count += 1
            #Saving the new frame dictionary
            self.parent.cfg_session.index['status_frame'] = frame
        elif self.updateTableSizes and self.rType != 'status':
            _tuple = (logicalIndex, newSize)
            self.columnSizeChanged.emit(_tuple)

    #Function that returns a dictionary with the columns that have constant length
    def columnsWithConstantLength(self, df: pl.DataFrame, *args) -> dict[str, bool]:
        result = {}
        schema = df.schema
        self.delegate.columnNames = df.columns
        
        #Iterating through the columns to check their types
        for col in schema:
            if schema[col] in self.delegate.stringTypes:
                #Calculate the lengths of all column strings
                lengths = df.select(pl.col(col).cast(pl.String).str.len_chars()).to_series()
                #Verify if all values ​​have the same length (without going through pure python)
                valores_unicos = lengths.unique()
                result[col] = valores_unicos.len() == 1
        return result
    
    #Function to identify table redimension event
    def resizeEvent(self, event, *args):
        super().resizeEvent(event)
    
    #Function to load data from pl.DataFrame
    def loadData(self, df, rType:str=None, drop_bkp=False, *args):
        #Indicating to delegate the data type
        if not rType:
            rType = self.rType
        self.rType = rType
        self.updateTableSizes = False

        #Differentiating between status and results
        if rType == 'status':
            #Modifying DF according to what the user wants to visualize
            frame = self.parent.cfg_session.index.get('status_frame')
            #Taking translated values
            headers = self.i18nNes('execution', 'header')
            columns = []
            new_names = []
            for key, val in frame.items():
                if val[0] is True:
                    columns.append(key)
                    new_names.append(headers[key])
            #Setting the model with the DataFrame
            df = df.select(columns)
            df = df.rename(dict(zip(df.columns, new_names)))
            self.model.setDataFrame(df)
            #Modifying sizes
            self.applyColumnSizes()
            #Checking the msg of the last error and show message
            mask = pl.col(self._status) == self._failed
            matches = df.filter(mask)
            if matches.height > 0:
                df_with_idx = df.with_row_index(name='__idx', offset=0)
                last_idx = df_with_idx.filter(mask).select(pl.col('__idx')).to_series().to_list()[-1]
                col = df.columns.index(self._error)
                self.showCellInfo(last_idx, col)
        elif rType in ('result', 'base'):
            #Setting the model with the DataFrame
            self.model.setDataFrame(df)
            self.resizeColumnsToContents()
            #Adjust eachrow and column to the max value. Only once
            fontMetrics = self.fontMetrics()
            #If they are more than 10 columns, it is applied a fixed, if not, it fits the content           
            _columnCount = self.model.columnCount()
            for col in range(_columnCount):
                header_text = self.model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
                if header_text is None:
                    header_text = ''
                text_width = fontMetrics.horizontalAdvance(str(header_text))
                if _columnCount < 10:
                    _width = min(self.maxColumnWidth, self.columnWidth(col))
                else:
                    _prewidth = max(text_width+20, self.minColumnWidth)
                    _width = min(_prewidth, self.columnWidth(col))

                self.setColumnWidth(col, _width)

        #identifying columns with constant width
        self.delegate.rType = rType
        self.delegate.schema = df.schema
        self.delegate.lengths = self.columnsWithConstantLength(df)
        #Allowing the update of columan size values
        self.updateTableSizes = True

        #Dropping the backup if requested
        if drop_bkp:
            self.df_bkp = None
        
    #Function to detect double clicking on a cell
    def mouseDoubleClickEvent(self, event, *args):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.showCellInfo(index.row(), index.column())
    
    #Defining event for how much the mouse scroll is touched     
    def wheelEvent(self, event, *args):
        #Check if the Control key is pressed when scrolling with the mouse
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.changeFontSize(1)
            else:
                self.changeFontSize(-1)
        else:
            super().wheelEvent(event)
        
    #Creating a function that will change the font size
    def changeFontSize(self, delta, *args):
        #Getting current font size
        current_font = self.font()
        font_size = current_font.pointSizeF()
        #Adjust font size
        font_size += delta
        #Set the new font with the modified size
        new_font = QFont(current_font)
        new_font.setPointSizeF(font_size)
        self.setFont(new_font)
        #Saving the new size in the config file
        self.parent.cfg_session.index.get('prede_font')['result-size'] = int(font_size)
        self.sizeChanged.emit(new_font)
    
    #-------------------------------------------
    #Functions associated with the Cell Menu
    #-------------------------------------------
    #Function to copy selected cells
    #This function is input for others later
    def copySelected(self, *args):
        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return None

        # Obtener filas y columnas seleccionadas
        rows = sorted(set(index.row() for index in selection))
        cols = sorted(set(index.column() for index in selection))
        #Obtain real column names
        col_names = [self.model.ResultDF.columns[col] for col in cols]
        #Extract data directly from DataFrame
        data = self.model.ResultDF[rows, cols]
        return data
    
    #Function to copy as filter
    def copyAsFilter(self, *args):
        data = self.copySelected()
        text = ''
        if data is not None and data.height > 0:
            for key in data.columns:
                values = data[key].to_list()
                if len(values) == 1:
                    value = values[0]
                    if isinstance(value, str):
                        text += f"{key} = '{value}'\nAND "
                    else:
                        text += f'{key} = {value}\nAND '
                else:
                    formatted_values = []
                    all_numeric = all(isinstance(value, (int, float)) for value in values)
                    for value in values:
                        if all_numeric:
                            formatted_values.append(str(value))
                        else:
                            formatted_values.append(f"'{value}'")
                    values_str = ', '.join(formatted_values)
                    text += f'{key} IN ({values_str})\nAND '
            text = text.rstrip('AND \n')
            self.app.clipboard().setText(text)
            
    #Function to identify what to copy
    def controlC(self, *args):
        selection = self.selectionModel()
        #Getting the total number of rows and columns
        num_rows = self.model.rowCount()
        num_columns = self.model.columnCount()
        
        #Checking if the table has only one row and column
        if num_rows == num_columns == 1:
            self.copySelectedValue()
            return

        #Checking if any column is completely selected
        columns_selected = set()
        for index in selection.selectedColumns():
            columns_selected.add(index.column())
        
        #Checking if any row is completely selected
        rows_selected = set()
        for index in selection.selectedRows():
            rows_selected.add(index.row())
        
        #Checking if the entire table is selected
        if len(columns_selected) == num_columns and len(rows_selected) == num_rows:
            self.copyWholeTable()
            return 
        #Checking if any row or column is completely selected
        elif columns_selected or rows_selected:
            self.copySelectedValueH()
            return
        else:
            self.copySelectedValue()
            return
 
    #Function to copy all selected cells
    def copySelectedValue(self, *args):
        data = self.copySelected()
        if data is not None and data.height > 0:
            #Converts to tabular text (without heading)
            rows = []
            for i in range(data.height):
                row = [str(data[i, j]) for j in range(data.width)]
                rows.append('\t'.join(row))
            text = '\n'.join(rows)
            self.app.clipboard().setText(text)

    #Function to copy the entire table
    def copyWholeTable(self, *args):
        df = self.model.ResultDF
        if df is not None and df.height > 0:
            #Headers
            header = '\t'.join(df.columns)
            #Rows
            rows = []
            for i in range(df.height):
                row = [str(df[i, j]) for j in range(df.width)]
                rows.append('\t'.join(row))
            text = header + '\n' + '\n'.join(rows)
            clipboard = self.app.clipboard()
            clipboard.setText(text)

    #-------------------------------------------
    #Functions associated with the Column Menu
    #-------------------------------------------
    #Function to restore original after applying filters
    def restoreTable(self, *args):
        if self.df_bkp is not None:
            self.loadData(self.df_bkp, drop_bkp=True)
      
    #Sorting table according to column
    def sortByColumn(self, logical_index, order, *args):
        #Getting the name of the column to order
        column_name = self.model.ResultDF.columns[logical_index]
        #Ordering the dataframe with polars
        ascending = (order == Qt.SortOrder.AscendingOrder)
        sorted_df = self.model.ResultDF.sort(column_name, descending=not ascending)
        #Updating the table with the ordered dataframe
        self.loadData(sorted_df)
        #Changing order for next time
        self.sort_order = Qt.SortOrder.DescendingOrder if order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        #Emitting signal
        self.columnSorted.emit(logical_index, order)
    
    #Function to copy all selected cells with header
    def copySelectedValueH(self, *args):
        data = self.copySelected()
        if data is not None and data.height > 0:
            #Selected columns headers
            header = '\t'.join(data.columns)
            #Selected ranks
            rows = []
            for i in range(data.height):
                row = [str(data[i, j]) for j in range(data.width)]
                rows.append('\t'.join(row))
            text = header + '\n' + '\n'.join(rows)
            self.app.clipboard().setText(text)
    
    #Function to copy the entire column
    def copyWholeColumn(self, col_index, *args):
        #Verifing that the index is valid
        if self.model.ResultDF is not None and 0 <= col_index < self.model.ResultDF.width:
            #Getting the name of the column
            col_name = self.model.ResultDF.columns[col_index]
            #Getting the column data as a strings list
            col_data = [str(val) for val in self.model.ResultDF[col_name].to_list()]
            #Preparing the text with header
            text = f'{col_name}\n' + '\n'.join(col_data)
            #Coping to the clipboard
            clipboard = self.app.clipboard()
            clipboard.setText(text)
    
    #Function to show filter input dialog
    def showNumFilterInput(self, logical_index, filter_type, *args):       
        column_name = self.model.ResultDF.columns[logical_index]
        #Getting text of filters
        _filter_title = self.i18nNes('tab-result', 'filter-value-num', 'title')
        _title_between = self.i18nNes('tab-result', 'between', 'title')
        _min = self.i18nNes('tab-result', 'between', 'min')
        _max = self.i18nNes('tab-result', 'between', 'max')
        #Filters that do not require user input
        if filter_type in ['top_10', 'above_avg', 'below_avg']:
            self.filterNumColumn(column_name, filter_type, None)
            return
        #Filters that require a range of values
        if filter_type == 'between':
            min_value, ok_min = QInputDialog.getDouble(self, _title_between, f'{_min}:')
            if not ok_min:
                return
            max_value, ok_max = QInputDialog.getDouble(self, _title_between, f'{_max}:')
            if not ok_max:
                return
            self.filterNumColumn(column_name, filter_type, (min_value, max_value))
            return
        #If ok, filtering the column
        _msg = self.filtersTexts.get(filter_type)
        value, ok = QInputDialog.getText(self, _filter_title, f'{_msg}:')
        if ok:
            #Filtering the DataFrame based on the value input
            self.filterNumColumn(column_name, filter_type, value)

    #Function to apply specific text filter
    def showTxtFilterInput(self, logical_index, filter_type, *args):
        #Getting text of filters
        _filter_title = self.i18nNes('tab-result', 'filter-value-text', 'title')
        _msg = self.filtersTexts.get(filter_type)
        #Getting the name of the column to filter
        column_name = self.model.ResultDF.columns[logical_index]
        value, ok = QInputDialog.getText(self, _filter_title, f'{_msg}:')
        if ok:
            #Filtering the DataFrame based on the text input
            self.filterTextColumn(column_name, filter_type, value)
      
    #Function to apply number filters
    def filterNumColumn(self, column_name, filter_type, value, *args):
        #Creating a backup of the original DataFrame
        if self.df_bkp is None:
            self.df_bkp = self.model.ResultDF.clone()
    
        #Taking the column series
        df = self.model.ResultDF
        series = df[column_name].cast(pl.Float32)
        value = float(value)
        
        if filter_type == 'between' and isinstance(value, tuple):
            min_value, max_value = value
            mask = (series >= min_value) & (series <= max_value)
        elif filter_type == 'num_equal':
            mask = series == value
        elif filter_type == 'num_not_equal':
            mask = series != value
        elif filter_type == 'greater':
            mask = series > value
        elif filter_type == 'greater_equal':
            mask = series >= value
        elif filter_type == 'lesser':
            mask = series < value
        elif filter_type == 'lesser_equal':
            mask = series <= value
        elif filter_type == 'above_avg':
            mean_value = series.mean()
            mask = series > mean_value
        elif filter_type == 'below_avg':
            mean_value = series.mean()
            mask = series < mean_value
        elif filter_type == 'top_10':
            filtered_df = df.sort(column_name, descending=True).head(10)
            self.loadData(filtered_df)
            return
        else:
            return
        
        #Filter the dataframe using the mask
        filtered_df = df.filter(mask)
        #Showing the filtering data
        self.loadData(filtered_df)
        
    #Function to apply text filters
    def filterTextColumn(self, column_name, filter_type, value, *args):
        #Creating a backup of the original DataFrame
        if self.df_bkp is None:
            self.df_bkp = self.model.ResultDF.clone()

        #Turnnig everything to string and lowercase for capital comparison to capital letters
        df = self.model.ResultDF
        series = df[column_name].cast(pl.String).str.to_lowercase()
        value = value.lower()
        #Creating a mask based on the filter type
        if filter_type == 'txt_equal':
            mask = series == value
        elif filter_type == 'txt_not_equal':
            mask = series != value
        elif filter_type == 'start_with':
            mask = series.str.starts_with(value)
        elif filter_type == 'end_with':
            mask = series.str.ends_with(value)
        elif filter_type == 'contains':
            mask = series.str.contains(value)
        elif filter_type == 'not_contains':
            mask = ~series.str.contains(value)
        else:
            return

        #Filter the dataframe using the mask
        filtered_df = df.filter(mask)
        #Showing the filtering data
        self.loadData(filtered_df)
        return

    #-------------------------------------------
    #Functions associated with the Row Menu
    #-------------------------------------------
    #Function to copy the entire row
    def copySelectedRow(self, *args):
        #Getting the selected row index
        selection = self.selectionModel().currentIndex()
        if selection.isValid():
            row_idx = selection.row()
            #Getting the data from the row directly from the dataframe
            row_data = [str(self.model.ResultDF[row_idx, col]) for col in range(self.model.ResultDF.width)]
            #Coping to the clipboard, separated by tabulators
            self.app.clipboard().setText('\t'.join(row_data))

    #Function to copy the entire row with header
    def copySelectedRowWithHeader(self, *args):
        #Getting the selected row index
        selection = self.selectionModel().currentIndex()
        if selection.isValid():
            row_idx = selection.row()
            #Getting headers and row data from Dataframe
            header_data = list(self.model.ResultDF.columns)
            row_data = [str(self.model.ResultDF[row_idx, col]) for col in range(self.model.ResultDF.width)]
            #Coping to the clipboard, separated by tabulators
            data_with_header = '\t'.join(header_data) + '\n' + '\t'.join(row_data)
            self.app.clipboard().setText(data_with_header)

    #-------------------------------------------
    #Functions to create Menus
    #-------------------------------------------
    #Menu for cells
    #--------------
    #Showing contextual menu
    def cellMenu(self, pos, *args):
        #Show menu at right click position
        self.cellMenu.exec(self.mapToGlobal(pos))

    #Column menu
    #------------------
    def headerMenuH(self, pos, *args):        
        #Start of the function code
        #--------------------------
        logical_index = self.horizontalHeader().logicalIndexAt(pos)
        self.selectColumn(logical_index)

        #Getting the name and type of the selected column
        column_name = self.model.ResultDF.columns[logical_index]
        _type = self.model.ResultDF.schema[column_name]

        #Cleannig and clearing the menus
        self.headerMenu.clear()
        self.numFilterMenu.clear()
        self.textFilterMenu.clear()

        # Desconectar acciones previas para evitar múltiples conexiones
        try:
            self.copyColumnAction.triggered.disconnect()
            self.sortAscAction.triggered.disconnect()
            self.sortDescAction.triggered.disconnect()
            self.restoreAction.triggered.disconnect()
        except TypeError:
            pass

        # Conectar acciones con el logical_index actual
        self.copyColumnAction.triggered.connect(partial(self.copyWholeColumn, logical_index))
        self.sortAscAction.triggered.connect(partial(self.sortByColumn, logical_index, Qt.SortOrder.AscendingOrder))
        self.sortDescAction.triggered.connect(partial(self.sortByColumn, logical_index, Qt.SortOrder.DescendingOrder))
        self.restoreAction.triggered.connect(self.restoreTable)
        
        #Adding general actions to the main menu
        self.headerMenu.addAction(self.copyColumnAction)
        self.headerMenu.addSeparator()
        self.headerMenu.addAction(self.sortAscAction)
        self.headerMenu.addAction(self.sortDescAction)
        self.headerMenu.addSeparator()
        self.headerMenu.addAction(self.restoreAction)

        #Showing the menu for the header
        if self.df_bkp is None:
            self.restoreAction.setVisible(False)
        else:
            self.restoreAction.setVisible(True)

        #Filling the appropriate submenu and add it
        if _type in (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64):
            for text, filter_type in self.numFilterActions:
                if text is None:
                    self.numFilterMenu.addSeparator()
                else:
                    action = QAction(text, self)
                    action.triggered.connect(partial(self.showNumFilterInput, logical_index, filter_type))
                    self.numFilterMenu.addAction(action)
            self.headerMenu.addMenu(self.numFilterMenu)
        elif _type == pl.Utf8:
            for text, filter_type in self.textFilterActions:
                if text is None:
                    self.textFilterMenu.addSeparator()
                else:
                    action = QAction(text, self)
                    action.triggered.connect(partial(self.showTxtFilterInput, logical_index, filter_type))
                    self.textFilterMenu.addAction(action)
            self.headerMenu.addMenu(self.textFilterMenu)

        #Showing the text filter menu
        global_pos = self.mapToGlobal(pos)
        self.headerMenu.exec(global_pos)
    
    #Menu for rows
    #-------------
    def headerMenuV(self, pos, *args):
        #Names of the menu options
        _copy_row = self.i18nNes('tab-result', 'headerMenuV', 'copy-row')
        _copy_row_header = self.i18nNes('tab-result', 'headerMenuV', 'copy-row-header')

        #Start of the function code
        logical_index = self.verticalHeader().logicalIndexAt(pos)
        self.selectRow(logical_index)
        menu = QMenu(self)

        #Action to copy current row
        copyRowAction = QAction(_copy_row, self)
        copyRowAction.triggered.connect(self.copySelectedRow)
        menu.addAction(copyRowAction)
        
        #Action to copy row with header
        copyRowWHAction = QAction(_copy_row_header, self)
        copyRowWHAction.triggered.connect(self.copySelectedRowWithHeader)
        menu.addAction(copyRowWHAction)
        menu.addSeparator()

        global_pos = self.mapToGlobal(pos)
        menu.exec(global_pos)

