"""Dostawcy OCR dla MyszkaHUD."""

from typing import Protocol


class OCRProvider(Protocol):
    """
    Protokół dostawcy OCR.
    Przyjmuje surowe bajty obrazu (PNG/JPEG) i zwraca rozpoznany tekst.
    """
    def extract_text(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        ...


from .windows_ocr import WindowsLocalOCRProvider
from .gemini_ocr import GeminiOCRProvider, build_ocr_prompt, build_ocr_system_instruction

__all__ = [
    "OCRProvider",
    "WindowsLocalOCRProvider",
    "GeminiOCRProvider",
    "build_ocr_prompt",
    "build_ocr_system_instruction",
]
