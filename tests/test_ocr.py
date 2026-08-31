"""Testy jednostkowe dla modułu OCR (MyszkaHUD v0.4).

Sprawdza:
- normalizację prostokątów we wszystkich 4 kierunkach przeciągania (L->R, R->L, T->B, B->T),
- ujemne współrzędne (monitory poboczne po lewej/u góry),
- walidację progów minimalnego rozmiaru i pustego zaznaczenia,
- wirtualny pulpit dla układów wielomonitorowych,
- transformację współrzędnych i mapowanie DPI (100%, 150%, offsety monitorów),
- wybór i dynamiczne przełączanie providerów (OCRProvider),
- FakeOCRProvider success & error,
- GeminiOCRProvider oraz WindowsLocalOCRProvider,
- cykl życia wątku roboczego OCRWorker (start, success, error, cancel),
- przepływ OCR -> TranslationService (brak powielania TranslationService),
- bezpieczną obsługę błędów (401, 429, 503).
"""

import unittest
from unittest.mock import MagicMock
from myszkahud.core.geometry import (
    ScreenRect,
    normalize_selection_rect,
    is_valid_selection,
    calculate_virtual_desktop_geometry,
    map_logical_to_screen_crop
)
from myszkahud.services.gemini.client import (
    GeminiService,
    GeminiAuthError,
    GeminiQuotaError,
    GeminiServiceError,
    GeminiAllModelsFailedError
)
from myszkahud.services.ocr.service import OCRService
from myszkahud.services.ocr.providers import (
    OCRProvider,
    GeminiOCRProvider,
    WindowsLocalOCRProvider,
    build_ocr_prompt,
    build_ocr_system_instruction
)
from myszkahud.services.translation.translator import TranslationService
from myszkahud.ui.ocr.worker import OCRWorker


class FakeSuccessOCRProvider:
    """Mock provider zwracający sukces dla testów domenowych."""
    def __init__(self, output_text: str = "Testowy tekst z OCR"):
        self.output_text = output_text

    def extract_text(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        if not image_bytes:
            return ""
        return self.output_text


class FakeErrorOCRProvider:
    """Mock provider rzucający wyjątek."""
    def __init__(self, error_to_raise: Exception = None):
        self.error_to_raise = error_to_raise or RuntimeError("Błąd providera OCR")

    def extract_text(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        raise self.error_to_raise


class TestScreenGeometryAndCoordinates(unittest.TestCase):
    """Testy geometrii ekranów, normalizacji wektorów myszy i mapowania DPI."""

    def test_normalize_selection_top_left_to_bottom_right(self):
        # Przeciąganie z lewej-góry do prawej-dołu (standard)
        x, y, w, h = normalize_selection_rect(100, 150, 300, 450)
        self.assertEqual((x, y, w, h), (100, 150, 200, 300))

    def test_normalize_selection_bottom_right_to_top_left(self):
        # Przeciąganie z prawej-dołu do lewej-góry
        x, y, w, h = normalize_selection_rect(300, 450, 100, 150)
        self.assertEqual((x, y, w, h), (100, 150, 200, 300))

    def test_normalize_selection_top_right_to_bottom_left(self):
        # Przeciąganie z prawej-góry do lewej-dołu
        x, y, w, h = normalize_selection_rect(300, 150, 100, 450)
        self.assertEqual((x, y, w, h), (100, 150, 200, 300))

    def test_normalize_selection_bottom_left_to_top_right(self):
        # Przeciąganie z lewej-dołu do prawej-góry
        x, y, w, h = normalize_selection_rect(100, 450, 300, 150)
        self.assertEqual((x, y, w, h), (100, 150, 200, 300))

    def test_normalize_selection_negative_coordinates_left_screen(self):
        # Lewy monitor o ujemnych współrzędnych X
        x, y, w, h = normalize_selection_rect(-500, -200, -100, 100)
        self.assertEqual((x, y, w, h), (-500, -200, 400, 300))

    def test_normalize_selection_negative_coordinates_drag_reversed(self):
        # Przeciąganie odwrócone w obszarze ujemnym
        x, y, w, h = normalize_selection_rect(-100, 100, -500, -200)
        self.assertEqual((x, y, w, h), (-500, -200, 400, 300))

    def test_is_valid_selection_thresholds(self):
        # Puste zaznaczenie (0x0)
        self.assertFalse(is_valid_selection(0, 0))
        # Zbyt małe zaznaczenie (< minimalny próg)
        self.assertFalse(is_valid_selection(4, 4, min_width=8, min_height=8))
        self.assertFalse(is_valid_selection(10, 2, min_width=8, min_height=8))
        self.assertFalse(is_valid_selection(2, 10, min_width=8, min_height=8))
        # Prawidłowy rozmiar
        self.assertTrue(is_valid_selection(8, 8, min_width=8, min_height=8))
        self.assertTrue(is_valid_selection(100, 50, min_width=8, min_height=8))

    def test_virtual_desktop_single_monitor(self):
        s1 = ScreenRect(x=0, y=0, width=1920, height=1080)
        vx, vy, vw, vh = calculate_virtual_desktop_geometry([s1])
        self.assertEqual((vx, vy, vw, vh), (0, 0, 1920, 1080))

    def test_virtual_desktop_multi_monitor_with_negative_x(self):
        # Lewy monitor: (-1920, 0, 1920, 1080), Główny: (0, 0, 1920, 1080)
        s_left = ScreenRect(x=-1920, y=0, width=1920, height=1080)
        s_main = ScreenRect(x=0, y=0, width=1920, height=1080)
        vx, vy, vw, vh = calculate_virtual_desktop_geometry([s_left, s_main])
        self.assertEqual((vx, vy, vw, vh), (-1920, 0, 3840, 1080))

    def test_virtual_desktop_stacked_vertical_monitors(self):
        # Monitor dolny (0, 1080, 1920, 1080), Górny (0, 0, 1920, 1080)
        s_top = ScreenRect(x=0, y=0, width=1920, height=1080)
        s_bottom = ScreenRect(x=0, y=1080, width=1920, height=1080)
        vx, vy, vw, vh = calculate_virtual_desktop_geometry([s_top, s_bottom])
        self.assertEqual((vx, vy, vw, vh), (0, 0, 1920, 2160))

    def test_virtual_desktop_empty_screens_fallback(self):
        vx, vy, vw, vh = calculate_virtual_desktop_geometry([])
        self.assertEqual((vx, vy, vw, vh), (0, 0, 1920, 1080))

    def test_map_logical_to_screen_crop_standard_dpi(self):
        screen = ScreenRect(x=0, y=0, width=1920, height=1080, device_pixel_ratio=1.0)
        px, py, pw, ph = map_logical_to_screen_crop(100, 200, 300, 400, screen)
        self.assertEqual((px, py, pw, ph), (100, 200, 300, 400))

    def test_map_logical_to_screen_crop_hidpi_150_percent(self):
        # Ekran 4K lub laptop ze skalowaniem 150% (DPR = 1.5)
        screen = ScreenRect(x=0, y=0, width=1920, height=1080, device_pixel_ratio=1.5)
        px, py, pw, ph = map_logical_to_screen_crop(100, 200, 300, 400, screen)
        self.assertEqual((px, py, pw, ph), (150, 300, 450, 600))

    def test_map_logical_to_screen_crop_secondary_monitor_offset(self):
        # Drugi monitor z lewej (-1920, 0)
        screen = ScreenRect(x=-1920, y=0, width=1920, height=1080, device_pixel_ratio=1.0)
        px, py, pw, ph = map_logical_to_screen_crop(-1820, 100, 200, 150, screen)
        self.assertEqual((px, py, pw, ph), (100, 100, 200, 150))


class TestGeminiMultimodalService(unittest.TestCase):
    """Testy metody generate_multimodal w GeminiService bez połączeń sieciowych."""

    def test_multimodal_empty_bytes_returns_empty_string(self):
        mock_client = MagicMock()
        service = GeminiService(api_key="test-key", client=mock_client)
        result = service.generate_multimodal(prompt="test", image_bytes=b"")
        self.assertEqual(result, "")
        mock_client.models.generate_content.assert_not_called()

    def test_multimodal_primary_success(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Rozpoznany tekst z obrazka"
        mock_client.models.generate_content.return_value = mock_response

        service = GeminiService(api_key="test-key", client=mock_client)
        result = service.generate_multimodal(
            prompt="Odczytaj",
            image_bytes=b"fake-png-data",
            mime_type="image/png"
        )

        self.assertEqual(result, "Rozpoznany tekst z obrazka")
        mock_client.models.generate_content.assert_called_once()
        args, kwargs = mock_client.models.generate_content.call_args
        self.assertEqual(kwargs.get("model"), "gemini-3.7-flash")

    def test_multimodal_fallback_on_429(self):
        mock_client = MagicMock()
        mock_resp_36 = MagicMock()
        mock_resp_36.text = "Wynik z modelu zapasowego 3.6"

        mock_client.models.generate_content.side_effect = [
            Exception("429 Resource has been exhausted"),
            mock_resp_36
        ]

        service = GeminiService(api_key="test-key", client=mock_client)
        result = service.generate_multimodal(
            prompt="OCR",
            image_bytes=b"sample-bytes"
        )

        self.assertEqual(result, "Wynik z modelu zapasowego 3.6")
        self.assertEqual(mock_client.models.generate_content.call_count, 2)
        calls = mock_client.models.generate_content.call_args_list
        self.assertEqual(calls[0][1]["model"], "gemini-3.7-flash")
        self.assertEqual(calls[1][1]["model"], "gemini-3.6-flash")

    def test_multimodal_no_fallback_on_auth_error_401(self):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("401 API_KEY_INVALID")

        service = GeminiService(api_key="test-key", client=mock_client)
        with self.assertRaises(GeminiAuthError):
            service.generate_multimodal(prompt="OCR", image_bytes=b"data")
        self.assertEqual(mock_client.models.generate_content.call_count, 1)

    def test_multimodal_all_failed_raises(self):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            Exception("503 Service Unavailable"),
            Exception("503 Service Unavailable")
        ]

        service = GeminiService(api_key="test-key", client=mock_client)
        with self.assertRaises(GeminiAllModelsFailedError):
            service.generate_multimodal(prompt="OCR", image_bytes=b"data")
        self.assertEqual(mock_client.models.generate_content.call_count, 2)


class TestOCRServiceAndProviders(unittest.TestCase):
    """Testy serwisów domenowych OCR i wymiennych dostawców."""

    def test_build_ocr_prompt_and_instruction(self):
        prompt = build_ocr_prompt()
        instruction = build_ocr_system_instruction()
        self.assertIn("Odczytaj", prompt)
        self.assertIn("Optical Character Recognition", instruction)
        self.assertIn("WYŁĄCZNIE", instruction)

    def test_fake_ocr_provider_success(self):
        fake = FakeSuccessOCRProvider("Rozpoznano tekst testowy")
        service = OCRService(provider=fake)
        self.assertEqual(service.recognize_text(b"raw-image-bytes"), "Rozpoznano tekst testowy")

    def test_fake_ocr_provider_error(self):
        fake = FakeErrorOCRProvider(ValueError("Błąd formatu obrazu"))
        service = OCRService(provider=fake)
        with self.assertRaises(ValueError):
            service.recognize_text(b"corrupted-bytes")

    def test_gemini_ocr_provider_extract_text(self):
        mock_vision = MagicMock()
        mock_vision.generate_multimodal.return_value = "Definicja funkcji main()"

        provider = GeminiOCRProvider(vision_provider=mock_vision)
        service = OCRService(provider=provider)

        result = service.recognize_text(b"raw-image-bytes", mime_type="image/png")

        self.assertEqual(result, "Definicja funkcji main()")
        mock_vision.generate_multimodal.assert_called_once()
        args, kwargs = mock_vision.generate_multimodal.call_args
        self.assertEqual(kwargs.get("image_bytes"), b"raw-image-bytes")
        self.assertIn("system_instruction", kwargs)

    def test_ocr_service_empty_bytes_returns_empty_string(self):
        mock_provider = MagicMock()
        service = OCRService(provider=mock_provider)
        self.assertEqual(service.recognize_text(b""), "")
        mock_provider.extract_text.assert_not_called()

    def test_switch_ocr_provider(self):
        provider_a = FakeSuccessOCRProvider("Tekst A")
        provider_b = FakeSuccessOCRProvider("Tekst B")

        service = OCRService(provider=provider_a)
        self.assertEqual(service.get_provider(), provider_a)
        self.assertEqual(service.recognize_text(b"img"), "Tekst A")

        service.set_provider(provider_b)
        self.assertEqual(service.get_provider(), provider_b)
        self.assertEqual(service.recognize_text(b"img"), "Tekst B")

    def test_windows_local_ocr_provider_raises_not_implemented(self):
        local_provider = WindowsLocalOCRProvider()
        with self.assertRaises(NotImplementedError):
            local_provider.extract_text(b"some-image-data")


class TestOCRWorkerLifecycle(unittest.TestCase):
    """Testy cyklu życia wątku roboczego OCRWorker."""

    def test_worker_success(self):
        mock_service = MagicMock()
        mock_service.recognize_text.return_value = "KOD BŁĘDU: 404"

        worker = OCRWorker(service=mock_service, image_bytes=b"fake-bytes")
        results = []
        worker.finished_success.connect(lambda txt: results.append(txt))

        worker.run()
        self.assertEqual(results, ["KOD BŁĘDU: 404"])

    def test_worker_error(self):
        mock_service = MagicMock()
        mock_service.recognize_text.side_effect = GeminiAuthError("Brak klucza")

        worker = OCRWorker(service=mock_service, image_bytes=b"fake-bytes")
        errors = []
        worker.finished_error.connect(lambda msg, code: errors.append((msg, code)))

        worker.run()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0][1], "AUTH_ERROR")

    def test_worker_cancel_ignores_output(self):
        mock_service = MagicMock()
        mock_service.recognize_text.return_value = "Late OCR Result"

        worker = OCRWorker(service=mock_service, image_bytes=b"fake-bytes")
        results = []
        worker.finished_success.connect(lambda txt: results.append(txt))

        worker.cancel()
        worker.run()

        self.assertEqual(len(results), 0)


class TestOCRToTranslationFlow(unittest.TestCase):
    """Test integracyjny przepływu: rozpoznany tekst z OCR -> TranslationService."""

    def test_ocr_to_translation_pipeline_single_gemini_instance(self):
        mock_ai = MagicMock()
        # 1. OCR Multimodal
        mock_ai.generate_multimodal.return_value = "Hello World from Screen"
        # 2. Text Translation
        mock_ai.generate_text.return_value = "Witaj Świecie z Ekranu"

        # OCR Service i TranslationService współdzielą tę samą instancję mock_ai
        ocr_provider = GeminiOCRProvider(vision_provider=mock_ai)
        ocr_service = OCRService(provider=ocr_provider)
        translation_service = TranslationService(ai_provider=mock_ai)

        # Krok 1: OCR
        extracted_text = ocr_service.recognize_text(b"screenshot-bytes")
        self.assertEqual(extracted_text, "Hello World from Screen")

        # Krok 2: Przekazanie tekstu do tłumacza
        translated_text = translation_service.translate(
            text=extracted_text,
            source_lang="en",
            target_lang="pl"
        )
        self.assertEqual(translated_text, "Witaj Świecie z Ekranu")


if __name__ == "__main__":
    unittest.main()
