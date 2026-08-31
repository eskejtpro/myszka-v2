"""Zdarzeniowy monitor schowka systemowego z zabezpieczeniem Self-Change Suppression."""

import sys
import ctypes
from contextlib import contextmanager
from typing import Optional

try:
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtGui import QGuiApplication, QClipboard
except ImportError:
    # Środowisko testowe / bez Qt
    class QObject:
        def __init__(self, parent=None):
            pass

    def Signal(*types):
        class MockSignal:
            def __init__(self):
                self._handlers = []

            def connect(self, handler):
                self._handlers.append(handler)

            def disconnect(self, handler=None):
                if handler:
                    self._handlers.remove(handler)
                else:
                    self._handlers.clear()

            def emit(self, *args, **kwargs):
                for h in list(self._handlers):
                    h(*args, **kwargs)

        return MockSignal()

    QGuiApplication = None
    QClipboard = None

from myszkahud.services.clipboard.models import ClipboardEntry
from myszkahud.services.clipboard.clipboard_service import ClipboardService
from myszkahud.core.windows import WindowManager


class ClipboardWriteGuard:
    """
    Zabezpieczenie przed samorozpoznawaniem zmian schowka (Self-Change Suppression).
    Gdy MyszkaHUD sam zapisuje tekst do QClipboard (np. podczas operacji Kopiuj lub
    przygotowania przed Wklejaniem), oznaczamy operację jako wewnętrzną.
    """

    def __init__(self):
        self._suppressed: bool = False
        self._suppressed_text: Optional[str] = None

    @contextmanager
    def suppress(self, text: Optional[str] = None):
        """Menedżer kontekstu blokujący rejestrację wewnętrznego zapisu schowka."""
        prev_suppressed = self._suppressed
        prev_text = self._suppressed_text
        self._suppressed = True
        self._suppressed_text = text
        try:
            yield
        finally:
            self._suppressed = prev_suppressed
            self._suppressed_text = prev_text

    def is_suppressed(self, current_text: Optional[str] = None) -> bool:
        """Sprawdza czy aktualna zmiana schowka jest operacją wewnętrzną aplikacji."""
        if self._suppressed:
            return True
        if (
            current_text is not None
            and self._suppressed_text is not None
            and current_text == self._suppressed_text
        ):
            return True
        return False

    def clear_suppression(self) -> None:
        """Czyści flagi blokady."""
        self._suppressed = False
        self._suppressed_text = None


def detect_source_application(window_manager: Optional[WindowManager] = None) -> Optional[str]:
    """
    Pobiera nazwę procesu lub tytuł aktywnego okna źródłowego (Best-effort).
    Jeśli nie można jednoznacznie ustalić lub system != win32, zwraca None.
    """
    if sys.platform != "win32":
        return None

    try:
        user32 = ctypes.windll.user32
        hwnd = None

        if window_manager and window_manager.target_hwnd:
            hwnd = window_manager.target_hwnd
        else:
            hwnd = user32.GetForegroundWindow()

        if not hwnd:
            return None

        # Pobieramy długość tytułu okna
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.strip()
            if title:
                # Jeśli w tytule jest popularny program (np. Chrome, Code, Notepad)
                return title[:60]

        return None
    except Exception:
        return None


class ClipboardMonitor(QObject):
    """
    Zdarzeniowy monitor nasłuchujący sygnałów QClipboard.dataChanged.
    Gwarantuje:
    - Brak zapisu starej zawartości schowka podczas startu programu,
    - Ignorowanie wewnętrznych operacji schowka (Self-Change Suppression),
    - Rejestrację nowych wpisów w ClipboardService bez pollingu.
    """

    entry_recorded = Signal(object)  # Emituje nowo zapisany ClipboardEntry
    error_occurred = Signal(str)

    def __init__(
        self,
        service: ClipboardService,
        write_guard: Optional[ClipboardWriteGuard] = None,
        window_manager: Optional[WindowManager] = None,
        parent=None,
    ):
        if QObject is not object:
            super().__init__(parent)

        self.service = service
        self.guard = write_guard or ClipboardWriteGuard()
        self.window_manager = window_manager
        self._is_monitoring = False
        self._clipboard = None
        self._last_seen_text: Optional[str] = None

    @property
    def is_monitoring(self) -> bool:
        return self._is_monitoring

    def start_monitoring(self, clipboard_instance=None) -> bool:
        """
        Rozpoczyna nasłuchiwanie schowka.
        Początkowy stan schowka jest zapamiętywany jako _last_seen_text,
        dzięki czemu stary tekst nie jest automatycznie dodawany do bazy przy starcie.
        """
        if self._is_monitoring:
            return True

        if clipboard_instance is not None:
            self._clipboard = clipboard_instance
        elif QGuiApplication is not None:
            self._clipboard = QGuiApplication.clipboard()

        if not self._clipboard:
            return False

        # Inicjalizacja: zapamiętujemy obecną zawartość bez dodawania do historii
        try:
            if hasattr(self._clipboard, "text"):
                self._last_seen_text = self._clipboard.text()
        except Exception:
            self._last_seen_text = None

        if hasattr(self._clipboard, "dataChanged"):
            self._clipboard.dataChanged.connect(self._on_clipboard_changed)

        self._is_monitoring = True
        return True

    def stop_monitoring(self) -> None:
        """Zatrzymuje nasłuchiwanie schowka."""
        if not self._is_monitoring:
            return

        if self._clipboard and hasattr(self._clipboard, "dataChanged"):
            try:
                self._clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            except Exception:
                pass

        self._is_monitoring = False

    def _on_clipboard_changed(self) -> None:
        """Wywoływane zdarzeniowo przy zmianie zawartości schowka."""
        if not self._is_monitoring or not self.service.is_enabled or self.service.is_paused:
            return

        if not self._clipboard or not hasattr(self._clipboard, "text"):
            return

        try:
            current_text = self._clipboard.text()
        except Exception as e:
            self.error_occurred.emit(f"Błąd odczytu schowka: {e}")
            return

        if not current_text or not current_text.strip():
            return

        # 1. Sprawdzenie ochrony przed własnym zapisem (Self-Change Suppression)
        if self.guard.is_suppressed(current_text):
            self._last_seen_text = current_text
            return

        # 2. Sprawdzenie czy to nie jest identyczny tekst z poprzednim zdarzeniem
        if self._last_seen_text is not None and current_text == self._last_seen_text:
            return

        self._last_seen_text = current_text

        # 3. Próba ustalenia aplikacji źródłowej
        source_app = detect_source_application(self.window_manager)

        # 4. Zapisanie do serwisu
        entry = self.service.add_clipboard_text(current_text, source_app=source_app)
        if entry:
            self.entry_recorded.emit(entry)
