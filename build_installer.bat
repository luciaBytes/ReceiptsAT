@echo off
echo =====================================
echo Building Windows Installer
echo =====================================

:: Check if Inno Setup is installed
where iscc >nul 2>nul
if errorlevel 1 (
    echo Inno Setup not found in PATH.
    echo Please install Inno Setup from: https://jrsoftware.org/isinfo.php
    echo After installation, add the Inno Setup installation directory to your PATH
    echo or run this script from the Inno Setup directory.
    pause
    exit /b 1
)

:: Check if application is built
if not exist "dist\PortalReceiptsApp\PortalReceiptsApp.exe" (
    echo Application not built yet. Building first...
    call build_app.bat
    if errorlevel 1 (
        echo Application build failed!
        pause
        exit /b 1
    )
)

:: Create assets directory if it doesn't exist
if not exist "assets" mkdir assets

:: Create installer output directory
if not exist "installer_output" mkdir installer_output

:: Build the installer
echo Building installer with Inno Setup...
iscc installer_script.iss

if errorlevel 1 (
    echo Installer build failed!
    pause
    exit /b 1
)

echo =====================================
echo Installer build completed successfully!
echo =====================================
echo Installer location: installer_output\PortalReceiptsApp_Setup_v1.0.0.exe
echo.
echo You can now distribute this installer to users.
echo.
pause
