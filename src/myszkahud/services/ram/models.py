"""Modele danych dla modułu monitorowania i bezpiecznego zwalniania pamięci RAM (v0.8)."""

from dataclasses import dataclass, field
from typing import List, Optional
from myszkahud.services.process.models import ProcessInfo


@dataclass
class RamStats:
    """Statystyki pamięci operacyjnej RAM."""

    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent: float
    swap_total_bytes: int = 0
    swap_used_bytes: int = 0
    top_processes: List[ProcessInfo] = field(default_factory=list)

    @property
    def total_gb(self) -> float:
        return round(self.total_bytes / (1024 ** 3), 2)

    @property
    def used_gb(self) -> float:
        return round(self.used_bytes / (1024 ** 3), 2)

    @property
    def available_gb(self) -> float:
        return round(self.available_bytes / (1024 ** 3), 2)

    @property
    def used_mb(self) -> float:
        return round(self.used_bytes / (1024 ** 2), 1)

    @property
    def total_mb(self) -> float:
        return round(self.total_bytes / (1024 ** 2), 1)

    def to_dict(self) -> dict:
        return {
            "total_gb": self.total_gb,
            "used_gb": self.used_gb,
            "available_gb": self.available_gb,
            "percent": self.percent,
            "used_mb": self.used_mb,
            "total_mb": self.total_mb,
            "top_processes": [p.to_dict() for p in self.top_processes],
        }


@dataclass
class RamReleaseResult:
    """Rezultat bezpiecznej próby zwolnienia pamięci RAM."""

    before_used_bytes: int
    after_used_bytes: int
    released_bytes: int
    trimmed_processes_count: int
    success: bool = True
    details: str = ""

    @property
    def released_mb(self) -> float:
        return round(self.released_bytes / (1024 ** 2), 1)

    @property
    def before_used_mb(self) -> float:
        return round(self.before_used_bytes / (1024 ** 2), 1)

    @property
    def after_used_mb(self) -> float:
        return round(self.after_used_bytes / (1024 ** 2), 1)
