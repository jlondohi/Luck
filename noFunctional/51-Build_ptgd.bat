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
--hidden-import=re ^
--hidden-import=os ^
--hidden-import=sys ^
--hidden-import=yaml ^
--hidden-import=time ^
--hidden-import=math ^
--hidden-import=json ^
--hidden-import=pickle ^
--hidden-import=pandas ^
--hidden-import=socket ^
--hidden-import=winreg ^
--hidden-import=ctypes ^
--hidden-import=ctypes.wintypes ^
--hidden-import=base64 ^
--hidden-import=pyodbc ^
--hidden-import=random ^
--hidden-import=string ^
--hidden-import=getpass ^
--hidden-import=platform ^
--hidden-import=tempfile ^
--hidden-import=warnings ^
--hidden-import=subprocess ^
--hidden-import=Crypto.Cipher ^
--hidden-import=Crypto.Cipher.AES ^
--hidden-import=Crypto.Util.Padding ^
--hidden-import=Crypto.Util.Padding.unpad ^
--hidden-import=datetime ^
--hidden-import=datetime.timedelta ^
--hidden-import=contextlib.contextmanager ^
--hidden-import=PyQt6 ^
--hidden-import=PyQt6.QtWidgets ^
--hidden-import=PyQt6.QtGui ^
--hidden-import=PyQt6.QtCore ^
--hidden-import=PyQt6.uic ^
--hidden-import=MyPackages ^
--hidden-import=MyPackages.AboutWidget ^
--hidden-import=MyPackages.ConnectionManager ^
--hidden-import=MyPackages.JsonHandler ^
--hidden-import=MyPackages.JulHelper ^
--hidden-import=MyPackages.LineNumberArea ^
--hidden-import=MyPackages.MainWindow ^
--hidden-import=MyPackages.MyPlainTextEdit ^
--hidden-import=MyPackages.MySyntaxHighlighter ^
--hidden-import=MyPackages.MyTitleBar ^
--hidden-import=MyPackages.MyTooltip ^
--hidden-import=MyPackages.MyTreeView ^
--hidden-import=MyPackages.ResultTable_dev ^
--hidden-import=MyPackages.ResultTable ^
--hidden-import=MyPackages.SearchWidget ^
--hidden-import=MyPackages.SessionHandler ^
--hidden-import=MyPackages.SplashScreen ^
--hidden-import=MyPackages.SQLAnalyzer ^
--hidden-import=MyPackages.UploadDBWidget ^
--hidden-import=MyPackages.Worker ^
--hidden-import=MyPackages.YamlHandler ^
--hidden-import=MyPackages.utils ^
--hidden-import=MyPackages.utils.ai_methods ^
--hidden-import=MyPackages.utils.create_menus ^
--hidden-import=MyPackages.utils.ecosystem_methods ^
--hidden-import=MyPackages.utils.execute_methods ^
--hidden-import=MyPackages.utils.plain_text_edit_methods ^
--hidden-import=MyPackages.utils.results_table_methods ^
--hidden-import=MyPackages.utils.tabs_methods ^
--hidden-import=MyPackages.utils.window_methods ^
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
xcopy /E /I /Y "LICENSE" "%DIST_DIR%\LICENSE"

:: Final confirmation
echo [SUCCESS] Process completed successfully. The compiled application is located in "%DIST_DIR%".
endlocal
pause
exit /b 0
