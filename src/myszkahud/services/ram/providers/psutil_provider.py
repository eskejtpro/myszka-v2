"""Dostawca statystyk RAM oparty o psutil i Windows API EmptyWorkingSet."""

import gc
import os
import sys
import logging
from typing import List

from myszkahud.services.process.models import ProcessInfo, CRITICAL_SYSTEM_PROCESSES
from myszkahud.services.process.providers.psutil_provider import PsutilProcessProvider
from myszkahud.services.ram.models import RamStats
from myszkahud.services.ram.providers.base import BaseRamProvider

logger = logging.getLogger(__name__)


class PsutilRamProvider(BaseRamProvider):
    """Pobiera statystyki RAM i bezpiecznie wywołuje zwolnienie working setów."""

    def __init__(self, process_provider: PsutilProcessProvider = None):
        self._process_provider = process_provider or PsutilProcessProvider()
        self._own_pid = os.getpid()

    def get_ram_stats(self) -> RamStats:
        try:
            import psutil
            vmem = psutil.virtual_memory()
            swap = psutil.swap_memory() if hasattr(psutil, 'swap_memory') else None

            # Pobierz top 5 procesów wg RAM
            procs = self._process_provider.list_processes()
            procs.sort(key=lambda p: p.ram_bytes, reverse=True)
            top_procs = procs[:5]

            return RamStats(
                total_bytes=vmem.total,
                used_bytes=vmem.used,
                available_bytes=vmem.available,
                percent=vmem.percent,
                swap_total_bytes=swap.total if swap else 0,
                swap_used_bytes=swap.used if swap else 0,
                top_processes=top_procs,
            )
        except ImportError:
            # Fallback dla środowisk bez psutil
            total = 16 * 1024 * 1024 * 1024  # 16 GB
            used = 8 * 1024 * 1024 * 1024   # 8 GB
            return RamStats(
                total_bytes=total,
                used_bytes=used,
                available_bytes=total - used,
                percent=50.0,
                top_processes=[],
            )
        except Exception as e:
            logger.error(f"Błąd odczytu statystyk RAM: {e}")
            return RamStats(
                total_bytes=0,
                used_bytes=0,
                available_bytes=0,
                percent=0.0,
                top_processes=[],
            )

    def trim_working_sets(self) -> int:
        """Konserwatywne i bezpieczne zwolnienie pamięci (GC + Windows EmptyWorkingSet)."""
        # 1. Zawsze uruchom garbage collection Pythona wewnątrz aplikacji
        gc.collect()

        trimmed_count = 0
        if sys.platform != "win32":
            # Poza Windows wykonano tylko gc.collect()
            return 1

        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi

            # Stałe uprawnień
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_SET_QUOTA = 0x0100
            desired_access = PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA

            # 2. Zawsze zoptymalizuj własny proces MyszkaHUD
            own_handle = kernel32.OpenProcess(desired_access, False, self._own_pid)
            if own_handle:
                try:
                    if psapi.EmptyWorkingSet(own_handle):
                        trimmed_count += 1
                finally:
                    kernel32.CloseHandle(own_handle)

            # 3. Bezpieczne odpytanie procesów użytkownika (pomijając chronione i systemowe)
            try:
                import psutil
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        pid = proc.info['pid']
                        name = proc.info.get('name', '')
                        if (
                            pid <= 4
                            or pid == self._own_pid
                            or (name and name.lower() in CRITICAL_SYSTEM_PROCESSES)
                        ):
                            continue

                        h_proc = kernel32.OpenProcess(desired_access, False, pid)
                        if h_proc:
                            try:
                                if psapi.EmptyWorkingSet(h_proc):
                                    trimmed_count += 1
                            finally:
                                kernel32.CloseHandle(h_proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception as e:
                logger.debug(f"Pominięto procesy zewnętrzne przy trimowaniu: {e}")

        except Exception as e:
            logger.warning(f"Błąd podczas wywołania EmptyWorkingSet: {e}")

        return max(1, trimmed_count)
