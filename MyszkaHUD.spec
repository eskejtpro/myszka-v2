# -*- mode: python ; coding: utf-8 -*-
"""Specyfikacja PyInstaller dla MyszkaHUD (Windows 10 x64).

Tworzy zoptymalizowaną, pojedynczą aplikację okienkową EXE (GUI / noconsole)
z kompletem wymaganych modułów PySide6, QtMultimedia, psutil, SQLite i Google GenAI.
"""

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Katalog źródłowy aplikacji
project_root = os.path.abspath(os.getcwd())
src_path = os.path.join(project_root, "src")

# Ukryte importy wymagane przez architekturę dynamiczną i providery
hidden_imports = [
    "myszkahud",
    "myszkahud.main",
    "myszkahud.application",
    "myszkahud.core",
    "myszkahud.core.hotkeys",
    "myszkahud.core.windows",
    "myszkahud.core.text_actions",
    "myszkahud.core.single_instance",
    "myszkahud.core.safe_logging",
    "myszkahud.services.gemini.client",
    "myszkahud.services.translation.translator",
    "myszkahud.services.ocr.engine",
    "myszkahud.services.speech.service",
    "myszkahud.services.clipboard",
    "myszkahud.services.process",
    "myszkahud.services.ram",
    "myszkahud.services.settings",
    "myszkahud.services.autostart",
    "myszkahud.storage.paths",
    "myszkahud.storage.database",
    "myszkahud.storage.clipboard_repo",
    "myszkahud.storage.notes_repo",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtMultimedia",
    "sqlite3",
    "json",
    "ctypes",
    "logging",
]

# Dodanie opcjonalnych pakietów jeśli są obecne
for pkg in ["psutil", "google.genai", "winsdk"]:
    try:
        hidden_imports.extend(collect_submodules(pkg))
    except Exception:
        pass

# Wykluczenia ciężkich, nieużywanych bibliotek w celu minimalizacji rozmiaru EXE
excludes = [
    "tkinter",
    "matplotlib",
    "numpy.distutils",
    "scipy",
    "pandas",
    "IPython",
    "notebook",
    "unittest",
    "test",
    "pytest",
]

a = Analysis(
    [os.path.join(src_path, "myszkahud", "main.py")],
    pathex=[src_path, project_root],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MyszkaHUD",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Produkcyjna aplikacja GUI bez czarnego okna CMD
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
