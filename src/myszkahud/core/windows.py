"""Adapter zarządzania oknami, fokusem i schowkiem Windows (Win32 API)."""

import sys
import time
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple


# Stałe konfiguracyjne schowka
DEFAULT_CLIPBOARD_CAPTURE_TIMEOUT_MS = 350
CLIPBOARD_POLL_INTERVAL_MS = 25


class WindowManager:
    """Zarządza zapamiętywaniem i przywracaniem aktywnego okna użytkownika (HWND)."""

    def __init__(self):
        self._target_hwnd: Optional[int] = None
        self._myszkahud_hwnd: Optional[int] = None

    def set_app_hwnd(self, hwnd: int) -> None:
        """Rejestruje HWND okna MyszkaHUD, aby unikać wysyłania akcji do samego siebie."""
        self._myszkahud_hwnd = hwnd

    def capture_foreground_window(self) -> Optional[int]:
        """Pobiera i zapamiętuje HWND aktualnie aktywnego okna przed pokazaniem HUD."""
        if sys.platform != "win32":
            return None

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()

        # Nie zapamiętujemy, jeśli aktywnym oknem jest już MyszkaHUD lub brak okna
        if hwnd and hwnd != self._myszkahud_hwnd:
            self._target_hwnd = hwnd
            return hwnd
        return None

    @property
    def target_hwnd(self) -> Optional[int]:
        """Zwraca ostatnio zapamiętany uchwyt HWND okna docelowego."""
        return self._target_hwnd

    def is_window_valid(self, hwnd: Optional[int] = None) -> bool:
        """Sprawdza czy dane okno (lub zapamiętane target_hwnd) nadal istnieje."""
        h = hwnd if hwnd is not None else self._target_hwnd
        if not h:
            return False
        if sys.platform != "win32":
            return True
        user32 = ctypes.windll.user32
        return bool(user32.IsWindow(h))

    def restore_focus(self, delay_ms: int = 40) -> bool:
        """
        Przywraca fokus do poprzednio aktywnego okna.
        Zwraca True, jeśli operacja powiodła się i okno jest poprawne.
        """
        if not self.is_window_valid():
            return False

        if sys.platform != "win32":
            return True

        user32 = ctypes.windll.user32

        # Jeśli okno jest zminimalizowane, przywracamy
        if user32.IsIconic(self._target_hwnd):
            user32.ShowWindow(self._target_hwnd, 9)  # SW_RESTORE = 9

        success = user32.SetForegroundWindow(self._target_hwnd)

        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

        return bool(success)

    def clear(self) -> None:
        """Czyści zapamiętany uchwyt okna."""
        self._target_hwnd = None


class ClipboardFreshnessGuard:
    """
    Zabezpieczenie przed używaniem przestarzałej zawartości schowka Windows.
    Wykorzystuje Win32 GetClipboardSequenceNumber, aby wykryć, czy po wysłaniu
    Ctrl+C schowek rzeczywiście uległ zmianie (użytkownik zaznaczył tekst).
    Nie czyści bezmyślnie istniejącej zawartości schowka użytkownika!
    """

    def __init__(self, timeout_ms: int = DEFAULT_CLIPBOARD_CAPTURE_TIMEOUT_MS):
        self.timeout_ms = timeout_ms

    def get_sequence_number(self) -> int:
        """Zwraca bieżący numer sekwencji schowka Windows (Win32 API)."""
        if sys.platform != "win32":
            return 0
        user32 = ctypes.windll.user32
        return int(user32.GetClipboardSequenceNumber())

    def wait_for_clipboard_change(
        self,
        initial_seq: int,
        poll_interval_ms: int = CLIPBOARD_POLL_INTERVAL_MS
    ) -> bool:
        """
        Krótki, nieblokujący polling oczekujący na zmianę numeru sekwencji schowka.
        Kończy się natychmiast po wykryciu zmiany lub po upływie timeout_ms.
        """
        if sys.platform != "win32":
            return False

        start_time = time.perf_counter()
        deadline = start_time + (self.timeout_ms / 1000.0)
        poll_sec = poll_interval_ms / 1000.0

        while time.perf_counter() < deadline:
            current_seq = self.get_sequence_number()
            if current_seq != initial_seq:
                return True
            time.sleep(poll_sec)

        return False
