# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Get the project root directory (parent of build directory)
# Use os.getcwd() since __file__ is not available during PyInstaller execution
if os.path.basename(os.getcwd()) == 'build':
    project_root = Path(os.getcwd()).parent
    build_dir = Path(os.getcwd())
else:
    project_root = Path(os.getcwd())
    build_dir = project_root / 'build'

# Add src directory to Python path
src_path = str(project_root / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Application metadata
APP_NAME = "PortalReceiptsApp"
APP_VERSION = "1.0.2" 
APP_DESCRIPTION = "Portal das Finanças - Automated Receipt Processing"
COMPANY_NAME = "LuciaBytes"

# Standard paths
DIST_PATH = project_root / 'dist'
WORKPATH = build_dir / 'temp'  # Use temp directory that will be cleaned up

# Build configuration
block_cipher = None

# Analysis configuration
a = Analysis(
    [str(project_root / 'src' / 'main.py')],
    pathex=[str(project_root), str(project_root / 'src')],
    binaries=[
        # Add explicit tkinter DLL paths to fix Python 3.13 issues
        (str(Path(sys.base_exec_prefix) / 'DLLs' / 'tcl86t.dll'), '.'),
        (str(Path(sys.base_exec_prefix) / 'DLLs' / 'tk86t.dll'), '.'),
    ],
    datas=[
        # Include all source files to ensure proper module discovery
        (str(project_root / 'src'), 'src'),
        # Include documentation files if they exist
        (str(project_root / 'README.md'), '.'),
        # Include version file for runtime version detection
        (str(project_root / '.version'), '.'),
        # Include config directory for language settings
        (str(project_root / 'config'), 'config'),
    ],
    hiddenimports=[
        'requests',
        'beautifulsoup4',
        'bs4',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'threading',
        'json',
        're',
        'csv',
        'datetime',
        'logging',
        'os',
        'sys',
        'pathlib',
        'urllib.parse',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'time',
        'queue',
        # Add multilingual localization modules
        'utils.multilingual_localization',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test files and development tools
        'pytest',
        'setuptools',
        'pip',
        'wheel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    workpath=str(WORKPATH),
    distpath=str(DIST_PATH),
)

# Remove test files from datas
a.datas = [x for x in a.datas if not x[0].startswith('test_')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to prevent DLL issues
    console=False,  # Set to False for GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'assets/app_icon.ico'
    version=str(build_dir / 'version_info.txt'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX to prevent DLL issues
    upx_exclude=[],
    name=APP_NAME,
    distpath=str(DIST_PATH),
)

# Cleanup function to remove build artifacts after successful build
import shutil
import atexit

def cleanup_build_artifacts():
    """Clean up temporary build artifacts after successful build"""
    try:
        if WORKPATH.exists():
            print(f"Cleaning up build artifacts from {WORKPATH}")
            shutil.rmtree(WORKPATH)
    except Exception as e:
        print(f"Note: Could not clean up build artifacts: {e}")

# Register cleanup to run after build completion
atexit.register(cleanup_build_artifacts)
