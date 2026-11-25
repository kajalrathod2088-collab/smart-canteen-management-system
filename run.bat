@echo off
echo ========================================================
echo   SMART CANTEEN MANAGEMENT SYSTEM - CAMPUS PORTAL
echo ========================================================
echo.
cd /d "%~dp0"
python -m pip install -r requirements.txt
echo.
echo Starting Smart Canteen Server...
echo Open your browser at: http://127.0.0.1:5000
echo.
python app.py
pause
