# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect dependencies for fontkit, openpyxl, etc. if needed
# usually auto-detected, but collect_all can help for complex packages
datas = []
binaries = []
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan.on',
    'engineio.async_drivers.asgi',
    'pandas',
    'openpyxl',
    'weasyprint'
]

# Add data files (source, destination in bundle)
# Note: we are running pyinstaller from the repo root or backend?
# The create_release.bat will likely run it from the root, pointing to backend/main.py
# Let's assume we run it from root for paths to be clear, or we adjust relative paths.
# To be safe, we will assume the spec file is in the root or we run it from root.
# Actually, standard is to put spec in root or same dir as script.
# I'll put spec in root for simplicity of relative paths.

# We need to bundle:
# 1. backend/quotation.html -> .
# 2. backend/Sarabun-Regular.ttf -> .
# 3. backend/mean_sd.json -> .
# 4. frontend/dist -> dist

datas += [
    ('backend/quotation.html', '.'),
    ('backend/Sarabun-Regular.ttf', '.'),
    ('backend/mean_sd.json', '.'),
    ('frontend/dist', 'dist'),
]

# Exclude the database from the bundle (we want it external)
# PyInstaller doesn't bundle non-code files by default unless specified in datas,
# so simply NOT adding 'backend/data/Quetung.db' is enough.

a = Analysis(
    ['backend/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='smart_pricing',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # Set to False if you want to hide the terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='smart_pricing',
)
