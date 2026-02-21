# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Bluestreak Box Uploader."""

import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = Path(SPECPATH)

# Data files to include
datas = [
    (str(project_root / 'app.ico'), '.'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'box_sdk_gen',
    'box_sdk_gen.managers',
    'box_sdk_gen.schemas',
    'pyodbc',
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'tomllib',
    'tomli_w',
]

a = Analysis(
    ['app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Bluestreak Box Uploader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'app.ico') if sys.platform == 'win32' else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Bluestreak Box Uploader',
)

# macOS app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Bluestreak Box Uploader.app',
        icon=str(project_root / 'app.icns') if (project_root / 'app.icns').exists() else None,
        bundle_identifier='com.burtonindustries.bluestreakboxuploader',
        info_plist={
            'CFBundleName': 'Bluestreak Box Uploader',
            'CFBundleDisplayName': 'Bluestreak Box Uploader',
            'CFBundleShortVersionString': '0.1.1',
            'CFBundleVersion': '0.1.1',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.15',
        },
    )
