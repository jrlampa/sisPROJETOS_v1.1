# -*- mode: python ; coding: utf-8 -*-

# sisPROJETOS PyInstaller Specification
# Optimized build configuration for production releases

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/resources', 'src/resources')],  # Database removed - goes to AppData
    hiddenimports=['encodings', 'customtkinter', 'tkinter', 'PIL', 'PIL.Image'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tests', 'pytest'],  # Removed setuptools, pip, wheel, distutils - needed by dependencies
    noarchive=False,
    optimize=2,  # Bytecode optimization level 2
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='sisPROJETOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Remove debug symbols
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86_64',  # Explicit x64
    codesign_identity=None,  # TODO: Add certificate for code signing
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,  # Remove debug symbols
    upx=True,
    upx_exclude=['vcruntime140.dll', 'python312.dll'],  # Don't compress runtime DLLs
    name='sisPROJETOS',
)
