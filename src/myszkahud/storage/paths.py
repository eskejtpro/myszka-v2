"""Bezpieczne zarządzanie ścieżkami katalogów i baz danych MyszkaHUD."""

import os
import sys
from pathlib import Path
from typing import Optional


_OVERRIDE_DB_PATH: Optional[str] = None


def set_custom_database_path(path: Optional[str]) -> None:
    """Umożliwia ustawienie ścieżki testowej (np. :memory: lub pliku tymczasowego)."""
    global _OVERRIDE_DB_PATH
    _OVERRIDE_DB_PATH = path


def get_app_data_dir() -> Path:
    """
    Zwraca bezpieczną ścieżkę do katalogu danych aplikacji:
    - Windows: %LOCALAPPDATA%\\MyszkaHUD (lub ~\\AppData\\Local\\MyszkaHUD)
    - Linux / Inne: ~/.local/share/myszkahud lub /tmp/myszkahud
    """
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base_dir = Path(local_app_data)
        else:
            base_dir = Path.home() / "AppData" / "Local"
    else:
        # Linux / MacOS / AI Studio Container
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            base_dir = Path(xdg_data)
        else:
            base_dir = Path.home() / ".local" / "share"

    app_dir = base_dir / "MyszkaHUD"
    try:
        app_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Awaryjny fallback do katalogu tymczasowego w przypadku braku uprawnień
        import tempfile
        app_dir = Path(tempfile.gettempdir()) / "MyszkaHUD"
        app_dir.mkdir(parents=True, exist_ok=True)

    return app_dir


def get_database_path() -> str:
    """Zwraca ścieżkę do bazy SQLite (domyślnie myszkahud.db w AppData lub ścieżkę testową)."""
    global _OVERRIDE_DB_PATH
    if _OVERRIDE_DB_PATH:
        return _OVERRIDE_DB_PATH

    data_dir = get_app_data_dir()
    return str(data_dir / "myszkahud.db")
