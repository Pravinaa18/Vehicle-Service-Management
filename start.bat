@echo off
echo ========================================================
echo   AutoCare - Vehicle Service Management System
echo ========================================================
echo.

if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
)

echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [*] Installing / verifying dependencies...
pip install -r requirements.txt --quiet

echo.
echo [*] Starting AutoCare server...
echo [*] Open http://127.0.0.1:5000 in your browser.
echo.
python app.py
pause
