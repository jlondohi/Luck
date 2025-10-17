import os, re

#======================================================
### Creating a css handler to load system configuration
#======================================================
class CssHandler:
    """
    Handler for loading, parsing, and rendering CSS files with variable substitution.

    Attributes:
        userArgs (dict): User-defined arguments for CSS variables.
        css_path (str): Path to the CSS file.
        fullContent (str): Full content of the loaded CSS file.
        content (str): CSS content without the :root block.
        variables (dict): Dictionary of parsed CSS variables.
        rendered (str): CSS content with variables applied.
        userVars (dict): Dictionary of user-defined variables.

    Methods:
        __init__(self, css_path='', **userArgs): Initializes the CssHandler and loads the CSS if the path exists.
        load(self, *args): Loads the CSS file from disk.
        render(self, reParse=False, *args): Renders the CSS content with variables.
        parseVariables(self, fullContent, *args): Parses CSS variables from the :root block.
        applyVariables(self, reParse=False, *args): Applies variables to the CSS content.
        save(self, new_path=None, *args): Saves the current content to disk.
    """

    def __init__(self, css_path='', **userArgs):
        """
        Initializes the CssHandler and loads the CSS file if the path exists.

        Args:
            css_path (str, optional): Path to the CSS file. Defaults to ''.
            **userArgs: User-defined arguments for CSS variables.
        """
        self.userArgs    = userArgs
        self.css_path    = css_path
        self.fullContent = ''
        self.content     = ''
        self.variables   = {}
        self.rendered    = ''
        self.userVars    = {}
        if os.path.exists(css_path):
            self.load()
            self.render()
    
    #Loading the CSS file
    def load(self, *args):
        """
        Loads the CSS file from disk and removes the :root block.

        Args:
            *args: Additional arguments (unused).

        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        #Loading the complete CSS
        try:
            with open(self.css_path, 'r', encoding='utf-8') as file:
                self.fullContent = file.read()
                self.content = re.sub(r':root\s*{[^}]*}', '', self.fullContent, flags=re.DOTALL).strip()
        except FileNotFoundError:
            print(f'The file {self.css_path} was not found.')
            return False
        except Exception as e:
            print(f'Error loading CSS: {e}')
            return False
        else:
            return True
    
    #Function to render according to the variables
    def render(self, reParse=False, *args):
        """
        Renders the CSS content by applying variables.

        Args:
            reParse (bool, optional): Whether to re-parse variables. Defaults to False.
            *args: Additional arguments (unused).
        """
        #If the user defined the variables the system will not look for them
        if not self.variables or reParse:
            #If the document is loaded well it will look for the CSS variables
            self.parseVariables(self.fullContent)
        #Only if they loaded variables or previously applied
        if self.variables:
            self.applyVariables()
        
    #Extracting the variables declared in: ROOT {--Key: Value; }
    def parseVariables(self, fullContent, *args):
        """
        Parses CSS variables declared in the :root block.

        Args:
            fullContent (str): The full CSS content.
            *args: Additional arguments (unused).
        """
        self.variables.clear()
        root_match = re.search(r':root\s*{([^}]*)}', fullContent, re.DOTALL)
        if not root_match:
            return
        #Extracting the variables from the root match
        raw_vars = root_match.group(1)
        #Identifying user variables
        user_vars = re.findall(r'--app:([a-zA-Z0-9_-]+)', raw_vars)
        #Replacing the variables in the raw_vars
        for var in user_vars:
            value = self.userArgs.get(var, '')
            raw_vars = raw_vars.replace(f'--app:{var}', value)
        #Concatenating the final list of variables
        matches = re.findall(r'(--[\w-]+)\s*:\s*([^;]+)', raw_vars)
        #Storing the variables in the dictionary
        for key, value in matches:
            self.variables[key.strip()] = value.strip()
        return

    #Replacing all VAR (-Key) with content in the content.    
    def applyVariables(self, reParse=False, *args):
        """
        Applies parsed variables to the CSS content, replacing var(--key) with their values.

        Args:
            reParse (bool, optional): Whether to re-parse variables. Defaults to False.
            *args: Additional arguments (unused).
        """
        missing_vars = set()
        def replaceVar(match):
            var_name = f'--{match.group(1)}'
            value = self.variables.get(var_name)
            if value is None:
                missing_vars.add(var_name)
                return f'var({var_name})'
            return value
        #Capturing the variable name
        pattern = re.compile(r'var\(--([\w-]+)\)')
        self.rendered = pattern.sub(replaceVar, self.content)
        #Checking for missing variables
        if missing_vars:
            print('Non defined variables:', ', '.join(missing_vars))

    #Saving the current content (without replace) on disk.
    def save(self, new_path=None, *args):
        """
        Saves the current CSS content (without variable replacement) to disk.

        Args:
            new_path (str, optional): Path to save the CSS file. Defaults to None (uses self.css_path).
            *args: Additional arguments (unused).

        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            path = new_path or self.css_path
            with open(path, 'w', encoding='utf-8') as file:
                file.write(self.content)
            return True
        except Exception as exc:
            print(f'Error saving CSS: {exc}.')
            return False