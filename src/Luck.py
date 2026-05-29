#==================================================================
# Author: Julian D. Londoño H.
# Title: 'Luck'. It is the name of my beloved departed pet. 
#        The name of this application is a loving tribute that reflects 
#        the energy and joy he brought to my life.
# RIP: 2024-03-13
# Version:
#================================================================== 

import argparse
import ctypes
import logging
import os
import shutil
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Importación de paquetes propios
from MyPackages import YamlHandler
from MyPackages.MySplashScreen import MySplashScreen

#==============================================================================
#1. ROUTE AND ENVIRONMENT CONFIGURATION
#==============================================================================
#Secure base directory resolution
baseDir = Path(__file__).resolve().parent
if str(baseDir).endswith('_internal'):
    baseDir = baseDir.parent

#Critical File System Infrastructure Validations
if not baseDir.exists():
    raise FileNotFoundError(f"Base directory does not exist: {baseDir}")
if not baseDir.is_dir():
    raise NotADirectoryError(f"Base directory is not a directory: {baseDir}")
if not os.access(baseDir, os.R_OK):
    raise PermissionError(f"Base directory is not readable: {baseDir}")

#Determining standard user paths based on the OS
if sys.platform == "win32": #Windows
    userDir = os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')
elif sys.platform == "darwin": # macOS (Apple)
    userDir = Path.home() / 'Library' / 'Application Support'
else: #Linux y otros sistemas Unix
    userDir = os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share')

#Defining user folders
UserDataDir = Path(userDir) / 'Luck'
settingsDir = UserDataDir / 'Settings'
sessionsDir = UserDataDir / 'Sessions'
logsDir     = UserDataDir / 'Logs'

#Creating user folders
settingsDir.mkdir(parents=True, exist_ok=True)
sessionsDir.mkdir(parents=True, exist_ok=True)
logsDir.mkdir(parents=True, exist_ok=True)

def setupLogging():
    """Configure the registration system (Log) under the international standard."""
    
    #We configure the industrial standard format
    logging.basicConfig(
        filename=str(logsDir / 'Luck-Debug.log'),
        filemode='a',
        level=logging.INFO, #Change to logging.DEBUG if you need to see the internals
        format='%(asctime)s - [%(levelname)s] - %(message)s',
        encoding='utf-8'
    )
    #We silence the noise of third-party libraries (like PyQt)
    logging.getLogger('PyQt6').setLevel(logging.WARNING)

def parseArguments():
    """Manages Command Line Arguments (CLI) natively."""
    parser = argparse.ArgumentParser(
        description="Luck Application - A professional queries management software."
    )
    #Standard arguments you can receive from the console
    parser.add_argument('--debug', action='store_true', help='Run the app in debug mode')   
    return parser.parse_args()

def setApplicationId(app=None):
    """Establishes the identity and icon of the application natively according to the Operating System."""
    #1. Exclusive configuration for WINDOWS (Icon grouping in taskbar)
    if os.name == 'nt':
        try:
            version_path = baseDir / 'Settings' / 'version.yaml'
            if version_path.exists():
                version = YamlHandler(str(version_path))
                _version = version.index.get('version', '1.0.0')
                major_version = _version.split('.')[0]
                myappid = f'luck.luck.{major_version}'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as exc:
            logging.error(f"Failed to register Windows AppUserModelID: {exc}")

def prepareEnvironment():
    """
    Prepare the user environment. Copy the initial settings from the 
    base directory to AppData if files are missing or the version changed.
    """
    
    srcSettingsDir = baseDir / 'Settings'
    #1. If the configuration source folder does not exist, there is nothing to copy
    if not srcSettingsDir.exists():
        logging.warning(f"The configuration source folder was not found in: {srcSettingsDir}")
        return

    #2. Version Control (Comparison between Source and Destination)
    srcVersionPath = srcSettingsDir / 'version.yaml'
    destVersionPath = settingsDir / 'version.yaml'
    
    #By default we assume it changed if we cannot verify it
    versionChanged = True
    
    if srcVersionPath.exists() and destVersionPath.exists():
        try:
            srcVersion  = YamlHandler(str(srcVersionPath)) .index.get('version', '0.0.0')
            destVersion = YamlHandler(str(destVersionPath)).index.get('version', '0.0.0')
            
            #If the versions are exactly the same, it is not mandatory to update by version
            if srcVersion == destVersion:
                versionChanged = False
        except Exception as e:
            logging.error(f"Error comparing configuration versions: {e}")

    #3. Integrity Control (Check if all files are complete)
    srcFiles = [f for f in srcSettingsDir.iterdir() if f.is_file()]
    destFiles = [f for f in settingsDir.iterdir() if f.is_file()]
    
    #Integrity is missing if the destination has fewer files than the source
    isIncomplete = len(destFiles) < len(srcFiles)

    #4. Execute copy/update if any condition is met
    if versionChanged or isIncomplete:
        logging.info(f"Updating Luck configuration files (Reason: Different version={versionChanged}, Incomplete={isIncomplete})")
        
        try:
            for item in srcSettingsDir.iterdir():
                if item.is_file():
                    destFile = settingsDir / item.name
                    
                    # If the version changed, we overwrite EVERYTHING to update parameters.
                    # If only files were missing, we copy only those that do not exist.
                    if versionChanged or not destFile.exists():
                        shutil.copy2(item, destFile)
                        logging.debug(f"File copied/updated: {item.name}")
                        
            logging.info("Environment synchronization completed successfully.")
        except Exception as e:
            logging.error(f"Critical failure when copying configurations to user environment: {e}")
    else:
        logging.info("The user environment is complete and up-to-date. No copy was required.")

#==============================================================================
#3. MAIN ENTRY POINT
#==============================================================================
def main():
    #1. Capturing console arguments
    args = parseArguments()
    
    #2. Initialize environment and Logs before the interface
    setupLogging()
    prepareEnvironment()
    setApplicationId()
    
    #Standard Boot Log (INFO Level)
    logging.info("==================================================")
    logging.info("'Luck' application started successfully.")
    logging.info(f"Execution path: {baseDir}")
    logging.info(f"User storage: {UserDataDir}")
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Detailed debugging mode enabled via console.")
    logging.info("==================================================")

    #3. Initialize PyQt6 lifecycle
    app = QApplication(sys.argv)
    
    #4. Starting SplashScreen
    splash = MySplashScreen(baseDir, UserDataDir)
    splash.show()
    #Linking system/app shutdown
    sys.exit(app.exec())

if __name__ == '__main__':
    main()