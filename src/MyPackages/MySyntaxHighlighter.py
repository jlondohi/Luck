#Importing own PyQt6 packages
from PyQt6.QtGui import (QTextCharFormat, QColor
    , QFont, QSyntaxHighlighter)
from PyQt6.QtCore import QRegularExpression
#====================================================
### Creating a custom class for SQL syntax highlighting
#====================================================
class MySyntaxHighlighter(QSyntaxHighlighter):
    """
    Custom QSyntaxHighlighter for SQL syntax highlighting with support for color profiles and parenthesis coloring.

    Attributes:
        parent (QWidget): Parent widget.
        syntaxList (object): Syntax list for highlighting.
        profiles (dict): Color and style profiles for highlighting.
        rules (dict): Dictionary of syntax highlighting rules.
        otherColors (dict): Dictionary of color settings for different elements.
        _blocks (int): Number of colored blocks.
        _parenthesis (int): Number of colored parenthesis.
        blocksPalette (list): List of colors for block highlighting.
        parenthesisPalette (list): List of colors for parenthesis highlighting.

    Methods:
        __init__(self, document, syntaxList, parent=None): Initializes the syntax highlighter.
        generateAnalogousColors(hexColor: str, count: int = 5, hueStep: int = 15) -> list: Generates a palette of analogous colors.
        myFormat(self, elemnt:str, upper=False, *args): Returns a QTextCharFormat for a given element.
        myFormatB(self, elemnt:int, *args): Returns a QTextCharFormat for a block element.
        updateSettings(self, profileName, *args): Updates the highlighter settings and rules.
        highlightBlock(self, text, *args): Applies syntax highlighting to a block of text.
        getParenFormat(self, colorIndex: int, *args) -> QTextCharFormat: Returns a QTextCharFormat for parenthesis coloring.
    """
    def __init__(self, document, syntaxList, parent=None):
        """
        Initializes the syntax highlighter with the given document, syntax list, and parent.

        Args:
            document (QTextDocument): The document to highlight.
            syntaxList (object): Syntax list for highlighting.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(document)
        self.parent = parent
        self.syntaxList = syntaxList
        #Loading profiles
        profileName = self.parent.cfg_session.index.get('internal_profile')
        self.profiles = self.parent.dict_profiles[profileName]
        #Running the rule generator with its formats
        self.rules = []
        self.updateSettings(profileName)
        
    #Function to create an analog color palette
    @staticmethod
    def generateAnalogousColors(hexColor: str, count: int = 5, hueStep: int = 15) -> list:
        """
        Generates a list of analogous colors based on a base color.

        Args:
            hexColor (str): The base color in hex format.
            count (int, optional): Number of colors to generate. Defaults to 5.
            hueStep (int, optional): Step size for hue shift. Defaults to 15.

        Returns:
            list: List of color hex strings.
        """
        base = QColor(hexColor)
        h, s, l, _ = base.getHsl()
        half = count // 2
        offsets = [i for i in range(-half, half + 1)]  # [-2, -1, 0, 1, 2]
        #Resorting: 0 (base), -1, 1, -2, 2...
        orderedOffsets = sorted(offsets, key=lambda x: (abs(x), x))
        colors = []
        for i in orderedOffsets:
            newHue = (h + i * hueStep) % 360
            c = QColor()
            c.setHsl(newHue, s, l)
            colors.append(c.name())
        return colors
    
    #Function to load and set Qt format
    def myFormat(self, elemnt:str, upper=False, *args):
        """
        Returns a QTextCharFormat for the given element.

        Args:
            elemnt (str): The element key for color lookup.
            upper (bool, optional): Whether to use uppercase formatting. Defaults to False.
            *args: Additional arguments (unused).

        Returns:
            QTextCharFormat: The configured text format.
        """
        color = self.otherColors[elemnt]
        format = QTextCharFormat()
        format.setForeground(QColor(color[0]))
        format.setFontWeight(QFont.Weight.Bold) if color[1] else format.setFontWeight(QFont.Weight.Normal)
        if upper:
            if color[2]:
                format.setFontCapitalization(QFont.Capitalization.AllUppercase)
        return format
    
    #Function to load and set Qt format for blocks
    def myFormatB(self, elemnt:int, *args):
        """
        Returns a QTextCharFormat for a block element.

        Args:
            elemnt (int): Index for the block color.
            *args: Additional arguments (unused).

        Returns:
            QTextCharFormat: The configured text format.
        """
        color = list(self.otherColors['block_format'])
        color[0] = self.blocksPalette[elemnt]
        format = QTextCharFormat()
        format.setForeground(QColor(color[0]))
        format.setFontWeight(QFont.Weight.Bold) if color[1] else format.setFontWeight(QFont.Weight.Normal)
        return format

    def updateSettings(self, profileName, *args):
        """
        Updates the highlighter settings and rules based on the given profile name.

        Args:
            profileName (str): The profile name to use.
            *args: Additional arguments (unused).
        """
        #Getting the default profile
        self.profiles = self.parent.dict_profiles[profileName]
        ##Getting colors for the Highlighter
        self.otherColors = self.profiles['other_colors']
        #Number of Numbered Blocks
        self._blocks = self.parent.cfg_app.index.get('max-colored-blocks', 11)
        self._parenthesis = self.parent.cfg_app.index.get('max-colored-parenthesis', 11)
        base_color = self.otherColors['block_format'][0]
        self.blocksPalette = self.generateAnalogousColors(base_color, count=self._blocks)
        base_color = self.otherColors['parenthesis'][0]
        self.parenthesisPalette = self.generateAnalogousColors(base_color, count=self._parenthesis)
        
        #Note: be careful, the order entered in rules matters
        rules = {}

        #Adding unique formats
        #-------------------------
        sensitive = QRegularExpression.PatternOption.CaseInsensitiveOption
        #Semicolon
        rules['PyC'] = (QRegularExpression(r'\;', sensitive), self.myFormat('semicolon'))
        #Numbers
        rules['Numbers'] = (QRegularExpression(r'\b\d+\b', sensitive), self.myFormat('numbers'))
        #User-defined syntax lists
        count = 0
        for elemnt in self.syntaxList.index.keys():
            #Concatenating all the elements that belong to the pattern (| means OR)
            pattern = '|'.join(self.syntaxList.index[elemnt])
            #Defining format set
            set_ = (QRegularExpression(r'\b({})\b'.format(pattern), sensitive), self.myFormat(elemnt, True))
            rules[f'List{count}'] = set_
            count += 1
        #Strings
        rules['String1'] = (QRegularExpression(r"'([^']*)'", sensitive), self.myFormat('strings')) #Between ''
        rules['String2'] = (QRegularExpression(r'"([^"]*)"', sensitive), self.myFormat('strings')) #Between ""
        #In parameters
        rules['Par'] = (QRegularExpression(r'\{([^{}]*)\}', sensitive), self.myFormat('parameter_format'))
        #Comments
        format = self.myFormat('comment_format')
        rules['Coment1'] = (QRegularExpression(r'--[^\n]*', sensitive), format) #Started with --
        rules['Coment2I'] = (QRegularExpression(r'/\*.*'), format) #Content started with /*
        #Blocks
        format = self.myFormat('block_format')
        rules['Bloques'] = (QRegularExpression(r'--#([^0-9]|$)[^\n]*', sensitive), format) #Started with --#
        #Numbered Blocks
        format = self.myFormatB(self._blocks-1)
        rules['Bloques_i'] = (QRegularExpression(r'--#\d+[^\n]*', sensitive), format) #Started with --# and a number
        for i in range(self._blocks):
            format = self.myFormatB(i)
            rules[f'Bloque_{i}'] = (QRegularExpression(rf'--#{i}(?!\d)[^\n]*', sensitive), format) #Started with --#i

        #Bringing rules to the classroom slot
        self.rules = rules
        return None

    def highlightBlock(self, text, *args):
        """
        Applies syntax highlighting to a block of text.

        Args:
            text (str): The text block to highlight.
            *args: Additional arguments (unused).
        """
        #Base editor format
        default_format = QTextCharFormat()
        
        #Formatting parenthesis
        #----------------------
        block_data = self.currentBlock().userData()
        if block_data is not None:
            for p in block_data.parens:
                fmt = self.getParenFormat(p.color)
                self.setFormat(p.col, 1, fmt)

        #Formatting according to rules
        #-----------------------------
        for key in self.rules.keys():
            char_format = self.rules[key][1]
            regex = self.rules[key][0]
            match = regex.match(text)
            special_format = char_format.foreground().color()
            special_format.setAlpha(128)  #Opacity

            while match.hasMatch():
                index = match.capturedStart()
                length = match.capturedLength() 
                self.setFormat(index, length, char_format)
                #Finding the next match
                match = regex.match(text, match.capturedEnd())

    def getParenFormat(self, colorIndex: int, *args) -> QTextCharFormat:
        """
        Returns a QTextCharFormat for parenthesis coloring.

        Args:
            colorIndex (int): Index for the parenthesis color.
            *args: Additional arguments (unused).

        Returns:
            QTextCharFormat: The configured text format for parenthesis.
        """
        format = QTextCharFormat()

        #Obtaining the color palette for parentheses from the topic configuration
        palette = self.parenthesisPalette
        bold = self.otherColors['parenthesis'][1]
        error_color = bold = self.otherColors['error'][0]
        error_bold= self.otherColors['error'][1]

        #If there is imbalance, special color will be used, for example red
        if colorIndex == 999:
            format.setForeground(QColor(error_color))
            format.setFontWeight(QFont.Weight.Bold if error_bold else QFont.Weight.Normal)
            return format

        #Appling a cyclic color if the index is greater than the number of colors
        colorCode = palette[colorIndex % len(palette)]
        format.setForeground(QColor(colorCode))

        #Appling bold style if you configure like this
        format.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        return format





