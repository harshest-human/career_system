@echo off
title Career System - Diagnostic Doctor & System Self-Test
echo ========================================================
echo   Running Career System Diagnostics & Self-Test Suite
echo ========================================================
echo.

:: Ensure virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [Setup] Initializing environment...
    powershell -ExecutionPolicy ByPass -File ./setup.ps1
)

.venv\Scripts\python.exe test_system.py
echo.
pause
