"""Testy jednostkowe dla modułu Single Instance Guard oraz Bezpiecznego Logowania (v0.12)."""

import os
import tempfile
import unittest
import logging
from myszkahud.core.single_instance import SingleInstanceGuard
from myszkahud.core.safe_logging import sanitize_text, SensitiveDataFilter


class TestSingleInstanceGuard(unittest.TestCase):
    """Testy działania ochrony przed wielokrotnym uruchomieniem instancji."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_single_instance_primary_and_secondary(self):
        guard1 = SingleInstanceGuard(mutex_name="Local\\Test_MyszkaHUD_Mutex_1", app_dir=self.temp_dir)
        is_primary1 = guard1.acquire()
        self.assertTrue(is_primary1)
        self.assertTrue(guard1.is_primary)

        # Druga próba powinna zostać odrzucona
        guard2 = SingleInstanceGuard(mutex_name="Local\\Test_MyszkaHUD_Mutex_1", app_dir=self.temp_dir)
        is_primary2 = guard2.acquire()
        self.assertFalse(is_primary2)
        self.assertFalse(guard2.is_primary)

        # Zwolnienie pierwszej instancji
        guard1.release()
        self.assertFalse(guard1.is_primary)

        # Teraz guard2 (lub kolejna instancja) może zająć blokadę
        guard3 = SingleInstanceGuard(mutex_name="Local\\Test_MyszkaHUD_Mutex_1", app_dir=self.temp_dir)
        is_primary3 = guard3.acquire()
        self.assertTrue(is_primary3)
        guard3.release()


class TestSafeLogging(unittest.TestCase):
    """Testy automatycznej sanityzacji danych wrażliwych w logach."""

    def test_sanitize_gemini_api_key(self):
        raw_log = "Init with key AIzaSyDUMMYKEY1234567890ABCDEFabcdef12"
        sanitized = sanitize_text(raw_log)
        self.assertNotIn("AIzaSyDUMMYKEY", sanitized)
        self.assertIn("[GEMINI_API_KEY_REDACTED]", sanitized)

    def test_sanitize_bearer_token(self):
        raw_log = "Authorization header: Bearer ya29.a0AfH6SMDUMMYTOKEN..."
        sanitized = sanitize_text(raw_log)
        self.assertIn("Bearer [TOKEN_REDACTED]", sanitized)

    def test_filter_record(self):
        filt = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=1,
            msg="Sending request with key AIzaSyABCDEFGHIJKLMN12345678901234567",
            args=(),
            exc_info=None
        )
        filt.filter(record)
        self.assertIn("[GEMINI_API_KEY_REDACTED]", record.msg)
        self.assertNotIn("AIzaSy", record.msg)


if __name__ == "__main__":
    unittest.main()
