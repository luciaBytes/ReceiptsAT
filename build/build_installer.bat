@echo off
echo Creating Windows installer...

cd /d "%~dp0\.."

rem Read version from .version file
if exist ".version" (
    set /p APP_VERSION=<.version
    echo Using version: %APP_VERSION%
) else (
    echo ERROR: .version file not found
    exit /b 1
)

rem Check if executable exists
if not exist "dist\PortalReceiptsApp\PortalReceiptsApp.exe" (
    echo ERROR: Executable not found. Run build_executable.bat first.
    exit /b 1
)

rem Create releases directory
if not exist "releases" mkdir "releases"

rem Check for Inno Setup in common locations
set "INNO_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if "%INNO_PATH%"=="" (
    echo ERROR: Inno Setup not found. Please install Inno Setup 6.
    echo Download from: https://jrsoftware.org/isinfo.php
    echo After installation, add to PATH or ensure it's in Program Files.
    exit /b 1
)

echo Using Inno Setup: %INNO_PATH%

rem Build the installer with dynamic version
"%INNO_PATH%" "build\installer_script.iss" /DMyAppVersion=%APP_VERSION%

if %ERRORLEVEL% EQU 0 (
    echo Installer created successfully!
    echo Location: releases\PortalReceiptsApp_Setup_v%APP_VERSION%.exe
) else (
    echo ERROR: Failed to create installer
    exit /b 1
)
pause
