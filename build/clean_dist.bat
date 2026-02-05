@echo off
cd /d "%~dp0.."
echo Cleaning dist directory...
taskkill /F /IM PortalReceiptsApp.exe 2>nul
timeout /t 2 /nobreak >nul
rmdir /s /q "dist\PortalReceiptsApp" 2>nul
if exist "dist\PortalReceiptsApp" (
    echo Directory still exists, trying alternative method...
    rd /s /q "dist\PortalReceiptsApp" 2>nul
)
if exist "dist\PortalReceiptsApp" (
    echo Failed to delete directory. Please close any programs using the files.
    pause
    exit /b 1
) else (
    echo Successfully cleaned dist directory.
    exit /b 0
)
