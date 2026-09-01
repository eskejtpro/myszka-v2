"""Modele danych dla modułu Zarządzania Procesami i Aplikacjami (Process Manager)."""

import os
from dataclasses import dataclass
from typing import Optional, Set


# Zbiór krytycznych procesów systemowych Windows, których nie wolno ubijać
CRITICAL_SYSTEM_PROCESSES: Set[str] = {
    "system",
    "registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "lsass.exe",
    "winlogon.exe",
    "dwm.exe",
    "svchost.exe",
    "fontdrvhost.exe",
    "sihost.exe",
    "explorer.exe",
    "ntoskrnl.exe",
}


@dataclass
class ProcessInfo:
    """Reprezentuje pojedynczy proces w systemie operacyjnym."""

    pid: int
    name: str
    ram_bytes: int = 0
    cpu_percent: float = 0.0
    status: str = "running"
    exe_path: Optional[str] = None
    window_title: Optional[str] = None
    is_protected: bool = False
    is_current_app: bool = False

    @property
    def ram_mb(self) -> float:
        """Zwraca zużycie pamięci RAM w megabajtach."""
        return round(self.ram_bytes / (1024 * 1024), 1)

    @property
    def display_name(self) -> str:
        """Czytelna nazwa aplikacji do wyświetlenia w UI."""
        if self.window_title and len(self.window_title.strip()) > 0:
            return self.window_title
        return self.name

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "name": self.name,
            "display_name": self.display_name,
            "ram_bytes": self.ram_bytes,
            "ram_mb": self.ram_mb,
            "cpu_percent": self.cpu_percent,
            "status": self.status,
            "exe_path": self.exe_path,
            "window_title": self.window_title,
            "is_protected": self.is_protected,
            "is_current_app": self.is_current_app,
        }
