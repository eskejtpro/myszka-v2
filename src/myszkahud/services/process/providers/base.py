"""Abstrakcyjna klasa bazowa dostawcy procesów (Process Provider)."""

from abc import ABC, abstractmethod
from typing import List
from myszkahud.services.process.models import ProcessInfo


class BaseProcessProvider(ABC):
    """Interfejs dla źródeł danych o procesach systemowych."""

    @abstractmethod
    def list_processes(self) -> List[ProcessInfo]:
        """Pobiera listę uruchomionych procesów w systemie."""
        pass

    @abstractmethod
    def close_process(self, pid: int) -> bool:
        """Wysyła bezpieczny sygnał zamknięcia (WM_CLOSE / SIGTERM)."""
        pass

    @abstractmethod
    def force_kill_process(self, pid: int) -> bool:
        """Wymusza natychmiastowe zabicie procesu (TerminateProcess / SIGKILL)."""
        pass

    @abstractmethod
    def activate_window(self, pid: int) -> bool:
        """Przywraca i aktywuje okno procesu na pierwszym planie."""
        pass

    @abstractmethod
    def minimize_window(self, pid: int) -> bool:
        """Minimalizuje okno skojarzone z danym procesem."""
        pass
