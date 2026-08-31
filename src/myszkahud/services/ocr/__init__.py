"""Pakiet usług OCR (Optyczne Rozpoznawanie Znaków) dla MyszkaHUD."""

from .service import OCRService
from .providers import (
    OCRProvider,
    GeminiOCRProvider,
    WindowsLocalOCRProvider,
    build_ocr_prompt,
    build_ocr_system_instruction,
)

__all__ = [
    "OCRService",
    "OCRProvider",
    "GeminiOCRProvider",
    "WindowsLocalOCRProvider",
    "build_ocr_prompt",
    "build_ocr_system_instruction",
]
