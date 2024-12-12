#==================================================================
# Author: Julian David Londoño H.
# Title: "Luck" is the name of my beloved departed pet. 
        # The name of this application is a loving tribute that reflects 
        # the energy and joy he brought to my life.
# Date: 2024-03-13
# Version: Beta. Do not share or distribute.
#================================================================== 

import sys, os, ctypes
from datetime import datetime
#Importing own PyQt6 packages
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from MyPackages import YamlHandler
from MyPackages.SplashScreen import SplashScreen

#Add icon to the application
try:
    #By registering system id
    version = YamlHandler("Settings/version.yaml")
    _version = version.index.get('version')
    major_version = _version.split('.')[0]
    myappid = f'luck.luck.{major_version}'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception as exc:
    print("Error: {0}".format(exc))

#Redirecting terminal
log_file = "Luck-Debug.log"
if os.path.exists(log_file):
    with open(log_file, "r") as file:
        lineas = file.readlines()
        if len(lineas) > 1000:
            #If it has more than 1000 lines, we delete the file
            os.remove(log_file)
log_file = open(log_file, "w")
sys.stdout = log_file
print(f"Luck Started {datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")}")

#============================
#Start the application window
#============================
if __name__ == "__main__":
    #Starting application
    app = QApplication( sys.argv )
    
    #Loading home window
    splashScreen = SplashScreen()
    splashScreen.show()
    #Linking system/app shutdown
    sys.exit( app.exec() )

    
