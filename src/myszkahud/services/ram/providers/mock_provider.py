"""Mock dostawcy pamięci RAM do testów jednostkowych."""

from typing import List, Optional
from myszkahud.services.process.models import ProcessInfo
from myszkahud.services.ram.models import RamStats
from myszkahud.services.ram.providers.base import BaseRamProvider


class MockRamProvider(BaseRamProvider):
    """Zapewnia kontrolowane i powtarzalne pomiary RAM dla testów."""

    def __init__(
        self,
        total_gb: float = 16.0,
        used_gb: float = 8.0,
        release_gain_mb: float = 250.0,
        top_processes: Optional[List[ProcessInfo]] = None,
    ):
        self.total_bytes = int(total_gb * (1024 ** 3))
        self.used_bytes = int(used_gb * (1024 ** 3))
        self.release_gain_bytes = int(release_gain_mb * (1024 ** 2))
        self.top_processes = top_processes or [
            ProcessInfo(pid=1001, name="chrome.exe", ram_bytes=800 * 1024 * 1024, is_protected=False),
            ProcessInfo(pid=1000, name="Code.exe", ram_bytes=450 * 1024 * 1024, is_protected=False),
        ]
        self.trim_calls_count = 0

    def get_ram_stats(self) -> RamStats:
        avail = max(0, self.total_bytes - self.used_bytes)
        percent = round((self.used_bytes / self.total_bytes) * 100, 1) if self.total_bytes > 0 else 0.0
        return RamStats(
            total_bytes=self.total_bytes,
            used_bytes=self.used_bytes,
            available_bytes=avail,
            percent=percent,
            top_processes=self.top_processes,
        )

    def trim_working_sets(self) -> int:
        self.trim_calls_count += 1
        # Zmniejsz zajętą pamięć o zadany realny zysk
        self.used_bytes = max(0, self.used_bytes - self.release_gain_bytes)
        return len(self.top_processes) + 1
