#Importing own PyQt6 packages
from PyQt6.QtGui import QTextCharFormat, QColor \
    , QFont, QSyntaxHighlighter
from PyQt6.QtCore import QRegularExpression
#====================================================
### Creating a custom class for SQL syntax highlighting
#====================================================
class MySyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, cfg_session, cfg_app, syntax_list):
        super().__init__(document)
        self.cfg_session = cfg_session
        self.cfg_app = cfg_app
        # self.cfg_user = cfg_user #PENDING
        self.syntax_list = syntax_list
        #Loading themes
        theme_name = self.cfg_session.index.get('internal_theme')
        self.themes = self.cfg_app.index.get('list_thems')[theme_name]
        #Running the rule generator with its formats
        self.rules = []
        self.updateSettings(theme_name)
        self.parenthesis_dict = {}
        #Creating marker to avoid unnecessarily highlight
        self.skip_highlight = False
        
    #Function to create an analog color palette
    @staticmethod
    def generateAnalogousColors(hexColor: str, count: int = 5, hueStep: int = 15) -> list:
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
    def myFormat(self, elemnt:str, upper=False):
        color = self.other_colors[elemnt]
        format = QTextCharFormat()
        format.setForeground(QColor(color[0]))
        format.setFontWeight(QFont.Weight.Bold) if color[1] else format.setFontWeight(QFont.Weight.Normal)
        if upper:
            if color[2]:
                format.setFontCapitalization(QFont.Capitalization.AllUppercase)
        return format
    
    #Function to load and set Qt format for blocks
    def myFormatB(self, elemnt:int):
        color = list(self.other_colors['block_format'])
        color[0] = self.blocks_palette[elemnt]
        format = QTextCharFormat()
        format.setForeground(QColor(color[0]))
        format.setFontWeight(QFont.Weight.Bold) if color[1] else format.setFontWeight(QFont.Weight.Normal)
        return format

    def updateSettings(self, theme_name):
        #Getting the default theme
        self.themes = self.cfg_app.index.get('list_thems')[theme_name]
        ##Getting colors for the Highlighter
        self.other_colors = self.themes['other_colors']
        #Number of Numbered Blocks
        self._blocks = 11
        self._parenthesis = 11
        # self._blocks = self.cfg_app.get('max-numbered-blocks', 11) #PENDING
        # self._parenthesis = self.cfg_app.get('max-numbered-parenthesis, 11) #PENDING
        base_color = self.other_colors['block_format'][0]
        self.blocks_palette = self.generateAnalogousColors(base_color, count=self._blocks)
        base_color = self.other_colors['parenthesis'][0]
        self.parenthesis_palette = self.generateAnalogousColors(base_color, count=self._parenthesis)
        
        #Note: be careful, the order entered in rules matters
        rules = {}

        #Adding unique formats
        #-------------------------
        sensitive = QRegularExpression.PatternOption.CaseInsensitiveOption
        #Semicolon
        rules["PyC"] = (QRegularExpression(r"\;", sensitive), self.myFormat("semicolon"))
        #Numbers
        rules["Numbers"] = (QRegularExpression(r'\b\d+\b', sensitive), self.myFormat("numbers"))
        #User-defined syntax lists
        count = 0
        for elemnt in self.syntax_list.index.keys():
            #Concatenating all the elements that belong to the pattern (| means OR)
            pattern = '|'.join(self.syntax_list.index[elemnt])
            #Defining format set
            set_ = (QRegularExpression(r"\b({})\b".format(pattern), sensitive), self.myFormat(elemnt, True))
            rules[f"List{count}"] = set_
            count += 1
        #Strings
        rules["String1"] = (QRegularExpression(r"'([^']*)'", sensitive), self.myFormat("strings")) #Between ''
        rules["String2"] = (QRegularExpression(r'"([^"]*)"', sensitive), self.myFormat("strings")) #Between ""
        #In parameters
        rules["Par"] = (QRegularExpression(r"\{([^{}]*)\}", sensitive), self.myFormat("parameter_format"))
        #Comments
        format = self.myFormat("comment_format")
        rules["Coment1"] = (QRegularExpression(r"--[^\n]*", sensitive), format) #Started with --
        rules["Coment2I"] = (QRegularExpression(r"/\*.*"), format) #Content started with /*
        #Blocks
        format = self.myFormat("block_format")
        rules["Bloques"] = (QRegularExpression(r"--#[^0-9][^\n]*", sensitive), format) #Started with --#
        #Numbered Blocks
        format = self.myFormatB(self._blocks-1)
        rules["Bloques_i"] = (QRegularExpression(r"--#\d+[^\n]*", sensitive), format) #Started with --# and a number
        for i in range(self._blocks):
            format = self.myFormatB(i)
            rules[f"Bloque_{i}"] = (QRegularExpression(rf"--#{i}(?!\d)[^\n]*", sensitive), format) #Started with --#i

        #Bringing rules to the classroom slot
        self.rules = rules
        return None

    #Function to avoid a recursive and infinite rehighlighting
    def safeRehighlight(self):
        if getattr(self, '_rehighlighting', False):
            return  # We are already rehighlighting, avoid recursion
        self._rehighlighting = True
        try:
            self.rehighlight()
        finally:
            self._rehighlighting = False
    
    def highlightBlock(self, text):
        if self.skip_highlight:
            return
        #Base editor format
        default_format = QTextCharFormat()
        #Mark to retain comment at the end
        retain = False
        
        #Special format for multiline comments. Previous state to check if it is inside a comment
        if self.previousBlockState() == 1: #1 means it is coming from a comment block
            end_index = text.find("*/", 0)
            #If it come from an open comment, it format the entire line
            self.setFormat(0, len(text), self.rules["Coment2I"][1])
            #If it find the closure (*/) in this block, it reset the state
            if end_index != -1:
                self.setFormat(0, end_index + 2, self.rules["Coment2I"][1])
                self.setCurrentBlockState(0)
                #Restoring base formatting on the rest of the line
                self.setFormat(end_index + 2, len(text) - (end_index + 2), default_format)
                retain = True
            else:
                self.setCurrentBlockState(1)
                #Lefting to avoid applying other rules on comments
                return
        
        #Formatting parenthesis
        line_num = self.currentBlock().blockNumber()
        if line_num in self.parenthesis_dict:
            for p in self.parenthesis_dict[line_num]:
                color = p.color if hasattr(p, 'color') else 0
                fmt = self.getParenFormat(color)
                self.setFormat(p.col, 1, fmt)

        #Formatting according to rules
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
                #Multiline comment
                if str(key).startswith("Coment2I"):
                    self.setCurrentBlockState(1)
                else:
                    self.setCurrentBlockState(0)

        if retain:
            self.setFormat(0, end_index + 2, self.rules["Coment2I"][1])

    def getParenFormat(self, color_index: int) -> QTextCharFormat:
        format = QTextCharFormat()

        #Obtaining the color palette for parentheses from the topic configuration
        palette = self.parenthesis_palette
        bold = self.other_colors['parenthesis'][1]
        error_color = bold = self.other_colors['error'][0]
        error_bold= self.other_colors['error'][1]

        #If there is imbalance, special color will be used, for example red
        if color_index == 999:
            format.setForeground(QColor(error_color))
            format.setFontWeight(QFont.Weight.Bold if error_bold else QFont.Weight.Normal)
            return format

        #Appling a cyclic color if the index is greater than the number of colors
        color_code = palette[color_index % len(palette)]
        format.setForeground(QColor(color_code))

        #Appling bold style if you configure like this
        format.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        return format
                
            

                
        
