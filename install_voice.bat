@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run.bat
.venv\Scripts\python.exe -m pip install -r requirements-voice.txt
pause
