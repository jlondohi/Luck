#Importing native packages
import re, os, json
from functools import partial

#Importing PyQt6 packages
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QSplitter
    , QLabel, QLineEdit, QHBoxLayout, QScrollArea, QInputDialog, QTabBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (QFont, QTextDocument, QTextCursor, QFontMetrics)
#Importing custom classes and methods
from MyPackages import (MySearchWidget, MyPlainTextEdit
    , MyResultTable, MyParamsManager, MyFlowLayout
    , YamlHandler)

#==================================================================
#Creating functions related to the Scripts tabs (Editor and Param)
#==================================================================
#Function that creates a new tab in the window
def newScriptTab(self, origin = '', *args):
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

    #Creating a horizontal spliter
    splitter_h = QSplitter(Qt.Orientation.Horizontal)
    splitter_h.splitterMoved.connect(self.syncSplitterH)
    self.splitHChanged.connect(splitter_h_slot := lambda pos: splitter_h.setSizes([pos, splitter_h.width() - pos]))
    
    #Creating a vertical spliter
    splitter_v = QSplitter(Qt.Orientation.Vertical)
    splitter_v.splitterMoved.connect(self.syncSplitterV)
    self.splitVChanged.connect(splitter_v_slot := lambda pos: splitter_v.setSizes([pos, splitter_v.height() - pos]))

    #Text Widget Editor
    textEditor = MyPlainTextEdit(self.syntaxList, self.autoCompleteList, self)
    textEditor.changeWrapMode( self.cfg_session.index.get('worldWrap') )
    textEditor.setAcceptDrops(True)
    textEditor.dragEnterEvent = self.dragEnterEvent
    textEditor.dropEvent = self.dropEvent

    textEditor.setPlaceholderText(self.i18nNes('tab-editor', 'pht-editor'))
    textEditor.setStyleSheet( self.dict_styledSheets['MyPlainTextEdit'] )
    _qfont = QFont(font['editor-font'], font['editor-size'])
    textEditor.setFont( _qfont )
    textEditor.sizeChanged.connect(lambda font: self.applyFontSize(font, 'editor'))
    
    #Changing the spaces for tab
    spaces = self.cfg_session.index.get('tab-spaces')
    fm = QFontMetrics(_qfont)
    tab_width = fm.horizontalAdvance(' '*spaces)
    textEditor.setTabStopDistance(tab_width)

    #Function to replace context menu
    textEditor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    textEditor.customContextMenuRequested.connect(partial(self.showMenu, 'assistant'))
    splitter_v.addWidget(textEditor)
    #Wire textChanged signal from textEditor to findSpecialEntries method
    textEditor.textReady.connect(self.findSpecialEntries)

    #Creating a QWidget to manage the parameters
    #All parameters are sorted here
    params_manager = MyParamsManager(self)
    params_manager.setAcceptDrops(True)
    params_manager.dragEnterEvent = self.dragEnterEvent
    params_manager.dropEvent = self.dropEventParam
    params_manager.setProperty('cls', 'MyParamsManager')
    params_manager.setStyleSheet( self.dict_styledSheets['MyParamsManager'] )
    params_manager.setLayout(MyFlowLayout())
    scroll_params = QScrollArea()
    scroll_params.setWidgetResizable(True)
    scroll_params.setWidget(params_manager)
    splitter_v.addWidget(scroll_params)
    self.current_pManager = params_manager

    #RESULTS table widget
    result = MyResultTable(self)
    result.setStyleSheet( self.dict_styledSheets['MyResultTable'] )
    result.setFont( QFont(font['result-font'], font['result-size']) )
    result.sizeChanged.connect(lambda font: self.applyFontSize(font, 'result'))
    
    #concatenating the splitters
    splitter_h.addWidget(splitter_v)
    splitter_h.addWidget(result)
    layoutTab.addWidget(splitter_h)

    #Adding and activating the new tab
    self.tabWidget.addTab(tab_new, f"{self.i18nNes('tab-editor', 'new')} ({self.num_Stab})")
    #Setting the index of the newly created tab
    currentIndex = self.tabWidget.count() - 1
    self.tabWidget.setCurrentIndex(currentIndex)
    #Establishing code for when the command arises from OpenFile
    origin_param = ''
    dict_params = {}
    if origin != '':
        #Loading script
        file = open(origin, 'r' , encoding='utf-8')
        text = file.read()
        textEditor.setPlainText( text )
        file.close()
        #Changing the name of the tab
        origin = origin.replace('\\', '/')
        name = origin.rsplit('/', 1)[-1]
        self.tabWidget.setTabText(currentIndex, name)

        #Checking if the companion file exists
        if os.path.exists(origin+'p'):
            origin_param = origin+'p'
            #Loading parameters
            params = YamlHandler(origin_param)
            dict_params = params.index
        else:
            pattern = r'--\s*PARAMS?\s*:\s*(\{\s*"(?:\{\d+\}"\s*:\s*".*?"\s*,?\s*)+\})'
            matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if matches:
                last = matches[-1]
                try:
                    dict_params = json.loads(last.replace("'", '"'))
                except Exception as e:
                    None

    #Store tab information in the tabInfo dictionary
    tab_name = self.tabWidget.currentWidget().objectName
    self.tabInfo[tab_name] = self.tabInfoTemplate.copy()
    tab_data = self.tabInfo[tab_name]
    tab_data['text_editor']     = textEditor
    tab_data['params_manager']  = params_manager
    tab_data['dict_paramsEtl']  = dict_params
    tab_data['result']          = result
    tab_data['origin']          = origin
    tab_data['origin_param']    = origin_param
    
    #Modifying the original button of the created tab
    self.createCustomCloseButton(currentIndex)
    #Modifying states
    tabBar = self.tabWidget.tabBar()
    btn = tabBar.tabButton(currentIndex, QTabBar.ButtonPosition.RightSide)
    btn.setProperty('type', 'saved')
    btn.style().unpolish(btn)
    btn.style().polish(btn)

    #Updating tab toolTips
    self.updateTabTooltips()
    #Note, do not update icons here

    #Setting splitter sizes
    geo = self.cfg_session.index.get('splitter_geo')
    splitter_h.setSizes([int( self.screen_width*geo[0] ), int( self.screen_width*(1-geo[0]) )])
    splitter_v.setSizes([int( self.screen_height*geo[1] ), int( self.screen_height*(1-geo[1]) )])
    #Setting the splitter handles to hover state
    handle_h = splitter_h.handle(1)
    handle_h.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
    handle_v = splitter_v.handle(1)
    handle_v.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
    #Loading info from the active tab
    self.tabChanged()
    #Running parameter search immediately starts
    self.findSpecialEntries(self.current_etlEditor, self.current_etlEditor.toPlainText()) #Only run after updating tabInfo
    self.updatePManager()
    #Changing mouse pointer to default state
    self.app.restoreOverrideCursor()

#Function to add the parameters to the corresponding parameter segment
def addParmScriptTab(self, origin, *args):
    #Terminating if there is no active tab
    if not self.tabWidget:
        return None
    
    params = YamlHandler(origin)
    #Saving the origin of the parameters
    tab_name = self.tabWidget.currentWidget().objectName
    tab_data = self.tabInfo.get(tab_name)
    tab_data['origin_param'] = origin
    tab_data['dict_paramsEtl'] = params.index
    self.current_paramsEtl = params.index
    self.updatePManager()

#Function to apply the new font to all text boxes connected to the signal  
def applyFontSize(self, new_font, cls, *args):
    if cls == 'editor':
        #Applying changes to all editors
        for editor in self.centralWidget().findChildren(MyPlainTextEdit):
            editor.setFont(new_font)
            #Changing the tab spaces
            fm = QFontMetrics(new_font)
            spaces = self.cfg_session.index.get('tab-spaces')
            tab_width = fm.horizontalAdvance(' '*spaces)
            editor.setTabStopDistance(tab_width)
        
        #Applying changes to all ParamsManager
        for manager in self.centralWidget().findChildren(MyParamsManager):
            #Change source in all QLabel Children
            for label in manager.findChildren(QLabel):
                label.setFont(new_font)
            #Change source in all QLineEdit Children
            for input in manager.findChildren(QLineEdit):
                input.setFont(new_font)
    elif cls == 'result':
        #Applying changes to all QTableView
        for result in self.centralWidget().findChildren(MyResultTable):
            result.setFont(new_font)

#Function to apply formatting according to source
def applyEditorFont(self, *args):
    sender = self.sender()
    #Verifying that the sender is not null and getting its text
    if not sender:
        return
    
    font = self.cfg_session.index.get('prede_font')
    font['editor-font'] = sender.text()
    #Applying changes to each plain text widget
    for editor in self.centralWidget().findChildren(MyPlainTextEdit):
        editor.setFont( QFont(font['editor-font'], font['editor-size']) )

    #Applying changes to all ParamsManager
    for manager in self.centralWidget().findChildren(MyParamsManager):
        #Change source in all QLabel Children
        for label in manager.findChildren(QLabel):
            label.setFont( QFont(font['editor-font'], font['editor-size']) )
        #Change source in all QLineEdit Children
        for input in manager.findChildren(QLineEdit):
            input.setFont( QFont(font['editor-font'], font['editor-size']) )
        
#Function to change the font size of Editor
def changeEtlFontSize(self, delta, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    self.current_etlEditor.changeFontSize(delta, *args)

#Function to change the spaces for tab
def changeSpacePerTab(self, *args):
    current_spaces = self.cfg_session.index.get('tab-spaces')
    #Getting text of msg
    _input_title = self.i18nNes('status-bar', 'spaces')
    _input_msg   = self.i18nNes('status-bar', 'lines-msg')
    #Showing the message
    value, ok = QInputDialog.getText(self, _input_title, _input_msg, QLineEdit.EchoMode.Normal, str(current_spaces))
    try:
        value = int(value)
    except:
        return
    #Making changes
    if ok and isinstance(value, int):
        #Loading the system source
        font = self.cfg_session.index.get('prede_font')
        _qfont = QFont(font['editor-font'], font['editor-size'])
        fm = QFontMetrics(_qfont)
        #converting the spaces
        spaces = int(value)
        self.cfg_session.index['tab-spaces'] = spaces
        self.cfg_session.save()

        tab_width = fm.horizontalAdvance(' '*spaces)
        #Applying changes to each plain text widget
        for editor in self.centralWidget().findChildren(MyPlainTextEdit):
            editor.setTabStopDistance(tab_width)
            editor.tabSpaces = spaces
        #Changing the visualization in the status bar
        label = f"{self.i18nNes('status-bar', 'spaces')}: {spaces:,}"
        self.bt_spaces.setText(label)

#Function to go to a specific line and block
def goToLineBlock(self, *args):
    if not self.current_etlEditor:
        return
    #Stopping the multicursor in case this asset
    if self.current_etlEditor.multiCursorEnabled:
        self.current_etlEditor.stopMultiCursor()
    #Current reference
    cursor = self.current_etlEditor.textCursor()
    current_line = cursor.blockNumber()+1
    #Getting text of msg
    _input_title = self.i18nNes('status-bar', 'goto-title')
    _input_msg   = self.i18nNes('status-bar', 'goto-msg')
    #Showing the message
    value, ok = QInputDialog.getText(self, _input_title, _input_msg, QLineEdit.EchoMode.Normal, str(current_line))
    try: 
        if ',' in str(value):
            line, block = str(value).split(',')
            line = int(line)
            block = int(block)
        else:
            line = int(value)
            block = 1
    except:
        return
    #Making changes
    if ok and isinstance(line, int) and isinstance(block, int):
        line = max(0, line - 1)
        column = max(0, block - 1)
        block = self.current_etlEditor.document().findBlockByNumber(line)
        if block.isValid():
            cursor.setPosition(block.position() + column)
            self.current_etlEditor.setTextCursor(cursor)
            self.current_etlEditor.centerCursor()
            self.current_etlEditor.setFocus()

#Defining a function that will search for parenthesis and the etl parameters
def findSpecialEntries(self, textEditor, plainText, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    #Searchin params
    #---------------
    self.paramSearcher(plainText)
    #Searchin parenthesis
    #--------------------
    #Avoiding recursion
    if self.asyncEditor.working or not plainText:
        return
    self.sendTextEditor.emit(textEditor, plainText)

#Function to paint the new parentheses structure
def paintParentheses(self, textEditor, *args):
    if not isinstance(textEditor, MyPlainTextEdit):
        return

    #Update the parenthesis index in highlight
    highlighter = textEditor.highlighter
    #Temporarily deactivate text change signals, if necessary
    textEditor.suppressTextChanged = True
    
    #Calculate the visible area of the editor
    viewport = textEditor.viewport()
    visible_rect = viewport.rect()
    top_left = textEditor.cursorForPosition(visible_rect.topLeft())
    bottom_left = textEditor.cursorForPosition(visible_rect.bottomLeft())
    start_block = top_left.block().blockNumber()
    end_block = bottom_left.block().blockNumber()

    #Rehighlight only visible blocks
    for block_number in range(start_block, end_block + 1):
        block = textEditor.document().findBlockByNumber(block_number)
        if block.isValid():
            highlighter.rehighlightBlock(block)

    #Update the viewport to reflect the changes
    viewport.update()
    textEditor.suppressTextChanged = False

#Optimized function to look for ETL parameters
def paramSearcher(self, text, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    """Look for parameters between {} keys and update the dictionary."""
    params_etl = {f'{{{match}}}' for match in re.findall(self.re_parameters, text)}

    #If the keys to the new dictionary and the local are the same then the process ends
    if params_etl == set(self.current_paramsEtl.keys()):
        return

    #Keep only keys that do not already exist in text_etl
    for clave in params_etl - self.current_paramsEtl.keys():
        self.current_paramsEtl[clave] = ''
    #Removing keys that no longer exist in text_etl
    for clave in list(self.current_paramsEtl.keys() - params_etl):
        self.current_paramsEtl.pop(clave)
    #Update view
    self.updatePManager()

#Defining a function that will give values ​​to the stored ETL parameters
#in a dictionary
def paramDefiner(self, value, *args):
    sender = self.sender()
    sender_name = str(sender.objectName())[4:]
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    #Modifying the local parameters dictionary
    self.current_paramsEtl[sender_name] = str(value)
    sender.style().unpolish(sender)
    sender.setProperty('empty', True if str(value).strip()=='' else False)
    sender.style().polish(sender)

#Defining function that updates display in parameters manager
def updatePManager(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    #Each parameter must have its corresponding label and entry into the manager
    params_manager = self.current_pManager
    params = self.current_paramsEtl
    #Cleaning the parameter manager
    for i in reversed(range(params_manager.layout().count())):
        widget = params_manager.layout().itemAt(i).widget()
        if widget is not None:
            widget.deleteLater()
    #Adding the parameters to the manager
    for key in sorted(params):
        value = params[key]
        #If the value is void, then looking in the parameter bag
        if not value:
            value = params_manager.parameterBag.get(key, '')
        params_manager.parameterBag[key] = value
        self.addParamToManager(str(key), str(value))
        
    #Adding the parameter to de parameter bag
    params_manager = self.current_pManager

#Function to add a parameter to the current tab
def addParamToManager(self, key, value, *args):
    #Identifying the parameter widget
    params_manager = self.current_pManager
    #Terminating if there is no active tab
    if not self.tabWidget or not params_manager:
        return None
    
    #Predetermined Font
    fonts = self.cfg_session.index.get('prede_font')
    font = fonts.get('editor-font', 'Segoe UI')
    size = fonts.get('editor-size', 10)
    formated_font = QFont(font, size)
    
    #Creating a label and input field for the parameter
    name = f'{key}'
    _label = QLabel(name)
    _label.setObjectName(f'lbl_{name}')
    _label.setFont(formated_font)
    
    _input = QLineEdit()
    _input.setPlaceholderText('None')
    _input.setObjectName(f'qle_{name}')
    _input.setFont(formated_font)
    #Function that adjusts the width to the content
    def adjust_width():
        padding = 15
        fm = _input.fontMetrics()
        text_width = fm.horizontalAdvance(_input.text() or _input.placeholderText())
        _input.setFixedWidth(text_width+padding)
    #Connecting the textChanged signal to adjust_width
    _input.textChanged.connect(adjust_width)
    _input.textChanged.connect(self.paramDefiner)
    _input.setText(value)
    _input.setProperty('empty', True if value.strip()=='' else False)
    
    #Creating a horizontal layout for the label and input
    pair_layout = QHBoxLayout()
    pair_layout.setContentsMargins(0, 0, 0, 0) #(Iz,Ar,De,Ab)
    pair_layout.setSpacing(0)
    pair_layout.addWidget(_label)
    pair_layout.addWidget(_input)
    #Creating a container widget for the previous layout
    container = QWidget()
    container.setLayout(pair_layout)
    #Adding the container to the params_manager layout
    params_manager.layout().addWidget(container)
    #Initialize size
    adjust_width()

#Function to search the text
def findSearched(self, textEditor, cls='n', *args):
    searchWidget = self.dict_MySearchWidget.get(textEditor.objectName, None)
    if searchWidget:
        textF = searchWidget.qle_textSearch.text()
        if cls == 'n':
            status = textEditor.find(textF, QTextDocument.FindFlag(0))
            if status == False:
                textEditor.moveCursor(QTextCursor.MoveOperation.Start)
                textEditor.find(textF, QTextDocument.FindFlag(0))
        elif cls == 'p':
            status = textEditor.find(textF, QTextDocument.FindFlag.FindBackward)
            if status == False:
                textEditor.moveCursor(QTextCursor.MoveOperation.End)
                textEditor.find(textF, QTextDocument.FindFlag.FindBackward)
            return status
    
#Function to replace one of the elements as determined by the user
def replaceOne(self, textEditor, *args):
    searchWidget = self.dict_MySearchWidget.get(textEditor.objectName, None)
    if searchWidget:
        textR = searchWidget.qle_textReplace.text()
        cursor = textEditor.textCursor()
        selected_text = cursor.selectedText()
        if selected_text:
            cursor.insertText(textR)
            status = self.findSearched(textEditor, cls='n')
            return status
        else:
            status = self.findSearched(textEditor, cls='n')
            return status

#Function to replace all elements as determined by the user
def replaceAll(self, textEditor, *args):
    searchWidget = self.dict_MySearchWidget.get(textEditor.objectName, None)
    if searchWidget:
        textF = searchWidget.qle_textSearch.text()
        textR = searchWidget.qle_textReplace.text()
        actualCursor = textEditor.textCursor()
        textEditor.moveCursor(QTextCursor.MoveOperation.Start)
        status = textEditor.find(textF, QTextDocument.FindFlag(0))
        while status:
            cursor = textEditor.textCursor().insertText(textR)
            status = textEditor.find(textF, QTextDocument.FindFlag(0))
        textEditor.setTextCursor(actualCursor)

#Features to search
def searchText(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    textEditor = self.current_etlEditor
    #Disabling multicursor mode
    if textEditor.multiCursorEnabled:
        textEditor.stopMultiCursor()

    #Creating cursor to determine selection
    cursor = textEditor.textCursor()
    selectedText = cursor.selectedText()
    selectedText = '' if '\n' in selectedText else selectedText
    #Checking if self.MySearchWidget already exists
    if not self.dict_MySearchWidget.get(textEditor.objectName, None):
        #Instantiating Search
        self.MySearchWidget = MySearchWidget(textEditor)
        self.MySearchWidget.setStyleSheet( self.dict_styledSheets['MySearchWidget'] )
        #Adding instance to search engine dictionary
        self.dict_MySearchWidget[textEditor.objectName] = self.MySearchWidget
        #Making connections
        self.MySearchWidget.endSearching.connect(partial(self.closeMySearchWidget, textEditor))
        self.MySearchWidget.returnKeyF.connect(partial(self.findSearched, textEditor, 'n'))
        self.MySearchWidget.upBoton.connect(partial(self.findSearched, textEditor, 'p'))
        self.MySearchWidget.downBoton.connect(partial(self.findSearched, textEditor, 'n'))
        self.MySearchWidget.reemOne.connect(partial(self.replaceOne, textEditor))
        self.MySearchWidget.reemAll.connect(partial(self.replaceAll, textEditor))
        #Parenting to anchor the window
        parent = textEditor.parentWidget().parentWidget()
        parent.splitterMoved.connect(lambda : self.moveMySearchWidget(textEditor))
        self.MySearchWidget.setParent(textEditor)
        top_right = textEditor.mapToGlobal(textEditor.rect().topRight())
        #Showing window and defining search text
        self.MySearchWidget.myShow()
        self.MySearchWidget.qle_textSearch.setText(selectedText)
        self.MySearchWidget.qle_textSearch.setFocus()
    else:
        self.dict_MySearchWidget[textEditor.objectName].qle_textSearch.setText(selectedText)
        self.dict_MySearchWidget[textEditor.objectName].qle_textSearch.setFocus()


#Function to move the search window as the parent spliter moves
def moveMySearchWidget(self, textEditor, *args):
    for element in self.dict_MySearchWidget.keys():
        searchWidget = self.dict_MySearchWidget.get(element, None)
        if searchWidget:
            searchWidget.myMove(textEditor)

#Function to close dependencies created with the search engine
def closeMySearchWidget(self, textEditor, *args):
    searchWidget = self.dict_MySearchWidget.get(textEditor.objectName, None)
    if searchWidget:
        self.dict_MySearchWidget.pop(textEditor.objectName, None)

#Functions replace the replace text button
def replaceText(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    textEditor = self.current_etlEditor
    self.searchText()
    searchWidget = self.dict_MySearchWidget.get(textEditor.objectName, None)
    
    self.MySearchWidget.fm_replace.show()
    self.MySearchWidget.bt_showReplace.setEnabled(False)
    self.MySearchWidget.setGeometry(self.MySearchWidget.geometry().x()
                    , self.MySearchWidget.geometry().y()
                    , 400, 80)
    #Modifying the visual style of replace
    searchWidget.fm_search.setProperty('search', False)
    searchWidget.fm_search.style().unpolish(searchWidget.fm_search)
    searchWidget.style().polish(searchWidget.fm_search)

#Function to comment or uncomment text
def commentText(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    textEditor = self.current_etlEditor
    cursor = textEditor.textCursor()
    cursor.select(QTextCursor.SelectionType.LineUnderCursor)
    line_text = cursor.selectedText()
    if line_text.startswith('--'):
        #Remove '--' from start of line
        textEditor.uncommentSelection()
    else:
        #Insert '--' at the beginning of the line
        textEditor.commentSelection()
    return None

#Function to insert a super comment
def insertSuperComment(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    textEditor = self.current_etlEditor
    cursor = textEditor.textCursor()
    cursor.select(QTextCursor.SelectionType.LineUnderCursor)
    line_text = cursor.selectedText()
    if line_text.startswith('--'):
        #Remove '--' from start of line
        textEditor.uncommentSelection()
        textEditor.commentSelection('#')
    else:
        #Insert '--#' at the beginning of the line
        textEditor.commentSelection('#')
    return None

#Generalized function to search for a specific character
def specialFind(self, character=';', forward=True, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    #going back
    if forward==False:
        textEditor = self.current_etlEditor
        status = textEditor.find(character, QTextDocument.FindFlag.FindBackward)
        if status == False:
            textEditor.moveCursor(QTextCursor.MoveOperation.Start)
            textEditor.find(character, QTextDocument.FindFlag.FindBackward)
    #going forward
    elif forward==True:
        textEditor = self.current_etlEditor
        status = textEditor.find(character, QTextDocument.FindFlag(0))
        if status == False:
            textEditor.moveCursor(QTextCursor.MoveOperation.Start)
            textEditor.find(character, QTextDocument.FindFlag(0))

#Function to select up to previous query
def selectUpToPreviousQuery(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    textEditor = self.current_etlEditor
    #Current position
    pos_start = textEditor.textCursor().position()
    #Going to previous ;
    self.specialFind(';', False)
    #Final position
    pos_end = textEditor.textCursor().position()
    #Selecting route
    cursor = QTextCursor(textEditor.document())
    cursor.setPosition(pos_start+1)
    cursor.setPosition(pos_end, QTextCursor.MoveMode.KeepAnchor)
    textEditor.setTextCursor(cursor)

#Function to select until next query
def selectUpToNextQuery(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    textEditor = self.current_etlEditor
    #Current position
    pos_start = textEditor.textCursor().position()
    #Going to next ; 
    self.specialFind(';', True)
    #Final position
    pos_end = textEditor.textCursor().position()
    #Selecting route
    cursor = QTextCursor(textEditor.document())
    cursor.setPosition(pos_start)
    cursor.setPosition(pos_end-1, QTextCursor.MoveMode.KeepAnchor)
    textEditor.setTextCursor(cursor)

#Function to go to the beginning of the document
def goToStartOfDocument(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    textEditor = self.current_etlEditor
    cursor = QTextCursor(textEditor.document())
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    textEditor.setTextCursor(cursor)

#Function to go to the end of the document
def goToEndOfDocument(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    textEditor = self.current_etlEditor
    cursor = QTextCursor(textEditor.document())
    cursor.movePosition(QTextCursor.MoveOperation.End)
    textEditor.setTextCursor(cursor)

#Function to add the next occurrence to the selection
def addNextOccurrence(self, *args):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    textEditor = self.current_etlEditor
    cursor = textEditor.textCursor()
    #Only acts if there is any selection
    if cursor.hasSelection():
        #Getting the selection
        findText = cursor.selectedText()
        len_text = len(findText)
        #Looking for the next occurrence
        text = textEditor.toPlainText()
        right_index = text.find(findText, cursor.selectionEnd())
        if right_index != -1:
            #Creating new cursor
            new_cursor = textEditor.textCursor()
            new_cursor.setPosition(right_index)
            new_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len_text)
            #Saving the previous cursor
            if cursor not in textEditor.multiCursorList:
                textEditor.multiCursorList.append(cursor)
            #Setting the new cursor
            textEditor.setTextCursor(new_cursor)
            #Adding the new cursor to the list
            textEditor.multiCursorList.append(new_cursor)
            #Setting multicursor values
            textEditor.multiCursorEnabled = True
            textEditor.blinkState = False
            textEditor.blinkTimer.stop()
            textEditor.viewport().update()
    textEditor.cursorChanged()
   
#Function to create a cursor on each line. At the beginning or at the end
def addCursorsToLineBorders(self, checked, _start=True, *args):
    #Terminating if there is no active tab
    if not self.tabWidget:
        return None
    #Determining direction
    if _start:
        direction = QTextCursor.MoveOperation.StartOfBlock
    else:
        direction = QTextCursor.MoveOperation.EndOfBlock

    textEditor = self.current_etlEditor
    cursor = textEditor.textCursor()
    #It only acts if there is a selection and not multicursor
    if cursor.hasSelection() \
        and cursor.document().findBlock(cursor.selectionStart()).blockNumber() != cursor.document().findBlock(cursor.selectionEnd()).blockNumber() \
        and not textEditor.multiCursorEnabled:

        #Getting the range of the selection
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        #Moving through each of the rows of the cursor
        cursor.setPosition(start)
        cursor.movePosition(direction, QTextCursor.MoveMode.KeepAnchor)
        #Activating multiCursor
        textEditor.multiCursorEnabled = True
        textEditor.multiCursorList.clear()
        #Moving through each line in the selection
        while cursor.position() < end:
            #Creating a copy of the cursor
            new_cursor = textEditor.textCursor()
            new_cursor.setPosition(cursor.position())
            #Moving to the end of the first line block
            new_cursor.movePosition(direction)
            #Saving the new cursor to the list
            textEditor.multiCursorList.append(new_cursor)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            #Moving to the next block and stopping if you have reached the end
            moved = cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
            if not moved:
                break
        #Removing initial selection shading
        cursor.setPosition(new_cursor.position())
        textEditor.setTextCursor(cursor)

        #Resetting blinker
        textEditor.blinkState = True
        textEditor.blinkTimer.start(500)
        textEditor.viewport().update()
        textEditor.cursorChanged()

#Function to create an up or down cursor
def addCursorToAboveBelow(self, checked, _above=True, *args):
    #Terminating if there is no active tab
    if not self.tabWidget:
        return
    #Determining direction of the new cursor
    if _above:
        direction = QTextCursor.MoveOperation.Up
    else:
        direction = QTextCursor.MoveOperation.Down
    #Referencing current cursor
    textEditor = self.current_etlEditor
    #If the multicursor is active
    if textEditor.multiCursorEnabled:
        #Moving through each of the already constructed cursors
        actual_cursors = textEditor.multiCursorList.copy()
        for cursor in actual_cursors:
            new_cursor = QTextCursor(cursor)
            new_cursor.setPosition(cursor.position())
            new_cursor.movePosition(direction)
            #Saving only if it does not exist in the list
            if all(new_cursor.position() != c.position() for c in actual_cursors):
                textEditor.multiCursorList.append(new_cursor)
                #Depending on where it was added, auto-scrolling
                textEditor.setTextCursor(new_cursor)
                textEditor.ensureCursorVisible()
                textEditor.setTextCursor(QTextCursor())
    #If there is multicursor active yet
    else:
        cursor = textEditor.textCursor()
        #Activating multiCursor
        textEditor.multiCursorEnabled = True
        #Creating a new cursor
        new_cursor = textEditor.textCursor()
        new_cursor.setPosition(cursor.position())
        new_cursor.movePosition(direction)
        #Saving cursors in the list
        textEditor.multiCursorList.append(cursor)
        textEditor.multiCursorList.append(new_cursor)

    #Resetting blinker
    textEditor.startMultiCursor()
    textEditor.cursorChanged()