from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QSize

#================================================================
### Creating the class that contains the QPlainTextEdit numbering    
#================================================================
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor
    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)
    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)