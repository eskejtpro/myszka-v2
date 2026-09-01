"""Testy stabilności i odporności na błędy (v0.12)."""

import os
import unittest
from myszkahud.services.gemini.client import GeminiService, GeminiServiceError
from myszkahud.services.translation.translator import TranslationService
from myszkahud.services.ocr.engine import OCRService, GeminiOCRProvider
from myszkahud.services.speech.service import SpeechService, GeminiSpeechProvider
from myszkahud.services.process import ProcessService
from myszkahud.services.ram import RamService
from myszkahud.services.clipboard import ClipboardService, NotesService
from myszkahud.storage.clipboard_repo import SQLiteClipboardRepository
from myszkahud.storage.notes_repo import SQLiteNotesRepository


class TestStabilityAndErrorHandling(unittest.TestCase):
    """Weryfikacja braku awarii przy brakujących zależnościach i błędach środowiska."""

    def test_gemini_without_api_key(self):
        gemini = GeminiService(api_key=None)
        translator = TranslationService(ai_provider=gemini)
        
        with self.assertRaises((GeminiServiceError, Exception)):
            translator.translate("Hello world", "en", "pl")

    def test_ocr_without_api_key(self):
        gemini = GeminiService(api_key=None)
        provider = GeminiOCRProvider(vision_provider=gemini)
        ocr = OCRService(provider=provider)

        with self.assertRaises((GeminiServiceError, Exception)):
            ocr.recognize_text(b"fake_image_data")

    def test_speech_without_api_key(self):
        gemini = GeminiService(api_key=None)
        provider = GeminiSpeechProvider(audio_provider=gemini)
        speech = SpeechService(provider=provider)

        with self.assertRaises((GeminiServiceError, Exception)):
            speech.transcribe(b"fake_audio_bytes")

    def test_process_service_non_existent_pid(self):
        proc_service = ProcessService()
        success = proc_service.close_process(99999999)
        self.assertFalse(success)

        success_kill = proc_service.force_kill_process(99999999)
        self.assertFalse(success_kill)

    def test_ram_service_measure_safety(self):
        ram_service = RamService()
        stats = ram_service.get_stats()
        self.assertGreater(stats.total_bytes, 0)
        self.assertGreaterEqual(stats.percent, 0.0)

        result = ram_service.release_memory_safe()
        self.assertIsNotNone(result.released_bytes)
        self.assertTrue(result.success)

    def test_sqlite_in_memory_resilience(self):
        clip_repo = SQLiteClipboardRepository(db_path=":memory:")
        clip_svc = ClipboardService(repository=clip_repo)
        
        note_repo = SQLiteNotesRepository(db_path=":memory:")
        note_svc = NotesService(repository=note_repo)

        entry = clip_svc.add_clipboard_text("Wpis testowy")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.text, "Wpis testowy")

        note = note_svc.create_note("Tytuł", "Treść notatki")
        self.assertIsNotNone(note)
        self.assertEqual(note.title, "Tytuł")


if __name__ == "__main__":
    unittest.main()
