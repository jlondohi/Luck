#Importing native packages
import time

#Importing PyQt6 packages
from PyQt6.QtWidgets import (QApplication, QTextEdit
    , QPlainTextEdit, QCompleter)
from PyQt6.QtGui import (QTextCursor, QColor
    , QFont, QPainter, QTextFormat, QPalette, QPen)
from PyQt6.QtCore import (Qt, pyqtSignal, QRect
    , QRect, QStringListModel, QTimer)
from MyPackages import MyLineNumberArea

#Importing SyntaxHighlighter as Class
from MyPackages.MySyntaxHighlighter import MySyntaxHighlighter

#==================================================
### Creating a custom QPlainTextEdit class
#==================================================
class MyPlainTextEdit(QPlainTextEdit):
    """
    Custom QPlainTextEdit with line numbering, syntax highlighting, autocomplete, and multicursor support.

    Signals:
        sizeChanged (QFont): Emitted when the font size changes.
        focusIn (): Emitted when the editor gains focus.
        focusOut (): Emitted when the editor loses focus.
        textReady (object, str): Emitted when typing stops, passing the editor and its text.

    Attributes:
        multiCursorList (list): List of QTextCursor objects for multicursor mode.
        multiCursorEnabled (bool): Whether multicursor mode is enabled.
        searchedWord (str or None): The current searched word for highlighting.
        suppressTextChanged (bool): Flag to suppress textChanged events.
        app (QApplication): Reference to the QApplication instance.
        parent (QWidget): Parent widget.
        i18nNes (callable): Internationalization function.
        tabSpaces (int): Number of spaces per tab.
        lineNumberArea (QWidget): Widget for displaying line numbers.
        previousLine (int): Previously highlighted line number.
        completer (QCompleter): Autocomplete completer.
        completerModel (QStringListModel): Model for autocomplete suggestions.
        levelOne (list): List of autocomplete suggestions.
        blinkTimer (QTimer): Timer for blinking multicursors.
        blinkState (bool): State for blinking cursors.
        contextList (list): List of context positions for highlighting.
        highlighter (MySyntaxHighlighter): Syntax highlighter instance.
        typingTimer (QTimer): Timer for detecting typing pauses.
        reservedShortcuts (set): Set of reserved keyboard shortcuts.
        font (dict): Font configuration.
        internalProfile (str): Name of the internal profile.
        profile (dict): Profile configuration.
        lineColor (QColor): Color for highlighting the current line.
        painterColor (QColor): Background color for the editor.
        fontLineNumer (QFont): Font for line numbers.
        colorNumer (QColor): Color for line numbers.

    Methods:
        __init__(self, syntaxList, autoCompleteList, parent=None): Initializes the editor.
        scrollContentsBy(self, dx, dy, *args): Handles scrolling and re-highlighting.
        onTextChanged(self, *args): Handles textChanged events.
        onTypingStopped(self, *args): Handles typing pause and emits textReady.
        updateSettings(self, *args): Updates editor settings from configuration.
        focusInEvent(self, event, *args): Handles focus in events.
        focusOutEvent(self, event, *args): Handles focus out events.
        lineNumberAreaWidth(self, *args): Returns the width for the line number area.
        updateLineNumberAreaWidth(self, _, *args): Updates the viewport margins for line numbers.
        updateLineNumberArea(self, rect, dy, *args): Updates the line number area.
        resizeEvent(self, event, *args): Handles resize events.
        highlightCurrentLine(self, update=False, *args): Highlights the current line.
        lineNumberAreaPaintEvent(self, event, *args): Paints the line number area.
        wheelEvent(self, event, *args): Handles mouse wheel events for font size changes.
        changeFontSize(self, delta, *args): Changes the font size by delta.
        mouseDoubleClickEvent(self, event, *args): Handles double-click events, especially in multicursor mode.
        mousePressEvent(self, event, *args): Handles mouse press events for multicursor and context menu.
        cursorChanged(self, *args): Updates the status bar with cursor/selection info.
        manageAutocomplete(self, event): Handles autocomplete popup logic.
        keyPressEvent(self, event, *args): Handles key press events, including multicursor and autocomplete logic.
        nextChar(self, cursor=None, *args): Returns the next character after the cursor.
        identifyBlocks(self, *args): Identifies the start and end blocks of the selection.
        indentSelection(self, *args): Indents selected lines.
        unindentSelection(self, *args): Unindents selected lines.
        unindentLine(self, cursor, *args): Unindents a single line.
        commentSelection(self, plus='', *args): Comments selected lines.
        uncommentSelection(self, *args): Uncomments selected lines.
        insertCompletion(self, completion, *args): Inserts an autocomplete completion.
        textUnderCursor(self, *args): Returns the text under the cursor for autocomplete.
        changeWrapMode(self, status, *args): Changes the line wrap mode.
        startMultiCursor(self, *args): Starts multicursor mode.
        stopMultiCursor(self, *args): Stops multicursor mode.
        blinkCursors(self, *args): Handles blinking of multicursors.
        paintEvent(self, event, *args): Paints the editor, including multicursor and search highlights.
    """
    #Personalized signals
    sizeChanged = pyqtSignal(QFont)
    focusIn     = pyqtSignal()
    focusOut    = pyqtSignal()
    textReady = pyqtSignal(object, str)

    def __init__(self, syntaxList, autoCompleteList, parent=None):
        super().__init__()
        #Slots
        self.multiCursorList    = []
        self.multiCursorEnabled  = False
        self.searchedWord       = None
        self.suppressTextChanged = False
        
        self.app = QApplication.instance()
        self.parent = parent
        
        #Language
        self.i18nNes = parent.i18nNes
        _lines = self.i18nNes('status-bar', 'lines')
        
        #Tab spaces
        self.tabSpaces = self.parent.cfg_session.index.get('tab-spaces')

        #Area for line numbering
        self.lineNumberArea = MyLineNumberArea(self)
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
        #Configuring and connecting signals for line numbering
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.blockCountChanged.connect(
            lambda count: self.parent.bt_totalLines.setText(f'{_lines} {count:,}')
        )
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.cursorPositionChanged.connect(self.cursorChanged)
        self.updateLineNumberAreaWidth(0)
        #Slots necessary for proper functioning
        self.previousLine = 0
        self.updateSettings()
        #Setting up autocomplete
        self.completer = QCompleter()
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self.insertCompletion)

        #Loading lists
        self.levelOne = autoCompleteList.index['levelOne']
        #Defining the first list for testing
        self.completerModel = QStringListModel()
        self.completerModel.setStringList(self.levelOne)
        self.completer.setModel(self.completerModel)
        #Functions associated with the flashing cursor in multicursor mode
        self.blinkTimer = QTimer(self)
        self.blinkTimer.setInterval(500)
        self.blinkTimer.timeout.connect(self.blinkCursors)
        self.blinkState = True
        #Definitions for syntax
        self.contextList = []
        #Adding SQL syntax highlighting
        self.highlighter = MySyntaxHighlighter(  self.document(), syntaxList, self.parent )
        #Establishing a timer to respond to changes in text
        self.typingTimer = QTimer(self)
        self.typingTimer.setInterval(0)
        self.typingTimer.setSingleShot(True)
        self.typingTimer.timeout.connect(self.onTypingStopped)
        self.textChanged.connect(self.onTextChanged)

        #Set shortcuts reserved
        self.reservedShortcuts = {
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_A),
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_C),
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_V),
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_X),
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Z),
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Y),
            (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Right),
            (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Left),
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Right),
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Left),
            (Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Right),
            (Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Up),
            (Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Left),
            (Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Down),
            (Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Backtab),  # Shift+Tab
            (Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Tab),
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Tab),
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Home),
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_End),
            (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Home),
            (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_End),
        }

    def scrollContentsBy(self, dx, dy, *args):
        self.suppressTextChanged = True
        super().scrollContentsBy(dx, dy)
        #When making scroll, the visible blocks to restore all the formats are shown.
        viewport = self.viewport()
        visible_rect = viewport.rect()
        top_left = self.cursorForPosition(visible_rect.topLeft())
        bottom_left = self.cursorForPosition(visible_rect.bottomLeft())
        start_block = top_left.block().blockNumber()
        end_block = bottom_left.block().blockNumber()
        highlighter = self.highlighter
        for block_number in range(start_block, end_block + 1):
            block = self.document().findBlockByNumber(block_number)
            if block.isValid():
                highlighter.rehighlightBlock(block)
        self.suppressTextChanged = False
        
    def onTextChanged(self, *args):
        #Handling the changed text suppressor
        if self.suppressTextChanged:
            return
        self.typingTimer.start()

        #Marking the tab as changed
        tab_name = self.parent.tabWidget.currentWidget().objectName
        tab_data = self.parent.tabInfo.get(tab_name)
        if tab_data:
            past = tab_data['saved']
            present = False
            tab_data['saved'] = present
            #Updating only if there was a change
            if past != present:
                #Updating tab toolTips
                self.parent.updateTabTooltips()
                #Updating tab icons
                self.parent.updateTabIcons()
            
    
    def onTypingStopped(self, *args):
        #Note, a time is calculated to dynamically modify Typingtimer Timer
        start = time.perf_counter()
        #Transformando
        plainText = self.toPlainText()
        #Setting with new value the timer
        end = time.perf_counter()
        lasted = int(round((end - start)*1000, 0)+10)
        self.typingTimer.setInterval(lasted)
        self.textReady.emit(self, plainText)
    
    #Function to update the general profile presentation
    def updateSettings(self, *args):
        cfg_session = self.parent.cfg_session
        profile = self.parent.dict_profiles
        self.dict_paramsEtl = {}
        #Extracting font, color and profile information
        self.font = cfg_session.index.get('prede_font')
        self.internalProfile = cfg_session.index.get('internal_profile')
        self.profile = profile[self.internalProfile]
        #Defining colors from here so as not to search for it in each function
        self.lineColor = QColor(self.profile['editor-line-highlight']).lighter(160)
        self.painterColor = QColor(self.profile['editor-background-color'])
        self.fontLineNumer = QFont(self.font['editor-font'], int(self.font['editor-size']-1))
        self.colorNumer = QColor(self.profile['editor-color_num'])

    #Function to emit signal when focus is activated
    def focusInEvent(self, event, *args):
        self.focusIn.emit()
        super().focusInEvent(event)
        
    #Function to emit signal when focus is deactivated
    def focusOutEvent(self, event, *args):
        self.focusOut.emit()
        super().focusOutEvent(event)
        
    #Function to define the size of the area with line number
    def lineNumberAreaWidth(self, *args):
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    #Function to update the size of the area with line number
    def updateLineNumberAreaWidth(self, _, *args):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
    
    #Function to update the area with line number
    def updateLineNumberArea(self, rect, dy, *args):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    #Function for when the rescaling event is activated
    def resizeEvent(self, event, *args):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))
        
    #Highlighted on the current line (all line)
    def highlightCurrentLine(self, update=False, *args):
            currentLine = self.textCursor().blockNumber()
            if (self.previousLine != currentLine) or (update):
                self.previousLine = currentLine
                #Determining selection
                extraSelections = []
                selection = QTextEdit.ExtraSelection()
                selection.format.setBackground(self.lineColor)
                selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                cursor = self.textCursor()
                cursor.clearSelection()
                selection.cursor = cursor
                extraSelections.append(selection)
                self.setExtraSelections(extraSelections)

    #Function that is activated when the paint event is activated
    def lineNumberAreaPaintEvent(self, event, *args):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), self.painterColor)
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        height = self.fontMetrics().height()
        painter.setFont(self.fontLineNumer)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible():
                number = str(blockNumber + 1)
                painter.setPen( self.colorNumer )
                painter.drawText(0, int(top), int(self.lineNumberArea.width()), int(height), Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
            blockNumber += 1
    
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
        current_font = self.document().defaultFont()
        font_size = current_font.pointSizeF()
        #Adjust font size
        font_size += delta
        #Set the new font with the modified size
        new_font = QFont(current_font)
        new_font.setPointSizeF(font_size)
        self.setFont(new_font)
        #Saving the new size in the config file
        self.parent.cfg_session.index.get('prede_font')['editor-size'] = int(font_size)
        self.sizeChanged.emit(new_font)

    def mouseDoubleClickEvent(self, event, *args):
        #If the event was a double click within a multicursor, the position is modified
        if self.multiCursorEnabled:
            self.cursorChanged()
            cursor = self.multiCursorList[-1]
            cursor.movePosition(QTextCursor.MoveOperation.StartOfWord)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfWord, QTextCursor.MoveMode.KeepAnchor)
            self.multiCursorList[-1] = cursor
            return 
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event, *args):
        #Flow if Ctrl + Click is pressed
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.button() == Qt.MouseButton.LeftButton:
            #Obtaining the position of the cursor according to click
            cursor = self.cursorForPosition(event.pos())
            #If the multicursor was disabled, add the current one
            if not self.multiCursorEnabled:
                actual = self.textCursor()
                self.multiCursorList.append(actual)
                self.startMultiCursor()
            #Adding or deleting cursor
            if cursor in self.multiCursorList:
                self.multiCursorList.remove(cursor)
            else:
                self.multiCursorList.append(cursor)
            self.cursorChanged()
            return
        #Route if clicked when the multicursor is activated
        elif self.multiCursorEnabled and event.button() == Qt.MouseButton.LeftButton:
            #Obtaining the position of the cursor according to click
            cursor = self.cursorForPosition(event.pos())
            #Disabling multicursor mode
            self.stopMultiCursor()
        #Setting cursor where to right click
        elif event.button() == Qt.MouseButton.RightButton:
            cursor = self.cursorForPosition(event.pos())
            self.setTextCursor(cursor)
        super().mousePressEvent(event)
    
    #Function to show on status information about selections, cursors or cursor location
    def cursorChanged(self, *args):
        #General Message
        _line, _block   = self.i18nNes('status-bar', 'line-block')
        _selected_lines = self.i18nNes('status-bar', 'selected-lines')
        _cursors        = self.i18nNes('status-bar', 'cursors')
        _selections     = self.i18nNes('status-bar', 'selections')

        text = f'{_line}: {self.textCursor().blockNumber()+1}, {_block}: {self.textCursor().columnNumber()+1}'
        #Message if there are multiple selected lines
        cursor = self.textCursor()
        if cursor.hasSelection() and self.multiCursorEnabled:
            text = f'{_selections}: {len(self.multiCursorList)}'
        elif cursor.hasSelection() and not self.multiCursorEnabled:
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            start_line = cursor.blockNumber()
            cursor.setPosition(end)
            end_line = cursor.blockNumber()
            text = f'{_selected_lines}: {1 + end_line - start_line}'
        #Message if the multicursor is activated
        elif self.multiCursorEnabled:
            text = f'{_cursors}: {len(self.multiCursorList):,}'
        
        #Setting text
        self.parent.bt_lineBlock.setText(text)
    
    #Function to handle the Autocomplete
    def manageAutocomplete(self, event):
        key  = event.key()
        completionPrefix = self.textUnderCursor()
        if len(completionPrefix) < 1:
            self.completer.popup().hide()
        elif len(completionPrefix) >= 3 and completionPrefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completionPrefix)
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
            cr = self.cursorRect()
            cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        
        #PENDING -- It doesn work
        # #If the autocomplete popup is visible, modify the action of the following keys
        # if self.completer.popup().isVisible():
        #     index = self.completer.popup().currentIndex()
        #     if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        #         # nunca autocompletar con enter, siempre salto de línea
        #         self.completer.popup().hide()
        #         event.accept()
        #         return
        #     elif key == Qt.Key.Key_Tab:
        #         if index.isValid():
        #             text = self.completer.completionModel().data(index)
        #             self.insertPlainText(text[len(self.completer.completionPrefix()):])
        #         self.completer.popup().hide()
        #         event.accept()
        #         return
        #     elif key in (Qt.Key.Key_Escape, Qt.Key.Key_Backtab):
        #         self.completer.popup().hide()
        #         event.accept()
        #         return
    
    #Defining event for when special keys are pressed
    def keyPressEvent(self, event, *args):
        mods = event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
        keyCombo = (event.modifiers(), event.key())
        #Enter only if the event has a modifier (Ctrl, Alt or Shift)
        if mods != Qt.KeyboardModifier.NoModifier:
            #Enter only if the modifier is Ctrl or Alt, or combinations with them
            if event.modifiers() != Qt.KeyboardModifier.ShiftModifier:
                #Enter if the key combination is not on the list of reserved shortcuts
                if keyCombo not in self.reservedShortcuts:
                    event.ignore()
                    return
        
        key  = event.key()
        char = event.text()
        #Open-to-close character mapping dictionary
        char_map = {'"': '"', "'": "'", '(': ')', '{': '}', '[': ']'}
        
        #Trim newline at the end of clipboard text
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_V:
            clipboard_mod = self.app.clipboard().text()
            if clipboard_mod[-1] == '\n':
                clipboard_mod = clipboard_mod[:-1]
        
        #Defining autocomplete
        #------------------------
        self.manageAutocomplete(event)
        
        #If multicursor is active
        #------------------------
        if self.multiCursorEnabled:
            self.startMultiCursor()
            #Scape
            if key == Qt.Key.Key_Escape:
                self.stopMultiCursor()  
            #Backspace
            elif key == Qt.Key.Key_Backspace:
                for cursor in self.multiCursorList:
                    if not cursor.isNull() and cursor.hasSelection():
                        cursor.removeSelectedText()
                    else:
                        cursor.deletePreviousChar()
                return
            #Delete
            elif key == Qt.Key.Key_Delete:
                for cursor in self.multiCursorList:
                    if not cursor.isNull() and cursor.hasSelection():
                        cursor.removeSelectedText()
                    else:
                        cursor.deleteChar()
                return
            #Home/Ini
            elif event.modifiers() == Qt.KeyboardModifier.NoModifier and key == Qt.Key.Key_Home:
                for cursor in self.multiCursorList:
                    if not cursor.isNull() and cursor.hasSelection():
                        cursor.movePosition(QTextCursor.MoveOperation.EndOfWord)
                        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
                    else:
                        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                return
            #End
            elif event.modifiers() == Qt.KeyboardModifier.NoModifier and key == Qt.Key.Key_End:
                for cursor in self.multiCursorList:
                    if not cursor.isNull() and cursor.hasSelection():
                        cursor.movePosition(QTextCursor.MoveOperation.EndOfWord)
                        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                    else:
                        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                return
            #Ctrl + Z
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Z:
                undo_count = len(self.multiCursorList)
                for _ in range(undo_count):
                    self.undo()
                return
            #Ctrl + Y
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Y:
                redo_count = len(self.multiCursorList)
                for _ in range(redo_count):
                    self.redo()
                return
            #Ctrl + C
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_C:
                num_cursors = len(self.multiCursorList)
                if num_cursors > 0:
                    concated_text = ''
                    for cursor in self.multiCursorList:
                        concated_text += cursor.selectedText() + '\n'
                    #Removing the last extra line break at the end
                    if concated_text.endswith('\n'):
                        concated_text = concated_text[:-1]
                    #Setting concatenated text to the clipboard
                    clipboard = self.app.clipboard()
                    clipboard.setText(concated_text)
                else:
                    #Handle the case when there are no cursors, if necessary
                    clipboard = self.app.clipboard()
                    clipboard.clear()
                return
            #Ctrl + V
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_V:
                #Copying clipboard
                text = clipboard_mod
                #Counting the number of line breaks
                lines = text.split('\n')
                line_count = len(lines)
                #Counting number of cursors
                num_cursors = len(self.multiCursorList)
                #Comparing both
                if line_count == num_cursors:
                    #If the number of lines is equal to the number of cursors,
                    #paste each line at each cursor
                    for i, cursor in enumerate(self.multiCursorList):
                        if i < line_count:
                            cursor.insertText(lines[i])
                else:
                    #If the number of lines is not equal to the number of cursors,
                    #paste the full text at each cursor
                    for cursor in self.multiCursorList:
                        cursor.insertText(text)
                return
            #Ctrl + Shift + Right
            elif event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and key == Qt.Key.Key_Right:
                for i, cursor in enumerate(self.multiCursorList):
                    cursor.movePosition(QTextCursor.MoveOperation.NextWord, QTextCursor.MoveMode.KeepAnchor)
                    self.multiCursorList[i] = cursor
                return
            #Ctrl + Shift + Left
            elif event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and key == Qt.Key.Key_Left:
                for i, cursor in enumerate(self.multiCursorList):
                    cursor.movePosition(QTextCursor.MoveOperation.PreviousWord, QTextCursor.MoveMode.KeepAnchor)
                    self.multiCursorList[i] = cursor
                return
            #Ctrl + Right
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Right:
                for cursor in self.multiCursorList:
                    cursor.movePosition(QTextCursor.MoveOperation.NextWord)
                return
            #Ctrl + Left
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Left:
                for cursor in self.multiCursorList:
                    cursor.movePosition(QTextCursor.MoveOperation.PreviousWord)
                return
            #Shift + Right
            elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier and key == Qt.Key.Key_Right:
                for i, cursor in enumerate(self.multiCursorList):
                    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
                    self.multiCursorList[i] = cursor
                return
            #Shift + Left
            elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier and key == Qt.Key.Key_Left:
                for i, cursor in enumerate(self.multiCursorList):
                    cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor)
                    self.multiCursorList[i] = cursor
                return
            #Shift + Tab (Unindent)
            elif key == Qt.Key.Key_Backtab:
                for cursor in self.multiCursorList:
                    self.unindentLine(cursor)
                return
            #Shift + Home/Ini
            elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier and key == Qt.Key.Key_Home:
                for cursor in self.multiCursorList:
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
                return
            #Shift + End
            elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier and key == Qt.Key.Key_End:
                for cursor in self.multiCursorList:
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                return
            #Tab (indent)
            elif key == Qt.Key.Key_Tab:
                for cursor in self.multiCursorList:
                    cursor.insertText(' '*self.tabSpaces)
                return        
            #Right
            elif key == Qt.Key.Key_Right:
                for cursor in self.multiCursorList:
                    cursor.movePosition(QTextCursor.MoveOperation.Right)
                return
            #Left
            elif key == Qt.Key.Key_Left:
                for cursor in self.multiCursorList:
                    cursor.movePosition(QTextCursor.MoveOperation.Left)
                return
            #Up
            elif key == Qt.Key.Key_Up:
                indices_a_eliminar = []
                #Iterating over list of cursors to determine which indexes to delete
                for i, cursor in enumerate(self.multiCursorList):
                    if cursor.blockNumber() == 0:
                        indices_a_eliminar.append(i)
                    else:
                        cursor.movePosition(QTextCursor.MoveOperation.Up)

                #Deleting elements by their indexes, in reverse order to avoid index problems
                for index in reversed(indices_a_eliminar):
                    if len(self.multiCursorList)>1:
                        del self.multiCursorList[index]

                #Adjust the main cursor and disable multicursor if necessary
                if len(self.multiCursorList) == 1:
                    self.setTextCursor(self.multiCursorList[0])
                    self.stopMultiCursor()
                return
            #Down
            elif key == Qt.Key.Key_Down:
                indices_a_eliminar = []
                #Iterating over list of cursors to determine which indexes to delete
                for i, cursor in enumerate(self.multiCursorList):
                    if cursor.blockNumber() == cursor.document().blockCount() - 1:
                        indices_a_eliminar.append(i)
                    else:
                        cursor.movePosition(QTextCursor.MoveOperation.Down)

                #Deleting elements by their indexes, in reverse order to avoid index problems
                for index in reversed(indices_a_eliminar):
                    if len(self.multiCursorList)>1:
                        del self.multiCursorList[index]

                #Adjust the main cursor and disable multicursor if necessary
                if len(self.multiCursorList) == 1:
                    self.setTextCursor(self.multiCursorList[0])
                    self.stopMultiCursor()
                return
            #Self-closing characters
            elif char in char_map:
                for cursor in self.multiCursorList:
                    if cursor.hasSelection():
                        selection = cursor.selectedText()
                        cursor.insertText(f'{char}{selection}{char_map[char]}')
                    elif self.nextChar(cursor) == char:
                        cursor.insertText(char)
                    else:
                        #Inserting opening and closing character
                        cursor.insertText(f'{char}{char_map[char]}')
                        #Moving cursor one position to the left
                        cursor.movePosition(QTextCursor.MoveOperation.Left)
                return
            #Avoiding double closure
            elif char in [')', ']', '}']:
                for cursor in self.multiCursorList:
                    if self.nextChar(cursor) == char:
                        #Skipping entering the character and moving to the right
                        cursor.movePosition(QTextCursor.MoveOperation.Right)
                    else:
                        cursor.insertText(char)
                return
            else:
                for cursor in self.multiCursorList:
                    cursor.insertText(event.text())
                self.ensureCursorVisible()
                return
            
        #If the multicursor is not active
        #--------------------------------
        if not self.multiCursorEnabled:
            cursor = self.textCursor()
            #Escape
            if key == Qt.Key.Key_Escape:
                if cursor.hasSelection():
                    # Move the cursor to the start of the selection and delete the visual selection
                    cursor.setPosition(cursor.selectionEnd())
                    self.setTextCursor(cursor)
                    return
            #Ctrl + V
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_V:
                cursor.insertText(clipboard_mod)
                return
            #Enter - maintains indentation
            elif key in(Qt.Key.Key_Return, Qt.Key.Key_Enter):
                cursor_pos = cursor.position()
                #Moving the cursor to the start of the current line
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
                current_line = cursor.selectedText()
                #Clearing the selection
                cursor.clearSelection()
                cursor.setPosition(cursor_pos)
                #Getting the indentation of the current line
                indent = ''
                for char in current_line:
                    if char in [' ', '\t']:
                        indent += char
                    else:
                        break
                #Inserting new line
                cursor.insertText(f'\n{indent}')
                self.ensureCursorVisible()
                return
            #Shift+Tab
            elif key == Qt.Key.Key_Backtab:
                if cursor.hasSelection():
                    self.unindentSelection()
                else:
                    self.unindentLine(cursor)
                return
            #Tab
            elif key == Qt.Key.Key_Tab:
                if cursor.hasSelection():
                    self.indentSelection()
                else:
                    cursor.insertText(' '*self.tabSpaces)
                return
            #Ctrl+Shift+Home
            elif event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and key == Qt.Key.Key_Home:
                cursor.movePosition(QTextCursor.MoveOperation.Start, QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(cursor)
                return
            #Ctrl+Shift+End
            elif event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and key == Qt.Key.Key_End:
                cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(cursor)
                return
            #Inserting automatic opening and closing characters
            elif char in char_map:
                if cursor.hasSelection():
                    selection = cursor.selectedText()
                    cursor.insertText(f'{char}{selection}{char_map[char]}')
                elif self.nextChar() == char:
                    cursor.insertText(char)
                else:
                    #Inserting opening and closing character
                    cursor.insertText(f'{char}{char_map[char]}')
                    #Moving cursor one position to the left
                    cursor.movePosition(QTextCursor.MoveOperation.Left)
                    self.setTextCursor(cursor)
                return
            
            #Deleting next character if the same is entered    
            elif char in [')', ']', '}']:
                next_char = self.nextChar()
                # Checking if next character is equal to character in char_map
                if next_char == char:
                    #Skipping entering the character and moving to the right
                    cursor.movePosition(QTextCursor.MoveOperation.Right)
                    self.setTextCursor(cursor)
                    return
            #Continuing with default actions
            super().keyPressEvent(event)

    #Function to identify the next character
    def nextChar(self, cursor=None, *args):
        if not cursor:
            cursor = self.textCursor()
        #Getting the next character
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
        next_char = cursor.selectedText()
        #Restoring original position
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        return next_char

    #Identifying blocks
    def identifyBlocks(self, *args):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(end)
        end_block = cursor.blockNumber()
        cursor.setPosition(start)
        start_block = cursor.blockNumber()
        return start_block, end_block

    #Managing and identifying multiple lines 
    def indentSelection(self, *args):
        #Identifying selected blocks
        start_block, end_block = self.identifyBlocks()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(cursor.selectionStart())
        #Moving through each block
        for _ in range(start_block, end_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.insertText(' '*self.tabSpaces)
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.endEditBlock()
  
    #Managing and separating multiple lines
    def unindentSelection(self, *args):
        #Identifying selected blocks
        start_block, end_block = self.identifyBlocks()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(cursor.selectionStart())
        
        #Moving through each block
        for _ in range(start_block, end_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            line_text = cursor.block().text()
            if line_text.startswith((' '*self.tabSpaces, '\t')):
                cursor.deleteChar()
            for _ in range(self.tabSpaces):
                line_text = cursor.block().text()
                cursor.deleteChar() if line_text.startswith(' ') else None
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.endEditBlock()

    #Longing for a line
    def unindentLine(self, cursor, *args):
        #Saving the cursor position
        current_position = cursor.position()
        #unindent
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        line_text = cursor.block().text()
        cursor.beginEditBlock()
        count = 0
        if line_text.startswith(' '):
            for _ in range(self.tabSpaces):
                if line_text.startswith(' '):
                    cursor.deleteChar()
                    line_text = cursor.block().text()
                    count += 1
        if line_text.startswith('\t'):
            cursor.deleteChar()
            count += 1
        cursor.endEditBlock()
        #Restoring cursor position
        cursor.setPosition(current_position)
        #Modifying cursor in multicursor list
        if self.multiCursorEnabled:
            for _ in range(count):
                cursor.movePosition(QTextCursor.MoveOperation.Left)

    #Managing and commenting on multiple lines
    def commentSelection(self, plus='', *args):
        #Identifying selected blocks
        start_block, end_block = self.identifyBlocks()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(cursor.selectionStart())
        #Moving through each block
        for _ in range(start_block, end_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.insertText(f'--{plus} ')
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.endEditBlock()
  
    #Managing and separating multiple lines 
    def uncommentSelection(self, *args):
        #Identifying selected blocks
        start_block, end_block = self.identifyBlocks()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(cursor.selectionStart())
        #Moving through each block
        for _ in range(start_block, end_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            line_text = cursor.block().text()
            cursor.deleteChar() if line_text.startswith('--') else None
            cursor.deleteChar() if line_text.startswith('--') else None
            cursor.deleteChar() if line_text.startswith(('-- ','--#')) else None
            cursor.deleteChar() if line_text.startswith(('--# ', '--#-')) else None
            cursor.deleteChar() if line_text.startswith('--#- ') else None
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.endEditBlock()
    
    #Insert autocomplete plugin
    def insertCompletion(self, completion, *args):
        if self.completer.widget() != self:
            return
        cursor = self.textCursor()

        #Getting current cursor position
        cursor_pos = cursor.position()
        #Moving the cursor to the beginning of the word under the cursor
        cursor.movePosition(QTextCursor.MoveOperation.StartOfWord, QTextCursor.MoveMode.KeepAnchor)
        #Getting the text under the cursor
        current_text = cursor.selectedText()
        #Inserting missing autocomplete text
        extra = completion[len(current_text):]
        cursor.clearSelection()
        cursor.setPosition(cursor_pos)
        cursor.insertText(extra)
        self.setTextCursor(cursor)

    #Identifying text under the cursor for autocomplete
    def textUnderCursor(self, *args):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfWord, QTextCursor.MoveMode.KeepAnchor)
        return cursor.selectedText()

    #Changing the mode (Wrap, noWrap)
    def changeWrapMode(self, status, *args):
        if status:
            self.currentWrapMode = QPlainTextEdit.LineWrapMode.WidgetWidth
        elif not status:
            self.currentWrapMode = QPlainTextEdit.LineWrapMode.NoWrap
        self.setLineWrapMode(self.currentWrapMode)

    #Functions associated with the multicursor and its flash
    #-----------------------------------------------------------
    def startMultiCursor(self, *args):
        self.blinkState = True
        self.multiCursorEnabled = True
        self.blinkTimer.start()
        self.setTextCursor(QTextCursor())
        self.viewport().update()
        self.cursorChanged()

    def stopMultiCursor(self, *args):
        self.setTextCursor(self.multiCursorList[0])
        self.multiCursorList.clear()
        self.blinkState = False
        self.multiCursorEnabled = False
        self.blinkTimer.stop()
        self.viewport().update()
        self.cursorChanged()

    def blinkCursors(self, *args):
        self.blinkState = not self.blinkState
        self.viewport().update()

    def paintEvent(self, event, *args):
        super().paintEvent(event)
        painter = QPainter(self.viewport())

        #Painting depending on whether the multicursor is active or not
        ##Multicursor active
        if self.multiCursorEnabled:
            #Orange color with medium transparency
            #For multicursor selection
            color = QColor(255, 165, 0, 127)
            painter.setBrush(color)

            for cursor in self.multiCursorList:
                if cursor.hasSelection():
                    start = cursor.selectionStart()
                    end = cursor.selectionEnd()
                    #Creating a new temporary cursor so as not to modify the original
                    temp_cursor = QTextCursor(cursor)
                    temp_cursor.setPosition(start)
                    rect_start = self.cursorRect(temp_cursor)
                    temp_cursor.setPosition(end)
                    rect_end = self.cursorRect(temp_cursor)
                    #Creating a rectangle that covers the selection
                    selection_rect = QRect(rect_start.topLeft(), rect_end.bottomRight())
                    #Drawing the rectangle with rounded edges without border
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRoundedRect(selection_rect, 2, 2)

                #Drawing the blinking cursor
                rect = self.cursorRect(cursor)
                if self.blinkState:
                    painter.setPen(self.palette().color(QPalette.ColorRole.Text))
                    painter.drawLine(rect.topRight(), rect.bottomRight())
                else:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawLine(rect.topRight(), rect.bottomRight())
        ##Multicursor not active
        else:
            #Coloring self.searchedWord
            if hasattr(self, 'searchedWord') and self.searchedWord:
                doc = self.document()
                cursor = QTextCursor(doc)
                color = QColor(self.profile['other_colors']['searching'])
                color.setAlpha(127)
                painter.setBrush(color)

                while not cursor.isNull() and not cursor.atEnd():
                    cursor = doc.find(self.searchedWord, cursor)
                    if not cursor.isNull():
                        start = cursor.selectionStart()
                        end = cursor.selectionEnd()

                        #Creating a temporary cursor to get the position of the rectangle
                        temp_cursor = QTextCursor(cursor)
                        temp_cursor.setPosition(start)
                        rect_start = self.cursorRect(temp_cursor)
                        temp_cursor.setPosition(end)
                        rect_end = self.cursorRect(temp_cursor)

                        #Creating a rectangle that covers the selection
                        selection_rect = QRect(rect_start.topLeft(), rect_end.bottomRight())

                        #Drawing the yellow rectangle
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawRoundedRect(selection_rect, 2, 2)
        
        #Indifferent to multicursor state
        ##PENDING. Drawing the bottom yellow tilde at contextList positions
        painter.setPen(QPen(QColor('yellow'), 1, Qt.PenStyle.SolidLine))  # Yellow color for the tilde

        if len(self.contextList) > 0:
            for position in self.contextList:
                line = position[2]
                column = position[3]        
        painter.end()