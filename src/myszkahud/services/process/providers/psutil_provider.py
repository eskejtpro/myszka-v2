"""Dostawca procesów oparty o bibliotekę psutil i Windows API ctypes."""

import os
import sys
import logging
from typing import List, Optional

from myszkahud.services.process.models import ProcessInfo, CRITICAL_SYSTEM_PROCESSES
from myszkahud.services.process.providers.base import BaseProcessProvider

logger = logging.getLogger(__name__)


class PsutilProcessProvider(BaseProcessProvider):
    """Pobiera i zarządza procesami przy użyciu psutil oraz natywnych wywołań Windows."""

    def __init__(self):
        self._current_pid = os.getpid()

    def list_processes(self) -> List[ProcessInfo]:
        try:
            import psutil
        except ImportError:
            logger.warning("Biblioteka psutil nie jest zainstalowana. Zwracanie pustej listy.")
            return []

        results: List[ProcessInfo] = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'status', 'exe']):
            try:
                info = proc.info
                pid = info.get('pid')
                if pid is None or pid == 0:
                    continue

                name = info.get('name') or f"Process_{pid}"
                mem_info = info.get('memory_info')
                ram_bytes = mem_info.rss if mem_info else 0
                cpu = info.get('cpu_percent') or 0.0
                status = info.get('status') or "running"
                exe = info.get('exe')

                is_current = (pid == self._current_pid)
                is_protected = (
                    is_current or
                    name.lower() in CRITICAL_SYSTEM_PROCESSES or
                    pid <= 4  # System Idle Process / System
                )

                # Próba odczytania tytułu okna (w Windows)
                window_title = self._get_window_title(pid)

                results.append(
                    ProcessInfo(
                        pid=pid,
                        name=name,
                        ram_bytes=ram_bytes,
                        cpu_percent=cpu,
                        status=str(status),
                        exe_path=exe,
                        window_title=window_title,
                        is_protected=is_protected,
                        is_current_app=is_current,
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug(f"Błąd odczytu informacji o procesie: {e}")
                continue

        return results

    def _get_window_title(self, pid: int) -> Optional[str]:
        if sys.platform != "win32":
            return None
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            found_title = None

            def enum_windows_proc(hwnd, lparam):
                nonlocal found_title
                if not user32.IsWindowVisible(hwnd):
                    return True
                window_pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                if window_pid.value == pid:
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        if buff.value:
                            found_title = buff.value
                            return False  # stop enumeration
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
            return found_title
        except Exception:
            return None

    def close_process(self, pid: int) -> bool:
        """Wysyła bezpieczny sygnał zamknięcia (WM_CLOSE dla okna lub terminate())."""
        try:
            import psutil
            proc = psutil.Process(pid)
            proc.terminate()
            return True
        except ImportError:
            logger.warning("Brak biblioteki psutil.")
            return False
        except Exception as e:
            logger.warning(f"Nie udało się zamknąć procesu PID {pid}: {e}")
            return False

    def force_kill_process(self, pid: int) -> bool:
        """Wymusza natychmiastowe zabicie procesu."""
        try:
            import psutil
            proc = psutil.Process(pid)
            proc.kill()
            return True
        except ImportError:
            logger.warning("Brak biblioteki psutil.")
            return False
        except Exception as e:
            logger.warning(f"Nie udało się wymusić zabicia procesu PID {pid}: {e}")
            return False

    def activate_window(self, pid: int) -> bool:
        if sys.platform != "win32":
            return False
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32

            target_hwnd = None
            def enum_proc(hwnd, lparam):
                nonlocal target_hwnd
                if user32.IsWindowVisible(hwnd):
                    window_pid = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                    if window_pid.value == pid:
                        target_hwnd = hwnd
                        return False
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
            if target_hwnd:
                user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(target_hwnd)
                return True
            return False
        except Exception:
            return False

    def minimize_window(self, pid: int) -> bool:
        if sys.platform != "win32":
            return False
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32

            target_hwnd = None
            def enum_proc(hwnd, lparam):
                nonlocal target_hwnd
                if user32.IsWindowVisible(hwnd):
                    window_pid = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
                    if window_pid.value == pid:
                        target_hwnd = hwnd
                        return False
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
            if target_hwnd:
                user32.ShowWindow(target_hwnd, 6)  # SW_MINIMIZE
                return True
            return False
        except Exception:
            return False
