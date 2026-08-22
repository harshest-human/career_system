#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Anti-Gravity: Automated Job Application & Pipeline Setup"
echo "=========================================================="

# 1. Install uv if needed
if ! command -v uv &> /dev/null; then
    echo "[1/4] Installing 'uv' package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "[1/4] 'uv' package manager found."
fi

# 2. Setup Virtual Environment
echo "[2/4] Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    uv venv --python 3.12 .venv
fi

# 3. Install Dependencies
echo "[3/4] Installing dependencies..."
uv pip install --python .venv/bin/python fastapi uvicorn httpx python-multipart pdfplumber pypdf jinja2 pandas openpyxl pyyaml beautifulsoup4 requests reportlab

# 4. Check LaTeX
echo "[4/4] Checking LaTeX compiler..."
if command -v xelatex &> /dev/null; then
    echo "      XeLaTeX detected."
else
    echo "      NOTE: Install TeXLive or MacTeX for PDF compilation."
fi

echo ""
echo "Running system diagnostic test..."
.venv/bin/python test_system.py

echo ""
echo "Setup complete! Run:"
echo "  ./start_web.sh  (or .venv/bin/python app.py)"
echo "=========================================================="
