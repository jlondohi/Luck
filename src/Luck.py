#==================================================================
# Author: Julian D. Londoño H.
# Title: 'Luck'. It is the name of my beloved departed pet. 
        # The name of this application is a loving tribute that reflects 
        # the energy and joy he brought to my life.
# RIP: 2024-03-13
# Version:
#================================================================== 

import sys, ctypes
#Importing own PyQt6 packages
from PyQt6.QtWidgets import QApplication
from MyPackages import YamlHandler
from MyPackages.MySplashScreen import MySplashScreen

#Add icon to the application
try:
    #By registering system id
    version      = YamlHandler('Settings\\version.yaml')
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
    splash  = MySplashScreen()
    splash.show()
    #Linking system/app shutdown
    sys.exit( app.exec() )

#============================
#Start the application window
#============================
if __name__ == '__main__':
    main()