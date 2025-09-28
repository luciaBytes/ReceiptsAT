@echo off
echo ==========================================
echo Building Receipts App (DEBUG VERSION)
echo ==========================================
echo.

cd /d "%~dp0"
cd ..

echo Checking Python environment...
python --version
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    pause
    exit /b 1
)

echo.
echo Building DEBUG executable with PyInstaller...
echo This version will show console for logging visibility.
echo.

cd build
python -m PyInstaller receipts_app_debug.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for details.
    pause
    exit /b 1
) else (
    echo.
    echo ==========================================
    echo DEBUG BUILD SUCCESSFUL!
    echo ==========================================
    echo.
    echo Debug executable location: dist\PortalReceiptsApp_Debug\PortalReceiptsApp_Debug.exe
    echo This version shows console window for logging visibility.
    echo.
    echo You can also run the regular version with debug mode:
    echo   PortalReceiptsApp.exe --debug
    echo   PortalReceiptsApp.exe --console
    echo.
    echo Or set environment variable:
    echo   set RECEIPTS_DEBUG=1 ^&^& PortalReceiptsApp.exe
    echo.
    pause
)