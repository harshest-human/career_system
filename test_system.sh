#!/usr/bin/env bash
echo "========================================================"
echo "  Running Career System Diagnostics & Self-Test Suite"
echo "========================================================"
echo ""

if [ ! -f ".venv/bin/python" ]; then
    echo "[Setup] Initializing environment..."
    chmod +x ./setup.sh
    ./setup.sh
fi

.venv/bin/python test_system.py
