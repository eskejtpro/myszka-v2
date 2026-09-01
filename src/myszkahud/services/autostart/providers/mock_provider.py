"""Mock dostawcy autostartu do testów jednostkowych."""

from myszkahud.services.autostart.providers.base import BaseAutostartProvider


class MockAutostartProvider(BaseAutostartProvider):
    """Przechowuje stan autostartu w pamięci dla testów."""

    def __init__(self, initial_enabled: bool = False):
        self._enabled = initial_enabled
        self._entries = {}
        if initial_enabled:
            self._entries["MyszkaHUD"] = "C:\\Program Files\\MyszkaHUD\\MyszkaHUD.exe"

    def is_enabled(self, app_name: str = "MyszkaHUD") -> bool:
        return app_name in self._entries

    def enable(self, app_name: str = "MyszkaHUD", exec_path: str = "") -> bool:
        self._entries[app_name] = exec_path or "C:\\MyszkaHUD.exe"
        self._enabled = True
        return True

    def disable(self, app_name: str = "MyszkaHUD") -> bool:
        self._entries.pop(app_name, None)
        self._enabled = False
        return True
