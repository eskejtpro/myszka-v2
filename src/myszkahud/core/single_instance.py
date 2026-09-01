"""Mechanizm ochrony przed wielokrotnym uruchomieniem (Single Instance Guard).

W systemie Windows wykorzystuje Win32 Named Mutex (CreateMutexW).
W innych środowiskach (Linux/Testy) wykorzystuje blokadę plikową w katalogu tymczasowym / LocalAppData.
"""

import os
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)

MUTEX_NAME = "Local\\MyszkaHUD_App_SingleInstance_Mutex"
LOCK_FILE_NAME = "myszkahud.lock"


class SingleInstanceGuard:
    """Zapewnia, że w systemie uruchomiona jest tylko jedna instancja MyszkaHUD."""

    def __init__(self, mutex_name: str = MUTEX_NAME, app_dir: Optional[str] = None):
        self.mutex_name = mutex_name
        self.app_dir = app_dir
        self._mutex_handle = None
        self._lock_file_fd = None
        self._is_primary_instance: bool = False

    def acquire(self) -> bool:
        """
        Próbuje zająć blokadę instancji.
        Zwraca True, jeśli ta instancja jest jedyną/główną instancją.
        Zwraca False, jeśli inna instancja już działa.
        """
        if sys.platform == "win32":
            return self._acquire_windows_mutex()
        else:
            return self._acquire_fallback_lock()

    def _acquire_windows_mutex(self) -> bool:
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32
            ERROR_ALREADY_EXISTS = 183

            kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
            kernel32.CreateMutexW.restype = ctypes.c_void_p

            handle = kernel32.CreateMutexW(None, True, self.mutex_name)
            last_error = kernel32.GetLastError()

            if not handle:
                logger.warning(f"Nie udało się utworzyć mutexu Windows {self.mutex_name}")
                return True

            if last_error == ERROR_ALREADY_EXISTS:
                kernel32.CloseHandle(handle)
                self._mutex_handle = None
                self._is_primary_instance = False
                logger.info(f"Wykryto inną aktywną instancję MyszkaHUD (Mutex: {self.mutex_name}).")
                return False

            self._mutex_handle = handle
            self._is_primary_instance = True
            return True
        except Exception as e:
            logger.warning(f"Błąd Win32 Mutex: {e}. Przełączanie na blokadę awaryjną.")
            return self._acquire_fallback_lock()

    def _acquire_fallback_lock(self) -> bool:
        try:
            if not self.app_dir:
                if sys.platform == "win32":
                    base = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
                else:
                    base = os.getenv("XDG_RUNTIME_DIR", "/tmp")
                self.app_dir = os.path.join(base, "MyszkaHUD")

            os.makedirs(self.app_dir, exist_ok=True)
            lock_path = os.path.join(self.app_dir, LOCK_FILE_NAME)

            if sys.platform != "win32":
                import fcntl
                fd = open(lock_path, "w")
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fd.write(str(os.getpid()))
                    fd.flush()
                    self._lock_file_fd = fd
                    self._is_primary_instance = True
                    return True
                except (IOError, BlockingIOError):
                    fd.close()
                    self._is_primary_instance = False
                    return False
            else:
                if os.path.exists(lock_path):
                    try:
                        os.remove(lock_path)
                    except OSError:
                        self._is_primary_instance = False
                        return False
                self._lock_file_fd = open(lock_path, "w")
                self._lock_file_fd.write(str(os.getpid()))
                self._lock_file_fd.flush()
                self._is_primary_instance = True
                return True
        except Exception as e:
            logger.warning(f"Błąd blokady instancji fallback: {e}")
            self._is_primary_instance = True
            return True

    def release(self) -> None:
        """Zwalnia mutex lub deskryptor blokady plikowej."""
        if sys.platform == "win32" and self._mutex_handle:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.ReleaseMutex(self._mutex_handle)
                kernel32.CloseHandle(self._mutex_handle)
            except Exception as e:
                logger.debug(f"Błąd zwalniania mutexu: {e}")
            finally:
                self._mutex_handle = None

        if self._lock_file_fd:
            try:
                if sys.platform != "win32":
                    import fcntl
                    fcntl.flock(self._lock_file_fd, fcntl.LOCK_UN)
                self._lock_file_fd.close()
            except Exception as e:
                logger.debug(f"Błąd zamykania pliku blokady: {e}")
            finally:
                self._lock_file_fd = None

        self._is_primary_instance = False

    def __del__(self):
        self.release()

    @property
    def is_primary(self) -> bool:
        return self._is_primary_instance
