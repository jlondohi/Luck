@echo off
setlocal

set requirements_name=requirements.txt

echo Activating the virtual environment...
cd ..
call Scripts\activate
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b %errorlevel%
)

echo Installing dependencies from %requirements_name%...
python -m pip install -r %requirements_name%
if %errorlevel% neq 0 (
    echo Error: Dependencies could not be installed.
    pause
    exit /b %errorlevel%
)

echo Installation completed successfully.
pause
