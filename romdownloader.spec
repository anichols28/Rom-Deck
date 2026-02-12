# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for ROM Downloader

a = Analysis(
    ['romdownloader.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'paramiko',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='romdownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    icon=None,
)
