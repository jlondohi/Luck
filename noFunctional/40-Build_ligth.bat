@echo off
setlocal

cd ..
call Scripts\activate
pyinstaller --onedir --optimize=2 --windowed --noupx --strip --icon=src\Guis\Resources\icon0.ico --specpath . src\Luck.py

rem Copy the Guis and Settings folders to the Luck_ligth directory
xcopy /E /I /Y "src\Guis" "dist\Luck\Guis"
xcopy /E /I /Y "src\Settings" "dist\Luck\Settings"

pause