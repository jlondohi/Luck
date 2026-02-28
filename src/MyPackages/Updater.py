import sys, os, requests, subprocess
from PyQt6.QtCore import QObject

#==============================================================================
### Creating Updater (Execution in second thread)
#==============================================================================
class Updater(QObject):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.server_url = ''
        self.version = 'v0.0.0'
        self.latest = None

        self.OWNER = 'jlondohi'
        self.REPO = 'Luck'
        
    #Function to know what is the last release (RENDER)
    def checkForUpdate_render(self, *args):
        nested = self.parent.i18nNes
        version = 'v0.0.0'
        try:
            path = os.path.join(self.server_url, 'api/latest')
            r = requests.get(path, timeout=10)
            r.raise_for_status()
            data = r.json()
            web_version = data['version']
            version = web_version
        except Exception as e:
            version = f'error: {e}'
        else:
            self.version = version
        return version
    
    #Function to know what is the last release (GITHUB)
    def checkForUpdate(self, *args):
        try:
            releases = self.getLatestRelease()

            if not releases:
                self.latest = None
            else:
                self.latest = releases[0] #Github returns the ordered releases (des)
                version = self.latest['tag_name']

        except Exception as e:
            version = f'error: {e}'
        else:
            self.version = version
        return version    

    #Function to download and update
    def downloadUpdate(self, *args):
        route_actual = os.getcwd()
        if not self.latest:
            return
        
        github_url = self.latest['assets'][0]['browser_download_url']
        self.UpdateAndExit(github_url, route_actual, self.version)

    #Opening a window in CMD to download the new version
    def UpdateAndExit(self, github_url, route_actual, version, *args):
        #Build the command to open CMD and run the update script
        comand = [
            'cmd', '/k',  # /k To keep the window open after running
            f'python Update.py {github_url} {route_actual} {version}'
        ]
        subprocess.Popen(comand)
        sys.exit()  #Close the main program

    #-------------------------------------------------------------------------------
    # Connection functions
    #-------------------------------------------------------------------------------
    def getLatestRelease(self, *args):
        url = f'https://api.github.com/repos/{self.OWNER}/{self.REPO}/releases'
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        releases = r.json()

        return releases