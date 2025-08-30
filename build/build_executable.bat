@echo off
echo =====================================
echo Building Portal Receipts Application
echo =====================================

rem Store original directory
set ORIGINAL_DIR=%cd%
set BUILD_DIR=%~dp0

echo.
echo 1. Cleaning previous builds...

rem Clean previous builds from standardized locations  
if exist "%BUILD_DIR%..\build\temp" (
    echo    Removing build temp artifacts...
    rmdir /s /q "%BUILD_DIR%..\build\temp"
)
if exist "%BUILD_DIR%..\build\receipts_app" (
    echo    Removing old build artifacts...
    rmdir /s /q "%BUILD_DIR%..\build\receipts_app"
)
if exist "%BUILD_DIR%..\dist" (
    echo    Removing previous distribution...
    rmdir /s /q "%BUILD_DIR%..\dist"
)

echo.
echo 2. Checking PyInstaller installation...
rem Check if virtual environment exists, otherwise use system Python
if exist "%BUILD_DIR%..\.venv\Scripts\python.exe" (
    echo    Using virtual environment at %BUILD_DIR%..\.venv\
    set "PYTHON_EXE=%BUILD_DIR%..\.venv\Scripts\python.exe"
    set "PIP_EXE=%BUILD_DIR%..\.venv\Scripts\pip.exe"
) else (
    echo    Virtual environment not found, using system Python
    set "PYTHON_EXE=python"
    set "PIP_EXE=pip"
)

rem Check if PyInstaller is installed
%PIP_EXE% show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    Installing PyInstaller...
    %PIP_EXE% install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo    ERROR: Failed to install PyInstaller
        exit /b 1
    )
) else (
    echo    PyInstaller is already installed
)

echo.
echo 3. Building executable...
cd /d "%BUILD_DIR%.."
echo    Working directory: %cd%
echo    Spec file: build/receipts_app.spec
echo    Using Python: %PYTHON_EXE%

%PYTHON_EXE% -m PyInstaller build/receipts_app.spec --noconfirm --clean

echo.
echo 4. Verifying build results...

if %ERRORLEVEL% EQU 0 (
    if exist "dist\PortalReceiptsApp\PortalReceiptsApp.exe" (
        echo Build completed successfully!
        echo    Executable: %cd%\dist\PortalReceiptsApp\PortalReceiptsApp.exe
        echo    Distribution folder: %cd%\dist\PortalReceiptsApp\
        
        rem Clean up any remaining build artifacts
        echo.
        echo 5. Cleaning up build artifacts...
        if exist "build\temp" (
            echo    Removing temp build files...
            rmdir /s /q "build\temp" >nul 2>&1
        )
        if exist "build\receipts_app" (
            echo    Removing intermediate build files...
            rmdir /s /q "build\receipts_app" >nul 2>&1
        )
        echo    Build artifacts cleaned up
    ) else (
        echo Build failed: Executable not found in expected location
        echo    Expected: %cd%\dist\PortalReceiptsApp\PortalReceiptsApp.exe
        echo    Current directory: %cd%
        dir dist 2>nul
        exit /b 1
    )
) else (
    echo PyInstaller build failed (exit code: %ERRORLEVEL%)
    exit /b %ERRORLEVEL%
)
echo.
echo =====================================
echo Build completed successfully!
echo =====================================
echo.
echo To create an installer, run: build_installer.bat
echo.

rem Return to original directory
cd /d "%ORIGINAL_DIR%"
