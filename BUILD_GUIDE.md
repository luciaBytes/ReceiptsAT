# Building and Distributing Portal das Finanças Receipts

This guide explains how to build the Windows executable and create a professional installer for distribution.

## 🏗️ Build Process Overview

The build process consists of two main steps:
1. **Build the executable** using PyInstaller
2. **Create the Windows installer** using Inno Setup

## 📋 Prerequisites

### Required Software
- **Python 3.8+** (with pip)
- **Inno Setup 6.0+** ([Download here](https://jrsoftware.org/isinfo.php))
- **Windows 10+** (64-bit)

### Environment Setup
1. **Install Python dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```

2. **Install Inno Setup** and add to PATH:
   - Download from [https://jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php)
   - Install with default settings
   - Add `C:\Program Files (x86)\Inno Setup 6` to your Windows PATH environment variable

## 🚀 Quick Build (Automated)

### Option 1: Complete Build Pipeline
```cmd
# Build everything: executable + installer + release package
build_all.bat
```

### Option 2: Individual Build Steps
```cmd
# Build just the executable
scripts\build_executable.bat

# Create the Windows installer
scripts\build_installer.bat

# Package for distribution
build\package_release.bat
```

## 🔧 Manual Build Process

### Step 1: Build the Executable

```cmd
# Clean previous builds
rmdir /s /q build dist

# Build with PyInstaller
pyinstaller --clean receipts_app.spec
```

**Output**: `dist/PortalReceiptsApp/PortalReceiptsApp.exe`

### Step 2: Create the Installer

```cmd
# Using Inno Setup compiler
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" installer_script.iss
```

**Output**: `releases\PortalReceiptsApp_Setup_v1.0.0.exe`

## 📁 Build Configuration Files

### `receipts_app.spec`
PyInstaller specification file that defines:
- **Entry point**: `src/main.py`
- **Hidden imports**: All required dependencies
- **Data files**: Source code and documentation
- **Executable settings**: No console window, version info
- **Output format**: One directory with all dependencies

### `installer_script.iss`
Inno Setup script that creates:
- **Professional installer**: Windows-standard installation experience
- **Start menu shortcuts**: Application and uninstaller links
- **Registry entries**: Proper Windows integration
- **Multi-language**: English and Portuguese support
- **Uninstaller**: Clean removal capability

### `version_info.txt`
Windows version information displayed in:
- File properties dialog
- Process manager
- Installation details

## 🎯 Build Output

After successful build:

```
dist/
└── PortalReceiptsApp/
    ├── PortalReceiptsApp.exe          # Main executable
    ├── _internal/                     # Python runtime and dependencies
    │   ├── base_library.zip
    │   ├── python39.dll
    │   └── [other dependencies]
    └── src/                           # Application source code
        ├── main.py
        ├── gui/
        └── utils/

releases/
├── PortalReceiptsApp_Setup_v1.0.0.exe      # Windows installer (~12MB)
├── PortalReceiptsApp_v1.0.0_Release.zip    # Complete release package
└── PortalReceiptsApp_v1.0.0_Release/       # Unpacked release folder
    ├── PortalReceiptsApp_Setup_v1.0.0.exe
    ├── README.md
    ├── CHANGELOG.md
    └── docs/USER_INSTALLATION_GUIDE.md
```

## 🧪 Testing the Build

### Test the Executable
```cmd
# Run from build directory
dist\PortalReceiptsApp\PortalReceiptsApp.exe

# Or use the test script
tests\test_build.bat
```

### Test the Installer
1. Run `releases\PortalReceiptsApp_Setup_v1.0.0.exe`
2. Follow installation wizard
3. Launch from Start Menu or Desktop shortcut
4. Verify all features work correctly

## 🛠️ Troubleshooting

### Common Build Issues

**PyInstaller Import Errors**:
- Add missing imports to `hiddenimports` in `receipts_app.spec`
- Check `build/receipts_app/warn-receipts_app.txt` for warnings

**Inno Setup Icon Missing**:
- Comment out `SetupIconFile=assets\app_icon.ico` if icon doesn't exist
- Or add a `.ico` file to the `assets/` directory

**Missing Dependencies**:
```cmd
# Reinstall dependencies
pip install --upgrade -r requirements.txt
pip install pyinstaller
```

**PATH Issues**:
- Ensure Inno Setup is in Windows PATH
- Use full path: `"C:\Program Files (x86)\Inno Setup 6\iscc.exe"`

## 🏷️ Version Management

### Manual Version Control
To update version numbers:

1. **Update `.version` file**:
   ```
   1.1.0
   ```

2. **Update `receipts_app.spec`** (if needed):
   ```python
   APP_VERSION = "1.1.0"
   ```

3. **Update `installer_script.iss`**:
   ```ini
   AppVersion=1.1.0
   VersionInfoVersion=1.1.0.0
   OutputBaseFilename=PortalReceiptsApp_Setup_v1.1.0
   ```

### Automated Version Management (GitHub Actions)
The project includes automated CI/CD that handles versioning:

- **Automatic Patch Bumping**: If `.version` unchanged in PR, auto-increment patch
- **Manual Version Control**: Update `.version` in PR for specific releases
- **Automated Builds**: Every merge to main triggers automatic build and release
- **GitHub Releases**: Professional releases with installers and documentation

**Automated Release Process**:
1. Create PR with changes
2. Unit tests run automatically 
3. Merge to main branch
4. CI/CD auto-bumps version (if not manually changed)
5. Builds Windows executable and installer
6. Creates release branch and GitHub release
7. Uploads installer and complete package

## 📊 Build Performance

**Typical build times**:
- Executable build: 30-60 seconds
- Installer creation: 5-10 seconds
- Total process: ~1-2 minutes

**Output sizes**:
- Executable directory: ~40-50MB
- Installer file: ~12MB
- Installed application: ~45-55MB

## 🔄 GitHub Actions CI/CD

The project includes complete CI/CD automation:

### Automated Testing
- **PR Testing**: Unit tests run on every pull request
- **Main Branch Testing**: Comprehensive testing on merge to main
- **61 Unit Tests**: Complete test coverage with 100% pass rate

### Automated Building
- **Windows Executable**: PyInstaller build with all dependencies
- **Professional Installer**: Inno Setup installer creation
- **Release Packaging**: Complete distribution packages

### Automated Releases
- **Version Management**: Auto-increment patch or manual version control
- **GitHub Releases**: Professional releases with proper tagging
- **Artifact Distribution**: Windows installer and complete packages
- **Release Branches**: Organized release branch structure

**Workflow Files**:
- `.github/workflows/pr-tests.yml` - PR testing
- `.github/workflows/ci.yml` - Continuous integration  
- `.github/workflows/release.yml` - Release automation
- `.github/workflows/release-branch.yml` - Release branch testing

**For Developers**: Simply merge to main and CI/CD handles the rest!

---

*This build process creates a professional, self-contained Windows application that requires no Python installation on end-user machines.*
