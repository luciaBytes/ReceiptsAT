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
    exit /b 1
)

echo.
echo [2/4] Building executable...
call build\build_executable.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build executable
    exit /b 1
)

echo.
echo [2.1] Final cleanup of build artifacts...
if exist "build\temp" rmdir /s /q "build\temp" >nul 2>&1
if exist "build\receipts_app" rmdir /s /q "build\receipts_app" >nul 2>&1
echo Build artifacts cleaned up

echo.
echo [3/5] Code signing...
call "%~dp0build\code_sign.bat"
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Code signing failed, continuing without signatures
    echo Set CODE_SIGN_CERT and CODE_SIGN_PASSWORD environment variables to enable signing
)

echo.
echo [4/5] Creating installer...
call "%~dp0build\build_installer.bat"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create installer
    exit /b 1
)

echo.
echo [5/5] Packaging for distribution...
call "%~dp0build\package_release.bat"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to package release
    exit /b 1
)

rem Read version for display
if exist ".version" (
    set /p APP_VERSION=<.version
) else (
    set APP_VERSION=1.0.0
)

echo.
echo ======================================
echo BUILD COMPLETED SUCCESSFULLY!
echo ======================================
echo.
echo Installer: releases\PortalReceiptsApp_Setup_v%APP_VERSION%.exe
echo Release folder: releases\
echo.
echo Ready for distribution!
echo.

exit /b 0
