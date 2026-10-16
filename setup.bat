@echo off
REM One-time setup (Windows). Needs Python 3.10+ from python.org (tick "Add to PATH").
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Downloading the AI models (~600 MB, one time only) and seeding demo items...
python seed.py
echo.
echo Done. Now run: start.bat
pause
