"""Moduł wstecznej kompatybilności dla silnika OCR (re-export z service i providers)."""

from .service import OCRService
from .providers import (
    OCRProvider,
    GeminiOCRProvider,
    WindowsLocalOCRProvider,
    build_ocr_prompt,
    build_ocr_system_instruction,
)

__all__ = [
    "OCRProvider",
    "OCRService",
    "GeminiOCRProvider",
    "WindowsLocalOCRProvider",
    "build_ocr_prompt",
    "build_ocr_system_instruction",
]
