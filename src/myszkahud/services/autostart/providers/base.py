"""Abstrakcyjna klasa bazowa dla zarządzania autostartem (BaseAutostartProvider)."""

from abc import ABC, abstractmethod


class BaseAutostartProvider(ABC):
    """Interfejs dostawcy autostartu aplikacji w systemie operacyjnym."""

    @abstractmethod
    def is_enabled(self, app_name: str = "MyszkaHUD") -> bool:
        """Sprawdza, czy aplikacja jest dodana do autostartu."""
        pass

    @abstractmethod
    def enable(self, app_name: str = "MyszkaHUD", exec_path: str = "") -> bool:
        """Włącza autostart aplikacji."""
        pass

    @abstractmethod
    def disable(self, app_name: str = "MyszkaHUD") -> bool:
        """Wyłącza autostart aplikacji."""
        pass
