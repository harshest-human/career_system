@echo off
title Career System - Diagnostic Doctor & System Self-Test
echo ========================================================
echo   Running Career System Diagnostics & Self-Test Suite
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

%PYTHON_EXE% test_system.py
echo.
pause
