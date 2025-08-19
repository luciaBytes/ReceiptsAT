@echo off
echo Packaging release files for distribution...

cd /d "%~dp0\.."

rem Check if installer exists
if not exist "releases\PortalReceiptsApp_Setup_v1.0.0.exe" (
    echo ERROR: Installer not found. Run build_installer.bat first.
    exit /b 1
)

rem Create release package directory
set "RELEASE_DIR=releases\PortalReceiptsApp_v1.0.0_Release"
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%"

rem Copy installer
copy "releases\PortalReceiptsApp_Setup_v1.0.0.exe" "%RELEASE_DIR%\"

rem Copy documentation
copy "docs\USER_INSTALLATION_GUIDE.md" "%RELEASE_DIR%\"
copy "CHANGELOG.md" "%RELEASE_DIR%\"
copy "README.md" "%RELEASE_DIR%\README_PROJECT.md"

rem Create release README
echo Portal das Financas Receipts v1.0.0 > "%RELEASE_DIR%\README.txt"
echo ======================================= >> "%RELEASE_DIR%\README.txt"
echo. >> "%RELEASE_DIR%\README.txt"
echo Quick Installation: >> "%RELEASE_DIR%\README.txt"
echo 1. Run PortalReceiptsApp_Setup_v1.0.0.exe >> "%RELEASE_DIR%\README.txt"
echo 2. Follow the installation wizard >> "%RELEASE_DIR%\README.txt"
echo 3. Launch from Start Menu ^> Portal das Financas Receipts >> "%RELEASE_DIR%\README.txt"
echo. >> "%RELEASE_DIR%\README.txt"
echo For detailed instructions, see USER_INSTALLATION_GUIDE.md >> "%RELEASE_DIR%\README.txt"
echo. >> "%RELEASE_DIR%\README.txt"
echo System Requirements: >> "%RELEASE_DIR%\README.txt"
echo - Windows 10 or later (64-bit) >> "%RELEASE_DIR%\README.txt"
echo - 50MB available disk space >> "%RELEASE_DIR%\README.txt"
echo - Internet connection required >> "%RELEASE_DIR%\README.txt"
echo. >> "%RELEASE_DIR%\README.txt"
echo Files in this package: >> "%RELEASE_DIR%\README.txt"
echo - PortalReceiptsApp_Setup_v1.0.0.exe   (Windows Installer) >> "%RELEASE_DIR%\README.txt"
echo - USER_INSTALLATION_GUIDE.md           (Detailed Instructions) >> "%RELEASE_DIR%\README.txt"
echo - CHANGELOG.md                         (Version History) >> "%RELEASE_DIR%\README.txt"
echo - README_PROJECT.md                    (Project Information) >> "%RELEASE_DIR%\README.txt"

rem Generate checksum for installer
echo. >> "%RELEASE_DIR%\README.txt"
echo Security Verification: >> "%RELEASE_DIR%\README.txt"
certutil -hashfile "%RELEASE_DIR%\PortalReceiptsApp_Setup_v1.0.0.exe" SHA256 > temp_checksum.txt
for /f "skip=1 tokens=*" %%a in (temp_checksum.txt) do if "%%a" neq "" echo SHA256: %%a >> "%RELEASE_DIR%\README.txt" & goto :done_checksum
:done_checksum
del temp_checksum.txt

rem Create ZIP package
powershell -Command "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath 'releases\PortalReceiptsApp_v1.0.0_Release.zip' -Force"

if %ERRORLEVEL% EQU 0 (
    echo Release package created successfully!
    echo.
    echo Files ready for distribution:
    echo - releases\PortalReceiptsApp_Setup_v1.0.0.exe          (12MB installer)
    echo - releases\PortalReceiptsApp_v1.0.0_Release.zip        (Complete package)
    echo - releases\PortalReceiptsApp_v1.0.0_Release\           (Package contents)
    echo.
    echo 📋 Next steps for GitHub release:
    echo 1. Go to: https://github.com/luciaBytes/receipts/releases/new
    echo 2. Tag version: v1.0.0
    echo 3. Upload both files above
    echo 4. Copy release notes from CHANGELOG.md
    exit /b 0
) else (
    echo ERROR: Failed to create release package
    exit /b 1
)
