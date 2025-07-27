@echo off
echo =====================================
echo Testing Built Application
echo =====================================

:: Check if executable exists
if not exist "dist\PortalReceiptsApp\PortalReceiptsApp.exe" (
    echo Application executable not found!
    echo Please run build_app.bat first.
    pause
    exit /b 1
)

echo Testing application startup...
echo Note: This will launch the application briefly to test if it loads correctly.
echo Close the application window to complete the test.
echo.
pause

:: Launch the application
start "" "dist\PortalReceiptsApp\PortalReceiptsApp.exe"

echo.
echo Test completed. If the application launched successfully, the build is working.
echo You can now proceed to create the installer with build_installer.bat
echo.
pause
