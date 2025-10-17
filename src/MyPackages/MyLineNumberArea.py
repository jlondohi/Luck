from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QSize

#================================================================
### Creating the class that contains the QPlainTextEdit numbering    
#================================================================
class MyLineNumberArea(QWidget):
    """
    Widget for displaying line numbers alongside a QPlainTextEdit.

    Attributes:
        codeEditor (QPlainTextEdit): Reference to the associated code editor.

    Methods:
        __init__(self, editor): Initializes the line number area with the given editor.
        sizeHint(self, *args): Returns the recommended size for the widget.
        paintEvent(self, event, *args): Handles the paint event for drawing line numbers.
    """
    def __init__(self, editor):
        """
        Initializes the line number area widget.

        Args:
            editor (QPlainTextEdit): The code editor to associate with this line number area.
        """
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self, *args):
        """
        Returns the recommended size for the line number area.

        Args:
            *args: Additional arguments (unused).

        Returns:
            QSize: The recommended size.
        """
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event, *args):
        """
        Handles the paint event to draw the line numbers.

        Args:
            event (QPaintEvent): The paint event.
            *args: Additional arguments (unused).
        """
        self.codeEditor.lineNumberAreaPaintEvent(event)