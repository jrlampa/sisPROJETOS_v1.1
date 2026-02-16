# -*- mode: python ; coding: utf-8 -*-

# sisPROJETOS PyInstaller Specification
# Optimized build configuration for production releases

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Templates: DWG, XLSX files (prancha.dwg, cqt.xlsx, ambiental.xlsx)
        ('src\\resources\\templates', 'resources\\templates'),
        # Database
        ('src\\resources\\sisprojetos.db', 'resources'),
        # Catenaria module resources (condutores.json)
        ('src\\modules\\catenaria\\resources', 'modules\\catenaria\\resources'),
    ],
    hiddenimports=[
        # Core
        'encodings', 'encodings.utf_8', 'codecs',
        # GUI
        'customtkinter', 'tkinter', 'tkinter.font', 'tkinter.filedialog', 'tkinter.messagebox',
        # Imaging
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'PIL.JpegImagePlugin',
        # Data processing
        'numpy', 'pandas', 'scipy', 'scipy.optimize',
        # Additional utilities
        'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends.backend_tkagg',
        # Geospatial
        'pyproj',
        # Network
        'requests', 'urllib3', 'urllib',
        # Extensions
        'json', 'csv', 'datetime', 'os', 'sys', 'pathlib', 're',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tests', 'pytest', 'notebook', 'jupyter', 'IPython'],
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
    strip=False,  # Don't strip - can cause issues
    upx=False,    # Don't compress - can cause issues
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
    strip=False,  # Don't strip - can cause issues
    upx=False,    # Don't compress - can cause issues
    name='sisPROJETOS',
)
