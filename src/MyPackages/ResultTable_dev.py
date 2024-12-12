import pandas as pd
from PyQt6.QtWidgets import QApplication, QTableView \
    , QMenu, QHeaderView, QInputDialog, QAbstractItemView \
    , QStyledItemDelegate
from PyQt6.QtGui import QAction, QStandardItemModel \
    , QStandardItem, QFont, QColor, QBrush, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QSortFilterProxyModel \
    , QAbstractTableModel, QModelIndex
from MyPackages.MyTooltip import MyTooltip

#========================================
### Creating class to draw results table
#========================================
class CustomDelegate(QStyledItemDelegate):
    #Defining Slots
    #-----------------
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
        super().__init__(parent)

    def updatePaint(self, theme_name):
        self.theme = self.cfg_app.index.get("list_thems")[theme_name]
        self.tl_1, self.tl_2, self.tl_3 = self.theme["result-trafficlight"]
        self.background_color = self.theme["result-background-color"]
        self.alter_background_color = self.theme["result-alternate-background-color"]
        self.gridline_color = self.theme["result-gridline-color"]

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
            if value == "Ejecutado":
                option.backgroundBrush = QBrush(QColor(self.tl_1))
            elif value == "Ejecutando":
                option.backgroundBrush = QBrush(QColor(self.tl_2))
            elif value == "Falló":
                option.backgroundBrush = QBrush(QColor(self.tl_3))

        #Painting the bottom of the cell
        painter.fillRect(option.rect, option.backgroundBrush)

        #Painting the border of the cell
        pen = QPen(QColor(self.gridline_color))
        painter.setPen(pen)
        painter.drawRect(option.rect)

        #Painting the content
        super().paint(painter, option, index)

class SoftLoadTableModel(QAbstractTableModel):
    def __init__(self, df, parent=None, chunk_size=100):
        super().__init__(parent)
        self._df = df
        self.chunk_size = chunk_size
        self.loaded_rows = min(chunk_size, len(df))

    def rowCount(self, parent=None):
        return self.loaded_rows

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._df.columns[section]
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None

    def data(self, index, role):
        if not index.isValid():
            return None

        row, col = index.row(), index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if row < self.loaded_rows:
                # Formatea las variables según sea necesario
                value = self._df.iat[row, col]
                return f"{value:.2f}" if isinstance(value, float) else str(value)

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Alinea numéricos a la derecha y texto a la izquierda
            return Qt.AlignmentFlag.AlignRight if isinstance(self._df.iat[row, col], (int, float)) else Qt.AlignmentFlag.AlignLeft

        return None

    def fetchMore(self, parent=None):
        rows_to_load = min(self.chunk_size, len(self._df) - self.loaded_rows)
        if rows_to_load <= 0:
            return

        self.beginInsertRows(QModelIndex(), self.loaded_rows, self.loaded_rows + rows_to_load - 1)
        self.loaded_rows += rows_to_load
        self.endInsertRows()

    def canFetchMore(self, parent=None):
        return self.loaded_rows < len(self._df)
    

class ResultTable(QTableView):
    #Signs
    dfChanged = pyqtSignal(pd.DataFrame)
    columnSorted = pyqtSignal(int, Qt.SortOrder)
    sizeChanged = pyqtSignal(QFont)
    #Slots
    _df = None
    
    def __init__(self, parent):
        super().__init__()
        self.app = QApplication.instance()
        self.cfg_session = parent.cfg_session
        self.cfg_app = parent.cfg_app

        #Language
        self.i18n = parent.i18n
        self.lgg = parent.lgg
        nested = self.i18n.getNested
        lgg = self.lgg
        #Headers
        self._status = nested(lgg, "execution", "header", "status")
        self._query = nested(lgg, "execution", "header", "query")
        self._shape = nested(lgg, "execution", "header", "shape")
        self._time = nested(lgg, "execution", "header", "time")
        self._resources = nested(lgg, "execution", "header", "resources")
        self._error = nested(lgg, "execution", "header", "error")
        #States
        self._failed = nested(lgg, "execution", "status", "failed")
        
        self.model = QStandardItemModel(self)
        #Adding sorting and filtering options
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(-1)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setModel(self.proxy_model)
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
        
        #Conectando Ctrl+C a copy_selected_value
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
        self.updateTable = False
        
    #Function to show a window with the cell information
    def showCellInfo(self, row, column):
        #Getting cell text
        index = self.model.index(row, column)
        cell_text = self.model.data(index, Qt.ItemDataRole.DisplayRole)
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
        if self.updateTable:
            sizes = self.cfg_session.index.get("result_geo")
            header = self.horizontalHeader()
            for i in range(header.count()):
                sizes[i] = header.sectionSize(i)
            self.cfg_session.index["result_geo"] = sizes

    def loadData(self, df, backup=True):
        self.setModel(self.proxy_model)
        #Storing a copy of the original DataFrame
        if backup:
            self._df = df.copy()

        #Cleaning the model
        #self.model.clear()
        
        # Cargar modelo de datos con `SoftLoadTableModel`
        self.model = SoftLoadTableModel(df, parent=self, chunk_size=500)
        self.proxy_model.setSourceModel(self.model)
        self.setModel(self.proxy_model)

        # Configurar encabezados
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.model.layoutChanged.emit()

        # Restaurar delegado y conectores
        self.delegate.updatePaint(self.cfg_session.index.get("internal_theme"))
        self.setItemDelegate(self.delegate)
        self.horizontalHeader().sectionResized.connect(self.updateColumnSizes)

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
        if selection:
            #Creating a dictionary to store the data
            data = {}
            #Sorting indexes by rows and columns
            selection = sorted(selection, key=lambda index: (index.row(), index.column()))
            rows = sorted(set(index.row() for index in selection))
            columns = sorted(set(index.column() for index in selection))
            column_names = [self.model.headerData(col, Qt.Orientation.Horizontal) for col in columns]
            
            #Starting empty lists for each column
            for col in columns:
                col_name = self.model.headerData(col, Qt.Orientation.Horizontal)
                data[col_name] = []
            
            #Filling the data in each column
            for row in rows:
                row_data = []
                for col in columns:
                    index = self.model.index(row, col)
                    value = self.model.data(index, Qt.ItemDataRole.DisplayRole)
                    row_data.append(value)
                for i, col in enumerate(columns):
                    col_name = self.model.headerData(col, Qt.Orientation.Horizontal)
                    data[col_name].append(row_data[i])
            return data
        
        else: 
            return None
    
    #Function to copy as filter
    def copyAsFilter(self):
        data = self.copySelected()
        text = ""
        
        if data:
            for key, values in data.items():
                if len(values) == 1:
                    # There is only one value selected
                    value = values[0]
                    if isinstance(value, str):
                        text += f"{key} = '{value}'\n AND "
                    else:
                        text += f"{key} = {value}\n AND "
                else:
                    # More than one value selected
                    formatted_values = []
                    all_numeric = all(isinstance(value, (int, float)) for value in values)
                    
                    for value in values:
                        if all_numeric:
                            formatted_values.append(str(value))
                        else:
                            formatted_values.append(f"'{value}'")
                    
                    values_str = ", ".join(formatted_values)
                    text += f"{key} IN ({values_str})\n AND "
            
            text = text.rstrip(" AND \n")
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
        #Converting to text
        if data:
            df = pd.DataFrame(data)
            df.to_clipboard(index=False, header=False)
            #Modifying the clipboard
            clipboard = self.app.clipboard()
            text_mod = clipboard.text()[:-1] #.rstrip()

            clipboard.setText(text_mod)

    #Function to copy the entire table
    def copyWholeTable(self):
        # Copy the entire table to the clipboard, including the headers
        header_data = [self.model.headerData(col, Qt.Orientation.Horizontal) for col in range(self.model.columnCount())]
        table_data = "\t".join(header_data) + "\n"
        for row in range(self.model.rowCount()):
            row_data = [str(self.model.data(self.model.index(row, col))) for col in range(self.model.columnCount())]
            table_data += "\t".join(row_data) + "\n"
        self.app.clipboard().setText(table_data)

    
    #-------------------------------------------
    #Functions associated with the Column Menu
    #-------------------------------------------
    #Function to restore original after applying filters
    def restoreTable(self):
        if hasattr(self, '_df'):
            self.loadData(self._df, backup=False)
      
    #Sorting table according to column
    def sortByColumn(self, logical_index, order):
        #Use proxy_model to sort
        self.proxy_model.sort(logical_index, order)
        #Change the sorting direction for next time
        self.sort_order = Qt.SortOrder.DescendingOrder if self.sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        #Emit a signal to indicate that a column has been sorted
        self.columnSorted.emit(logical_index, order)
    
    #Function to copy all selected cells with header
    def copySelectedValueH(self):
        data = self.copySelected()
        #Converting to text
        if data:
            df = pd.DataFrame(data)
            df.to_clipboard(index=False, header=True)
    
    #Function to copy the entire column
    def copyWholeColumn(self, col_index):
        #Verifying that the column index is valid
        if 0 <= col_index < self.model.columnCount():
            #Getting column header
            header = self.model.headerData(col_index, Qt.Orientation.Horizontal)
            column_data = [str(self.model.data(self.model.index(row, col_index))) for row in range(self.model.rowCount())]
            #Concatenating the header with the column data
            data_with_header = header + "\n" + "\n".join(column_data)
            #Copying the column to the clipboard
            self.app.clipboard().setText(data_with_header)
    
    #Function to show filter input dialog
    def showFilterInput(self, logical_index, filter_type):
        text, ok = QInputDialog.getText(self, 'Input Dialog', f'Ingrese el valor para filtrar ({filter_type}):')
        if ok:
            self.filterByValue(logical_index, text, filter_type)
    
    #Function to apply number filters
    def filterByValue(self, logical_index, value, filter_type):
        df = self.modelToDataframe()
        column_name = self.model.horizontalHeaderItem(logical_index).text()
        
        if filter_type == 'equals':
            filtered_df = df[df[column_name] == value]
        elif filter_type == 'not_equals':
            filtered_df = df[df[column_name] != value]
        elif filter_type == 'greater':
            filtered_df = df[df[column_name] > value]
        elif filter_type == 'greater_equal':
            filtered_df = df[df[column_name] >= value]
        elif filter_type == 'lesser':
            filtered_df = df[df[column_name] < value]
        elif filter_type == 'lesser_equal':
            filtered_df = df[df[column_name] <= value]
        elif filter_type == 'between':
            min_value, ok_min = QInputDialog.getDouble(self, 'Filtrar Entre', 'Valor Mínimo:')
            max_value, ok_max = QInputDialog.getDouble(self, 'Filtrar Entre', 'Valor Máximo:')
            if ok_min and ok_max:
                filtered_df = df[(df[column_name] >= min_value) & (df[column_name] <= max_value)]
        elif filter_type == 'top_10':
            df_sorted = df.sort_values(by=column_name, ascending=False)
            filtered_df = df_sorted.head(10)
        elif filter_type == 'above_avg':
            mean_value = df[column_name].mean()
            filtered_df = df[df[column_name] > mean_value]
        elif filter_type == 'below_avg':
            mean_value = df[column_name].mean()
            filtered_df = df[df[column_name] < mean_value]
        else:
            filtered_df = df  # Do not apply filter


        self.loadData(filtered_df, backup=False)

    #Function to apply specific text filter
    def applyTextFilter(self, logical_index, filter_type):
        #Getting the text to filter
        column_name = self.model.horizontalHeaderItem(logical_index).text()
        filter_text, ok = QInputDialog.getText(self, "Filtrar", f"Introduce el valor para filtrar en la columna '{column_name}':")
        if ok:
            df = self.modelToDataframe()
            if column_name in df.columns:
                filtered_df = self.filterTextColumn(df, column_name, filter_type, filter_text)
                self.loadData(filtered_df, backup=False)

    #Function to apply text filters
    def filterTextColumn(self, df, column_name, filter_type, value):
        if filter_type == "equals":
            return df[df[column_name].astype(str).str.lower() == value.lower()]
        elif filter_type == "not_equals":
            return df[df[column_name].astype(str).str.lower() != value.lower()]
        elif filter_type == "starts_with":
            return df[df[column_name].astype(str).str.lower().str.startswith(value.lower())]
        elif filter_type == "ends_with":
            return df[df[column_name].astype(str).str.lower().str.endswith(value.lower())]
        elif filter_type == "contains":
            return df[df[column_name].astype(str).str.lower().str.contains(value.lower())]
        elif filter_type == "not_contains":
            return df[~df[column_name].astype(str).str.lower().str.contains(value.lower())]
        return df

    
    #Function to convert the model to a DataFrame
    def modelToDataframe(self):
        data = []
        for row in range(self.model.rowCount()):
            row_data = []
            for column in range(self.model.columnCount()):
                item = self.model.item(row, column)
                row_data.append(item.text())
            data.append(row_data)
        
        columns = [self.model.horizontalHeaderItem(column).text() for column in range(self.model.columnCount())]
        return pd.DataFrame(data, columns=columns)

    #-------------------------------------------
    #Functions associated with the Row Menu
    #-------------------------------------------
    #Function to copy the entire row
    def copySelectedRow(self):
        #Getting selected row
        selection = self.selectionModel().currentIndex()
        if selection.isValid():
            row_data = [str(self.model.data(self.model.index(selection.row(), col))) for col in range(self.model.columnCount())]
            self.app.clipboard().setText("\t".join(row_data))

    #Function to copy the entire row with header
    def copySelectedRowWithHeader(self):
        #Getting selected row along with headers
        selection = self.selectionModel().currentIndex()
        if selection.isValid():
            header_data = [self.model.headerData(col, Qt.Orientation.Horizontal) for col in range(self.model.columnCount())]
            row_data = [str(self.model.data(self.model.index(selection.row(), col))) for col in range(self.model.columnCount())]
            data_with_header = "\t".join(header_data) + "\n" + "\t".join(row_data)
            self.app.clipboard().setText(data_with_header)

    #-------------------------------------------
    #Functions to create Menus
    #-------------------------------------------
    #Menu for cells
    #------------------
    #Showing contextual menu
    def cellMenu(self, pos):
        #Creating the context menu
        menu = QMenu(self)

        #Action to copy cell value
        copyValueAction = QAction("Copiar valor", self)
        copyValueAction.triggered.connect(self.copySelectedValue)
        menu.addAction(copyValueAction)

        #Action to copy cell value
        copyValueActionH = QAction("Copiar valor con encabezado", self)
        copyValueActionH.triggered.connect(self.copySelectedValueH)
        menu.addAction(copyValueActionH)

        #Action to copy as filter
        copyAsFilter = QAction("Copiar como filtro", self)
        copyAsFilter.triggered.connect(self.copyAsFilter)
        menu.addAction(copyAsFilter)
        menu.addSeparator()
        
        #Action to copy the entire table
        copyTableAction = QAction("Copiar tabla completa", self)
        copyTableAction.triggered.connect(self.copyWholeTable)
        menu.addAction(copyTableAction)
        menu.addSeparator()
        
        #Show menu at right click position
        menu.exec(self.mapToGlobal(pos))

    #Column menu
    #------------------
    def headerMenuH(self, pos):
        logical_index = self.horizontalHeader().logicalIndexAt(pos)
        self.selectColumn(logical_index)
        menu = QMenu(self)

        #Action to copy column with header
        copyColumnAction = QAction("Copiar columna", self)
        copyColumnAction.triggered.connect(lambda: self.copyWholeColumn(logical_index))
        menu.addAction(copyColumnAction)
        menu.addSeparator()

        #Action to sort ascending
        sortAscAction = QAction("Ordenar ascendentemente", self)
        sortAscAction.triggered.connect(lambda: self.sortByColumn(logical_index, Qt.SortOrder.AscendingOrder))
        menu.addAction(sortAscAction)

        #Action to sort descending
        sortDescAction = QAction("Ordenar descendentemente", self)
        sortDescAction.triggered.connect(lambda: self.sortByColumn(logical_index, Qt.SortOrder.DescendingOrder))
        menu.addAction(sortDescAction)
        menu.addSeparator()

        #Action to restore the table to its original version
        restoreAction = QAction("Restaurar tabla original", self)
        restoreAction.triggered.connect(self.restoreTable)
        menu.addAction(restoreAction)

        #Submenu for filtering
        numFilterMenu = QMenu("Filtros de número", self)

        #Filter actions
        num_filter_actions = {
            "Es igual a...": "equals",
            "No es igual a...": "not_equals",
            "Separador 1": None,
            "Mayor que...": "greater",
            "Mayor o igual que...": "greater_equal",
            "Menor que...": "lesser",
            "Menor o igual que...": "lesser_equal",
            "Entre...": "between",
            "Separador 2": None,
            "Diez mejores": "top_10",
            "Superior al promedio": "above_avg",
            "Inferior al promedio": "below_avg",
            "Separador 3": None
        }
        
        for action_text, filter_type in num_filter_actions.items():
            if "Separador" in action_text:
                numFilterMenu.addSeparator()
            else:
                action = QAction(action_text, self)
                action.triggered.connect(lambda checked, f=filter_type: self.showFilterInput(logical_index, f))
                numFilterMenu.addAction(action)
        menu.addMenu(numFilterMenu)

        #Submenu for filtering
        textFilterMenu = QMenu("Filtros de texto", self)

        #Text filtering
        text_filter_options = {
            "Es igual a": "equals",
            "No es igual a": "not_equals",
            "Separador 1": None,
            "Comienza por": "starts_with",
            "Termina con": "ends_with",
            "Separador 2": None,
            "Contiene": "contains",
            "No contiene": "not_contains",
            "Separador 3": None
        }
        
        for action_text, filter_type in text_filter_options.items():
            if "Separador" in action_text:
                textFilterMenu.addSeparator()
            else:
                action = QAction(action_text, self)
                action.triggered.connect(lambda checked, ft=filter_type: self.applyTextFilter(logical_index, ft))
                textFilterMenu.addAction(action)
        menu.addMenu(textFilterMenu)
        menu.addSeparator()

        global_pos = self.mapToGlobal(pos)
        menu.exec(global_pos)
    
    #Menu for rows
    #------------------
    def headerMenuV(self, pos):
        logical_index = self.verticalHeader().logicalIndexAt(pos)
        self.selectRow(logical_index)
        menu = QMenu(self)

        #Action to copy current row
        copyRowAction = QAction("Copiar fila", self)
        copyRowAction.triggered.connect(self.copySelectedRow)
        menu.addAction(copyRowAction)
        
        #Action to copy row with header
        copyRowWHAction = QAction("Copiar fila con encabezado", self)
        copyRowWHAction.triggered.connect(self.copySelectedRowWithHeader)
        menu.addAction(copyRowWHAction)
        menu.addSeparator()

        global_pos = self.mapToGlobal(pos)
        menu.exec(global_pos)

