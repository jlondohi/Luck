import os, pickle, tempfile

#==================================================================
### Creating a session handler to load and save system configuration
#==================================================================
class SessionHandler:
    """
    Handler for loading and saving user session, tree, and history data using pickle serialization.

    Attributes:
        parent (object): Parent object.
        path (str): Directory path for session files.
        user (str): Username for session identification.
        version (str): Application version string.
        session (dict or None): Loaded session data.
        tree (object or None): Loaded tree data.
        history (object or None): Loaded history data.
        sessionPath (str): Path to the session file.
        sessionTreePath (str): Path to the session tree file.
        sessionHistoryPath (str): Path to the session history file.
        sessionExists (bool): Whether the session file exists.
        sessionTreeExists (bool): Whether the session tree file exists.
        sessionHistoryExists (bool): Whether the session history file exists.
        i18nNes (callable): Internationalization function.
        _errorS (str): Localized error message for save errors.
        _errorL (str): Localized error message for load errors.

    Methods:
        __init__(self, parent): Initializes the SessionHandler and loads session data if available.
        loadSession(self, *args): Loads the session data from file.
        loadSessionTree(self, *args): Loads the session tree data from file.
        loadSessionHistory(self, *args): Loads the session history data from file.
        saveSession(self, tabInfo, *args): Saves the current session data to file.
        saveSessionTree(self, object, *args): Saves the tree data to file.
        saveSessionHistory(self, object=None, *args): Saves the history data to file.
        checkVersion(self, version, *args): Checks version compatibility between session and application.
    """
    def __init__(self, parent):
        """
        Initializes the SessionHandler and loads session, tree, and history data if available.

        Args:
            parent (object): The parent object containing configuration and user information.
        """
        self.parent = parent
        self.path = parent.cfg_session.index.get('session_path')
        self.path = os.path.join(tempfile.gettempdir(), 'Luck', 'session') if self.path is None else self.path
        self.user = parent.user
        self.version = parent.version.index.get('version')
        self.session = None
        self.tree = None
        self.history = None

        #Defining the paths
        self.sessionPath = os.path.join(self.path, self.user+'.pkl')
        self.sessionTreePath = os.path.join(self.path, self.user+'_tree.pkl')
        self.sessionHistoryPath = os.path.join(self.path, self.user+'_history.pkl')
        #Confirming if the file exists
        self.sessionExists = os.path.exists(self.sessionPath)
        self.sessionTreeExists = os.path.exists(self.sessionTreePath)
        self.sessionHistoryExists = os.path.exists(self.sessionHistoryPath)
        #Requesting opening if it exists
        if self.sessionExists:
            self.session = self.loadSession()
        if self.sessionTreeExists:
            self.tree = self.loadSessionTree()
        if self.sessionHistoryExists:
            self.history = self.loadSessionHistory()
        
        #Language
        self.i18nNes = parent.i18nNes
        #MSGs
        self._errorS = self.i18nNes('log-messages', 'error-save')
        self._errorL = self.i18nNes('log-messages', 'error-load')
        
    #Function to load the session
    def loadSession(self, *args):
        """
        Loads the session data from the session file.

        Args:
            *args: Additional arguments (unused).

        Returns:
            dict or None: The loaded session data if compatible, otherwise None.
        """
        try:
            session = pickle.load(open(self.sessionPath, 'rb'))
        except Exception as exc:
            self.sessionExists = False
            return None
        else:
            #Note: there are sessions that are incompatible due to the changes made
            version = session.get('version', '0.0.0')
            if self.checkVersion(version):
                return session
            else:
                self.sessionExists = False
                return None
    
    #Function to load the tree
    def loadSessionTree(self, *args):
        """
        Loads the session tree data from the session tree file.

        Args:
            *args: Additional arguments (unused).

        Returns:
            object or None: The loaded tree data, or None if loading fails.
        """
        try:
            tree = pickle.load(open(self.sessionTreePath, 'rb'))
        except Exception as exc:
            print(f'{self._errorL}: {exc}')
            self.sessionTreeExists = False
            return None
        else:
            return tree
    
    #Function to load history
    def loadSessionHistory(self, *args):
        """
        Loads the session history data from the session history file.

        Args:
            *args: Additional arguments (unused).

        Returns:
            object or None: The loaded history data, or None if loading fails.
        """
        try:
            history = pickle.load(open(self.sessionHistoryPath, 'rb'))
        except Exception as exc:
            print(f'{self._errorL}: {exc}')
            self.sessionHistoryExists = False
            return None
        else:
            return history

    #Function to save the session
    def saveSession(self, tabInfo, *args):
        """
        Saves the current session data to the session file.

        Args:
            tabInfo (dict): Dictionary containing tab information to save.
            *args: Additional arguments (unused).
        """
        #Extracting information from the session
        count = 0
        session = {'version': self.version}
        for tab_index in range(self.parent.tabWidget.count()):
            tab_name = self.parent.tabWidget.widget(tab_index).objectName
            #Verifying that the information of the log or ecosystem will not be saved
            tab_text = self.parent.tabWidget.tabText(tab_index)
            if ( tab_text.startswith('Log') or
                tab_text == self.i18nNes('tab-eco', 'eco') ):
                continue
            
            tab_data = tabInfo.get(tab_name)
            #Saving all the information in a dictionary
            template = self.parent.tabInfoTemplate.copy()
            session[count] = template
            for key in template.keys():
                #Exceptions because they are references to widgets
                ##Exception 1
                if key == 'text_editor':
                    session[count][key] = tab_data[key].toPlainText()
                ##Exception 2
                elif key in ('result', 'params_manager'):
                    None
                else:
                    #Save all other values
                    session[count][key] = tab_data[key]
            count += 1
        try:
            pickle.dump(session, open(self.sessionPath, 'wb'))
        except Exception as exc:
            print(f'{self._errorS}: {exc}')
            self.sessionExists = False
        else:
            self.sessionExists = True
    
    #Function to save the tree
    def saveSessionTree(self, object, *args):
        """
        Saves the tree data to the session tree file.

        Args:
            object: The tree object to save.
            *args: Additional arguments (unused).
        """
        if not object:
            return
        
        try:
            pickle.dump(object, open(self.sessionTreePath, 'wb'))
        except Exception as exc:
            print(f'{self._errorS}: {exc}')
            self.sessionTreeExists = False
        else:
            self.tree = object
            self.sessionTreeExists = True
    
    #Function to save history
    def saveSessionHistory(self, object=None, *args):
        """
        Saves the history data to the session history file.

        Args:
            object (optional): The history object to save. If None, saves self.history.
            *args: Additional arguments (unused).
        """
        try:
            if object==None:
                pickle.dump(self.history, open(self.sessionHistoryPath, 'wb'))
            else:
                pickle.dump(object, open(self.sessionHistoryPath, 'wb'))
        except Exception as exc:
            print(f'{self._errorS}: {exc}')
            self.sessionHistoryExists = False
        else:
            self.sessionHistoryExists = True
    
    #Function to verify version compatibility
    def checkVersion(self, version, *args):
        """
        Checks version compatibility between the session and the application.

        Args:
            version (str): Version string from the session.
            *args: Additional arguments (unused).

        Returns:
            bool: True if compatible, False otherwise.
        """
        if version is None:
            return False
        majorS, minorS, _ = map(int, version.split('.'))
        majorA, minorA, _ = map(int, self.version.split('.'))
        versionS = majorS*100 + minorS
        versionA = majorA*100 + minorA
        
        if versionA == versionS:
            return True
        #Old apps versions are not compatible with new sessions
        elif versionA < versionS:
            return False
        #Apss versions are comptaible with some old sessions
        elif versionA > versionS:
            if versionS >= 63:
                return True
            else:
                return False