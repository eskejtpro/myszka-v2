"""Główny serwis monitorowania i bezpiecznego zwalniania RAM (RamService)."""

import logging
from typing import Optional

from myszkahud.services.ram.models import RamStats, RamReleaseResult
from myszkahud.services.ram.providers.base import BaseRamProvider
from myszkahud.services.ram.providers.psutil_provider import PsutilRamProvider

logger = logging.getLogger(__name__)


class RamService:
    """Warstwa logiki dla monitoringu i zwalniania pamięci operacyjnej."""

    def __init__(self, provider: Optional[BaseRamProvider] = None):
        self._provider = provider or PsutilRamProvider()

    def get_stats(self) -> RamStats:
        """Zwraca aktualny stan pamięci RAM."""
        return self._provider.get_ram_stats()

    def release_memory_safe(self) -> RamReleaseResult:
        """Wykonuje bezpieczne i konserwatywne odzyskanie pamięci RAM z realnym pomiarem przed/po."""
        # 1. Dokładny pomiar PRZED
        before_stats = self._provider.get_ram_stats()
        before_used = before_stats.used_bytes

        # 2. Wykonanie bezpiecznego trimowania
        try:
            trimmed_count = self._provider.trim_working_sets()
        except Exception as e:
            logger.error(f"Wyjątek podczas zwalniania pamięci: {e}")
            trimmed_count = 0

        # 3. Dokładny pomiar PO
        after_stats = self._provider.get_ram_stats()
        after_used = after_stats.used_bytes

        released_bytes = max(0, before_used - after_used)

        details = (
            f"Zwolniono bezpiecznie {round(released_bytes / (1024*1024), 1)} MB "
            f"(obsłużono {trimmed_count} procesów)."
        )

        return RamReleaseResult(
            before_used_bytes=before_used,
            after_used_bytes=after_used,
            released_bytes=released_bytes,
            trimmed_processes_count=trimmed_count,
            success=True,
            details=details,
        )
