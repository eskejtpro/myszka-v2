"""Abstrakcyjna klasa bazowa dostawcy pamięci RAM (BaseRamProvider)."""

from abc import ABC, abstractmethod
from myszkahud.services.ram.models import RamStats, RamReleaseResult


class BaseRamProvider(ABC):
    """Interfejs dostawcy statystyk i operacji na pamięci RAM."""

    @abstractmethod
    def get_ram_stats(self) -> RamStats:
        """Pobiera aktualne statystyki pamięci RAM."""
        pass

    @abstractmethod
    def trim_working_sets(self) -> int:
        """Wykonuje bezpieczne odzyskanie pamięci (working set trim) i zwraca liczbę obsłużonych procesów."""
        pass
