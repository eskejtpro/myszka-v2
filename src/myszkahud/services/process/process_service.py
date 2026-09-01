"""Główny serwis zarządzania procesami i aplikacjami (ProcessService)."""

import os
import logging
from typing import List, Optional

from myszkahud.services.process.models import ProcessInfo, CRITICAL_SYSTEM_PROCESSES
from myszkahud.services.process.providers.base import BaseProcessProvider
from myszkahud.services.process.providers.psutil_provider import PsutilProcessProvider

logger = logging.getLogger(__name__)


class ProcessService:
    """Warstwa logiki biznesowej i bezpieczeństwa dla procesów systemowych."""

    def __init__(self, provider: Optional[BaseProcessProvider] = None):
        self._provider = provider or PsutilProcessProvider()
        self._own_pid = os.getpid()

    def list_processes(
        self,
        search_query: Optional[str] = None,
        only_with_windows: bool = False,
        sort_by: str = "ram",
        reverse: bool = True,
    ) -> List[ProcessInfo]:
        """Zwraca przefiltrowaną i posortowaną listę procesów."""
        procs = self._provider.list_processes()

        # Oznacz procesy chronione
        for p in procs:
            if p.pid == self._own_pid or p.name.lower() in CRITICAL_SYSTEM_PROCESSES:
                p.is_protected = True
            if p.pid == self._own_pid:
                p.is_current_app = True

        # Filtrowanie
        if only_with_windows:
            procs = [p for p in procs if p.window_title and len(p.window_title.strip()) > 0]

        if search_query and search_query.strip():
            q = search_query.strip().lower()
            procs = [
                p for p in procs
                if q in p.name.lower() or (p.window_title and q in p.window_title.lower()) or q in str(p.pid)
            ]

        # Sortowanie
        if sort_by == "ram":
            procs.sort(key=lambda p: p.ram_bytes, reverse=reverse)
        elif sort_by == "cpu":
            procs.sort(key=lambda p: p.cpu_percent, reverse=reverse)
        elif sort_by == "name":
            procs.sort(key=lambda p: p.display_name.lower(), reverse=not reverse)
        elif sort_by == "pid":
            procs.sort(key=lambda p: p.pid, reverse=not reverse)

        return procs

    def is_protected(self, pid: int, name: Optional[str] = None) -> bool:
        """Sprawdza czy dany proces jest procesem chronionym."""
        if pid == self._own_pid or pid <= 4:
            return True
        if name and name.lower() in CRITICAL_SYSTEM_PROCESSES:
            return True
        # Pobierz informację z providera jeśli nazwa nie została podana
        procs = self._provider.list_processes()
        for p in procs:
            if p.pid == pid:
                return p.is_protected or (p.name.lower() in CRITICAL_SYSTEM_PROCESSES)
        return False

    def close_process(self, pid: int) -> bool:
        """Bezpieczne zamykanie procesu (odmowa dla procesów chronionych)."""
        if self.is_protected(pid):
            logger.warning(f"Odmowa zamknięcia: proces PID {pid} jest chroniony!")
            return False
        return self._provider.close_process(pid)

    def force_kill_process(self, pid: int) -> bool:
        """Wymuszone ubicie procesu (odmowa dla procesów chronionych)."""
        if self.is_protected(pid):
            logger.warning(f"Odmowa ubicia: proces PID {pid} jest chroniony!")
            return False
        return self._provider.force_kill_process(pid)

    def activate_window(self, pid: int) -> bool:
        """Aktywacja okna procesu."""
        return self._provider.activate_window(pid)

    def minimize_window(self, pid: int) -> bool:
        """Minimalizacja okna procesu."""
        return self._provider.minimize_window(pid)
