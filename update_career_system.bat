@echo off
title Career System - 1-Click Update ^& Sync
echo ========================================================
echo   Updating Career System to Latest GitHub Version
echo ========================================================
echo.

git pull origin main
echo.

cd /d "%~dp0career_system"

set PYTHON_EXE=.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    if exist "..\.venv\Scripts\python.exe" (
        set PYTHON_EXE=..\.venv\Scripts\python.exe
    )
)

if exist "%PYTHON_EXE%" (
    echo [Doctor] Running system diagnostic check...
    %PYTHON_EXE% test_system.py
)

echo.
echo ========================================================
echo   Update Complete! All new features ^& fixes are active.
echo   You can now run start_career_system.bat
echo ========================================================
pause
