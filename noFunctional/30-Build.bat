@echo off
setlocal

cd ..
call %CD%\Scripts\activate
pyinstaller --onefile --windowed --noupx --icon=src\Guis\Resources\icon0.ico --specpath . src\Luck.py

rem Copy the Guis and Settings folders to the Luck directory
xcopy /E /I /Y "src\Guis" "dist\Guis"
xcopy /E /I /Y "src\Settings" "dist\Settings"

pause