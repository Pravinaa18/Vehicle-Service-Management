#!/usr/bin/env bash
echo "========================================================"
echo "  AutoCare - Vehicle Service Management System"
echo "========================================================"
echo ""

if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "[*] Activating virtual environment..."
source .venv/bin/activate

echo "[*] Installing / verifying dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "[*] Starting AutoCare server..."
echo "[*] Open http://127.0.0.1:5000 in your browser."
echo ""
python3 app.py
