"""Asynchroniczny pracownik PySide6 dla zapytań OCR (QThread)."""

from typing import Optional

try:
    from PySide6.QtCore import QThread, Signal
except ImportError:
    class QThread:
        def __init__(self, parent=None):
            self.parent = parent
            self._is_running = False

        def start(self):
            self._is_running = True
            self.run()

        def isRunning(self):
            return self._is_running

        def quit(self):
            self._is_running = False

        def wait(self, msecs=None):
            pass

    class Signal:
        def __init__(self, *types):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self, *args):
            for cb in self._callbacks:
                cb(*args)


from myszkahud.services.ocr.engine import OCRService
from myszkahud.services.gemini.client import GeminiServiceError, GeminiAuthError


class OCRWorker(QThread):
    """
    Wątek wykonujący OCR w tle.
    Bezpieczny lifecycle:
    - ocr_started
    - finished_success(extracted_text)
    - finished_error(error_message, error_code)
    - cancel() z bezpiecznym ignorowaniem późnych odpowiedzi (brak zombie).
    """

    ocr_started = Signal()
    finished_success = Signal(str)
    finished_error = Signal(str, str)  # msg, code

    def __init__(
        self,
        service: OCRService,
        image_bytes: bytes,
        mime_type: str = "image/png",
        parent=None
    ):
        super().__init__(parent)
        self.service = service
        self.image_bytes = image_bytes
        self.mime_type = mime_type
        self._is_cancelled = False

    def cancel(self):
        """Oznacza zadanie jako anulowane."""
        self._is_cancelled = True

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def run(self):
        """Metoda wykonywana w osobnym wątku roboczym."""
        if self._is_cancelled:
            return

        self.ocr_started.emit()

        try:
            result = self.service.recognize_text(
                image_bytes=self.image_bytes,
                mime_type=self.mime_type
            )

            if not self._is_cancelled:
                self.finished_success.emit(result)

        except GeminiAuthError as e:
            if not self._is_cancelled:
                self.finished_error.emit(str(e), "AUTH_ERROR")
        except GeminiServiceError as e:
            if not self._is_cancelled:
                self.finished_error.emit(str(e), e.error_code)
        except Exception as e:
            if not self._is_cancelled:
                self.finished_error.emit(f"Błąd OCR: {e}", "OCR_ERROR")
