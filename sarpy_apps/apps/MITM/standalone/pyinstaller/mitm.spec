# -*- mode: python ; coding: utf-8 -*-

# *******************************************************************************
# To compile PyMITM as a standalone executable with PyInstaller:
#       $ cd standalone/pyinstaller 
#       $ pyinstaller mitm.spec
# To run the resulting executable:
#       $ ./dist/mitm.exe
# *******************************************************************************

import sys

data_files = [
    (sys.prefix + '/Lib/site-packages/sarpy/io/complex/sicd_schema/*.xsd', 'sarpy/io/complex/sicd_schema'),
    (sys.prefix + '/Lib/site-packages/sarpy/io/phase_history/cphd_schema/*.xsd', 'sarpy/io/phase_history/cphd_schema'),
    (sys.prefix + '/Lib/site-packages/PyMITM/resources/', 'PyMITM/resources')
]

a = Analysis(
    ['../../main.py'],
    pathex=[],
    binaries=[],
    datas=data_files,
    hiddenimports=['PyMITM'],
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
    name='mitm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
