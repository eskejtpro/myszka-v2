"""Adapter transkrypcji mowy (STT) wykorzystujący Gemini Audio API."""

from typing import List, Optional
from myszkahud.services.gemini.client import AudioTranscribeProvider, DEFAULT_STT_MODELS


def build_stt_system_instruction(language_tag: str = "pl-PL") -> str:
    """Instrukcja systemowa dla modelu STT."""
    lang_name = "języka polskiego (pl-PL)" if "pl" in language_tag.lower() else language_tag
    return (
        f"Jesteś precyzyjnym systemem rozpoznawania mowy (Speech-to-Text / STT) dla {lang_name}.\n"
        "Twoim jedynym zadaniem jest dokładne przepisanie słów wypowiedzianych w nagraniu audio na tekst.\n"
        "ZASADY:\n"
        "1. Zwróć WYŁĄCZNIE przepisany tekst mowy. Nie dodawaj żadnych własnych wstępów, podsumowań, cudzysłowów ani komentarzy.\n"
        "2. Zastosuj poprawną ortografię, interpunkcję oraz wielkie i małe litery.\n"
        "3. Jeśli w nagraniu nie ma żadnej mowy, słychać tylko szum lub ciszę, zwróć pustą odpowiedź.\n"
        "4. Zachowaj naturalne akapity lub zdania."
    )


def build_stt_prompt(language_tag: str = "pl-PL") -> str:
    """Prompt dla zapytania STT."""
    return f"Przepisz dokładnie słowa z tego nagrania audio na tekst ({language_tag})."


class GeminiSpeechProvider:
    """
    Adapter Speech-to-Text wykorzystujący AudioTranscribeProvider (GeminiService).
    Wspólne źródło prawdy:
    - Primary: gemini-3.5-transcribe (dedykowany STT)
    - Fallback 1: gemini-3.7-flash
    - Fallback 2: gemini-3.6-flash
    - Wspólna autoryzacja GEMINI_API_KEY i klasyfikacja błędów
    """

    def __init__(
        self,
        audio_provider: AudioTranscribeProvider,
        models: Optional[List[str]] = None,
        default_language: str = "pl-PL"
    ):
        self.audio_provider = audio_provider
        self.models = models or list(DEFAULT_STT_MODELS)
        self.default_language = default_language

    def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
        language_tag: Optional[str] = None
    ) -> str:
        """Wykonuje transkrypcję audio na tekst."""
        if not audio_bytes:
            return ""

        lang = language_tag or self.default_language
        prompt = build_stt_prompt(lang)
        system_instruction = build_stt_system_instruction(lang)

        return self.audio_provider.generate_audio_transcription(
            prompt=prompt,
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            system_instruction=system_instruction,
            models=self.models
        )
