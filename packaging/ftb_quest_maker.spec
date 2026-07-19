# PyInstaller specification for the standalone FTB Quest Maker desktop application.
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules("content")
    + collect_submodules("generator")
    + collect_submodules("model")
)

a = Analysis(
    ["generator/desktop_entry.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
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
    name="FTBQuestMaker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
