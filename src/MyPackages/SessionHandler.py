import os, pickle, tempfile

#==================================================================
### Creating a session handler to load and save system configuration
#==================================================================
class SessionHandler:
    def __init__(self, parent):
        self.path = parent.cfg_session.index.get('path')
        self.path = os.path.join(tempfile.gettempdir(), 'Luck', 'session') if self.path is None else self.path
        self.user = parent.user
        self.version = parent.version.index.get("version")
        self.session = None
        self.tree = None
        self.history = None

        #Defining the paths
        self.sessionPath = os.path.join(self.path, self.user+".pkl")
        self.sessionTreePath = os.path.join(self.path, self.user+"_tree.pkl")
        self.sessionHistoryPath = os.path.join(self.path, self.user+"_history.pkl")
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
        nested = parent.i18n.getNested
        #MSGs
        self._errorS = nested("log-messages", "error-save")
        self._errorL = nested("log-messages", "error-load")
        
    #Function to load the session
    def loadSession(self):
        try:
            session = pickle.load(open(self.sessionPath, "rb"))
        except Exception as exc:
            self.sessionExists = False
            return None
        else:
            #Note: there are sessions that are incompatible due to the changes made
            version = session.get("version", "0.0.0")
            if self.checkVersion(version):
                return session
            else:
                self.sessionExists = False
                return None
    
    #Function to load the tree
    def loadSessionTree(self):
        try:
            tree = pickle.load(open(self.sessionTreePath, "rb"))
        except Exception as exc:
            print(f"{self._errorL}: {exc}")
            self.sessionTreeExists = False
            return None
        else:
            return tree
    
    #Function to load history
    def loadSessionHistory(self):
        try:
            history = pickle.load(open(self.sessionHistoryPath, "rb"))
        except Exception as exc:
            print(f"{self._errorL}: {exc}")
            self.sessionHistoryExists = False
            return None
        else:
            return history

    #Function to save the session
    def saveSession(self, object):
        #Extracting information from the session
        count = 0
        session = {'version': self.version}
        for tab in object.keys():
            tab_data = object.get(tab)
            #Saving all the information in a dictionary
            session[count] = {
                              'text_editor':tab_data.get('text_editor').toPlainText()
                            , 'text_params':tab_data.get('text_params').toPlainText() 
                            , 'dict_paramsEtl': tab_data.get('dict_paramsEtl')
                            , 'origin': tab_data.get('origin')
                            , 'origin_param': tab_data.get('origin_param')
                            , 'result_data': tab_data.get('result_data')
                            }
            count += 1
        try:
            pickle.dump(session, open(self.sessionPath, "wb"))
        except Exception as exc:
            print(f"{self._errorS}: {exc}")
            self.sessionExists = False
        else:
            self.sessionExists = True
    
    #Function to save the tree
    def saveSessionTree(self, object):
        try:
            pickle.dump(object, open(self.sessionTreePath, "wb"))
        except Exception as exc:
            print(f"{self._errorS}: {exc}")
            self.sessionTreeExists = False
        else:
            self.sessionTreeExists = True
    
    #Function to save history
    def saveSessionHistory(self, object=None):
        try:
            if object==None:
                pickle.dump(self.history, open(self.sessionHistoryPath, "wb"))
            else:
                pickle.dump(object, open(self.sessionHistoryPath, "wb"))
        except Exception as exc:
            print(f"{self._errorS}: {exc}")
            self.sessionHistoryExists = False
        else:
            self.sessionHistoryExists = True
    
    #Function to verify version compatibility
    def checkVersion(self, version):
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