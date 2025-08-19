@echo off
echo Building executable with PyInstaller...

rem Clean previous builds (use absolute paths)
if exist "%~dp0\..\build\build" rmdir /s /q "%~dp0\..\build\build"
if exist "%~dp0\..\dist" rmdir /s /q "%~dp0\..\dist"

rem Install PyInstaller if not present
pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

rem Change to build directory and run PyInstaller
cd /d "%~dp0"
echo Running from: %cd%

rem Build the executable
pyinstaller --clean receipts_app.spec

rem Move to correct location for installer
if exist "..\dist" (
    rmdir /s /q "..\dist"
)
if exist "dist\PortalReceiptsApp" (
    mkdir "..\dist" >nul 2>&1
    move "dist\PortalReceiptsApp" "..\dist\" >nul 2>&1
    echo Moved executable to project dist directory
)

if %ERRORLEVEL% EQU 0 (
    echo Executable built successfully!
    if exist "..\dist\PortalReceiptsApp\PortalReceiptsApp.exe" (
        echo Location: ..\dist\PortalReceiptsApp\PortalReceiptsApp.exe
    ) else (
        echo Location: .\dist\PortalReceiptsApp\PortalReceiptsApp.exe
    )
) else (
    echo ERROR: Failed to build executable
    exit /b 1
)
echo Build completed successfully!
echo =====================================
if exist "..\dist\PortalReceiptsApp\PortalReceiptsApp.exe" (
    echo Executable location: ..\dist\PortalReceiptsApp\PortalReceiptsApp.exe
) else (
    echo Executable location: .\dist\PortalReceiptsApp\PortalReceiptsApp.exe
)
echo.
echo To create an installer, run: build_installer.bat
echo.
pause
