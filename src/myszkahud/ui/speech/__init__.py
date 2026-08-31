"""Pakiet widoków UI dla modułu rozpoznawania mowy (Speech-to-Text)."""

from .speech_overlay import SpeechRecordingOverlay
from .speech_result_window import SpeechResultWindow
from .worker import SpeechWorker

__all__ = [
    "SpeechRecordingOverlay",
    "SpeechResultWindow",
    "SpeechWorker"
]
