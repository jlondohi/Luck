import sys, os, jwt, time, requests, subprocess, cryptography
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

        self.APP_ID = ''
        self.INSTALLATION_ID = ''
        self.PRIVATE_KEY = ""
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
            jwt_token = self.createJwt()
            access_token = self.getToken(jwt_token)
            releases = self.getLatestRelease(access_token)

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
        
        download_url = self.latest['assets'][0]['browser_download_url']
        self.UpdateAndExit(download_url, route_actual, self.version)

    #Opening a window in CMD to download the new version
    def UpdateAndExit(self, download_url, route_actual, version, *args):
        #Build the command to open CMD and run the update script
        comand = [
            'cmd', '/k',  # /k To keep the window open after running
            f'python Update.py {download_url} {route_actual} {version}'
        ]
        subprocess.Popen(comand)
        sys.exit()  #Close the main program

    #-------------------------------------------------------------------------------
    # Connection functions
    #-------------------------------------------------------------------------------
    def createJwt(self, *args):
        payload = {
            'iat': int(time.time()) - 60,
            'exp': int(time.time()) + (9 * 60), #9 minutes of validity
            'iss': self.APP_ID,
        }
        encode = jwt.encode(payload, self.PRIVATE_KEY, algorithm='RS256')
        return encode

    def getToken(self, jwt_token, *args):
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github+json'
        }
        url = f'https://api.github.com/app/installations/{self.INSTALLATION_ID}/access_tokens'
        r = requests.post(url, headers=headers)
        r.raise_for_status()
        return r.json()['token']

    def getLatestRelease(self, token, *args):
        url = f'https://api.github.com/repos/{self.OWNER}/{self.REPO}/releases'
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        r = requests.get(url, headers=headers)
        releases = r.json()

        return releases