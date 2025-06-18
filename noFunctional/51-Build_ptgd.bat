@echo off
setlocal enabledelayedexpansion

:: Configurable variables
set VENV_PATH=Scripts\activate
set OUTPUT_DIR=build_ptgd
set EXPIRE_DATE=2025-12-31
set SRC_DIR=src
set MAIN_SCRIPT=src\Luck.py
set ICON_PATH=src\Guis\Resources\icon0.ico
set DIST_DIR=dist\Luck

:: Change to the parent directory
cd ..

:: Check and delete the output directory if it exists
if exist "%OUTPUT_DIR%" (
    echo [INFO] The directory "%OUTPUT_DIR%" already exists. Deleting it...
    rmdir /S /Q "%OUTPUT_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to delete the directory "%OUTPUT_DIR%". Ensure it is not in use.
        pause
        exit /b 1
    )
)

:: Check and delete the dist directory if it exists
if exist dist (
    echo [INFO] The directory dist already exists. Deleting it...
    rmdir /S /Q dist
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to delete the directory dist. Ensure it is not in use.
        pause
        exit /b 1
    )
)

:: Check if the virtual environment exists
if not exist "%VENV_PATH%" (
    echo [ERROR] Virtual environment not found at "%VENV_PATH%".
    pause
    exit /b 1
)

:: Activate the virtual environment
call "%VENV_PATH%"

:: Validate if PyArmor is installed
pyarmor --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PyArmor is not installed in this virtual environment.
    pause
    exit /b 1
)

:: Obfuscate the main directory
echo Obfuscating the main source directory...
pyarmor gen -i "%SRC_DIR%" -O "%OUTPUT_DIR%" --expire "%EXPIRE_DATE%"
if %errorlevel% neq 0 (
    echo [ERROR] Obfuscation failed for the main directory.
    pause
    exit /b 1
)

:: Replace specific text in generated .py files
echo Cleaning up generated Python files...
powershell -Command "Get-ChildItem -Recurse -Filter *.py -Path build_ptgd | ForEach-Object { $fileContent = Get-Content $_.FullName; $newContent = $fileContent -replace 'from (\.\.?)+pyarmor_runtime_000000 import __pyarmor__', 'from pyarmor_runtime_000000 import __pyarmor__' | Where-Object {$_ -notmatch '^#'}; Set-Content $_.FullName -Value $newContent }"

:: Compile the obfuscated project using PyInstaller
echo Compiling the project with PyInstaller...
pyinstaller --onedir --optimize=2 --windowed --noupx --strip --icon="%ICON_PATH%" ^
--hidden-import=MyTreeView.MyTreeView ^
--hidden-import=PyQt6.QtGui.QBrush ^
--hidden-import=SearchWidget.SearchWidget ^
--hidden-import=SessionHandler ^
--hidden-import=PyQt6.QtGui.QPalette ^
--hidden-import=MyPackages.SplashScreen.SplashScreen ^
--hidden-import=PyQt6.QtCore.QStringListModel ^
--hidden-import=PyQt6.QtWidgets.QLineEdit ^
--hidden-import=AboutWidget.AboutWidget ^
--hidden-import=MyPackages.utils.window_methods ^
--hidden-import=pwd ^
--hidden-import=Worker ^
--hidden-import=PyQt6.QtCore ^
--hidden-import=PyQt6.QtWidgets.QVBoxLayout ^
--hidden-import=PyQt6.QtGui.QStandardItemModel ^
--hidden-import=Worker.Worker ^
--hidden-import=SQLAnalyzer.SQLAnalyzer ^
--hidden-import=PyQt6.QtGui.QTextFormat ^
--hidden-import=MyPackages.utils.ai_methods ^
--hidden-import=PyQt6.QtCore.QObject ^
--hidden-import=PyQt6.QtCore.QEvent ^
--hidden-import=MyPackages.utils.plain_text_edit_methods ^
--hidden-import=MyPackages.MyTreeView ^
--hidden-import=MyPackages ^
--hidden-import=PyQt6.QtGui.QActionGroup ^
--hidden-import=YamlHandler ^
--hidden-import=collections ^
--hidden-import=PyQt6.QtGui.QDragEnterEvent ^
--hidden-import=PyQt6.QtGui.QShortcut ^
--hidden-import=MyPackages.utils.results_table_methods ^
--hidden-import=PyQt6.QtWidgets.QHBoxLayout ^
--hidden-import=Crypto.Cipher.AES ^
--hidden-import=YamlHandler.YamlHandler ^
--hidden-import=pickle ^
--hidden-import=SearchWidget ^
--hidden-import=datetime.datetime ^
--hidden-import=ConnectionManager ^
--hidden-import=MyPackages.MyTooltip.MyTooltip ^
--hidden-import=PyQt6.QtCore.QSize ^
--hidden-import=Crypto.Util.Padding ^
--hidden-import=PyQt6.QtWidgets.QGroupBox ^
--hidden-import=LineNumberArea ^
--hidden-import=functools ^
--hidden-import=PyQt6.QtWidgets.QMessageBox ^
--hidden-import=PyQt6.QtCore.QPoint ^
--hidden-import=getpass ^
--hidden-import=PyQt6.QtWidgets.QSystemTrayIcon ^
--hidden-import=JulHelper ^
--hidden-import=MyPackages.MainWindow ^
--hidden-import=ResultTable ^
--hidden-import=PyQt6.QtCore.QAbstractTableModel ^
--hidden-import=PyQt6.QtGui.QPen ^
--hidden-import=PyQt6.QtGui.QCursor ^
--hidden-import=PyQt6.QtCore.Qt ^
--hidden-import=PyQt6.QtGui.QTextCursor ^
--hidden-import=MyPackages.utils.ecosystem_methods ^
--hidden-import=MyPackages.Updater ^
--hidden-import=PyQt6.QtWidgets.QTableView ^
--hidden-import=MyPackages.JulHelper ^
--hidden-import=ctypes.windll ^
--hidden-import=MyTooltip.MyTooltip ^
--hidden-import=tqdm.tqdm ^
--hidden-import=MyPackages.MainWindow.MainWindow ^
--hidden-import=PyQt6.QtWidgets.QPushButton ^
--hidden-import=polars ^
--hidden-import=MyPackages.MyTooltip ^
--hidden-import=PyQt6.uic ^
--hidden-import=PyQt6.QtGui.QGuiApplication ^
--hidden-import=Crypto.Util ^
--hidden-import=string ^
--hidden-import=functools.partial ^
--hidden-import=PyQt6.QtCore.QRegularExpression ^
--hidden-import=Crypto ^
--hidden-import=PyQt6.QtGui.QFontMetrics ^
--hidden-import=PyQt6.QtWidgets.QSpacerItem ^
--hidden-import=UploadDBWidget.UploadDBWidget ^
--hidden-import=yaml ^
--hidden-import=ConnectionManager.ConnectionManager ^
--hidden-import=PyQt6.QtGui.QStandardItem ^
--hidden-import=PyQt6.QtGui.QTextDocument ^
--hidden-import=winreg ^
--hidden-import=MyPackages.MySyntaxHighlighter ^
--hidden-import=PyQt6.QtGui.QTextCharFormat ^
--hidden-import=math ^
--hidden-import=ctypes.byref ^
--hidden-import=MyPackages.ResultTable ^
--hidden-import=platform ^
--hidden-import=json ^
--hidden-import=Updater.Updater ^
--hidden-import=SessionHandler.SessionHandler ^
--hidden-import=ctypes.c_long ^
--hidden-import=MyPackages.utils.create_menus ^
--hidden-import=Updater ^
--hidden-import=datetime ^
--hidden-import=PyQt6.QtCore.QThread ^
--hidden-import=collections.defaultdict ^
--hidden-import=ctypes.wintypes ^
--hidden-import=MyPackages.YamlHandler ^
--hidden-import=PyQt6.QtCore.QTimer ^
--hidden-import=SQLAnalyzer ^
--hidden-import=MyTitleBar ^
--hidden-import=PyQt6.QtWidgets.QTextEdit ^
--hidden-import=Crypto.Util.Padding.unpad ^
--hidden-import=base64 ^
--hidden-import=dataclasses.dataclass ^
--hidden-import=MyPackages.utils.tabs_methods ^
--hidden-import=PyQt6.QtWidgets.QSplitter ^
--hidden-import=MyPackages.MyTitleBar.MyTitleBar ^
--hidden-import=MyTooltip ^
--hidden-import=PyQt6.QtCore.QSortFilterProxyModel ^
--hidden-import=zipfile ^
--hidden-import=AboutWidget ^
--hidden-import=MyPackages.MyTitleBar ^
--hidden-import=sys ^
--hidden-import=PyQt6.QtGui.QPixmap ^
--hidden-import=PyQt6.QtWidgets.QWidget ^
--hidden-import=MyPackages.UploadDBWidget ^
--hidden-import=PyQt6.QtGui ^
--hidden-import=requests ^
--hidden-import=MyPackages.SplashScreen ^
--hidden-import=PyQt6.QtGui.QPainter ^
--hidden-import=MyPackages.Worker ^
--hidden-import=PyQt6.QtWidgets.QStyledItemDelegate ^
--hidden-import=time ^
--hidden-import=os ^
--hidden-import=jwt ^
--hidden-import=PyQt6.QtWidgets ^
--hidden-import=MyPackages.AboutWidget ^
--hidden-import=PyQt6.QtWidgets.QPlainTextEdit ^
--hidden-import=PyQt6.QtGui.QSyntaxHighlighter ^
--hidden-import=itertools.accumulate ^
--hidden-import=PyQt6.QtGui.QIcon ^
--hidden-import=PyQt6.QtWidgets.QSizePolicy ^
--hidden-import=socket ^
--hidden-import=LineNumberArea.LineNumberArea ^
--hidden-import=PyQt6.QtWidgets.QFrame ^
--hidden-import=contextlib.contextmanager ^
--hidden-import=MyPlainTextEdit.MyPlainTextEdit ^
--hidden-import=re ^
--hidden-import=PyQt6.QtWidgets.QFileDialog ^
--hidden-import=PyQt6.QtCore.QModelIndex ^
--hidden-import=MyPackages.MySyntaxHighlighter.MySyntaxHighlighter ^
--hidden-import=tempfile ^
--hidden-import=PyQt6.QtWidgets.QAbstractItemView ^
--hidden-import=dataclasses ^
--hidden-import=subprocess ^
--hidden-import=ResultTable.ResultTable ^
--hidden-import=JulHelper.JulHelper ^
--hidden-import=MyPackages.LineNumberArea ^
--hidden-import=itertools ^
--hidden-import=PyQt6.QtWidgets.QInputDialog ^
--hidden-import=PyQt6.QtWidgets.QCompleter ^
--hidden-import=MyPackages.utils.execute_methods ^
--hidden-import=Crypto.Cipher ^
--hidden-import=MyPackages.utils.polars_methods ^
--hidden-import=PyQt6.QtGui.QDropEvent ^
--hidden-import=random ^
--hidden-import=PyQt6.QtWidgets.QMainWindow ^
--hidden-import=PyQt6.QtGui.QColor ^
--hidden-import=PyQt6.QtGui.QKeySequence ^
--hidden-import=PyQt6.QtWidgets.QLabel ^
--hidden-import=contextlib ^
--hidden-import=PyQt6.QtWidgets.QMenu ^
--hidden-import=MyPackages.utils ^
--hidden-import=ctypes ^
--hidden-import=PyQt6.QtWidgets.QTreeView ^
--hidden-import=datetime.timedelta ^
--hidden-import=UploadDBWidget ^
--hidden-import=PyQt6.QtWidgets.QApplication ^
--hidden-import=PyQt6.QtGui.QAction ^
--hidden-import=MyPackages.ConnectionManager ^
--hidden-import=Crypto.Util.Padding.pad ^
--hidden-import=MyPackages.SessionHandler ^
--hidden-import=MyPackages.SearchWidget ^
--hidden-import=tqdm ^
--hidden-import=MyTitleBar.MyTitleBar ^
--hidden-import=pyodbc ^
--hidden-import=bisect ^
--hidden-import=PyQt6.QtGui.QFont ^
--hidden-import=PyQt6.QtCore.QRect ^
--hidden-import=MyPackages.SQLAnalyzer ^
--hidden-import=PyQt6.QtWidgets.QHeaderView ^
--hidden-import=MyPackages.MyPlainTextEdit ^
--hidden-import=PyQt6 ^
--hidden-import=MyPlainTextEdit ^
--hidden-import=MyTreeView ^
--hidden-import=PyQt6.QtCore.pyqtSignal ^
--hidden-import=PyQt6.QtGui.QScreen ^
"%OUTPUT_DIR%\%MAIN_SCRIPT%"

@REM --hidden-import=sparky_bc.Sparky ^

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller failed to compile the project.
    pause
    exit /b 1
)

:: Copy additional required folders to the distribution directory
echo Copying additional resources...
xcopy /E /I /Y "src\Guis" "%DIST_DIR%\Guis"
xcopy /E /I /Y "src\Settings" "%DIST_DIR%\Settings"
xcopy /E /I /Y "src\i18n" "%DIST_DIR%\i18n"
xcopy /E /I /Y "LICENSE" "%DIST_DIR%\LICENSE"

:: Final confirmation
echo [SUCCESS] Process completed successfully. The compiled application is located in "%DIST_DIR%".
endlocal
pause
exit /b 0
