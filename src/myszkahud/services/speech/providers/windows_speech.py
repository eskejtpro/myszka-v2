"""Adapter lokalnego Windows Speech Recognition (Windows.Media.SpeechRecognition / WinRT).

STAN: Architektura gotowa dla Windows 10 x64 / OCZEKUJE NA WINDOWS VALIDATION.
W środowisku headless Linux lub bez bibliotek WinRT podnosi kontrolowany wyjątek.
"""

import sys
from typing import Optional


class WindowsSpeechProvider:
    """
    Adapter lokalnego Windows Speech Recognition wykorzystujący API Windows 10 (WinRT / Windows.Media.SpeechRecognition).
    
    Wymagania systemowe dla środowiska docelowego:
    - Windows 10 build 10240 lub nowszy (64-bit),
    - Zainstalowany pakiet mowy dla języka polskiego (Ustawienia -> Czas i język -> Mowa),
    - winsdk lub winrt-Windows.Media.SpeechRecognition (opcjonalna zależność dla trybu lokalnego).
    """

    def __init__(self, language_tag: str = "pl-PL"):
        self.language_tag = language_tag
        self._is_available = (sys.platform == "win32")

    def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
        language_tag: Optional[str] = None
    ) -> str:
        """
        Transkrypcja mowy przy użyciu natywnego silnika Windows 10 Speech.
        """
        if not audio_bytes:
            return ""

        if not self._is_available:
            raise NotImplementedError(
                "WindowsSpeechProvider jest dostępny wyłącznie w systemie Windows 10 x64. "
                "STAN: OCZEKUJE NA WINDOWS VALIDATION. Użyj dostawcy GeminiSpeechProvider."
            )

        try:
            # W środowisku docelowym Windows 10 x64 z winsdk:
            # import winsdk.windows.media.speechrecognition as win_sr
            raise NotImplementedError(
                "Lokalny moduł WinRT SpeechRecognition oczekuje na walidację runtime w Windows 10 x64. "
                "STAN: OCZEKUJE NA WINDOWS VALIDATION."
            )
        except ImportError as e:
            raise NotImplementedError(
                f"Brak biblioteki WinRT do lokalnego rozpoznawania mowy: {e}. "
                "Dla Windows 10 zaleca się GeminiSpeechProvider lub instalację pakietu winsdk."
            )
