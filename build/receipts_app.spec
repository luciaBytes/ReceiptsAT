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
APP_NAME = "Portal das Finanças Receipts"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Automates rent receipt issuance through Portuguese Tax Authority"
COMPANY_NAME = "LuciaBytes"

# Build configuration
block_cipher = None

# Analysis configuration
a = Analysis(
    [str(project_root / 'src' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include all source files to ensure proper module discovery
        (str(project_root / 'src'), 'src'),
        # Include documentation files if they exist
        (str(project_root / 'README.md'), '.'),
        # Include version file for runtime version detection
        (str(project_root / '.version'), '.'),
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
)

# Remove test files from datas
a.datas = [x for x in a.datas if not x[0].startswith('test_')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PortalReceiptsApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='PortalReceiptsApp',
    distpath=str(project_root / 'dist'),
)
