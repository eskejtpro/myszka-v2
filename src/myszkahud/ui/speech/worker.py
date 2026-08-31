"""Wątek roboczy asynchronicznej transkrypcji mowy (Speech-to-Text)."""

import time
from typing import Optional

try:
    from PySide6.QtCore import QThread, Signal
except ImportError:
    class QThread:
        def __init__(self, parent=None):
            self.parent = parent
        def start(self):
            pass
        def isRunning(self):
            return False
        def quit(self):
            pass
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

from myszkahud.services.speech.service import SpeechService
from myszkahud.services.gemini.client import (
    GeminiAuthError,
    GeminiQuotaError,
    GeminiUnavailableError,
    GeminiAllModelsFailedError,
    GeminiServiceError,
)


class SpeechWorker(QThread):
    """
    Wątek roboczy wykonujący asynchroniczną transkrypcję audio.
    Zapewnia pełną responsywność interfejsu PySide6.
    """

    started_transcription = Signal()
    finished_success = Signal(str)
    finished_error = Signal(str, str)  # (user_message, error_code)

    def __init__(
        self,
        service: SpeechService,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
        language_tag: str = "pl-PL",
        parent=None
    ):
        super().__init__(parent)
        self.service = service
        self.audio_bytes = audio_bytes
        self.mime_type = mime_type
        self.language_tag = language_tag
        self._is_cancelled = False

    def cancel(self):
        """Oznacza zadanie jako anulowane, ignorując spóźnione odpowiedzi."""
        self._is_cancelled = True

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def run(self):
        if self._is_cancelled or not self.audio_bytes:
            return

        self.started_transcription.emit()

        try:
            result_text = self.service.transcribe(
                audio_bytes=self.audio_bytes,
                mime_type=self.mime_type,
                language_tag=self.language_tag
            )

            if not self._is_cancelled:
                self.finished_success.emit(result_text)

        except GeminiAuthError as e:
            if not self._is_cancelled:
                self.finished_error.emit(
                    "Błąd autoryzacji: Brak lub niepoprawny klucz GEMINI_API_KEY.",
                    "AUTH_ERROR"
                )
        except GeminiQuotaError as e:
            if not self._is_cancelled:
                self.finished_error.emit(
                    "Przekroczono limit zapytań (429). Spróbuj ponownie za chwilę.",
                    "QUOTA_EXCEEDED"
                )
        except GeminiUnavailableError as e:
            if not self._is_cancelled:
                self.finished_error.emit(
                    "Usługa rozpoznawania mowy jest chwilowo niedostępna (503).",
                    "SERVICE_UNAVAILABLE"
                )
        except GeminiAllModelsFailedError as e:
            if not self._is_cancelled:
                self.finished_error.emit(
                    "Wszystkie modele transkrypcji zawiodły. Sprawdź połączenie z siecią.",
                    "ALL_MODELS_FAILED"
                )
        except NotImplementedError as e:
            if not self._is_cancelled:
                self.finished_error.emit(str(e), "NOT_IMPLEMENTED")
        except Exception as e:
            if not self._is_cancelled:
                self.finished_error.emit(f"Wystąpił nieoczekiwany błąd: {e}", "UNEXPECTED_ERROR")
