"""Modele danych dla modułu autostartu Windows (v0.10)."""

from dataclasses import dataclass


@dataclass
class AutostartStatus:
    """Informacje o stanie autostartu aplikacji."""

    is_enabled: bool
    app_name: str = "MyszkaHUD"
    executable_path: str = ""
    details: str = ""
