"""Serwis zarządzania autostartem aplikacji w systemie Windows (v0.10)."""

import os
import sys
import logging
from typing import Optional

from myszkahud.services.autostart.models import AutostartStatus
from myszkahud.services.autostart.providers.base import BaseAutostartProvider
from myszkahud.services.autostart.providers.windows_provider import WindowsRegistryAutostartProvider

logger = logging.getLogger(__name__)


class AutostartService:
    """Warstwa serwisowa konfiguracji autostartu z Windows."""

    def __init__(self, provider: Optional[BaseAutostartProvider] = None, app_name: str = "MyszkaHUD"):
        self.app_name = app_name
        self._provider = provider or WindowsRegistryAutostartProvider()

    def is_autostart_enabled(self) -> bool:
        """Zwraca True, jeśli aplikacja uruchamia się przy starcie systemu."""
        return self._provider.is_enabled(self.app_name)

    def enable_autostart(self, custom_path: str = "") -> bool:
        """Włącza autostart aplikacji."""
        path = custom_path or sys.executable
        return self._provider.enable(self.app_name, path)

    def disable_autostart(self) -> bool:
        """Wyłącza autostart aplikacji."""
        return self._provider.disable(self.app_name)

    def toggle_autostart(self) -> bool:
        """Przełącza stan autostartu."""
        if self.is_autostart_enabled():
            self.disable_autostart()
            return False
        else:
            self.enable_autostart()
            return True

    def get_status(self) -> AutostartStatus:
        """Zwraca szczegółowy status autostartu."""
        enabled = self.is_autostart_enabled()
        return AutostartStatus(
            is_enabled=enabled,
            app_name=self.app_name,
            executable_path=sys.executable,
            details="Włączony w rejestrze HKCU (Windows Run)" if enabled else "Wyłączony",
        )
