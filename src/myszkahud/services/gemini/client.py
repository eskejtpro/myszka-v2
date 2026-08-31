"""Moduł integracji z Google Gemini API."""

import os
import time
from typing import List, Optional, Protocol


class AITextProvider(Protocol):
    """Protokół / interfejs dostawcy tekstu AI dla luźnego powiązania."""
    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        ...


class VisionProvider(Protocol):
    """Protokół dostawcy analizy wizualnej / multimodalnej dla luźnego powiązania."""
    def generate_multimodal(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
        system_instruction: Optional[str] = None
    ) -> str:
        ...


class AudioTranscribeProvider(Protocol):
    """Protokół dostawcy transkrypcji mowy (STT) dla luźnego powiązania."""
    def generate_audio_transcription(
        self,
        prompt: str,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
        system_instruction: Optional[str] = None,
        models: Optional[List[str]] = None
    ) -> str:
        ...


class GeminiServiceError(Exception):
    """Bazowy wyjątek dla błędów GeminiService."""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", should_fallback: bool = False):
        super().__init__(message)
        self.error_code = error_code
        self.should_fallback = should_fallback


class GeminiAuthError(GeminiServiceError):
    """Błąd braku lub niepoprawnego klucza API."""
    def __init__(self, message: str = "Brak skonfigurowanego GEMINI_API_KEY"):
        super().__init__(message, error_code="AUTH_ERROR", should_fallback=False)


class GeminiQuotaError(GeminiServiceError):
    """Błąd limitu zapytań / rate limit (429)."""
    def __init__(self, message: str = "Przekroczono limit zapytań Gemini API (429)"):
        super().__init__(message, error_code="QUOTA_EXCEEDED", should_fallback=True)


class GeminiUnavailableError(GeminiServiceError):
    """Błąd przejściowej niedostępności usługi / błąd 5xx."""
    def __init__(self, message: str = "Usługa Gemini API jest chwilowo niedostępna"):
        super().__init__(message, error_code="SERVICE_UNAVAILABLE", should_fallback=True)


class GeminiAllModelsFailedError(GeminiServiceError):
    """Wyjątek rzucany po wyczerpaniu wszystkich modeli w łańcuchu fallbacku."""
    def __init__(self, last_error: Optional[Exception] = None):
        msg = f"Wszystkie modele Gemini zawiodły. Ostatni błąd: {last_error}"
        super().__init__(msg, error_code="ALL_MODELS_FAILED", should_fallback=False)
        self.last_error = last_error


# Domyślny łańcuch modeli dla tekstu i wizji
DEFAULT_MODELS = [
    "gemini-3.7-flash",  # PRIMARY
    "gemini-3.6-flash",  # FALLBACK
]

# Domyślny łańcuch modeli dla transkrypcji mowy (STT)
DEFAULT_STT_MODELS = [
    "gemini-3.5-transcribe",  # PRIMARY dla transkrypcji audio
    "gemini-3.7-flash",       # FALLBACK 1 (multimodal)
    "gemini-3.6-flash",       # FALLBACK 2 (multimodal)
]


class GeminiService:
    """
    Centralna usługa komunikacji z Google Gemini API.
    Obsługuje:
    - odczyt GEMINI_API_KEY,
    - listę modeli z automatycznym fallbackiem (3.7-flash -> 3.6-flash),
    - klasyfikację błędów sieciowych i limitów,
    - wstrzykiwanie klienta (mocking dla testów).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        models: Optional[List[str]] = None,
        client: Optional[object] = None,
        timeout_sec: float = 20.0
    ):
        if api_key is not None:
            self._api_key = api_key
        else:
            self._api_key = os.getenv("GEMINI_API_KEY", "")
        self.models = models or list(DEFAULT_MODELS)
        self.client = client
        self.timeout_sec = timeout_sec

    def _ensure_client(self):
        """Lazy-inicjalizacja klienta Google GenAI."""
        if self.client is not None:
            return self.client

        if not self._api_key or not self._api_key.strip():
            raise GeminiAuthError("Brak klucza API. Ustaw zmienną środowiskową GEMINI_API_KEY.")

        try:
            from google import genai
            self.client = genai.Client(api_key=self._api_key)
            return self.client
        except ImportError:
            raise GeminiServiceError(
                "Pakiet 'google-genai' nie jest zainstalowany. Zainstaluj go przez pip install google-genai",
                error_code="MISSING_PACKAGE"
            )
        except Exception as e:
            raise GeminiServiceError(f"Nie udało się zainicjalizować klienta GenAI: {e}", error_code="INIT_ERROR")

    def _is_fallback_error(self, err: Exception) -> bool:
        """Sprawdza, czy dany błąd kwalifikuje się do przełączenia na model zapasowy."""
        if isinstance(err, (GeminiQuotaError, GeminiUnavailableError)):
            return True

        err_str = str(err).lower()
        # Kody HTTP kwalifikujące się do fallbacku
        if "429" in err_str or "quota" in err_str or "rate limit" in err_str or "resource_exhausted" in err_str:
            return True
        if "500" in err_str or "503" in err_str or "unavailable" in err_str or "overloaded" in err_str:
            return True

        return False

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Wysyła zapytanie do Gemini z automatycznym przełączaniem na model zapasowy.
        """
        if not prompt or not prompt.strip():
            return ""

        client = self._ensure_client()
        last_error = None

        for model_name in self.models:
            try:
                # Wywołanie SDK Google GenAI
                config = {}
                if system_instruction:
                    config["system_instruction"] = system_instruction

                # Obsługa prawdziwego klienta SDK lub mocka testowego
                if hasattr(client, "models") and hasattr(client.models, "generate_content"):
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config if config else None
                    )
                elif callable(client):
                    # Wsparcie dla wstrzykniętych funkcji testowych
                    response = client(model=model_name, prompt=prompt, system_instruction=system_instruction)
                else:
                    raise GeminiServiceError(f"Nieprawidłowy interfejs klienta: {type(client)}")

                # Ekstrakcja tekstu z odpowiedzi
                if hasattr(response, "text"):
                    return response.text.strip()
                elif isinstance(response, str):
                    return response.strip()
                else:
                    return str(response).strip()

            except Exception as e:
                last_error = e
                # Sprawdzamy czy to błąd autoryzacji (wtedy nie robimy fallbacku)
                err_str = str(e).lower()
                if "401" in err_str or "403" in err_str or "api_key_invalid" in err_str or "invalid api key" in err_str:
                    raise GeminiAuthError(f"Niepoprawny klucz Gemini API: {e}")

                if self._is_fallback_error(e):
                    # Przechodzimy do kolejnego modelu w liście
                    continue
                else:
                    # Błąd programistyczny lub niekwalifikujący się do fallbacku
                    raise GeminiServiceError(f"Błąd zapytania Gemini API: {e}", error_code="API_ERROR")

        # Jeśli pętla wyczerpała wszystkie modele
        raise GeminiAllModelsFailedError(last_error)

    def generate_multimodal(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Wysyła zapytanie multimodalne (tekst + obraz) z automatycznym fallbackiem (3.7 -> 3.6).
        """
        if not image_bytes:
            return ""

        client = self._ensure_client()
        last_error = None

        for model_name in self.models:
            try:
                config = {}
                if system_instruction:
                    config["system_instruction"] = system_instruction

                if hasattr(client, "models") and hasattr(client.models, "generate_content"):
                    try:
                        from google.genai import types
                        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                    except ImportError:
                        # Środowisko testowe / mock bez zainstalowanego pakietu google.genai
                        part = {"data": image_bytes, "mime_type": mime_type}
                    contents = [prompt, part] if prompt else [part]

                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config if config else None
                    )
                elif callable(client):
                    # Wsparcie dla wstrzykniętych funkcji testowych / mocków
                    response = client(
                        model=model_name,
                        prompt=prompt,
                        image_bytes=image_bytes,
                        mime_type=mime_type,
                        system_instruction=system_instruction
                    )
                else:
                    raise GeminiServiceError(f"Nieprawidłowy interfejs klienta: {type(client)}")

                if hasattr(response, "text"):
                    return response.text.strip()
                elif isinstance(response, str):
                    return response.strip()
                else:
                    return str(response).strip()

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if "401" in err_str or "403" in err_str or "api_key_invalid" in err_str or "invalid api key" in err_str:
                    raise GeminiAuthError(f"Niepoprawny klucz Gemini API: {e}")

                if self._is_fallback_error(e):
                    continue
                else:
                    raise GeminiServiceError(f"Błąd multimodalnego zapytania Gemini API: {e}", error_code="API_ERROR")

        raise GeminiAllModelsFailedError(last_error)

    def generate_audio_transcription(
        self,
        prompt: str,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
        system_instruction: Optional[str] = None,
        models: Optional[List[str]] = None
    ) -> str:
        """
        Wysyła zapytanie transkrypcji audio (STT) z automatycznym fallbackiem modeli STT.
        """
        if not audio_bytes:
            return ""

        client = self._ensure_client()
        target_models = models or list(DEFAULT_STT_MODELS)
        last_error = None

        for model_name in target_models:
            try:
                config = {}
                if system_instruction:
                    config["system_instruction"] = system_instruction

                if hasattr(client, "models") and hasattr(client.models, "generate_content"):
                    try:
                        from google.genai import types
                        part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
                    except ImportError:
                        # Środowisko testowe / mock bez pakietu google.genai
                        part = {"data": audio_bytes, "mime_type": mime_type}
                    contents = [prompt, part] if prompt else [part]

                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config if config else None
                    )
                elif callable(client):
                    # Wsparcie dla wstrzykniętych funkcji testowych / mocków
                    response = client(
                        model=model_name,
                        prompt=prompt,
                        audio_bytes=audio_bytes,
                        mime_type=mime_type,
                        system_instruction=system_instruction
                    )
                else:
                    raise GeminiServiceError(f"Nieprawidłowy interfejs klienta: {type(client)}")

                if hasattr(response, "text"):
                    return response.text.strip()
                elif isinstance(response, str):
                    return response.strip()
                else:
                    return str(response).strip()

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if "401" in err_str or "403" in err_str or "api_key_invalid" in err_str or "invalid api key" in err_str:
                    raise GeminiAuthError(f"Niepoprawny klucz Gemini API: {e}")

                if self._is_fallback_error(e):
                    continue
                else:
                    raise GeminiServiceError(f"Błąd transkrypcji audio Gemini API: {e}", error_code="API_ERROR")

        raise GeminiAllModelsFailedError(last_error)


