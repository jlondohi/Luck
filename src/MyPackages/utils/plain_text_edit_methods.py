#Importing native packages
import re, os
import bisect
from itertools import accumulate
from functools import partial
from dataclasses import dataclass
from collections import defaultdict

#Importing PyQt6 packages
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextDocument, QTextCursor
#Importing custom classes and methods
from MyPackages import SearchWidget, MyPlainTextEdit, ResultTable

#================================================================== =======================
#Creating functions related to the Scripts tabs (Editor and Param)
#================================================================== =======================
#Function that creates a new tab in the window
def newScriptTab(self, origin = ""):
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
    #Create a new QSplitter to allow workspace adjustment
    splitter_h = QSplitter(Qt.Orientation.Horizontal)
    splitter_v = QSplitter(Qt.Orientation.Vertical)
    #Connecting signal
    splitter_h.splitterMoved.connect(partial(self.applySplitH))
    splitter_v.splitterMoved.connect(partial(self.applySplitV))
    #Text Widget Editor
    text_editor = MyPlainTextEdit(self.cfg_session, self.cfg_app, self.syntax_list, self.autoComplete_list)
    text_editor.widgetType = 'Editor'
    text_editor.changeWrapMode( self.cfg_session.index.get("worldWrap") )
    text_editor.setAcceptDrops(True)
    text_editor.dragEnterEvent = self.dragEnterEvent
    text_editor.dropEvent = self.dropEvent

    text_editor.setPlaceholderText(nested("tab-editor", "pht-editor"))
    text_editor.setStyleSheet( self.dict_styledSheets["editor_styler"] )
    text_editor.setFont( QFont(font["editor-font"], font["editor-size"]) )
    text_editor.sizeChanged.connect(lambda font: self.applyFontSize(font, "editor"))
    #Function to replace context menu
    text_editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    text_editor.customContextMenuRequested.connect(partial(self.showMenu, "assistant"))
    splitter_v.addWidget(text_editor)
    #Wire textChanged signal from text_editor to findSpecialEntries method
    text_editor.textChanged.connect(self.findSpecialEntries)

    #PARAMETERS text widget
    text_params = MyPlainTextEdit(self.cfg_session, self.cfg_app, self.syntax_list, self.autoComplete_list)
    text_params.setPlaceholderText(nested("tab-editor", "pht-param"))
    text_params.widgetType = 'Param'
    text_params.setAcceptDrops(True)
    text_params.dragEnterEvent = self.dragEnterEvent
    text_params.dropEvent = self.dropEventParam
    text_params.setStyleSheet( self.dict_styledSheets["editor_styler"] )
    text_params.setFont( QFont(font["editor-font"], font["editor-size"]) )
    text_params.sizeChanged.connect(lambda font: self.applyFontSize(font, "editor"))
    #PENDING This line may not be necessary. 
    #If commented out and it doesn't seem necessary, it will be deleted.
    # text_params.focusOut.connect(self.findSpecialEntries)
    splitter_v.addWidget(text_params)

    #RESULTS table widget 
    result = ResultTable(self)
    result.setStyleSheet( self.dict_styledSheets["result_styler"] )
    result.setFont( QFont(font["result-font"], font["result-size"]) )
    result.sizeChanged.connect(lambda font: self.applyFontSize(font, "result"))
    
    #concatenating the splitters
    splitter_h.addWidget(splitter_v)
    splitter_h.addWidget(result)
    layoutTab.addWidget(splitter_h)
    text_params.selectionChanged.connect(self.paramDefiner)
    text_params.textChanged.connect(self.paramDefiner)
            
    #Adding all QPlainTextEdit to its list
    self.list_Qtexts.append(text_editor)
    self.list_Qtexts.append(text_params)
    #Adding all results to its list
    self.list_QTable.append(result)
    #Adding all spliters to their respective list
    self.dict_splitters['h'].append(splitter_h)
    self.dict_splitters['v'].append(splitter_v)
    #Adding and activating the new tab
    self.tabWidget.addTab(tab_new, f'{nested("tab-editor", "new")} ({self.num_Stab})')
    self.tabWidget.setCurrentIndex(self.tabWidget.count() - 1)
    #Establishing code for when the command arises from OpenFile
    origin_param = ""
    if origin != "":
        #Loading script
        archivo = open(origin, "r" , encoding='utf-8')
        text_editor.setPlainText( archivo.read() )
        archivo.close()
        #Changing the name of the tab
        origin = origin.replace("\\", "/")
        nombre = origin.rsplit('/', 1)[-1]
        self.tabWidget.setTabText(self.tabWidget.count() - 1, nombre)

        #Checking if the companion file exists
        if os.path.exists(origin+"p"):
            origin_param = origin+"p"
            #Loading parameters
            archivo = open(origin_param, "r" , encoding='utf-8')
            text_params.setPlainText( archivo.read() )
            archivo.close()

    #Store tab information in the tab_info dictionary
    self.tab_info[self.tabWidget.currentWidget().objectName] = {
        'text_editor': text_editor,
        'text_params': text_params,
        'result': result,
        'result_data': {},
        'dict_paramsEtl': {},
        'origin': origin,
        'origin_param': origin_param
    }

    #Setting splitter sizes
    geo = self.cfg_session.index.get('splitter_geo')
    splitter_h.setSizes([int(self.screen_width*geo[0]), int(self.screen_width*geo[1])])
    splitter_v.setSizes([int(self.screen_height*geo[2]), int(self.screen_height*geo[3])])
    #Loading info from the active tab
    self.tabChanged()
    #Running parameter search immediately starts
    self.findSpecialEntries() #Only run after updating tab_info
    #Changing mouse pointer to default state
    self.app.restoreOverrideCursor()

#Function to add the parameters to the corresponding parameter segment
def addParmScriptTab(self, origin):
    #Running if tab is active
    if self.tabWidget:
        text_params = self.current_param
        archivo = open(origin, "r" , encoding='utf-8')
        text_params.setPlainText( archivo.read() )
        archivo.close()
        #Saving the origin of the parameters
        tab_name = self.tabWidget.currentWidget().objectName
        tab_data = self.tab_info.get(tab_name)
        tab_data['origin_param'] = origin

#Creating a function that is responsible for filling the styledSheets
def styler(self, theme_name):
    #Bringing all the information on the selected topic
    theme = self.cfg_app.index.get("list_thems")[theme_name]
    color1 = theme["editor-color_text"]
    color2 = theme["editor-background-color"]
    
    color3 = theme["editor-color_num"]
    color4 = theme["editor-line-highlight"]
    
    color5 = theme["result-color_text"]
    color6 = theme["result-background-color"]
    color7 = theme["result-alternate-background-color"]
    color8 = theme["result-gridline-color"]
    color9 = theme["result-highlight"]
    color10 = theme["result-header-color"]

    color11 = theme["other_colors"]

    #Modifying styleSheets templates
    self.dict_styledSheets["editor_styler"] = \
        self.dict_styleSheets["editor_styler"].format(color1, color2)
    
    self.dict_styledSheets["result_styler"] = \
        self.dict_styleSheets["result_styler"].format(color5, color6, color7, color8, color9, color10)
    
    self.dict_styledSheets["tab_styler"] = \
        self.dict_styleSheets["tab_styler"].format(color10, color1, color2)
    
    self.dict_styledSheets["tree_styler"] = \
        self.dict_styleSheets["tree_styler"].format(color5, color6, color9)

    return None

#Function to apply the new font to all text boxes connected to the signal  
def applyFontSize(self, new_font, cls):
    if cls == "editor":
        #Applying changes to all Qtexts
        for text_widget in self.list_Qtexts:
            text_widget.setFont(new_font)
    elif cls == "result":
        #Applying changes to all QTableView
        for result_widget in self.list_QTable:
            result_widget.setFont(new_font)

#Function to apply formatting according to source
def applyEditorFont(self):
    action = self.sender()
    #Verifying that the action is not null and getting its text
    if action is not None:
        font = self.cfg_session.index.get("prede_font")
        font["editor-font"] = action.text()
        #Applying changes to each plain text widget
        for text_widget in self.list_Qtexts:
            text_widget.setFont( QFont(font["editor-font"], font["editor-size"]) )

#Function to change the font size of Editor and Param
def changeEtlFontSize(self, delta):
    #Running if tab is active
    if self.tabWidget:
        self.current_etl.changeFontSize(delta)
       
#Function that captures user topic selection
def captureThemeFormat(self):
    action = self.sender()
    #Verifying that the action is not null and getting its text
    if action is not None:
        #Modifying default theme in cfg
        theme_name = action.text()
        self.cfg_session.index["internal_theme"] = theme_name
        self.applyThemeFormat(theme_name)
                    
#Function that applies theme as needed
def applyThemeFormat(self, theme_name, cls = "all"):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    self.styler(theme_name)
    if cls == "all":
        #Applying format to the widget
        self.tabWidget.setStyleSheet( self.dict_styledSheets["tab_styler"] )
        #Applying changes to each plain text widget
        for text_widget in self.list_Qtexts:
            #Applying change to window
            text_widget.setStyleSheet( self.dict_styledSheets["editor_styler"] )
            text_widget.updateSettings(self.cfg_session, self.cfg_app)
            #Applying change to each highlighter
            text_widget.highlighter.updateSettings(theme_name)
            text_widget.highlighter.rehighlight()
            text_widget.highlightCurrentLine(True)
        #Applying change to each result widget
        for result_widget in self.list_QTable:
            result_widget.setStyleSheet( self.dict_styledSheets["result_styler"] )
            result_widget.delegate.updatePaint(theme_name)
        #Applying changes to the single tree
        self.dataBaseTree.setStyleSheet( self.dict_styledSheets["tree_styler"] )
    elif cls == "result":
        #Applying format to the widget
        self.tabWidget.setStyleSheet( self.dict_styledSheets["tab_styler"] )
        #Applying change to each result widget
        for result_widget in self.list_QTable:
            result_widget.setStyleSheet( self.dict_styledSheets["result_styler"] )
            result_widget.delegate.updatePaint(theme_name)
        #Applying changes to the single tree
        self.dataBaseTree.setStyleSheet( self.dict_styledSheets["tree_styler"] )
        
#Functions to apply the new sizes within the tab
##Horizontal
def applySplitH(self, pos, cls=""):
    action = self.sender()
    #Verifying that the action is not null and getting its text
    if action is not None:
        ref = self.size().width()-39
        geo = round(pos/ref, 4)
        #Applying changes to horizontal splitter
        for splitter_h in self.dict_splitters['h']:
            splitter_h.setSizes([pos, ref - pos])
        ##Keeping new relationship
        if cls != "expand":
            self.cfg_session.index['splitter_geo'][0] = geo
            self.cfg_session.index['splitter_geo'][1] = 1 - geo

##Vertical
def applySplitV(self, pos, cls=""):
    action = self.sender()
    #Verifying that the action is not null and getting its text
    if action is not None:
        ref = self.size().height()-131
        geo = round(pos/ref, 4)
        #Applying changes to horizontal splitter
        for splitter_v in self.dict_splitters['v']:
            splitter_v.setSizes([pos, ref - pos])
        if cls != "expand":
            #Keeping new relationship
            self.cfg_session.index['splitter_geo'][2] = geo
            self.cfg_session.index['splitter_geo'][3] = 1 - geo

#Defining a function that will search for parenthesis and the etl parameters
def findSpecialEntries(self):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return

    #Getting the name of the current tab and referring
    tab_name = self.tabWidget.currentWidget().objectName
    tab_data = self.tab_info.get(tab_name)
    text_editor = tab_data['text_editor']
    highlighter = text_editor.highlighter

    if tab_data:
        etl_text = text_editor.toPlainText()
        #Searchin params
        self.paramSearcher(tab_data, tab_name, etl_text)
        #seraching for parenthesis. PENDING
        highlighter.skip_highlight = True
        self.parenthesisSearching(tab_data, etl_text)
        highlighter.skip_highlight = False
        highlighter.safeRehighlight()
        
@dataclass
class ParenthesisInfo:
    char:            str            #'(' or ')'
    col:             int            #Column on the line
    unmatched_open:  bool = False
    unmatched_close: bool = False
    color:           int = 0        #0: paired, 1: unbalanced

#Defining a function that will search for parenthesis and store them in a dictionary
def parenthesisSearching(self, tab_data, etl_text: str) -> dict[int, list[ParenthesisInfo]]:
    index = defaultdict(list)

    lines = etl_text.splitlines(keepends=True)
    lengths = [len(line) for line in lines]
    line_offsets = [0] + list(accumulate(lengths[:-1]))

    pattern = re.compile(r"[()]")
    stack = []  #Will contain tuples: (line_num, col, depth)

    for match in pattern.finditer(etl_text):
        char = match.group()
        abs_pos = match.start()
        line_num = bisect.bisect_right(line_offsets, abs_pos) - 1
        col = abs_pos - line_offsets[line_num]

        if char == '(':
            #The current depth is the current length of the battery
            depth = len(stack)
            stack.append((line_num, col, depth))
        else:  # char == ')'
            if stack:
                open_line, open_col, depth = stack.pop()
                info_open = ParenthesisInfo(char='(', col=open_col, color=depth)
                info_close = ParenthesisInfo(char=')', col=col, color=depth)
                index[open_line].append(info_open)
                index[line_num].append(info_close)
            else:
                info = ParenthesisInfo(char=')', col=col, unmatched_close=True, color=999)
                index[line_num].append(info)

    for open_line, open_col, depth in stack:
        info = ParenthesisInfo(char='(', col=open_col, unmatched_open=True, color=999)
        index[open_line].append(info)

    #Saving results in the highlight
    text_editor = tab_data['text_editor']
    highlighter = text_editor.highlighter
    highlighter.parenthesis_dict = dict(index)
    return
         
#Optimized function to look for ETL parameters
def paramSearcher(self, tab_data, tab_name, etl_text):
    """Look for parameters between {} keys and update the dictionary."""
    params_etl = {f"{{{match}}}" for match in re.findall(r'\{([^{}]*)\}', etl_text)}
    #Verifying dictionary
    tab_data.setdefault('dict_paramsEtl', {})
    #Keep only keys that do not already exist in text_etl
    for clave in params_etl - tab_data['dict_paramsEtl'].keys():
        tab_data['dict_paramsEtl'][clave] = None
    #Removing keys that no longer exist in text_etl
    for clave in list(tab_data['dict_paramsEtl'].keys() - params_etl):
        tab_data['dict_paramsEtl'].pop(clave)
    #Update view
    self.updateTextParm(tab_name)

#Defining a function that will give values ​​to the stored ETL parameters
#in a dictionary
def paramDefiner(self):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    #Getting the name of the current tab
    tab_name = self.tabWidget.currentWidget().objectName
    tab_data = self.tab_info.get(tab_name)
    if tab_data:
        cursor_position = tab_data['text_params'].textCursor().position()
        if cursor_position >= 0:
            #Find updated parameters in the PARAMETERS text
            regex = r"'{([^{}']*)}': ('[^']*'|\"[^\"]*\"|\d+\.\d+|\d+),"
            coincidencias = re.findall(regex, tab_data['text_params'].toPlainText() + ",")
            #Update the dict_paramsEtl dictionary of the tab
            for clave, valor in coincidencias:
                #Check if the value is wrapped in quotes
                if valor.startswith(("'", "\"")) and valor.endswith(("'", "\"")):
                    #Treat it as a string, so we remove the quotes
                    valor = valor.strip("'\"")
                elif re.match(r"^\d+\.\d+$", valor):  #Float
                    valor = float(valor)
                elif valor.isdigit():  #Integer
                    valor = int(valor)
                
                #Update the dictionary with the correct type
                tab_data['dict_paramsEtl']["{" + "{}".format(clave) + "}"] = valor

#Defining function that updates display in text_parm
def updateTextParm(self, tab_name):
    tab_data = self.tab_info.get(tab_name)
    if tab_data:
        dict_paramsEtl = tab_data['dict_paramsEtl']
        tab_data['text_params'].setPlainText(str(dict_paramsEtl)[1:-1])

#Function to search the text
def findSearched(self, text_editor, cls="n"):
    buscarWidget = self.searchWidget_dict.get(text_editor.objectName, None)
    if buscarWidget:
        textF = buscarWidget.qle_textBuscar.text()
        if cls == "n":
            status = text_editor.find(textF, QTextDocument.FindFlag(0))
            if status == False:
                text_editor.moveCursor(QTextCursor.MoveOperation.Start)
                text_editor.find(textF, QTextDocument.FindFlag(0))
        elif cls == "p":
            status = text_editor.find(textF, QTextDocument.FindFlag.FindBackward)
            if status == False:
                text_editor.moveCursor(QTextCursor.MoveOperation.End)
                text_editor.find(textF, QTextDocument.FindFlag.FindBackward)
            return status
    
#Function to replace one of the elements as determined by the user
def replaceOne(self, text_editor):
    buscarWidget = self.searchWidget_dict.get(text_editor.objectName, None)
    if buscarWidget:
        textR = buscarWidget.qle_textReem.text()
        cursor = text_editor.textCursor()
        selected_text = cursor.selectedText()
        if selected_text:
            cursor.insertText(textR)
            status = self.findSearched(text_editor, cls="n")
            return status
        else:
            status = self.findSearched(text_editor, cls="n")
            return status

#Function to replace all elements as determined by the user
def replaceAll(self, text_editor):
    buscarWidget = self.searchWidget_dict.get(text_editor.objectName, None)
    if buscarWidget:
        textF = buscarWidget.qle_textBuscar.text()
        textR = buscarWidget.qle_textReem.text()
        actualCursor = text_editor.textCursor()
        text_editor.moveCursor(QTextCursor.MoveOperation.Start)
        status = text_editor.find(textF, QTextDocument.FindFlag(0))
        while status:
            cursor = text_editor.textCursor().insertText(textR)
            status = text_editor.find(textF, QTextDocument.FindFlag(0))
        text_editor.setTextCursor(actualCursor)

#Features to search
def searchText(self):
    #Running if tab is active
    if self.tabWidget:
        text_editor = self.current_etl
        #Creating cursor to determine selection
        cursor = text_editor.textCursor()
        selectedText = cursor.selectedText()
        selectedText = "" if "\n" in selectedText else selectedText
        #Checking if self.searchWidget already exists
        if not self.searchWidget_dict.get(text_editor.objectName, None):
            #Instantiating Search
            self.searchWidget = SearchWidget(text_editor)
            #Adding instance to search engine dictionary
            self.searchWidget_dict[text_editor.objectName] = self.searchWidget
            #Making connections
            self.searchWidget.endSearching.connect(partial(self.closeSearchWidget, text_editor))
            self.searchWidget.returnKeyF.connect(partial(self.findSearched, text_editor, "n"))
            self.searchWidget.upBoton.connect(partial(self.findSearched, text_editor, "p"))
            self.searchWidget.downBoton.connect(partial(self.findSearched, text_editor, "n"))
            self.searchWidget.reemOne.connect(partial(self.replaceOne, text_editor))
            self.searchWidget.reemAll.connect(partial(self.replaceAll, text_editor))
            #Parenting to anchor the window
            parent = text_editor.parentWidget().parentWidget()
            parent.splitterMoved.connect(lambda : self.moveSearchWidget(text_editor))
            self.searchWidget.setParent(text_editor)
            top_right = text_editor.mapToGlobal(text_editor.rect().topRight())
            #Showing window and defining search text
            self.searchWidget.myShow()
            self.searchWidget.qle_textBuscar.setText(selectedText)
            self.searchWidget.qle_textBuscar.setFocus()

#Function to move the search window as the parent spliter moves
def moveSearchWidget(self, text_editor):
    for element in self.searchWidget_dict.keys():
        buscarWidget = self.searchWidget_dict.get(element, None)
        if buscarWidget:
            buscarWidget.myMove(text_editor)

#Function to close dependencies created with the search engine
def closeSearchWidget(self, text_editor):
    buscarWidget = self.searchWidget_dict.get(text_editor.objectName, None)
    if buscarWidget:
        self.searchWidget_dict.pop(text_editor.objectName, None)

#Functions replace the replace text button
def replaceText(self):
    #Running if tab is active
    if self.tabWidget:
        text_editor = self.current_etl
        self.searchText()
        buscarWidget = self.searchWidget_dict.get(text_editor.objectName, None)
        self.searchWidget.fm_reemplazar.show()
        self.searchWidget.bt_showReem.setEnabled(False)
        self.searchWidget.setGeometry(self.searchWidget.geometry().x()
                        , self.searchWidget.geometry().y()
                        , 400, 80)

#Function to comment or uncomment text
def commentText(self):
    #Running if tab is active
    if self.tabWidget:
        text_editor = self.current_etl
        cursor = text_editor.textCursor()
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line_text = cursor.selectedText()
        if line_text.startswith("--"):
            #Remove '--' from start of line
            text_editor.uncommentSelection()
        else:
            #Insert '--' at the beginning of the line
            text_editor.commentSelection()
        return None

#Function to insert a super comment
def insertSuperComment(self):
    #Running if tab is active
    if self.tabWidget:
        text_editor = self.current_etl
        cursor = text_editor.textCursor()
        cursor.insertText("--#")

#Generalized function to search for a specific character
def specialFind(self, character=";", forward=True):
    #Running if tab is active
    if self.tabWidget:
        #going back
        if forward==False:
            text_editor = self.current_etl
            status = text_editor.find(character, QTextDocument.FindFlag.FindBackward)
            if status == False:
                text_editor.moveCursor(QTextCursor.MoveOperation.Start)
                text_editor.find(character, QTextDocument.FindFlag.FindBackward)
        #going forward
        elif forward==True:
            text_editor = self.current_etl
            status = text_editor.find(character, QTextDocument.FindFlag(0))
            if status == False:
                text_editor.moveCursor(QTextCursor.MoveOperation.Start)
                text_editor.find(character, QTextDocument.FindFlag(0))

#Function to select up to previous query
def selectUpToPreviousQuery(self):
    #Running if tab is active
    if self.tabWidget:
        text_editor = self.current_etl
        #Current position
        pos_start = text_editor.textCursor().position()
        #Going to previous ;
        self.specialFind(";", False)
        #Final position
        pos_end = text_editor.textCursor().position()
        #Selecting route
        cursor = QTextCursor(text_editor.document())
        cursor.setPosition(pos_start+1)
        cursor.setPosition(pos_end, QTextCursor.MoveMode.KeepAnchor)
        text_editor.setTextCursor(cursor)

#Function to select until next query
def selectUpToNextQuery(self):
    #Running if tab is active
    if self.tabWidget:
        text_editor = self.current_etl
        #Current position
        pos_start = text_editor.textCursor().position()
        #Going to next ; 
        self.specialFind(";", True)
        #Final position
        pos_end = text_editor.textCursor().position()
        #Selecting route
        cursor = QTextCursor(text_editor.document())
        cursor.setPosition(pos_start)
        cursor.setPosition(pos_end-1, QTextCursor.MoveMode.KeepAnchor)
        text_editor.setTextCursor(cursor)

#Function to go to the beginning of the document
def goToStartOfDocument(self):
    #Running if tab is active
    if self.tabWidget:
        text_editor = self.current_etl
        cursor = QTextCursor(text_editor.document())
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        text_editor.setTextCursor(cursor)

#Function to go to the end of the document
def goToEndOfDocument(self):
    #Running if tab is active
    if self.tabWidget:
        text_editor = self.current_etl
        cursor = QTextCursor(text_editor.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        text_editor.setTextCursor(cursor)

#Function to add the next occurrence to the selection
def addNextOccurrence(self):
    #Running if tab is active
    if self.tabWidget:
        text_editor = self.current_etl
        cursor = text_editor.textCursor()
        #Only acts if there is any selection
        if cursor.hasSelection():
            text_editor.setCursorWidth(0)
            #Getting the selection
            findText = cursor.selectedText()
            len_text = len(findText)
            #Looking for the next occurrence
            text = text_editor.toPlainText()
            right_index = text.find(findText, cursor.selectionEnd())
            if right_index != -1:
                #Creating new cursor
                new_cursor = text_editor.textCursor()
                new_cursor.setPosition(right_index)
                new_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len_text)
                #Saving the previous cursor
                if cursor not in text_editor.multiCursor_list:
                    text_editor.multiCursor_list.append(cursor)
                #Setting the new cursor
                text_editor.setTextCursor(new_cursor)
                #Adding the new cursor to the list
                text_editor.multiCursor_list.append(new_cursor)
                #Setting multicursor values
                text_editor.multiCursorEnabled = True
                text_editor.blinkState = False
                text_editor.blinkTimer.stop()
                text_editor.viewport().update()
   
#Function to create a cursor on each line. At the beginning or at the end
def addCursorsToLineBorders(self, _start=True):
    #Running if tab is active
    if self.tabWidget:
        #Determining direction
        if _start:
            direction = QTextCursor.MoveOperation.StartOfBlock
        else:
            direction = QTextCursor.MoveOperation.EndOfBlock

        text_editor = self.current_etl
        cursor = text_editor.textCursor()
        #It only acts if there is a selection and not multicursor
        if cursor.hasSelection() \
            and cursor.document().findBlock(cursor.selectionStart()).blockNumber() != cursor.document().findBlock(cursor.selectionEnd()).blockNumber() \
            and not text_editor.multiCursorEnabled:

            text_editor.setCursorWidth(0)
            #Getting the range of the selection
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            #Moving through each of the rows of the cursor
            cursor.setPosition(start)
            cursor.movePosition(direction, QTextCursor.MoveMode.KeepAnchor)
            #Activating multiCursor
            text_editor.multiCursorEnabled = True
            text_editor.multiCursor_list.clear()
            #Moving through each line in the selection
            while cursor.position() < end:
                #Creating a copy of the cursor
                new_cursor = text_editor.textCursor()
                new_cursor.setPosition(cursor.position())
                #Moving to the end of the first line block
                new_cursor.movePosition(direction)
                #Saving the new cursor to the list
                text_editor.multiCursor_list.append(new_cursor)
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                #Moving to the next block and stopping if you have reached the end
                moved = cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
                if not moved:
                    break
            #Removing initial selection shading
            cursor.setPosition(new_cursor.position())
            text_editor.setTextCursor(cursor)

            #Resetting blinker
            text_editor.blinkState = True
            text_editor.blinkTimer.start(500)
            text_editor.viewport().update()

#Function to create an up or down cursor
def addCursorToAboveBelow(self, _above=True):
    #Running if tab is active
    if self.tabWidget:
        #Determining direction of the new cursor
        if _above:
            direction = QTextCursor.MoveOperation.Up
        else:
            direction = QTextCursor.MoveOperation.Down
        #Referencing current cursor
        text_editor = self.current_etl
        text_editor.setCursorWidth(0)
        cursor = text_editor.textCursor()
        #If there is no multicursor active yet
        if not text_editor.multiCursorEnabled:
            #Activating multiCursor
            text_editor.multiCursorEnabled = True
            #Creating a new cursor
            new_cursor = text_editor.textCursor()
            new_cursor.setPosition(cursor.position())
            new_cursor.movePosition(direction)
            #Saving cursors in the list
            text_editor.multiCursor_list.append(cursor)
            text_editor.multiCursor_list.append(new_cursor)
        #If the multicursor is active
        else:
            #Moving through each of the already constructed cursors
            actual_cursors = text_editor.multiCursor_list.copy()
            for cursor in actual_cursors:
                new_cursor = text_editor.textCursor()
                new_cursor.setPosition(cursor.position())
                new_cursor.movePosition(direction)
                #Saving only if it does not exist in the list
                if new_cursor not in actual_cursors:
                    text_editor.multiCursor_list.append(new_cursor)
        #Resetting blinker
        text_editor.startMultiCursor()