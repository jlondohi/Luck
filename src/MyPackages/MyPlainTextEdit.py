from PyQt6.QtWidgets import QApplication, QTextEdit \
    , QPlainTextEdit, QCompleter
from PyQt6.QtGui import QTextCursor, QColor \
    , QFont, QPainter, QTextFormat, QPalette, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QRect \
    , QRect, QStringListModel, QTimer
from MyPackages import LineNumberArea

#Importing SyntaxHighlighter as Class
from MyPackages.MySyntaxHighlighter import MySyntaxHighlighter

#==================================================
### Creating a custom QPlainTextEdit class
#==================================================
class MyPlainTextEdit(QPlainTextEdit):
    #Personalized signals
    sizeChanged = pyqtSignal(QFont)
    focusIn = pyqtSignal()
    focusOut = pyqtSignal()
    #Personalized slots
    widgetType = "" # "Editor", "Param" or other

    multiCursor_list = []
    multiCursorEnabled = False
    searched_word = None

    def __init__(self, cfg_session, cfg_app, syntax_list, autoComplete_list):
        super().__init__()
        self.app = QApplication.instance()
        #Area for line numbering
        self.lineNumberArea = LineNumberArea(self)
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
        #Configuring and connecting signals for line numbering
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        #Slots necessary for proper functioning
        self.previousLine = 0
        self.updateSettings(cfg_session, cfg_app)
        #Setting up autocomplete
        self.completer = QCompleter()
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self.insertCompletion)
        #Loading lists
        self.levelOne = autoComplete_list.index["levelOne"]
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
        self.context_list = []
        #Adding SQL syntax highlighting.
        # PENDING: It don't need the same highlighter for Params
        # if self.widgetType == "Editor":
        self.highlighter = MySyntaxHighlighter(  self.document(), cfg_session, cfg_app, syntax_list )
        #Establish tabulation width to about 4 spaces
        tab_width = self.fontMetrics().horizontalAdvance('\t') / 2
        self.setTabStopDistance(tab_width)

    #Function to update the general theme presentation
    def updateSettings(self, cfg_session, cfg_app):
        self.cfg_session = cfg_session
        self.cfg_app = cfg_app
        self.dict_paramsEtl = {}
        #Extracting font, color and theme information
        self.font = self.cfg_session.index.get("prede_font")
        self.internal_theme = self.cfg_session.index.get("internal_theme")
        self.theme = self.cfg_app.index.get("list_thems")[self.internal_theme]
        #Defining colors from here so as not to search for it in each function
        self.lineColor = QColor(self.theme["editor-line-highlight"]).lighter(160)
        self.painterColor = QColor(self.theme["editor-background-color"])
        self.fontLineNumer = QFont(self.font["editor-font"], int(self.font["editor-size"]-1))
        self.colorNumer = QColor(self.theme["editor-color_num"])

    #Function to emit signal when focus is activated
    def focusInEvent(self, event):
        self.focusIn.emit()
        super().focusInEvent(event)
        
    #Function to emit signal when focus is deactivated
    def focusOutEvent(self, event):
        self.focusOut.emit()
        super().focusOutEvent(event)
        
    #Function to define the size of the area with line number
    def lineNumberAreaWidth(self):
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    #Function to update the size of the area with line number
    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
    
    #Function to update the area with line number
    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    #Function for when the rescaling event is activated
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))
        
    #Highlighted on the current line
    def highlightCurrentLine(self, update=False):
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
    def lineNumberAreaPaintEvent(self, event):
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
        current_font = self.document().defaultFont()
        font_size = current_font.pointSizeF()
        #Adjust font size
        font_size += delta
        #Set the new font with the modified size
        new_font = QFont(current_font)
        new_font.setPointSizeF(font_size)
        self.setFont(new_font)
        #Saving the new size in the config file
        self.cfg_session.index.get("prede_font")["editor-size"] = int(font_size)
        self.sizeChanged.emit(new_font)

    def mouseDoubleClickEvent(self, event):
        #If the event was a double click within a multicursor, the position is modified
        if self.multiCursorEnabled:
            cursor = self.multiCursor_list[-1]
            cursor.movePosition(QTextCursor.MoveOperation.StartOfWord)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfWord, QTextCursor.MoveMode.KeepAnchor)
            self.multiCursor_list[-1] = cursor
            return 
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        #Flow if Ctrl + Click is pressed
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.button() == Qt.MouseButton.LeftButton:
            #Obtaining the position of the cursor according to click
            cursor = self.cursorForPosition(event.pos())
            #If the multicursor was disabled, add the current one
            if not self.multiCursorEnabled:
                actual = self.textCursor()
                self.multiCursor_list.append(actual)
                self.startMultiCursor()
            #Adding or deleting cursor
            if cursor in self.multiCursor_list:
                self.multiCursor_list.remove(cursor)
            else:
                self.multiCursor_list.append(cursor)
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
    
    #Defining event for when special keys are pressed
    def keyPressEvent(self, event):
        key = event.key()
        char = event.text()
        #Open-to-close character mapping dictionary
        char_map = {'"': '"', "'": "'", '(': ')', '{': '}', '[': ']'}
        
        #Modifying clipboard in case it is being used in parameters.
        ##It is done here so as not to modify the following logic
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_V:
            clipboard_mod = self.app.clipboard().text()
            #Removing \n at the end
            if clipboard_mod[-1] == "\n":
                clipboard_mod = clipboard_mod[:-1]
            #If we are in Param replacing \n with " "
            if self.widgetType != "Editor":
                clipboard_mod = clipboard_mod.replace("\n", " ")

        #Defining autocomplete
        #------------------------
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
        
        #If the autocomplete popup is visible, modify the action of the following keys
        if self.completer.popup().isVisible():
            if key in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                event.ignore()
                return
        
        #If multicursor is active
        #------------------------
        if self.multiCursorEnabled:
            self.startMultiCursor()

            #Escape
            if key == Qt.Key.Key_Escape:
                self.stopMultiCursor()
            #Backspace
            elif key == Qt.Key.Key_Backspace:
                for cursor in self.multiCursor_list:
                    if not cursor.isNull() and cursor.hasSelection():
                        cursor.removeSelectedText()
                    else:
                        cursor.deletePreviousChar()
                return
            #Delete
            elif key == Qt.Key.Key_Delete:
                for cursor in self.multiCursor_list:
                    if not cursor.isNull() and cursor.hasSelection():
                        cursor.removeSelectedText()
                    else:
                        cursor.deleteChar()
                return
            #Ctrl + Z
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Z:
                undo_count = len(self.multiCursor_list)
                for _ in range(undo_count):
                    self.undo()
                return
            #Ctrl + Y
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Y:
                redo_count = len(self.multiCursor_list)
                for _ in range(redo_count):
                    self.redo()
                return
            #Ctrl + C
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_C:
                num_cursors = len(self.multiCursor_list)
                if num_cursors > 0:
                    concated_text = ""
                    for cursor in self.multiCursor_list:
                        concated_text += cursor.selectedText() + "\n"
                    #Removing the last extra line break at the end
                    if concated_text.endswith("\n"):
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
                num_cursors = len(self.multiCursor_list)
                #Comparing both
                if line_count == num_cursors:
                    #If the number of lines is equal to the number of cursors,
                    #paste each line at each cursor
                    for i, cursor in enumerate(self.multiCursor_list):
                        if i < line_count:
                            cursor.insertText(lines[i])
                else:
                    #If the number of lines is not equal to the number of cursors,
                    #paste the full text at each cursor
                    for cursor in self.multiCursor_list:
                        cursor.insertText(text)
                return
            #Ctrl + Shift + Right
            elif event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and key == Qt.Key.Key_Right:
                for i, cursor in enumerate(self.multiCursor_list):
                    cursor.movePosition(QTextCursor.MoveOperation.NextWord, QTextCursor.MoveMode.KeepAnchor)
                    self.multiCursor_list[i] = cursor
                return
            #Ctrl + Shift + Left
            elif event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and key == Qt.Key.Key_Left:
                for i, cursor in enumerate(self.multiCursor_list):
                    cursor.movePosition(QTextCursor.MoveOperation.PreviousWord, QTextCursor.MoveMode.KeepAnchor)
                    self.multiCursor_list[i] = cursor
                return
            #Ctrl + Right
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Right:
                for cursor in self.multiCursor_list:
                    cursor.movePosition(QTextCursor.MoveOperation.NextWord)
                return
            #Ctrl + Left
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Left:
                for cursor in self.multiCursor_list:
                    cursor.movePosition(QTextCursor.MoveOperation.PreviousWord)
                return
            #Ctrl
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Control:
                return
            #Shift + Right
            elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier and key == Qt.Key.Key_Right:
                for i, cursor in enumerate(self.multiCursor_list):
                    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
                    self.multiCursor_list[i] = cursor
                return
            #Shift + Left
            elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier and key == Qt.Key.Key_Left:
                for i, cursor in enumerate(self.multiCursor_list):
                    cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor)
                    self.multiCursor_list[i] = cursor
                return
            #Shift + Tab (Desidentify)
            elif key == Qt.Key.Key_Backtab:
                for cursor in self.multiCursor_list:
                    self.unindentLine(cursor)
                return
            #Shift
            elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier and event.key() == Qt.Key.Key_Shift:
                return
            #Tab (identify)
            elif key == Qt.Key.Key_Tab:
                for cursor in self.multiCursor_list:
                    cursor.insertText("\t")
                return        
            #Right
            elif key == Qt.Key.Key_Right:
                for cursor in self.multiCursor_list:
                    cursor.movePosition(QTextCursor.MoveOperation.Right)
                return
            #Left
            elif key == Qt.Key.Key_Left:
                for cursor in self.multiCursor_list:
                    cursor.movePosition(QTextCursor.MoveOperation.Left)
                return
            #Above
            elif key == Qt.Key.Key_Up:
                indices_a_eliminar = []
                #Iterating over list of cursors to determine which indexes to delete
                for i, cursor in enumerate(self.multiCursor_list):
                    if cursor.blockNumber() == 0:
                        indices_a_eliminar.append(i)
                    else:
                        cursor.movePosition(QTextCursor.MoveOperation.Up)

                #Deleting elements by their indexes, in reverse order to avoid index problems
                for index in reversed(indices_a_eliminar):
                    if len(self.multiCursor_list)>1:
                        del self.multiCursor_list[index]

                #Adjust the main cursor and disable multicursor if necessary
                if len(self.multiCursor_list) == 1:
                    self.setTextCursor(self.multiCursor_list[0])
                    self.stopMultiCursor()
                return
            #Below
            elif key == Qt.Key.Key_Down:
                indices_a_eliminar = []
                #Iterating over list of cursors to determine which indexes to delete
                for i, cursor in enumerate(self.multiCursor_list):
                    if cursor.blockNumber() == cursor.document().blockCount() - 1:
                        indices_a_eliminar.append(i)
                    else:
                        cursor.movePosition(QTextCursor.MoveOperation.Down)

                #Deleting elements by their indexes, in reverse order to avoid index problems
                for index in reversed(indices_a_eliminar):
                    if len(self.multiCursor_list)>1:
                        del self.multiCursor_list[index]

                #Adjust the main cursor and disable multicursor if necessary
                if len(self.multiCursor_list) == 1:
                    self.setTextCursor(self.multiCursor_list[0])
                    self.stopMultiCursor()
                return
            #Self-closing characters
            elif char in char_map:
                for cursor in self.multiCursor_list:
                    if cursor.hasSelection():
                        selection = cursor.selectedText()
                        cursor.insertText(f"{char}{selection}{char_map[char]}")
                    elif self.nextChar(cursor) == char:
                        cursor.insertText(char)
                    else:
                        #Inserting opening and closing character
                        cursor.insertText(f"{char}{char_map[char]}")
                        #Moving cursor one position to the left
                        cursor.movePosition(QTextCursor.MoveOperation.Left)
                return
            #Avoiding double closure
            elif char in [')', ']', '}']:
                for cursor in self.multiCursor_list:
                    if self.nextChar(cursor) == char:
                        #Skipping entering the character and moving to the right
                        cursor.movePosition(QTextCursor.MoveOperation.Right)
                    else:
                        cursor.insertText(char)
                return
            else:
                for cursor in self.multiCursor_list:
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
                cursor.insertText(f"\n{indent}")
                self.ensureCursorVisible()
                return
            #If SHIF+TAB is pressed (Skip)
            elif key == Qt.Key.Key_Backtab:
                if cursor.hasSelection():
                    self.unindentSelection()
                else:
                    self.unindentLine(cursor)
                return
            #If pressed TAB (identify)
            elif key == Qt.Key.Key_Tab:
                if cursor.hasSelection():
                    self.indentSelection()
                else:
                    # cursor.insertText(" " * 4)
                    cursor.insertText("\t")
                return
            #Inserting automatic opening and closing characters
            elif char in char_map:
                if cursor.hasSelection():
                    selection = cursor.selectedText()
                    cursor.insertText(f"{char}{selection}{char_map[char]}")
                elif self.nextChar() == char:
                    cursor.insertText(char)
                else:
                    #Inserting opening and closing character
                    cursor.insertText(f"{char}{char_map[char]}")
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
    def nextChar(self, cursor=None):
        if not cursor:
            cursor = self.textCursor()
        #Getting the next character
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
        next_char = cursor.selectedText()
        #Restoring original position
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        return next_char

    #Identifying blocks
    def identifyBlocks(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(end)
        end_block = cursor.blockNumber()
        cursor.setPosition(start)
        start_block = cursor.blockNumber()
        return start_block, end_block

    #Managing and identifying multiple lines 
    def indentSelection(self):
        #Identifying selected blocks
        start_block, end_block = self.identifyBlocks()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(cursor.selectionStart())
        #Moving through each block
        for _ in range(start_block, end_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.insertText("\t")
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.endEditBlock()
  
    #Managing and separating multiple lines 
    def unindentSelection(self):
        #Identifying selected blocks
        start_block, end_block = self.identifyBlocks()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(cursor.selectionStart())
        #Moving through each block
        for _ in range(start_block, end_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            line_text = cursor.block().text()
            cursor.deleteChar() if line_text.startswith("\t") else None
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.endEditBlock()

    #Longing for a line
    def unindentLine(self, cursor):
        #Saving the cursor position
        current_position = cursor.position()
        #dissent
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        line_text = cursor.block().text()
        cursor.beginEditBlock()
        count = 0
        if line_text.startswith("\t"):
            line_text = cursor.block().text()
            if line_text.startswith("\t"):
                cursor.deleteChar()
                count += 1
        elif line_text.startswith("\t"):
            cursor.deleteChar()
        cursor.endEditBlock()
        #Restoring cursor position
        cursor.setPosition(current_position)
        #Modifying cursor in multicursor list
        if self.multiCursorEnabled:
            for _ in range(count):
                cursor.movePosition(QTextCursor.MoveOperation.Left)

    #Managing and commenting on multiple lines 
    def commentSelection(self):
        #Identifying selected blocks
        start_block, end_block = self.identifyBlocks()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(cursor.selectionStart())
        #Moving through each block
        for _ in range(start_block, end_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.insertText("-- ")
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.endEditBlock()
  
    #Managing and separating multiple lines 
    def uncommentSelection(self):
        #Identifying selected blocks
        start_block, end_block = self.identifyBlocks()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(cursor.selectionStart())
        #Moving through each block
        for _ in range(start_block, end_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            line_text = cursor.block().text()
            cursor.deleteChar() if line_text.startswith("--") else None
            cursor.deleteChar() if line_text.startswith("--") else None
            cursor.deleteChar() if line_text.startswith("-- ") else None
            cursor.deleteChar() if line_text.startswith("--#") else None
            cursor.deleteChar() if line_text.startswith("--#-") else None
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.endEditBlock()
    
    #Insert autocomplete plugin
    def insertCompletion(self, completion):
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
    def textUnderCursor(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfWord, QTextCursor.MoveMode.KeepAnchor)
        return cursor.selectedText()

    #Changing the mode (Wrap, noWrap)
    def changeWrapMode(self, status):
        if self.widgetType == "Editor":
            if status:
                self.currentWrapMode = QPlainTextEdit.LineWrapMode.WidgetWidth
            elif not status:
                self.currentWrapMode = QPlainTextEdit.LineWrapMode.NoWrap
            self.setLineWrapMode(self.currentWrapMode)

    #Functions associated with the multicursor and its flash
    #-----------------------------------------------------------
    def startMultiCursor(self):
        self.blinkState = True
        self.multiCursorEnabled = True
        self.blinkTimer.start()
        self.setCursorWidth(0)
        self.viewport().update()

    def stopMultiCursor(self):
        self.multiCursor_list.clear()
        self.blinkState = False
        self.multiCursorEnabled = False
        self.blinkTimer.stop()
        self.setCursorWidth(1)
        self.viewport().update()

    def blinkCursors(self):
        self.blinkState = not self.blinkState
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())

        #Painting depending on whether the multicursor is active or not
        ##Multicursor active
        if self.multiCursorEnabled:
            #Orange color with medium transparency
            #For multicursor selection
            color = QColor(255, 165, 0, 127)
            painter.setBrush(color)

            for cursor in self.multiCursor_list:
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
            #Coloring self.searched_word
            if hasattr(self, 'searched_word') and self.searched_word:
                doc = self.document()
                cursor = QTextCursor(doc)
                color = QColor(self.theme["other_colors"]["searching"])
                color.setAlpha(127)
                painter.setBrush(color)

                while not cursor.isNull() and not cursor.atEnd():
                    cursor = doc.find(self.searched_word, cursor)
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
        ##PENDING. Drawing the bottom yellow tilde at context_list positions
        painter.setPen(QPen(QColor("yellow"), 1, Qt.PenStyle.SolidLine))  # Yellow color for the tilde

        if len(self.context_list) > 0:
            for position in self.context_list:
                line = position[2]
                column = position[3]        
        painter.end()



        