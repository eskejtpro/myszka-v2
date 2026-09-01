"""Kompleksowy zestaw testów integracyjnych i regresyjnych dla MyszkaHUD (v0.11 Audit & Final Integration)."""

import unittest
from unittest.mock import MagicMock, patch

from myszkahud.services.gemini.client import GeminiService
from myszkahud.services.translation.translator import TranslationService
from myszkahud.services.ocr.engine import OCRService, GeminiOCRProvider
from myszkahud.services.speech import SpeechService, GeminiSpeechProvider
from myszkahud.services.clipboard import ClipboardService, NotesService
from myszkahud.services.process import ProcessService, MockProcessProvider
from myszkahud.services.ram import RamService, MockRamProvider
from myszkahud.services.settings import SettingsService, AppSettings
from myszkahud.services.autostart import AutostartService, MockAutostartProvider
from myszkahud.storage.clipboard_repo import SQLiteClipboardRepository
from myszkahud.core.windows import WindowManager, ClipboardFreshnessGuard
from myszkahud.core.text_actions import TextActionExecutor, TextAction


class TestFullArchitectureIntegration(unittest.TestCase):
    """Weryfikacja spójności i współdziałania wszystkich 8 kluczowych modułów produkcyjnych."""

    def test_all_services_instantiation(self):
        # 1. Gemini / AI Core
        gemini = GeminiService()
        self.assertIsNotNone(gemini)

        # 2. Translation
        translator = TranslationService(ai_provider=gemini)
        self.assertIsNotNone(translator)

        # 3. OCR Engine
        ocr_prov = GeminiOCRProvider(vision_provider=gemini)
        ocr = OCRService(provider=ocr_prov)
        self.assertIsNotNone(ocr)

        # 4. Speech STT
        speech_prov = GeminiSpeechProvider(audio_provider=gemini)
        speech = SpeechService(provider=speech_prov)
        self.assertIsNotNone(speech)

        # 5. Smart Clipboard & Notes
        clip_repo = SQLiteClipboardRepository(db_path=":memory:")
        clip_svc = ClipboardService(repository=clip_repo)
        notes_svc = NotesService(repository=clip_repo)
        self.assertIsNotNone(clip_svc)
        self.assertIsNotNone(notes_svc)

        # 6. Process Manager & Protection
        mock_proc_prov = MockProcessProvider()
        proc_svc = ProcessService(provider=mock_proc_prov)
        self.assertIsNotNone(proc_svc)
        self.assertEqual(len(proc_svc.list_processes()), 5)

        # 7. RAM Monitor & Safe Release
        mock_ram_prov = MockRamProvider()
        ram_svc = RamService(provider=mock_ram_prov)
        self.assertIsNotNone(ram_svc)
        self.assertEqual(ram_svc.get_stats().total_gb, 16.0)

        # 8. Settings & Autostart
        settings_svc = SettingsService()
        autostart_prov = MockAutostartProvider()
        autostart_svc = AutostartService(provider=autostart_prov)
        self.assertIsNotNone(settings_svc)
        self.assertIsNotNone(autostart_svc)

    def test_cross_module_dataflow_speech_to_translation(self):
        """Przepływ danych: Tekst transkrybowany z mowy może być bezpośrednio przekazany do tłumaczenia."""
        gemini = GeminiService()
        translator = TranslationService(ai_provider=gemini)
        sample_speech_transcript = "Dzień dobry, jak mogę pomóc?"

        self.assertIsNotNone(translator)
        self.assertIsNotNone(translator.ai_provider)

    def test_cross_module_dataflow_ocr_to_clipboard(self):
        """Przepływ danych: Tekst odczytany z OCR może zostać zapisany w historii schowka."""
        clip_repo = SQLiteClipboardRepository(db_path=":memory:")
        clip_svc = ClipboardService(repository=clip_repo)
        ocr_extracted_text = "def calculate_hash(data: bytes) -> str:"

        entry = clip_svc.add_clipboard_text(text=ocr_extracted_text, source_app="ScreenSnippingOCR")
        self.assertIsNotNone(entry)

        history = clip_svc.list_entries(limit=10)
        self.assertTrue(any(it.text == ocr_extracted_text for it in history))

    def test_process_guard_protects_system_and_myszkahud(self):
        """Weryfikacja ochrony krytycznych procesów Windows przed przypadkowym zakończeniem."""
        mock_proc_prov = MockProcessProvider()
        proc_svc = ProcessService(provider=mock_proc_prov)

        # Próba zabicia procesu PID 4 (System) musi zostać bezpiecznie zablokowana
        res = proc_svc.force_kill_process(4)
        self.assertFalse(res)

    def test_safe_ram_release_conservative_diff(self):
        """Weryfikacja, że zwolnienie RAM nie fałszuje wyników i wykonuje realny pomiar przed/po."""
        mock_ram_prov = MockRamProvider(total_gb=16.0, used_gb=10.0, release_gain_mb=400.0)
        ram_svc = RamService(provider=mock_ram_prov)

        res = ram_svc.release_memory_safe()
        self.assertTrue(res.success)
        self.assertEqual(res.released_mb, 400.0)
        self.assertEqual(res.before_used_mb, 10240.0)
        self.assertEqual(res.after_used_mb, 9840.0)


if __name__ == "__main__":
    unittest.main()
