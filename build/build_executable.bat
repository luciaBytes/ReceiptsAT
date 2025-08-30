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
echo 2. Activating virtual environment and checking PyInstaller...
rem Check if virtual environment exists
if not exist "%BUILD_DIR%..\.venv\Scripts\python.exe" (
    echo    Virtual environment not found at %BUILD_DIR%..\.venv\
    echo    Please ensure the virtual environment is created
    exit /b 1
)

rem Use virtual environment's pip
"%BUILD_DIR%..\.venv\Scripts\pip.exe" show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    Installing PyInstaller in virtual environment...
    "%BUILD_DIR%..\.venv\Scripts\pip.exe" install pyinstaller
) else (
    echo    PyInstaller already installed in virtual environment
)

echo.
echo 3. Building executable with virtual environment...
cd /d "%BUILD_DIR%.."
echo    Working directory: %cd%
echo    Spec file: build/receipts_app.spec
echo    Using Python: .venv\Scripts\python.exe

".venv\Scripts\python.exe" -m PyInstaller build/receipts_app.spec --noconfirm --clean

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
