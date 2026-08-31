"""Asynchroniczny pracownik PySide6 dla zapytań tłumaczenia tekstu (QThread)."""

from typing import Optional

try:
    from PySide6.QtCore import QThread, Signal
except ImportError:
    # Środowisko testowe bez PySide6
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


from myszkahud.services.translation.translator import TranslationService
from myszkahud.services.gemini.client import GeminiServiceError, GeminiAuthError


class TranslationWorker(QThread):
    """
    Wątek wykonujący zapytanie do TranslationService w tle.
    Posiada bezpieczny lifecycle:
    - started
    - finished_success(translated_text)
    - finished_error(error_message, error_code)
    - cancel() z bezpiecznym ignorowaniem późnych odpowiedzi (brak zombie / brak terminate).
    """

    translation_started = Signal()
    finished_success = Signal(str)
    finished_error = Signal(str, str)  # msg, code

    def __init__(
        self,
        service: TranslationService,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "en",
        parent=None
    ):
        super().__init__(parent)
        self.service = service
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self._is_cancelled = False

    def cancel(self):
        """Oznacza zadanie jako anulowane. Późny wynik z API zostanie zignorowany."""
        self._is_cancelled = True

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def run(self):
        """Metoda wykonywana w osobnym wątku roboczym."""
        if self._is_cancelled:
            return

        self.translation_started.emit()

        try:
            result = self.service.translate(
                text=self.text,
                source_lang=self.source_lang,
                target_lang=self.target_lang
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
                self.finished_error.emit(f"Nieoczekiwany błąd: {e}", "UNEXPECTED_ERROR")
