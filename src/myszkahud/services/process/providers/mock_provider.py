"""Mock dostawcy procesów do testów jednostkowych i symulacji."""

from typing import List, Dict, Optional
from myszkahud.services.process.models import ProcessInfo, CRITICAL_SYSTEM_PROCESSES
from myszkahud.services.process.providers.base import BaseProcessProvider


class MockProcessProvider(BaseProcessProvider):
    """Zapewnia kontrolowaną listę procesów dla testów jednostkowych."""

    def __init__(self, initial_processes: Optional[List[ProcessInfo]] = None):
        if initial_processes:
            self._processes: Dict[int, ProcessInfo] = {p.pid: p for p in initial_processes}
        else:
            self._processes: Dict[int, ProcessInfo] = {
                4: ProcessInfo(pid=4, name="System", ram_bytes=100 * 1024 * 1024, is_protected=True),
                100: ProcessInfo(pid=100, name="explorer.exe", ram_bytes=250 * 1024 * 1024, is_protected=True),
                1000: ProcessInfo(
                    pid=1000,
                    name="Code.exe",
                    ram_bytes=450 * 1024 * 1024,
                    cpu_percent=2.5,
                    window_title="MyszkaHUD - Visual Studio Code",
                    is_protected=False,
                ),
                1001: ProcessInfo(
                    pid=1001,
                    name="chrome.exe",
                    ram_bytes=800 * 1024 * 1024,
                    cpu_percent=5.1,
                    window_title="Google AI Studio - Google Chrome",
                    is_protected=False,
                ),
                1002: ProcessInfo(
                    pid=1002,
                    name="python.exe",
                    ram_bytes=80 * 1024 * 1024,
                    cpu_percent=1.0,
                    window_title="MyszkaHUD",
                    is_protected=True,
                    is_current_app=True,
                ),
            }
        self.closed_pids: List[int] = []
        self.killed_pids: List[int] = []
        self.activated_pids: List[int] = []
        self.minimized_pids: List[int] = []

    def list_processes(self) -> List[ProcessInfo]:
        return list(self._processes.values())

    def close_process(self, pid: int) -> bool:
        if pid in self._processes:
            self.closed_pids.append(pid)
            del self._processes[pid]
            return True
        return False

    def force_kill_process(self, pid: int) -> bool:
        if pid in self._processes:
            self.killed_pids.append(pid)
            del self._processes[pid]
            return True
        return False

    def activate_window(self, pid: int) -> bool:
        if pid in self._processes:
            self.activated_pids.append(pid)
            return True
        return False

    def minimize_window(self, pid: int) -> bool:
        if pid in self._processes:
            self.minimized_pids.append(pid)
            return True
        return False
