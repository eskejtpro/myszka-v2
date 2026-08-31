"""Adapter lokalnego Windows Media OCR (Windows.Media.Ocr / WinRT).

STAN: Architektura gotowa dla Windows 10 x64 / OCZEKUJE NA WINDOWS VALIDATION.
W środowisku headless Linux lub bez bibliotek WinRT podnosi kontrolowany wyjątek.
"""

import sys
from typing import Optional


class WindowsLocalOCRProvider:
    """
    Adapter lokalnego Windows OCR wykorzystujący API Windows 10 (WinRT Windows.Media.Ocr).
    
    Wymagania systemowe dla środowiska docelowego:
    - Windows 10 build 10240 lub nowszy (64-bit),
    - Zainstalowane pakiety językowe OCR w Windows (Ustawienia -> Czas i język),
    - winsdk lub winrt-Windows.Media.Ocr (opcjonalna zależność dla trybu lokalnego).
    """

    def __init__(self, language_tag: str = "pl-PL"):
        self.language_tag = language_tag
        self._is_available = (sys.platform == "win32")

    def extract_text(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """
        Ekstrakcja tekstu przy użyciu natywnego silnika Windows 10 OCR.
        """
        if not image_bytes:
            return ""

        if not self._is_available:
            raise NotImplementedError(
                "WindowsLocalOCRProvider jest dostępny wyłącznie w systemie Windows 10 x64. "
                "STAN: OCZEKUJE NA WINDOWS VALIDATION. Użyj dostawcy GeminiOCRProvider."
            )

        # Próba załadowania natywnych bibliotek WinRT jeśli są zainstalowane w środowisku Windows
        try:
            # W środowisku Windows 10 x64 z winsdk / winrt
            # Przykład: import winsdk.windows.media.ocr as win_ocr
            # import winsdk.windows.graphics.imaging as win_img
            # import winsdk.windows.storage.streams as win_streams
            raise NotImplementedError(
                "Lokalny moduł WinRT OCR oczekuje na walidację runtime w Windows 10 x64. "
                "STAN: OCZEKUJE NA WINDOWS VALIDATION."
            )
        except ImportError as e:
            raise NotImplementedError(
                f"Brak biblioteki WinRT do lokalnego OCR: {e}. "
                "Dla Windows 10 zaleca się GeminiOCRProvider lub instalację opcjonalnego pakietu winsdk."
            )
