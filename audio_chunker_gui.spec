# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Audio Processor - Production Build

a = Analysis(
    ['audio_chunker_gui.py'],
    pathex=[],
    binaries=[('ffmpeg', 'ffmpeg')],  # Dołącz ffmpeg folder
    datas=[],
    hiddenimports=[
        'librosa',
        'librosa.core',
        'librosa.feature',
        'soundfile',
        'numpy',
        'scipy',
        'scipy.fftpack',
        'sklearn',
        'sklearn.metrics',
        'audioread',
        'pooch',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MediaProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
