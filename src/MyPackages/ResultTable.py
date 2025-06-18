import polars as pl
from functools import partial
from PyQt6.QtWidgets import QApplication, QTableView \
    , QMenu, QHeaderView, QInputDialog, QAbstractItemView \
    , QStyledItemDelegate
from PyQt6.QtGui import QAction, QFont, QColor, QBrush, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QAbstractTableModel \
    , QModelIndex
from MyPackages.MyTooltip import MyTooltip

#========================================
### Creating class to draw results table
#========================================
class CustomDelegate(QStyledItemDelegate):
    #Defining Slots
    #--------------
    #Boolean for status or other results
    status = False
    #Trafficlight
    tl_1 = "white"
    tl_2 = "white"
    tl_3 = "white"
    #Other attributes
    background_color = "white"
    alter_background_color = "white"
    gridline_color = "black"

    def __init__(self, parent=None):
        self.cfg_app = parent.cfg_app

        #Language
        nested = parent.i18n.getNested
        #States
        self._running = nested("execution", "status", "running")
        self._executed = nested("execution", "status", "executed")
        self._failed = nested("execution", "status", "failed")
        #Others
        self._trunc = nested('tab-result', 'cell', 'truncated')
        super().__init__(parent)

    def updatePaint(self, theme_name):
        self.theme = self.cfg_app.index.get("list_thems")[theme_name]
        self.tl_1, self.tl_2, self.tl_3 = self.theme["result-trafficlight"]
        self.background_color = self.theme["result-background-color"]
        self.alter_background_color = self.theme["result-alternate-background-color"]
        self.gridline_color = self.theme["result-gridline-color"]

        #Setting colors for different types of data
        self.text_color    = self.theme["result-color_text"]
        self.numbers_color = self.theme["result-color_number"]
        self.floats_color  = self.theme["result-color_float"]
        self.boleans_color = self.theme["result-color_bolean"]
        self.strings_color = self.theme["result-color_string"]
        self.dates_color   = self.theme["result-color_date"]
        self.ids_color     = self.theme["result-color_id"]

    def paint(self, painter, option, index):
        #Getting cell value
        value = index.data()
        #Alternating color according to parameters
        if index.row() % 2 == 0:
            option.backgroundBrush = QBrush(QColor(self.background_color))
        else:
            option.backgroundBrush = QBrush(QColor(self.alter_background_color))

        #Modifying background color based on cell value
        if self.status:
            if value == self._executed:
                option.backgroundBrush = QBrush(QColor(self.tl_1))
            elif value == self._running:
                option.backgroundBrush = QBrush(QColor(self.tl_2))
            elif value == self._failed:
                option.backgroundBrush = QBrush(QColor(self.tl_3))

        #Painting the bottom of the cell
        painter.fillRect(option.rect, option.backgroundBrush)

        #Painting the border of the cell
        pen = QPen(QColor(self.gridline_color))
        painter.setPen(pen)
        painter.drawRect(option.rect)

        #Painting the content
        # --- NUEVO: Pintar el texto y el truncado con color especial ---
        _lenT = len(self._trunc)
        if isinstance(value, str) and value.endswith(self._trunc):
            # Pintar la parte normal
            main_text = value[:-_lenT]
            trunc_text = value[-_lenT:]
            # Calcula el ancho del texto principal
            font_metrics = painter.fontMetrics()
            main_width = font_metrics.horizontalAdvance(main_text)
            # Posición inicial
            x = option.rect.x() + 2
            y = option.rect.y() + (option.rect.height() + font_metrics.ascent() - font_metrics.descent()) // 2

            # Pintar texto principal (color normal)
            painter.setPen(QColor(index.data(Qt.ItemDataRole.ForegroundRole)))
            painter.drawText(x, y, main_text)
            # Pintar truncado (color especial)
            painter.setPen(QColor(self.text_color))
            painter.drawText(x + main_width, y, trunc_text)
        else:
            # Pintar normalmente
            super().paint(painter, option, index)

#This is a class that is used to create a table model from a Polars Dataframe
class PolarsModel(QAbstractTableModel):
    def __init__(self, df=pl.DataFrame(), parent=None):
        super().__init__(parent)
        self.ResultDF = df
        self.i18n = parent.i18n
        self.cfg_user = parent.cfg_user
        self.app = QApplication.instance()

    #Method to count rows
    def rowCount(self, parent=QModelIndex()):
        return self.ResultDF.height

    #Method to count the columns
    def columnCount(self, parent=QModelIndex()):
        return self.ResultDF.width

    #Method to define the value of each cell
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        #PENDING - This is not here. No working
        # #Changing mouse pointer to standby state
        # self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        #Getting the column name, data type and value of the cell
        column_name = self.ResultDF.columns[index.column()]
        dtype = self.ResultDF.schema[column_name]
        value = self.ResultDF[index.row(), index.column()]
        delegate = self.parent().delegate

        #Lenguage and truncation
        nested = self.i18n.getNested
        _trunc = nested('tab-result', 'cell', 'truncated')
        trunc_value = int(self.cfg_user.index.get('truncate-after', 24))

        #Formatting the text alignment
        _left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        _center = Qt.AlignmentFlag.AlignCenter
        
        #Filling the value of the cell (format and truncate)
        if not delegate.status:
            if role == Qt.ItemDataRole.DisplayRole:
                #Truncating floats if they are too long
                if dtype in (pl.Float32, pl.Float64):
                    try:
                        float_val = float(value)
                        float_str_full = str(float_val)
                        if len(float_str_full) > trunc_value:
                            float_str = f"{float_val:.3f}{_trunc}"
                            return float_str
                        else:
                            return float_str_full
                    except Exception:
                        return str(value)
                #Truncating strings if they are too long
                elif isinstance(value, str):
                    if len(value) > trunc_value:
                        return value[:trunc_value] + f"{_trunc}"
                    return value
                #Truncating integers if they are too long
                else:
                    str_val = str(value)
                    if len(str_val) > trunc_value:
                        return str_val[:trunc_value] + f"{_trunc}"
                    return str_val
            
            #PENDING - This is not here. No working
            # #Changing mouse pointer to default state
            # self.app.restoreOverrideCursor()

            #Data type format-TextAlignmentRole
            if role == Qt.ItemDataRole.TextAlignmentRole:
                #Floats at the center
                if dtype in (pl.Float32, pl.Float64):
                    return _left
                #Texts at the left or center
                elif dtype in (pl.Utf8, pl.String):
                    col_values = self.ResultDF[column_name].to_list()
                    lengths = [len(str(v)) for v in col_values]
                    if len(set(lengths)) == 1:
                        return _center
                    else:
                        return _left
                #By default, all other types are aligned to the center
                else:
                    return _center
            
            #Changing the color of the text according to the type of column
            if role == Qt.ItemDataRole.ForegroundRole:
                if dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64):
                    return QBrush(QColor(delegate.numbers_color))
                elif dtype in (pl.Float32, pl.Float64):
                    return QBrush(QColor(delegate.floats_color))
                elif dtype == pl.Boolean:
                    return QBrush(QColor(delegate.boleans_color))
                elif dtype == pl.Utf8:
                    return QBrush(QColor(delegate.strings_color))
                elif dtype in (pl.Date, pl.Datetime, pl.Time):
                    return QBrush(QColor(delegate.dates_color))
                elif dtype in (pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64):
                    return QBrush(QColor(delegate.ids_color))
        
            #Determining the background color according to type of Table
            if role == Qt.ItemDataRole.BackgroundRole:
                if index.row() % 2 == 0:
                    return QBrush(QColor(delegate.background_color))
                else:
                    return QBrush(QColor(delegate.alter_background_color))
                
            # ToolTip estándar si la celda está truncada
            if role == Qt.ItemDataRole.ToolTipRole:
                column_name = self.ResultDF.columns[index.column()]
                dtype = self.ResultDF.schema[column_name]
                value = self.ResultDF[index.row(), index.column()]
                nested = self.i18n.getNested
                _trunc = nested('tab-result', 'cell', 'truncated')
                trunc_value = int(self.cfg_user.index.get('truncate-after', 24))

                # Si es float y está truncado
                if dtype in (pl.Float32, pl.Float64):
                    float_str_full = str(value)
                    if len(float_str_full) > trunc_value:
                        return float_str_full
                # Si es string y está truncado
                elif isinstance(value, str) and len(value) > trunc_value:
                    return value
                # Si es otro tipo y está truncado
                else:
                    str_val = str(value)
                    if len(str_val) > trunc_value:
                        return str_val
                return None
        
        elif delegate.status:
            #Show the value as in Displayrole
            if role == Qt.ItemDataRole.DisplayRole:
                return str(value)
            
            #Formatting TextAlignmentRole
            if role == Qt.ItemDataRole.TextAlignmentRole:
                if isinstance(value, str) and len(value) > trunc_value:
                    return _left
                return _center
            
            #Determining the background color according to type of Table
            if role == Qt.ItemDataRole.BackgroundRole:
                if value == self.parent()._executed:
                    return QBrush(QColor(delegate.tl_1))
                elif value == self.parent()._running:
                    return QBrush(QColor(delegate.tl_2))
                elif value == self.parent()._failed:
                    return QBrush(QColor(delegate.tl_3))     
        return None

    #Method to define the header of the table
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self.ResultDF.columns[section])
        else:
            return str(section)

    #Method to set the DataFrame
    def setDataFrame(self, df):
        self.beginResetModel()
        self.ResultDF = df.clone()
        self.endResetModel()

class ResultTable(QTableView):
    #Signs
    dfChanged = pyqtSignal(pl.DataFrame)
    columnSorted = pyqtSignal(int, Qt.SortOrder)
    sizeChanged = pyqtSignal(QFont)
    
    def __init__(self, parent):
        super().__init__()
        self.app = QApplication.instance()
        self.cfg_session = parent.cfg_session
        self.cfg_app = parent.cfg_app
        self.cfg_user = parent.cfg_user

        self.df_bkp = None

        #Language
        self.i18n = parent.i18n
        nested = self.i18n.getNested
        #Headers
        self._status = nested("execution", "header", "status")
        self._query = nested("execution", "header", "query")
        self._shape = nested("execution", "header", "shape")
        self._time = nested("execution", "header", "time")
        self._resources = nested("execution", "header", "resources")
        self._error = nested("execution", "header", "error")
        #States
        self._running = nested("execution", "status", "running")
        self._executed = nested("execution", "status", "executed")
        self._failed = nested("execution", "status", "failed")
        
        #Menus
        self.menu_texts = {
            'copy_column': nested('tab-result', 'headerMenuH', 'copy-column'),
            'sort_asc': nested('tab-result', 'headerMenuH', 'sort-asc'),
            'sort_des': nested('tab-result', 'headerMenuH', 'sort-des'),
            'restore': nested('tab-result', 'headerMenuH', 'restore'),
            'numbers_filter': nested('tab-result', 'headerMenuH', 'numbers-filter'),
            'texts_filter': nested('tab-result', 'headerMenuH', 'texts-filter'),
        }

        #Setting msgs of filters
        self.filters_texts = {
            #Numerical filters
            'num_equal': nested('tab-result', 'filter-value-num', 'num-equal'),
            'num_not_equal': nested('tab-result', 'filter-value-num', 'num-not-equal'),
            'greater': nested('tab-result', 'filter-value-num', 'greater'),
            'greater_equal': nested('tab-result', 'filter-value-num', 'greater-equal'),
            'lesser': nested('tab-result', 'filter-value-num', 'lesser'),
            'lesser_equal': nested('tab-result', 'filter-value-num', 'lesser-equal'),
            #Text filters
            'txt_equal': nested('tab-result', 'filter-value-text', 'txt-equal'),
            'txt_not_equal': nested('tab-result', 'filter-value-text', 'txt-not-equal'),
            'start_with': nested('tab-result', 'filter-value-text', 'start-with'),
            'end_with': nested('tab-result', 'filter-value-text', 'end-with'),
            'contains': nested('tab-result', 'filter-value-text', 'contains'),
            'not_contains': nested('tab-result', 'filter-value-text', 'not-contains')
        }

        #Defining number filter actions
        self.num_filter_actions = [
            (self.filters_texts.get('num_equal'), 'num_equal'),
            (self.filters_texts.get('num_not_equal'), 'num_not_equal'),
            (None, None),  #Separator
            (self.filters_texts.get('greater'), 'greater'),
            (self.filters_texts.get('greater_equal'), 'greater_equal'),
            (self.filters_texts.get('lesser'), 'lesser'),
            (self.filters_texts.get('lesser_equal'), 'lesser_equal'),
            (self.filters_texts.get('between'), 'between'),
            (None, None),  #Separator
            (self.filters_texts.get('top_10'), 'top_10'),
            (self.filters_texts.get('above_avg'), 'above_avg'),
            (self.filters_texts.get('below_avg'), 'below_avg'),
        ]

        #Defining text filter actions
        self.text_filter_actions = [
            (self.filters_texts.get('txt_equal'), 'txt_equal'),
            (self.filters_texts.get('txt_not_equal'), 'txt_not_equal'),
            (None, None),  #Separator
            (self.filters_texts.get('start_with'), 'start_with'),
            (self.filters_texts.get('end_with'), 'end_with'),
            (None, None),  #Separator
            (self.filters_texts.get('contains'), 'contains'),
            (self.filters_texts.get('not_contains'), 'not_contains'),
        ]

        #Setting the model
        self.model = PolarsModel(pl.DataFrame(), self)
        self.setModel(self.model)
        #Enabling mouse tracking
        self.setMouseTracking(True)
        #Column properties
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setDefaultSectionSize(150)
        self.horizontalHeader().setSectionsClickable(True)
        self.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.headerMenuH)
        #Row Properties
        self.verticalHeader().setSectionsClickable(True)
        self.verticalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.verticalHeader().customContextMenuRequested.connect(self.headerMenuV)
        
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
        #Defining internal theme
        theme_name = self.cfg_session.index.get("internal_theme")
        #Defining style delegator
        self.delegate = CustomDelegate(self)
        self.theme = self.cfg_app.index.get("list_thems")[theme_name]
        _, _, self.tl_3, = self.theme["result-trafficlight"]
        self.delegate.updatePaint(theme_name)
        self.setItemDelegate(self.delegate)
        #Attribute to determine whether or not to update sizes headers
        self.updateTableSizes = False

        #Creating transverse Menus and actions to the entire results table
        #-------------------------------------------------------
        #Principal menus
        self.headerMenu = QMenu(self)

        #Creating actions for the header menu
        self.copyColumnAction = QAction(self.menu_texts['copy_column'], self)
        self.sortAscAction = QAction(self.menu_texts['sort_asc'], self)
        self.sortDescAction = QAction(self.menu_texts['sort_des'], self)
        self.restoreAction = QAction(self.menu_texts['restore'], self)
        self.numFilterMenu = QMenu(self.menu_texts['numbers_filter'], self)
        self.textFilterMenu = QMenu(self.menu_texts['texts_filter'], self)
       
        #Creatting the cell menu
        #--------------------------------------
        #Names of the menu options
        _copy_value = nested('tab-result', 'cell-menu', 'copy-value')
        _copy_value_header = nested('tab-result', 'cell-menu', 'copy-value-header')
        _copy_vale_filter = nested('tab-result', 'cell-menu', 'copy-vale-filter')
        _copy_table = nested('tab-result', 'cell-menu', 'copy-table')
        
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



    #Function to show a window with the cell information
    def showCellInfo(self, row, column):
        #Getting cell text
        index = self.model.index(row, column)
        cell_text = str(self.model.ResultDF[index.row(), index.column()])
        #Obtaining global position
        cell_rect = self.visualRect(index)
        #Getting the global position of the top left corner of the cell
        global_pos = self.mapToGlobal(cell_rect.bottomLeft())
        #Defining an attribute that references the parent tab
        self.tab_parent = self.parent().parent()
        #Showing tooltip with information
        self.tooltip = MyTooltip(self)
        self.tooltip.setParent(self.tab_parent)
        self.tooltip.setText(cell_text)
        self.tooltip.myShow(cell_rect)
        self.tooltip.textContent.setFocus()
    
    #Function to apply custom size to columns
    def applyColumnSizes(self):
        sizes = self.cfg_session.index.get("result_geo")
        header = self.horizontalHeader()
        for i in range(header.count()):
            header.resizeSection(i, sizes[i])
    
    #Modifying the parameters assigned by the user
    def updateColumnSizes(self, logicalIndex, oldSize, newSize):
        if self.updateTableSizes:
            sizes = self.cfg_session.index.get("result_geo")
            header = self.horizontalHeader()
            for i in range(header.count()):
                sizes[i] = header.sectionSize(i)
            self.cfg_session.index["result_geo"] = sizes

    #Function to load data from pl.DataFrame
    def loadData(self, df, drop_bkp=False):
        self.updateTableSizes = False
        #Setting the model with the DataFrame
        self.model.setDataFrame(df)

        #Differentiating between status and results
        if df.columns == [self._status, self._query, self._shape, self._time \
                                , self._resources, self._error]:
            
            self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            #Activating traffic light
            self.delegate.status = True
            
            #Showing the end of the table
            self.scrollToBottom()
            #Modifying sizes
            self.applyColumnSizes()
            self.updateTableSizes = True
            #Checking the status of the last row, in case of error show message
            if df.item(-1, self._status) == self._failed:
                self.showCellInfo(len(df) - 1, len(df.columns) - 1)
            #Connecting header size modification signal
            self.horizontalHeader().sectionResized.connect(self.updateColumnSizes)
        else:
            #Deactivating traffic light
            self.delegate.status = False
            #Disconnecting header size modification signal
            try:
                self.horizontalHeader().sectionResized.disconnect(self.updateColumnSizes)
            except TypeError:
                pass
            
            self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        #     #self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        #Emmiting dfChanged signal
        self.dfChanged.emit(df)
        #Dropping the backup if requested
        if drop_bkp:
            self.df_bkp = None

    #Function to detect double clicking on a cell
    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.showCellInfo(index.row(), index.column())
    
    #Defining event for how much the mouse scroll is touched     
    def wheelEvent(self, event):
        #Check if the Control key is pressed when scrolling with the mouse
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.changeFontSize(1)
            else:
                self.changeFontSize(-1)
        else:
            super().wheelEvent(event)
        
    #Creating a function that will change the font size
    def changeFontSize(self, delta):
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
        self.cfg_session.index.get("prede_font")["result-size"] = int(font_size)
        self.sizeChanged.emit(new_font)
        
    #-------------------------------------------
    #Functions associated with the Cell Menu
    #-------------------------------------------
    #Function to copy selected cells
    #This function is input for others later
    def copySelected(self):
        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return None

        # Obtener filas y columnas seleccionadas
        rows = sorted(set(index.row() for index in selection))
        cols = sorted(set(index.column() for index in selection))
        # Obtener nombres de columnas reales
        col_names = [self.model.ResultDF.columns[col] for col in cols]
        # Extraer datos directamente del DataFrame
        data = self.model.ResultDF[rows, cols]
        return data
    
    #Function to copy as filter
    def copyAsFilter(self):
        data = self.copySelected()
        text = ""
        if data is not None and data.height > 0:
            for key in data.columns:
                values = data[key].to_list()
                if len(values) == 1:
                    value = values[0]
                    if isinstance(value, str):
                        text += f"{key} = '{value}'\nAND "
                    else:
                        text += f"{key} = {value}\nAND "
                else:
                    formatted_values = []
                    all_numeric = all(isinstance(value, (int, float)) for value in values)
                    for value in values:
                        if all_numeric:
                            formatted_values.append(str(value))
                        else:
                            formatted_values.append(f"'{value}'")
                    values_str = ", ".join(formatted_values)
                    text += f"{key} IN ({values_str})\nAND "
            text = text.rstrip("AND \n")
            self.app.clipboard().setText(text)
            
    #Function to identify what to copy
    def controlC(self):
        selection = self.selectionModel()
        #Getting the total number of rows and columns
        num_rows = self.model.rowCount()
        num_columns = self.model.columnCount()
        
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
    def copySelectedValue(self):
        data = self.copySelected()
        if data is not None and data.height > 0:
            #Converts to tabular text (without heading)
            rows = []
            for i in range(data.height):
                row = [str(data[i, j]) for j in range(data.width)]
                rows.append("\t".join(row))
            text = "\n".join(rows)
            self.app.clipboard().setText(text)

    #Function to copy the entire table
    def copyWholeTable(self):
        df = self.model.ResultDF
        if df is not None and df.height > 0:
            #Headers
            header = "\t".join(df.columns)
            #Rows
            rows = []
            for i in range(df.height):
                row = [str(df[i, j]) for j in range(df.width)]
                rows.append("\t".join(row))
            text = header + "\n" + "\n".join(rows)
            clipboard = self.app.clipboard()
            clipboard.setText(text)

    #-------------------------------------------
    #Functions associated with the Column Menu
    #-------------------------------------------
    #Function to restore original after applying filters
    def restoreTable(self):
        if self.df_bkp is not None:
            self.loadData(self.df_bkp, drop_bkp=True)
      
    #Sorting table according to column
    def sortByColumn(self, logical_index, order):
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
    def copySelectedValueH(self):
        data = self.copySelected()
        if data is not None and data.height > 0:
            #Selected columns headers
            header = "\t".join(data.columns)
            #Selected ranks
            rows = []
            for i in range(data.height):
                row = [str(data[i, j]) for j in range(data.width)]
                rows.append("\t".join(row))
            text = header + "\n" + "\n".join(rows)
            self.app.clipboard().setText(text)
    
    #Function to copy the entire column
    def copyWholeColumn(self, col_index):
        #Verifing that the index is valid
        if self.model.ResultDF is not None and 0 <= col_index < self.model.ResultDF.width:
            #Getting the name of the column
            col_name = self.model.ResultDF.columns[col_index]
            #Getting the column data as a strings list
            col_data = [str(val) for val in self.model.ResultDF[col_name].to_list()]
            #Preparing the text with header
            text = f"{col_name}\n" + "\n".join(col_data)
            #Coping to the clipboard
            clipboard = self.app.clipboard()
            clipboard.setText(text)
    
    #Function to show filter input dialog
    def showNumFilterInput(self, logical_index, filter_type):
        #Getting text of filters
        _filter_title = self.i18n.getNested('tab-result', 'filter-value-num', 'title')
        _title_between = self.i18n.getNested('tab-result', 'between', 'title')
        _min = self.i18n.getNested('tab-result', 'between', 'min')
        _max = self.i18n.getNested('tab-result', 'between', 'max')

        #Filters that do not require user input
        if filter_type in ['top_10', 'above_avg', 'below_avg']:
            self.filterByValue(logical_index, None, filter_type)
            return

        # Filtros que requieren un rango de valores
        if filter_type == 'between':
            min_value, ok_min = QInputDialog.getDouble(self, _title_between, f'{_min}:')
            if not ok_min:
                return
            max_value, ok_max = QInputDialog.getDouble(self, _title_between, f'{_max}:')
            if not ok_max:
                return
            self.filterByValue(logical_index, (min_value, max_value), filter_type)
            return
        
        _msg = self.filters_texts.get(filter_type)

        text, ok = QInputDialog.getText(self, _filter_title, f'{_msg}:')
        if ok:
            self.filterByValue(logical_index, text, filter_type)

    #Function to apply specific text filter
    def showTxtFilterInput(self, logical_index, filter_type):
        #Creating a backup of the original DataFrame
        if self.df_bkp is None:
            self.df_bkp = self.model.ResultDF.clone()
        #Getting text of filters
        _filter_title = self.i18n.getNested('tab-result', 'filter-value-text', 'title')
        _msg = self.filters_texts.get(filter_type)
        #Getting the name of the column to filter
        column_name = self.model.ResultDF.columns[logical_index]
        filter_text, ok = QInputDialog.getText(self, _filter_title, f"{_msg}:")
        if ok:
            #Filtering the DataFrame based on the text input
            filtered_df = self.filterTextColumn(self.model.ResultDF, column_name, filter_type, filter_text)
            self.loadData(filtered_df)
      
    #Function to apply number filters
    def filterByValue(self, logical_index, value, filter_type):
        #Creating a backup of the original DataFrame
        if self.df_bkp is None:
            self.df_bkp = self.model.ResultDF.clone()
    
        column_name = self.model.ResultDF.columns[logical_index]
        df = self.model.ResultDF

        if filter_type == 'between' and isinstance(value, tuple):
            min_value, max_value = value
            filtered_df = df.filter(
                (pl.col(column_name) >= min_value) & (pl.col(column_name) <= max_value)
            )
        elif filter_type == 'equals':
            filtered_df = df.filter(pl.col(column_name) == value)
        elif filter_type == 'not_equals':
            filtered_df = df.filter(pl.col(column_name) != value)
        elif filter_type == 'greater':
            filtered_df = df.filter(pl.col(column_name) > float(value))
        elif filter_type == 'greater_equal':
            filtered_df = df.filter(pl.col(column_name) >= float(value))
        elif filter_type == 'lesser':
            filtered_df = df.filter(pl.col(column_name) < float(value))
        elif filter_type == 'lesser_equal':
            filtered_df = df.filter(pl.col(column_name) <= float(value))
        elif filter_type == 'top_10':
            filtered_df = df.sort(column_name, descending=True).head(10)
        elif filter_type == 'above_avg':
            mean_value = df[column_name].mean()
            filtered_df = df.filter(pl.col(column_name) > mean_value)
        elif filter_type == 'below_avg':
            mean_value = df[column_name].mean()
            filtered_df = df.filter(pl.col(column_name) < mean_value)
        else:
            filtered_df = df  #No filter applied
        
        self.loadData(filtered_df)
        
    #Function to apply text filters
    def filterTextColumn(self, df, column_name, filter_type, value):
        #Turnnig everything to string and lowercase for capital comparison to capital letters
        series = df[column_name].cast(pl.String).str.to_lowercase()
        value = value.lower()

        if filter_type == "equal":
            mask = series == value
        elif filter_type == "not_equal":
            mask = series != value
        elif filter_type == "start_with":
            mask = series.str.starts_with(value)
        elif filter_type == "end_with":
            mask = series.str.ends_with(value)
        elif filter_type == "contains":
            mask = series.str.contains(value)
        elif filter_type == "not_contains":
            mask = ~series.str.contains(value)
        else:
            return df

        # Filtrar el DataFrame usando el mask
        filtered_df = df.filter(mask)
        return filtered_df

    #-------------------------------------------
    #Functions associated with the Row Menu
    #-------------------------------------------
    #Function to copy the entire row
    def copySelectedRow(self):
        #Getting the selected row index
        selection = self.selectionModel().currentIndex()
        if selection.isValid():
            row_idx = selection.row()
            #Getting the data from the row directly from the dataframe
            row_data = [str(self.model.ResultDF[row_idx, col]) for col in range(self.model.ResultDF.width)]
            #Coping to the clipboard, separated by tabulators
            self.app.clipboard().setText("\t".join(row_data))

    #Function to copy the entire row with header
    def copySelectedRowWithHeader(self):
        #Getting the selected row index
        selection = self.selectionModel().currentIndex()
        if selection.isValid():
            row_idx = selection.row()
            #Getting headers and row data from Dataframe
            header_data = list(self.model.ResultDF.columns)
            row_data = [str(self.model.ResultDF[row_idx, col]) for col in range(self.model.ResultDF.width)]
            #Coping to the clipboard, separated by tabulators
            data_with_header = "\t".join(header_data) + "\n" + "\t".join(row_data)
            self.app.clipboard().setText(data_with_header)

    #-------------------------------------------
    #Functions to create Menus
    #-------------------------------------------
    #Menu for cells
    #--------------
    #Showing contextual menu
    def cellMenu(self, pos):
        #Show menu at right click position
        self.cellMenu.exec(self.mapToGlobal(pos))

    #Column menu
    #------------------
    def headerMenuH(self, pos):        
        #Start of the function code
        #--------------------------
        logical_index = self.horizontalHeader().logicalIndexAt(pos)
        self.selectColumn(logical_index)

        #Getting the name and type of the selected column
        column_name = self.model.ResultDF.columns[logical_index]
        dtype = self.model.ResultDF.schema[column_name]

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
        if dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64):
            for text, filter_type in self.num_filter_actions:
                if text is None:
                    self.numFilterMenu.addSeparator()
                else:
                    action = QAction(text, self)
                    action.triggered.connect(partial(self.showNumFilterInput, logical_index, filter_type))
                    self.numFilterMenu.addAction(action)
            self.headerMenu.addMenu(self.numFilterMenu)
        elif dtype == pl.Utf8:
            for text, filter_type in self.text_filter_actions:
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
    def headerMenuV(self, pos):
        #Language
        nested = self.i18n.getNested
        
        #Names of the menu options
        _copy_row = nested('tab-result', 'headerMenuV', 'copy-row')
        _copy_row_header = nested('tab-result', 'headerMenuV', 'copy-row-header')

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

