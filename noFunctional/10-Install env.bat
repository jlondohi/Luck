@echo off
setlocal

cd ..
pip install virtualenv
python -m virtualenv %CD%

pause