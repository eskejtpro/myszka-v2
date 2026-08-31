"""Główna usługa domenowa Speech-to-Text (SpeechService)."""

from typing import Optional
from .providers import SpeechProvider, GeminiSpeechProvider, WindowsSpeechProvider
from .state_machine import SpeechState, SpeechStateMachine, InvalidStateTransitionError

# Globalny twardy limit czasu trwania nagrania mowy w sekundach
MAX_RECORDING_SECONDS: int = 60



class SpeechService:
    """
    Główna usługa domenowa transkrypcji mowy.
    Zarządza wymiennym dostawcą SpeechProvider (Gemini / Local WinRT) i walidacją wejścia audio.
    """

    def __init__(self, provider: SpeechProvider):
        self.provider = provider

    def set_provider(self, provider: SpeechProvider) -> None:
        """Pozwala na dynamiczne przełączanie dostawcy STT (np. Cloud <-> Local)."""
        self.provider = provider

    def get_provider(self) -> SpeechProvider:
        """Zwraca bieżącego dostawcę STT."""
        return self.provider

    def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
        language_tag: str = "pl-PL"
    ) -> str:
        """Wykonuje transkrypcję przekazanego nagrania audio na tekst."""
        if not audio_bytes or len(audio_bytes) == 0:
            return ""

        return self.provider.transcribe(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            language_tag=language_tag
        )
