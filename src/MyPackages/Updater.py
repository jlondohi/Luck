import sys, os, jwt, time, requests, subprocess
from PyQt6.QtCore import QObject

#==============================================================================
### Creating Updater (Execution in second thread)
#==============================================================================
class Updater(QObject):
    def __init__(self, parent):
        super().__init__()
        self.server_url = ''
        self.i18n = parent.i18n
        self.version = 'v0.0.0'
        self.latest = None

        self.APP_ID = '1405177'
        self.INSTALLATION_ID = '71235730'
        self.PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAortXnufwOfAxCBmh8y0ZsabXNgcNQ4kmOLqfznRg95yLZoQ0
2mVJ8OrL8Rf2gkpB/d2HJjJtt7m/vOBk3I5XTJsmozpOXI1674cboaIHIBHk0uTe
Wkgx4xBssApri0q9AgJMDLB1mYLSW3Yc0sRYqoibpJyBswZoaGRYUV1BGix7TZ8n
W6ZwPjRnHH5BdkRNjJ3H43/Oyh9jvFiiYxsKCr1ayQesohX5j1+93z2iX61rI2OK
hUAe9VMFGVIAgxfSF+ZXSgwLrp3Z9azXCJqeAH0rysVDpuFYOhTzTtSy9/2G2JQd
368eKxm42UWYRuBCyR2rl68JXbtpPxSV8pfiuQIDAQABAoIBAC0hJXCVRCLdQMvN
SAOHi2ugKGj8VapYG7h50R3RWp7w1BwPKBU1J+dfRkXLbnq9m0WLLRLjw1fDdLAt
zur3srA1CucToW27cs+AuaH+rFkxfTMbc6q4ANXG1U2Q5jhP9tDa0DpoqYR0KmBh
BidReoF4tylUmgeLDGN/CJsv8IEQSaLAZ5G//Z4dShDh4E9cGZhNTnJSHgU5dYK6
N8pjH19fw1aGA7vusDcIK5dgjLxMXhcJiNNi5TAOZKtmImp0lV0tlZoJ5EqPdNLH
0Io2wM53M+COrP607KDyaKmTVbfGNwBkdbqYm8WKN6WK33bfqWzEqVFhjAfa1aL5
nJ7x6bECgYEA1YdlBMD+7/UI1cufGyMjM2dNTwCy1j+yj0zcoLbDv/k5eBhUzc6/
CcMB2KhCaGgXqK5zA66xny+ehWM3ZOaPpOV62eYbEV3vfBfYJp544iEfU2y145/A
ohwn+U2hi+QfahO0oXTOWA4WrsXsZVx9rywiQi4xZZ313N+tyAFcRH0CgYEAwxlt
o/mqbPkx/OzPhsNpUWkmhATAmWPL6MIHKW1sWadhc3gDuvqwG8pjsJIDNhFRPkn0
4YjLtKYsjTU9jllRJdykKHKG1y4a9XLxVYWYDMoVZlYbsSO8cpgHzOr8w+bPTD3x
jkND9Q63KMjttskZikv59bNtI9XCvQo9DBteV+0CgYA047GA6PD8rLwAgMwrI5vv
epHqlKi3atWmqwonAL4hyfCTL6upwqENIPFPIfY4+DeL/5HbgqTaYigor/ejlXxV
AsZYPKfNuG++VAWlIzGcCUpCFrZC6GoFfWXlWXY/OUUSuEjQiScnJm414i54uN0k
y5C8xcZUfjjM+daIqNWa3QKBgQCufvfJSWxcuyUyiruyVOTFo76HJZj9mHywWZn+
O5hFN6e5lwX/HmiU8pfnPTESErsPcyZK8gcANAB068F6p/gkXQuWAZkIrHwAPCYN
z8cG6Vfqh+mMreHGvKN9bE9XCAEwt9Zs30zQybCYEd5LNeJaB0oxr6FWA8KBQb8I
LRJcoQKBgDlPCDiRNpSK8p9MySYxjjoGrKd/FURdDbjsaSEvoi58/cOcf3v3H68z
ORAiga9XrSk4fJXUHnK4AtqlFVIred6qZ1Sn7WQPsBwIlNLhLg27b4hUI3pdslaY
SpmrMzj5MV58E7LpsML3YfEMn3BvIRbSEBm9i+F2rwl+OLcwOxmk
-----END RSA PRIVATE KEY-----"""
        self.OWNER = "jlondohi"
        self.REPO = "Luck_releases"
        
    #Function to know what is the last release (RENDER)
    def checkForUpdate_render(self):
        nested = self.i18n.getNested
        version = "v0.0.0"
        try:
            r = requests.get(f"{self.server_url}/api/latest", timeout=10)
            r.raise_for_status()
            data = r.json()
            web_version = data["version"]
            version = web_version
        except Exception as e:
            version = f'error: {e}'
        else:
            self.version = version
        return version
    
    #Function to know what is the last release (GITHUB)
    def checkForUpdate(self):
        nested = self.i18n.getNested
        try:
            jwt_token = self.createJwt()
            access_token = self.getToken(jwt_token)
            releases = self.getLatestRelease(access_token)

            if not releases:
                self.latest = None
            else:
                self.latest = releases[0] #Github returns the ordered releases (des)
                version = self.latest["tag_name"]

        except Exception as e:
            version = f'error: {e}'
        else:
            self.version = version
        return version    

    #Function to download and update
    def downloadUpdate(self):
        route_actual = os.getcwd()
        if not self.latest:
            return
        
        download_url = self.latest["assets"][0]["browser_download_url"]
        print(download_url)
        self.UpdateAndExit(download_url, route_actual, self.version)

    #Opening a window in CMD to download the new version
    def UpdateAndExit(self, download_url, route_actual, version):
        #Build the command to open CMD and run the update script
        comand = [
            "cmd", "/k",  # /k To keep the window open after running
            f'python Update.py {download_url} {route_actual} {version}'
        ]
        subprocess.Popen(comand)
        sys.exit()  #Close the main program

    #-------------------------------------------------------------------------------
    # Connection functions
    #-------------------------------------------------------------------------------
    def createJwt(self):
        payload = {
            "iat": int(time.time()) - 60,
            "exp": int(time.time()) + (9 * 60), #9 minutes of validity
            "iss": self.APP_ID,
        }
        return jwt.encode(payload, self.PRIVATE_KEY, algorithm="RS256")

    def getToken(self, jwt_token):
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json"
        }
        url = f"https://api.github.com/app/installations/{self.INSTALLATION_ID}/access_tokens"
        r = requests.post(url, headers=headers)
        r.raise_for_status()
        return r.json()["token"]

    def getLatestRelease(self, token):
        url = f"https://api.github.com/repos/{self.OWNER}/{self.REPO}/releases"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        r = requests.get(url, headers=headers)
        releases = r.json()

        return releases