# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['background_sync_service.py'],
    pathex=[],
    binaries=[],
    datas=[('data_storage.py', '.'), ('adms_listener.py', '.')],
    hiddenimports=['data_storage', 'adms_listener', '_strptime'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='background_sync_service',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
