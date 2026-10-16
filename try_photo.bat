@echo off
REM Drag one or more photos onto this file to see what the AI thinks they are.
call "%~dp0.venv\Scripts\activate"
cd /d "%~dp0"
python try_photo.py %*
pause
