@echo off
echo ======================================
echo  Portal das Financas Receipts Builder
echo ======================================
echo.

cd /d "%~dp0"

echo [1/4] Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Building executable...
call build\build_executable.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build executable
    pause
    exit /b 1
)

echo.
echo [3/4] Creating installer...
call "%~dp0build\build_installer.bat"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create installer
    pause
    exit /b 1
)

echo.
echo [4/4] Packaging for distribution...
call "%~dp0build\package_release.bat"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to package release
    pause
    exit /b 1
)

echo.
echo ======================================
echo ✅ BUILD COMPLETED SUCCESSFULLY!
echo ======================================
echo.
echo 📦 Installer: releases\PortalReceiptsApp_Setup_v1.0.0.exe
echo 📁 Release folder: releases\
echo.
echo Ready for distribution!
echo.
pause
