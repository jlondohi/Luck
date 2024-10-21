import os, pickle

#==================================================================
### Creating a session handler to load and save system configuration
#==================================================================
class SessionHandler:
    def __init__(self, parent):
        self.path = parent.cfg_user.index['ruta_temp_sesion']
        self.user = parent.user
        self._version = parent.version.index.get("version")
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
            self.session = self.loadSesion()
        if self.sessionTreeExists:
            self.tree = self.loadSesionTree()
        if self.sessionHistoryExists:
            self.history = self.loadSesionHistory()
        
    #Function to load the session
    def loadSesion(self):
        try:
            sesion = pickle.load(open(self.sessionPath, "rb"))
        except Exception as exc:
            self.sessionExists = False
            return None
        else:
            return sesion
    
    #Function to load the tree
    def loadSesionTree(self):
        try:
            tree = pickle.load(open(self.sessionTreePath, "rb"))
        except Exception as exc:
            self.sessionTreeExists = False
            return None
        else:
            return tree
    
    #Function to load history
    def loadSesionHistory(self):
        try:
            history = pickle.load(open(self.sessionHistoryPath, "rb"))
        except Exception as exc:
            self.sessionHistoryExists = False
            return None
        else:
            return history

    #Function to save the session
    def saveSesion(self, object):
        #Extracting information from the session
        cont = 0
        sesion = {}
        for tab in object.keys():
            tab_data = object.get(tab)
            #Saving all the information in a dictionary
            sesion[cont] = {  'version': self._version
                            , 'text_editor':tab_data.get('text_editor').toPlainText()
                            , 'text_params':tab_data.get('text_params').toPlainText() 
                            , 'dict_paramsEtl': tab_data.get('dict_paramsEtl')
                            , 'origin': tab_data.get('origin')
                            , 'origin_param': tab_data.get('origin_param')
                            , 'result_data': tab_data.get('result_data')
                            }
            cont += 1
        try:
            pickle.dump(sesion, open(self.sessionPath, "wb"))
        except Exception as exc:
            self.sessionExists = False
        else:
            self.sessionExists = True
    
    #Function to save the tree
    def saveSesionTree(self, object):
        try:
            pickle.dump(object, open(self.sessionTreePath, "wb"))
        except Exception as exc:
            self.sessionTreeExists = False
        else:
            self.sessionTreeExists = True
    
    #Function to save history
    def saveSesionHistory(self, object=None):
        try:
            if object==None:
                pickle.dump(self.history, open(self.sessionHistoryPath, "wb"))
            else:
                pickle.dump(object, open(self.sessionHistoryPath, "wb"))
        except Exception as exc:
            self.sessionHistoryExists = False
        else:
            self.sessionHistoryExists = True