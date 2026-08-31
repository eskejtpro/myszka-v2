"""Testy jednostkowe GeminiService, TranslationService, ClipboardFreshnessGuard i Worker (MyszkaHUD 0.3)."""

import unittest
from unittest.mock import MagicMock
from myszkahud.services.gemini.client import (
    GeminiService,
    GeminiAuthError,
    GeminiQuotaError,
    GeminiUnavailableError,
    GeminiAllModelsFailedError,
    GeminiServiceError,
    DEFAULT_MODELS
)
from myszkahud.services.translation.translator import (
    TranslationService,
    build_translation_prompt,
    build_translation_system_instruction,
    SUPPORTED_LANGUAGES
)
from myszkahud.core.windows import ClipboardFreshnessGuard
from myszkahud.ui.translation.worker import TranslationWorker


class TestGeminiService(unittest.TestCase):
    """Testy jednostkowe logiki wyboru modelu, fallbacku i klasyfikacji błędów bez zapytań sieciowych."""

    def test_missing_api_key_raises_auth_error(self):
        service = GeminiService(api_key="", client=None)
        with self.assertRaises(GeminiAuthError):
            service.generate_text("test prompt")

    def test_default_models_chain(self):
        service = GeminiService(api_key="fake-key")
        self.assertEqual(service.models, ["gemini-3.7-flash", "gemini-3.6-flash"])

    def test_primary_model_success_no_fallback(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Tłumaczenie tekstu"
        mock_client.models.generate_content.return_value = mock_response

        service = GeminiService(api_key="fake-key", client=mock_client)
        result = service.generate_text("Witaj świecie")

        self.assertEqual(result, "Tłumaczenie tekstu")
        mock_client.models.generate_content.assert_called_once()
        args, kwargs = mock_client.models.generate_content.call_args
        self.assertEqual(kwargs.get("model"), "gemini-3.7-flash")

    def test_fallback_37_to_36_on_429_quota(self):
        mock_client = MagicMock()
        mock_response_36 = MagicMock()
        mock_response_36.text = "Odpowiedź z fallbacku 3.6"

        # Pierwsze wywołanie (3.7-flash) rzuca 429, drugie (3.6-flash) zwraca sukces
        mock_client.models.generate_content.side_effect = [
            Exception("429 Resource has been exhausted (e.g. check quota)"),
            mock_response_36
        ]

        service = GeminiService(api_key="fake-key", client=mock_client)
        result = service.generate_text("Długi tekst do tłumaczenia")

        self.assertEqual(result, "Odpowiedź z fallbacku 3.6")
        self.assertEqual(mock_client.models.generate_content.call_count, 2)
        
        # Weryfikacja modeli w kolejności
        calls = mock_client.models.generate_content.call_args_list
        self.assertEqual(calls[0][1]["model"], "gemini-3.7-flash")
        self.assertEqual(calls[1][1]["model"], "gemini-3.6-flash")

    def test_fallback_on_503_service_unavailable(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Sukces po 503"

        mock_client.models.generate_content.side_effect = [
            Exception("503 Service Unavailable / Overloaded"),
            mock_response
        ]

        service = GeminiService(api_key="fake-key", client=mock_client)
        result = service.generate_text("Test")
        self.assertEqual(result, "Sukces po 503")
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_no_fallback_on_invalid_api_key_401(self):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("401 API_KEY_INVALID")

        service = GeminiService(api_key="bad-key", client=mock_client)
        with self.assertRaises(GeminiAuthError):
            service.generate_text("Test")
        # Nie powinien próbować fallbacku przy błędnym kluczu
        self.assertEqual(mock_client.models.generate_content.call_count, 1)

    def test_all_models_failed_exhaustion(self):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            Exception("429 Quota Exceeded"),
            Exception("429 Quota Exceeded")
        ]

        service = GeminiService(api_key="fake-key", client=mock_client)
        with self.assertRaises(GeminiAllModelsFailedError):
            service.generate_text("Test")
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_empty_prompt_returns_empty_string_without_api_call(self):
        mock_client = MagicMock()
        service = GeminiService(api_key="fake-key", client=mock_client)
        self.assertEqual(service.generate_text("   "), "")
        mock_client.models.generate_content.assert_not_called()


class TestTranslationService(unittest.TestCase):
    """Testy domenowe tłumacza i budowania promptów."""

    def test_build_system_instruction(self):
        instr = build_translation_system_instruction()
        self.assertIn("profesjonalnym", instr)
        self.assertIn("WYŁĄCZNIE", instr)

    def test_build_prompt_auto_to_en(self):
        prompt = build_translation_prompt("Dzień dobry", source_lang="auto", target_lang="en")
        self.assertIn("Angielski", prompt)
        self.assertIn("Dzień dobry", prompt)

    def test_build_prompt_pl_to_de(self):
        prompt = build_translation_prompt("Cześć", source_lang="pl", target_lang="de")
        self.assertIn("Polski", prompt)
        self.assertIn("Niemiecki", prompt)
        self.assertIn("Cześć", prompt)

    def test_translate_empty_text_returns_empty(self):
        mock_ai = MagicMock()
        service = TranslationService(ai_provider=mock_ai)
        self.assertEqual(service.translate(""), "")
        self.assertEqual(service.translate("   "), "")
        mock_ai.generate_text.assert_not_called()

    def test_translate_delegates_to_ai_provider(self):
        mock_ai = MagicMock()
        mock_ai.generate_text.return_value = "Hello world"

        service = TranslationService(ai_provider=mock_ai)
        res = service.translate("Witaj świecie", source_lang="pl", target_lang="en")

        self.assertEqual(res, "Hello world")
        mock_ai.generate_text.assert_called_once()
        args, kwargs = mock_ai.generate_text.call_args
        self.assertIn("Witaj świecie", args[0])
        self.assertIn("system_instruction", kwargs)


class TestClipboardFreshnessGuard(unittest.TestCase):
    """Testy logiki strażnika świeżości schowka."""

    def test_default_timeout_setting(self):
        guard = ClipboardFreshnessGuard(timeout_ms=500)
        self.assertEqual(guard.timeout_ms, 500)

    def test_non_windows_sequence_fallback(self):
        guard = ClipboardFreshnessGuard()
        # Na platformie innej niż win32 zwraca 0
        self.assertEqual(guard.get_sequence_number(), 0)


class TestTranslationWorkerLifecycle(unittest.TestCase):
    """Testy cyklu życia wątku TranslationWorker."""

    def test_worker_success_signal(self):
        mock_service = MagicMock()
        mock_service.translate.return_value = "Translated output"

        worker = TranslationWorker(service=mock_service, text="Source text")
        
        success_results = []
        worker.finished_success.connect(lambda txt: success_results.append(txt))
        worker.run()

        self.assertEqual(success_results, ["Translated output"])

    def test_worker_error_signal(self):
        mock_service = MagicMock()
        mock_service.translate.side_effect = GeminiAuthError("Brak klucza")

        worker = TranslationWorker(service=mock_service, text="Source text")
        
        errors = []
        worker.finished_error.connect(lambda msg, code: errors.append((msg, code)))
        worker.run()

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0][1], "AUTH_ERROR")

    def test_worker_cancellation_ignores_result(self):
        mock_service = MagicMock()
        mock_service.translate.return_value = "Late response"

        worker = TranslationWorker(service=mock_service, text="Source text")
        success_results = []
        worker.finished_success.connect(lambda txt: success_results.append(txt))
        
        worker.cancel()
        worker.run()

        # Po anulowaniu nie wolno emitować wyników
        self.assertEqual(len(success_results), 0)


if __name__ == "__main__":
    unittest.main()
