"""Główna usługa domenowa OCR (OCRService)."""

from typing import Optional
from .providers import OCRProvider, GeminiOCRProvider, WindowsLocalOCRProvider


class OCRService:
    """
    Główna usługa domenowa OCR.
    Zarządza wymiennym dostawcą OCRProvider (Gemini / Local WinRT) i walidacją wejścia.
    """

    def __init__(self, provider: OCRProvider):
        self.provider = provider

    def set_provider(self, provider: OCRProvider) -> None:
        """Pozwala na dynamiczne przełączanie dostawcy (np. Cloud <-> Local)."""
        self.provider = provider

    def get_provider(self) -> OCRProvider:
        """Zwraca bieżącego dostawcę OCR."""
        return self.provider

    def recognize_text(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """Wykonuje rozpoznawanie tekstu z przekazanego obrazu."""
        if not image_bytes or len(image_bytes) == 0:
            return ""

        return self.provider.extract_text(image_bytes, mime_type=mime_type)
