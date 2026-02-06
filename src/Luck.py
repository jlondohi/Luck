#==================================================================
# Author: Julian D. Londoño H.
# Title: 'Luck'. It is the name of my beloved departed pet. 
        # The name of this application is a loving tribute that reflects 
        # the energy and joy he brought to my life.
# RIP: 2024-03-13
# Version:
#================================================================== 

import sys, os, ctypes
from pathlib import Path
#Importing own PyQt6 packages
from PyQt6.QtWidgets import QApplication
from MyPackages import YamlHandler
from MyPackages.MySplashScreen import MySplashScreen

baseDir = Path(__file__).resolve().parent
#Creating exceptions for baseDir
if not baseDir.exists():
    raise Exception(f'Base directory does not exist: {baseDir}')
elif not baseDir.is_dir():
    raise Exception(f'Base directory is not a directory: {baseDir}')
elif not os.access(baseDir, os.R_OK):
    raise Exception(f'Base directory is not readable: {baseDir}')
elif not os.access(baseDir, os.X_OK):
    raise Exception(f'Base directory is not executable: {baseDir}')
elif str(baseDir).endswith('_internal'):
    baseDir = baseDir.parent

#Add icon to the application
try:
    #By registering system id
    version      = YamlHandler(str(baseDir / 'Settings' / 'version.yaml'))
    _version     = version.index.get('version')
    majorVersion = _version.split('.')[0]
    myappid      = f'luck.luck.{majorVersion}'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception as exc:
    print('Error: {0}'.format(exc))

def main():
    #Starting application
    app     = QApplication( sys.argv )
    #Loading home window
    splash  = MySplashScreen(baseDir)
    splash.show()
    #Linking system/app shutdown
    sys.exit( app.exec() )

#============================
#Start the application window
#============================
if __name__ == '__main__':
    main()