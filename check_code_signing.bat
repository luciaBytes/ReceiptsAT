@echo off
echo ======================================
echo   Code Signing Setup Helper
echo ======================================
echo.

echo This script helps you set up code signing for your releases.
echo Code signing eliminates Windows security warnings for your users.
echo.

echo Current Status:
if "%CODE_SIGN_CERT%"=="" (
    echo ❌ Code signing: NOT CONFIGURED
    echo    - Users will see "Unknown Publisher" warnings
    echo    - Windows may block downloads
    echo.
    echo To enable code signing:
    echo 1. Purchase a code signing certificate from:
    echo    - DigiCert (~$300/year) - Recommended
    echo    - Sectigo (~$200/year) - Good alternative  
    echo    - GlobalSign (~$250/year)
    echo.
    echo 2. Add GitHub Secrets (Settings > Secrets and variables > Actions):
    echo    - CODE_SIGN_CERT_BASE64: Your certificate in Base64 format
    echo    - CODE_SIGN_PASSWORD: Your certificate password
    echo.
    echo 3. Next release will be automatically signed!
    echo.
    echo For detailed instructions, see: docs\CODE_SIGNING_SETUP.md
) else (
    echo ✅ Code signing: CONFIGURED
    echo    - Certificate: %CODE_SIGN_CERT%
    echo    - Users will see verified publisher
    echo    - No Windows security warnings
)

echo.
where signtool >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ SignTool: Available
    signtool /? | findstr "Microsoft"
) else (
    echo ❌ SignTool: Not found
    echo    Install Windows SDK or Visual Studio Build Tools
)

echo.
echo ======================================
pause
