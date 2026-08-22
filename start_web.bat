@echo off
title Career System Local Web App
echo ========================================================
echo   Starting Anti-Gravity Career System Web Application
echo ========================================================
echo.

:: Ensure virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [Setup] Initializing environment...
    powershell -ExecutionPolicy ByPass -File ./setup.ps1
)

echo [Server] Starting local server at http://localhost:8000 ...
start http://localhost:8000
.venv\Scripts\python.exe app.py
pause
