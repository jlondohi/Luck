#Importing own PyQt6 packages
from PyQt6.QtGui import QTextCharFormat, QColor \
    , QFont, QSyntaxHighlighter, QTextFormat
from PyQt6.QtCore import Qt, QRegularExpression

#====================================================
### Creating a custom class for SQL syntax highlighting
#====================================================
class MySyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, cfg_session, cfg_app, syntax_list):
        super().__init__(document)
        self.document = document
        self.cfg_session = cfg_session
        self.cfg_app = cfg_app
        self.syntax_list = syntax_list
        #Loading themes
        theme_name = self.cfg_session.index.get('internal_theme')
        self.themes = self.cfg_app.index.get('list_thems')[theme_name]
        #Running the rule generator with its formats
        self.rules = []
        self.updateSettings(theme_name)
        
    #Function to load and set Qt format
    def myFormat(self, elemnt:str):
        color = self.other_colors[elemnt]
        format = QTextCharFormat()
        format.setForeground(QColor(color[0]))
        format.setFontWeight(QFont.Weight.Bold) if color[1] else format.setFontWeight(QFont.Weight.Normal)
        return format

    def updateSettings(self, theme_name):
        #Getting the default theme
        self.themes = self.cfg_app.index.get('list_thems')[theme_name]
        ##Getting colors for the Highlighter
        self.other_colors = self.themes['other_colors']
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
        cont = 0
        for elemnt in self.syntax_list.index.keys():
            #Concatenating all the elements that belong to the pattern (| means OR)
            pattern = '|'.join(self.syntax_list.index[elemnt])
            #Defining format set
            set_ = (QRegularExpression(r"\b({})\b".format(pattern), sensitive), self.myFormat(elemnt))
            rules[f"List{cont}"] = set_
            cont += 1
        #Strings
        rules["String1"] = (QRegularExpression(r"'([^']*)'", sensitive), self.myFormat("strings")) #Between ''
        rules["String2"] = (QRegularExpression(r'"([^"]*)"', sensitive), self.myFormat("strings")) #Between ""
        #In parameters
        rules["Par"] = (QRegularExpression(r"\{([^{}]*)\}", sensitive), self.myFormat("parameter_format"))
        #Comments
        format = self.myFormat("comment_format")
        rules["Coment1"] = (QRegularExpression(r"--[^\n]*", sensitive), format) #Started with --
        rules["Coment2"] = (QRegularExpression(r"/\*.*$|^.*\*/", sensitive), format) #Content between /**/
        #Blocks
        format = self.myFormat("block_format")
        rules["Bloques"] = (QRegularExpression(r"--#[^\n]*", sensitive), format) #Started with --#
        #Bringing rules to the classroom slot
        self.rules = rules
        return None

    def highlightBlock(self, text):
        #Parentheses highlighting with nesting depth tracking
        stack_izq = []
        color = self.other_colors["parenthesis"]
        color_palette = color[0]
        bolt = color[1]
        color_mapping = {} #Dictionary to map colors based on nesting depth

        for i, char in enumerate(text):
            if char == "(":
                if len(stack_izq) < len(color_palette):
                    color_i = color_palette[len(stack_izq)]
                else:
                    color_i = color_palette[-1]
                color_mapping[i] = QColor(color_i)
                format = QTextCharFormat()
                format.setFontWeight(QFont.Weight.Bold) if bolt else format.setFontWeight(QFont.Weight.Normal)
                format.setForeground(color_mapping[i])
                self.setFormat(i, 1, format)
                stack_izq.append(i)
            elif char == ")":
                if stack_izq:
                    idx_izq = stack_izq.pop()
                    color_i = color_mapping[idx_izq]
                    format = QTextCharFormat()
                    format.setFontWeight(QFont.Weight.Bold) if bolt else format.setFontWeight(QFont.Weight.Normal)
                    format.setForeground(color_i)
                    self.setFormat(i, 1, format) #Apply the same color to the closed parenthesis

        for key in self.rules.keys():           
            char_format = self.rules[key][1]
            regex = self.rules[key][0]
            match = regex.match(text)
            special_format = char_format.foreground().color()
            special_format.setAlpha(128)  # Opacity

            while match.hasMatch():
                index = match.capturedStart()
                length = match.capturedLength()             
                self.setFormat(index, length, char_format)
                #Find the next match
                match = regex.match(text, match.capturedEnd())