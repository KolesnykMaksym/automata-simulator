# PyInstaller spec for the GUI binary (`automata-sim`).
# Build with: pyinstaller packaging/automata-sim.spec --clean

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

PROJECT_ROOT = Path(SPECPATH).parent  # noqa: F821 — SPECPATH injected by PyInstaller

block_cipher = None

a = Analysis(  # noqa: F821 — PyInstaller globals
    [str(PROJECT_ROOT / "automata_simulator" / "gui" / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[
        *collect_submodules("automata_simulator"),
        *collect_submodules("pydantic"),
        *collect_submodules("pydantic_core"),
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Keep the bundle small: skip test-only deps.
        "hypothesis",
        "pytest",
        "pytest_qt",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="automata-sim",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="automata-sim",
)
