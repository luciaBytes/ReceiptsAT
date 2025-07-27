@echo off
echo =====================================
echo Setting up GUI-based App Builder
echo =====================================

echo Installing auto-py-to-exe...
pip install auto-py-to-exe

if errorlevel 1 (
    echo Failed to install auto-py-to-exe
    pause
    exit /b 1
)

echo =====================================
echo Launching auto-py-to-exe GUI...
echo =====================================
echo.
echo Configuration suggestions:
echo - Script Location: src/main.py
echo - Onedir: Recommended for first build
echo - Console Window: Disabled (Window Based)
echo - Icon: Add an .ico file if available
echo - Additional Files: Add credentials.example, README.md
echo.
echo The GUI will open in your browser...
auto-py-to-exe
