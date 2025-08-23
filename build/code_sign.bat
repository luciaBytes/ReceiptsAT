@echo off
echo Code signing executable and installer...

rem Change to project root
cd /d "%~dp0\.."

rem Read version from .version file
if exist ".version" (
    set /p APP_VERSION=<.version
    echo Signing version: %APP_VERSION%
) else (
    echo ERROR: .version file not found
    exit /b 1
)

rem Check if we have signing credentials
if "%CODE_SIGN_CERT%"=="" (
    echo INFO: No code signing certificate configured
    echo Set CODE_SIGN_CERT environment variable to enable signing
    echo Example: set CODE_SIGN_CERT=path\to\certificate.pfx
    echo Example: set CODE_SIGN_PASSWORD=your_cert_password
    exit /b 0
)

rem Check if signtool exists
where signtool >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: signtool not found in PATH
    echo Install Windows SDK or Visual Studio Build Tools to enable signing
    exit /b 0
)

rem Sign the executable
set "EXE_PATH=dist\PortalReceiptsApp\PortalReceiptsApp.exe"
if exist "%EXE_PATH%" (
    echo Signing executable: %EXE_PATH%
    if "%CODE_SIGN_PASSWORD%"=="" (
        signtool sign /f "%CODE_SIGN_CERT%" /t http://timestamp.digicert.com "%EXE_PATH%"
    ) else (
        signtool sign /f "%CODE_SIGN_CERT%" /p "%CODE_SIGN_PASSWORD%" /t http://timestamp.digicert.com "%EXE_PATH%"
    )
    
    if %ERRORLEVEL% EQU 0 (
        echo ✓ Executable signed successfully
    ) else (
        echo ✗ Failed to sign executable
        exit /b 1
    )
) else (
    echo WARNING: Executable not found at %EXE_PATH%
)

rem Sign the installer
set "INSTALLER_PATH=releases\PortalReceiptsApp_Setup_v%APP_VERSION%.exe"
if exist "%INSTALLER_PATH%" (
    echo Signing installer: %INSTALLER_PATH%
    if "%CODE_SIGN_PASSWORD%"=="" (
        signtool sign /f "%CODE_SIGN_CERT%" /t http://timestamp.digicert.com "%INSTALLER_PATH%"
    ) else (
        signtool sign /f "%CODE_SIGN_CERT%" /p "%CODE_SIGN_PASSWORD%" /t http://timestamp.digicert.com "%INSTALLER_PATH%"
    )
    
    if %ERRORLEVEL% EQU 0 (
        echo ✓ Installer signed successfully
    ) else (
        echo ✗ Failed to sign installer
        exit /b 1
    )
) else (
    echo WARNING: Installer not found at %INSTALLER_PATH%
)

echo Code signing completed successfully!
