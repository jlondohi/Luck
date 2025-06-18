@echo off
setlocal
set python_path=C:/Users/%USERNAME%/AppData/Local/Programs/Python/Python312/python.exe
cd ..

echo Installing virtualenv...
%python_path% -m pip install virtualenv
if %errorlevel% neq 0 (
    echo Error: Failed to install virtualenv.
    pause
    exit /b %errorlevel%
)

echo Creating a virtual environment...
%python_path% -m virtualenv %CD%
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b %errorlevel%
)

echo Installation completed successfully.
pause