#!/usr/bin/env bash
echo "========================================================"
echo "  Starting Anti-Gravity Career System Web Application"
echo "========================================================"
echo ""

if [ ! -f ".venv/bin/python" ]; then
    echo "[Setup] Initializing environment..."
    chmod +x ./setup.sh
    ./setup.sh
fi

echo "[Server] Starting local server at http://localhost:8000 ..."
if which xdg-open > /dev/null; then
    xdg-open http://localhost:8000 &
elif which open > /dev/null; then
    open http://localhost:8000 &
fi

.venv/bin/python app.py
