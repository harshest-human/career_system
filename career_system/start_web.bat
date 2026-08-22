@echo off
title Career System Local Web App
echo ========================================================
echo   Starting Anti-Gravity Career System Web Application
echo ========================================================
echo.

cd /d "%~dp0"

set PYTHON_EXE=.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    if exist "..\.venv\Scripts\python.exe" (
        set PYTHON_EXE=..\.venv\Scripts\python.exe
    ) else (
        echo [Setup] Initializing environment...
        powershell -ExecutionPolicy ByPass -File ./setup.ps1
    )
)

echo [Server] Starting local server at http://localhost:8000 ...
start http://localhost:8000
%PYTHON_EXE% app.py
pause
