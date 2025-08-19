@echo off
REM Batch file to run the Receipts Processor application

echo Starting Receipts Processor...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher and try again.
    pause
    exit /b 1
)

REM Change to the src directory
cd /d "%~dp0src"

REM Run the application
python main.py

REM Pause to see any error messages
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
