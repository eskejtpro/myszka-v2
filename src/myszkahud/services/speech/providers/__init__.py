"""Protokoły i dostawcy transkrypcji mowy (STT) dla MyszkaHUD."""

from typing import Protocol, Optional


class SpeechProvider(Protocol):
    """Protokół / interfejs wymiennego dostawcy transkrypcji mowy."""

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav", language_tag: str = "pl-PL") -> str:
        """
        Przekształca surowe audio (np. WAV/PCM) na tekst w zadanym języku.
        """
        ...


from .gemini_speech import GeminiSpeechProvider
from .windows_speech import WindowsSpeechProvider

__all__ = [
    "SpeechProvider",
    "GeminiSpeechProvider",
    "WindowsSpeechProvider"
]

