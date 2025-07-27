@echo off
echo =====================================
echo Building Portal das Financas Receipts App
echo =====================================

:: Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller
        pause
        exit /b 1
    )
)

:: Check if required packages are installed
echo Checking dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements
    pause
    exit /b 1
)

:: Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"

:: Build the application
echo Building application...
pyinstaller --clean receipts_app.spec

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

:: Check if build was successful
if not exist "dist\PortalReceiptsApp\PortalReceiptsApp.exe" (
    echo Build failed - executable not found!
    pause
    exit /b 1
)

echo =====================================
echo Build completed successfully!
echo =====================================
echo Executable location: dist\PortalReceiptsApp\PortalReceiptsApp.exe
echo.
echo To create an installer, run: build_installer.bat
echo.
pause
