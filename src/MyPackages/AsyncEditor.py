import re
from itertools import accumulate
from dataclasses import dataclass

from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QTextBlockUserData

#==============================================================================
### Creating AsyncEditor (Execution in second thread)
#==============================================================================
@dataclass
class ParenthesisInfo:
    char:            str            #'(' or ')'
    col:             int            #Column on the line
    unmatched_open:  bool = False
    unmatched_close: bool = False
    color:           int = 0        #0: paired, 1: unbalanced

class ParenthesisBlockData(QTextBlockUserData):
    def __init__(self, parens=None):
        super().__init__()
        self.parens = parens if parens is not None else []

class AsyncEditor(QObject):
    """
    Asynchronous editor processor for parenthesis highlighting in a QTextDocument.

    Inherits from:
        QObject

    Signals:
        finished (object): Emitted when processing is finished, passing the text editor.

    Attributes:
        working (bool): Indicates if the processor is currently working.
        parent (QObject): Parent object.
        paren_pattern (re.Pattern): Compiled regex pattern to match parentheses.

    Methods:
        __init__(self, parent): Initializes the AsyncEditor.
        processTextEditor(self, textEditor, text: str, *args): Processes the text for parenthesis matching.
    """

    finished = pyqtSignal(object)

    def __init__(self, parent):
        """
        Initializes the AsyncEditor.

        Args:
            parent (QObject): The parent QObject.
        """
        super().__init__()
        self.working = False
        self.parent = parent
        self.paren_pattern = re.compile(r'[()]')

    #Function that processes the entire text
    def processTextEditor(self, textEditor, text: str, *args):
        """
        Processes the entire text for parenthesis matching and updates the QTextDocument.

        Args:
            textEditor: The text editor widget containing the document.
            text (str): The text to process.
            *args: Additional arguments (unused).

        Emits:
            finished (object): When processing is complete.
        """
        self.working = True
        
        lines = text.splitlines(keepends=True)
        line_offsets = [0] + list(accumulate(len(l) for l in lines[:-1]))
        results = {}

        stack = []
        line_idx = 0
        next_offset = line_offsets[1] if len(line_offsets) > 1 else len(text)

        for match in self.paren_pattern.finditer(text):
            char = match.group()
            abs_pos = match.start()
            # avanzar hasta línea correcta
            while abs_pos >= next_offset and line_idx < len(lines) - 1:
                line_idx += 1
                next_offset = line_offsets[line_idx+1] if line_idx+1 < len(line_offsets) else len(text)

            col = abs_pos - line_offsets[line_idx]

            if line_idx not in results:
                results[line_idx] = []

            if char == '(':
                depth = len(stack)
                stack.append((line_idx, col, depth))
            else:
                if stack:
                    open_line, open_col, depth = stack.pop()
                    results.setdefault(open_line, []).append(
                        ParenthesisInfo(char='(', col=open_col, color=depth))
                    results[line_idx].append(
                        ParenthesisInfo(char=')', col=col, color=depth))
                else:
                    results[line_idx].append(
                        ParenthesisInfo(char=')', col=col, unmatched_close=True, color=999))

        #Open parenthesis without closing
        for open_line, open_col, depth in stack:
            results.setdefault(open_line, []).append(
                ParenthesisInfo(char='(', col=open_col, unmatched_open=True, color=999))  
        
        #Apply parentheses results to the document
        doc = textEditor.document()
        for line_index, parens in results.items():
            block = doc.findBlockByNumber(line_index)
            if block.isValid():
                userData = block.userData()
                if userData is None:
                    userData = ParenthesisBlockData()
                    block.setUserData(userData)
                userData.parens = parens

        self.working = False
        self.finished.emit(textEditor)