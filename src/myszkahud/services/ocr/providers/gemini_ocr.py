"""Adapter OCR wykorzystujący Gemini Vision (GeminiService multimodal)."""

from typing import Optional
from myszkahud.services.gemini.client import VisionProvider, GeminiServiceError


def build_ocr_system_instruction() -> str:
    """Instrukcja systemowa dla modelu multimodalnego wykonującego OCR."""
    return (
        "Jesteś precyzyjnym systemem Optical Character Recognition (OCR). "
        "Twoim jedynym zadaniem jest dokładne odczytanie i przepisanie całego tekstu widocznego na przekazanym zrzucie ekranu.\n"
        "ZASADY:\n"
        "1. Zwróć WYŁĄCZNIE odczytany tekst bez żadnych własnych komentarzy, wstępów czy podsumowań.\n"
        "2. Zachowaj oryginalny układ, podziały wierszy, spacje i interpunkcję.\n"
        "3. Jeśli obraz zawiera kod źródłowy, zachowaj wcięcia i składnię.\n"
        "4. Jeśli na obrazie nie ma żadnego tekstu, zwróć pustą odpowiedź."
    )


def build_ocr_prompt() -> str:
    """Prompt dla zapytania OCR."""
    return "Odczytaj i przepisz dokładnie cały tekst z tego obrazu."


class GeminiOCRProvider:
    """
    Adapter OCR wykorzystujący VisionProvider (GeminiService).
    Wspólne źródło prawdy:
    - primary: gemini-3.7-flash
    - fallback: gemini-3.6-flash
    - wspólna autoryzacja GEMINI_API_KEY
    """

    def __init__(self, vision_provider: VisionProvider):
        self.vision_provider = vision_provider

    def extract_text(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        if not image_bytes:
            return ""

        prompt = build_ocr_prompt()
        system_instruction = build_ocr_system_instruction()

        return self.vision_provider.generate_multimodal(
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
            system_instruction=system_instruction
        )
