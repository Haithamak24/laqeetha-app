@echo off
REM Wipes all items and reports, then reloads the 6 demo items. Run before each rehearsal.
call .venv\Scripts\activate
if exist data rmdir /s /q data
python seed.py
pause
