@echo off
call .venv\Scripts\activate
echo Open http://localhost:8000   (staff PIN: 1234)
echo Booth screen for the laptop: http://localhost:8000/booth  then press F11
echo On your phone (same Wi-Fi/hotspot): http://YOUR-LAPTOP-IP:8000   - find the IP with: ipconfig
uvicorn app.main:app --host 0.0.0.0 --port 8000
