"""Pakiet UI modułu OCR."""

from .worker import OCRWorker
from .ocr_window import OCRResultWindow
from .snipping_overlay import ScreenSnippingOverlay

__all__ = [
    "OCRWorker",
    "OCRResultWindow",
    "ScreenSnippingOverlay",
]
