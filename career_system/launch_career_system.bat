@echo off
title Career System — 100% Offline Local Studio
color 0B

echo =======================================================================
echo           CAREER SYSTEM — 100%% OFFLINE LOCAL CAREER STUDIO
echo =======================================================================
echo.

cd /d "%~dp0"

echo [1/4] Conducting environment inspection...

:: Check if uv exists
where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo  - Found 'uv' fast package manager.
    set "RUN_CMD=uv run python"
) else (
    :: Check if local virtual environment exists in parent or current dir
    if exist "..\.venv\Scripts\python.exe" (
        echo  - Found virtual environment at ..\.venv
        set "RUN_CMD=..\.venv\Scripts\python.exe"
    ) else if exist ".venv\Scripts\python.exe" (
        echo  - Found virtual environment at .venv
        set "RUN_CMD=.venv\Scripts\python.exe"
    ) else (
        where python >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo  - Using system Python.
            set "RUN_CMD=python"
        ) else (
            echo [ERROR] Python was not detected on your system.
            echo Please install Python 3.10+ or uv to run Career System.
            pause
            exit /b 1
        )
    )
)

echo [2/4] Verifying and installing dependencies...
%RUN_CMD% -m pip install -r requirements.txt --quiet 2>nul || (
    echo Installing required packages...
    %RUN_CMD% -m pip install fastapi uvicorn beautifulsoup4 pdfplumber reportlab jinja2 pyyaml pypdf
)

echo [3/4] Initializing local database and templates...
%RUN_CMD% -c "import app; print(' Database and templates initialized successfully.')"

echo [4/4] Launching Career System Web Studio...
echo.
echo  Web App URL : http://localhost:8000 (or http://127.0.0.1:8000)
echo.

:: Open browser automatically
start http://127.0.0.1:8000

:: Start server
%RUN_CMD% app.py

pause
