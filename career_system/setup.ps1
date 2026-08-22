# Anti-Gravity Job Application Pipeline - Quick Setup Script (Windows PowerShell)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Anti-Gravity: Automated Job Application & Pipeline Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check or install uv
if (!(Get-Command uv -ErrorAction SilentlyContinue) -and !(Test-Path "$HOME\.local\bin\uv.exe")) {
    Write-Host "[1/4] Installing 'uv' fast package manager..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$HOME\.local\bin;$env:Path"
} else {
    Write-Host "[1/4] 'uv' package manager found." -ForegroundColor Green
    $env:Path = "$HOME\.local\bin;$env:Path"
}

# 2. Setup Virtual Environment
Write-Host "[2/4] Initializing Python 3.12 virtual environment..." -ForegroundColor Yellow
if (!(Test-Path ".venv")) {
    uv venv --python 3.12 .venv
}

# 3. Install Dependencies
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Yellow
uv pip install --python .venv\Scripts\python.exe fastapi uvicorn httpx python-multipart google-genai pdfplumber pypdf jinja2 pandas openpyxl pyyaml beautifulsoup4 requests reportlab

# 4. Check MiKTeX / LaTeX
Write-Host "[4/4] Verifying LaTeX installation..." -ForegroundColor Yellow
if (Get-Command xelatex -ErrorAction SilentlyContinue) {
    Write-Host "      XeLaTeX detected on PATH." -ForegroundColor Green
} elseif (Test-Path "C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe") {
    Write-Host "      MiKTeX detected in standard location." -ForegroundColor Green
} else {
    Write-Host "      NOTE: MiKTeX or TeXLive is recommended for PDF generation." -ForegroundColor DarkYellow
    Write-Host "      Download from: https://miktex.org/download" -ForegroundColor DarkYellow
}

Write-Host "`nRunning system diagnostic check..." -ForegroundColor Cyan
.venv\Scripts\python.exe test_system.py

Write-Host "`nSetup complete! You can now run:" -ForegroundColor Green
Write-Host "  start_web.bat  (or .venv\Scripts\python.exe app.py)" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
