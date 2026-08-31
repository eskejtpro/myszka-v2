"""Testy jednostkowe modułu Speech-to-Text (STT) dla MyszkaHUD v0.5."""

import io
import wave
import unittest
from typing import List, Optional

from myszkahud.services.gemini.client import (
    GeminiService,
    GeminiAuthError,
    GeminiQuotaError,
    GeminiUnavailableError,
    DEFAULT_STT_MODELS,
)
from myszkahud.services.speech.audio_recorder import (
    build_wav_container,
    AudioDeviceNotFoundError,
    AudioRecorder
)
from myszkahud.services.speech.providers import (
    SpeechProvider,
    GeminiSpeechProvider,
    WindowsSpeechProvider
)
from myszkahud.services.speech.service import SpeechService, MAX_RECORDING_SECONDS
from myszkahud.services.speech.state_machine import (
    SpeechState,
    SpeechStateMachine,
    InvalidStateTransitionError
)
from myszkahud.ui.speech.worker import SpeechWorker
from myszkahud.ui.speech.speech_result_window import SpeechResultWindow
from myszkahud.ui.speech.speech_overlay import SpeechRecordingOverlay


class FakeAudioProvider:
    """Mock dostawcy audio dla testów GeminiSpeechProvider."""

    def __init__(self, response_text: str = "Witaj świecie testu mowy"):
        self.response_text = response_text
        self.last_prompt = ""
        self.last_audio_bytes = b""
        self.last_mime_type = ""
        self.last_system_instruction = ""
        self.last_models = None

    def generate_audio_transcription(
        self,
        prompt: str,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
        system_instruction: Optional[str] = None,
        models: Optional[List[str]] = None
    ) -> str:
        self.last_prompt = prompt
        self.last_audio_bytes = audio_bytes
        self.last_mime_type = mime_type
        self.last_system_instruction = system_instruction or ""
        self.last_models = models
        return self.response_text


class MockAudioFormat:
    """Mock obiektu QAudioFormat dla testów negocjacji formatu."""
    def __init__(self, sample_rate=16000, channels=1, sample_format=None):
        self._sample_rate = sample_rate
        self._channels = channels
        self._sample_format = sample_format

    def sampleRate(self):
        return self._sample_rate

    def setSampleRate(self, r):
        self._sample_rate = r

    def channelCount(self):
        return self._channels

    def setChannelCount(self, c):
        self._channels = c

    def sampleFormat(self):
        return self._sample_format

    def setSampleFormat(self, f):
        self._sample_format = f


class MockDeviceSupported:
    """Mock urządzenia z pełnym wsparciem dla 16 kHz mono Int16."""
    def isFormatSupported(self, fmt):
        return True

    def preferredFormat(self):
        return MockAudioFormat(48000, 2, "Int16")


class MockDeviceUnsupportedFallback:
    """Mock urządzenia bez wsparcia dla 16 kHz (np. profesjonalny mikser 48 kHz stereo)."""
    def isFormatSupported(self, fmt):
        return False

    def preferredFormat(self):
        return MockAudioFormat(48000, 2, "Int16")


class MockKeyEvent:
    """Mock zdarzenia klawiatury dla testów nakładki."""
    def __init__(self, key):
        self._key = key
        self._accepted = False

    def key(self):
        return self._key

    def accept(self):
        self._accepted = True

    def isAccepted(self):
        return self._accepted


class TestSpeechModule(unittest.TestCase):
    """Zestaw testów jednostkowych transkrypcji mowy."""

    # -------------------------------------------------------------
    # 1. State Machine Tests
    # -------------------------------------------------------------
    def test_state_machine_legal_full_flow(self):
        """Weryfikacja pełnego legalnego cyklu: IDLE -> RECORDING -> PROCESSING -> RESULT -> IDLE."""
        sm = SpeechStateMachine()
        self.assertEqual(sm.current_state, SpeechState.IDLE)
        self.assertTrue(sm.is_idle())

        sm.transition_to(SpeechState.RECORDING)
        self.assertEqual(sm.current_state, SpeechState.RECORDING)
        self.assertTrue(sm.is_recording())

        sm.transition_to(SpeechState.PROCESSING)
        self.assertEqual(sm.current_state, SpeechState.PROCESSING)
        self.assertTrue(sm.is_processing())

        sm.transition_to(SpeechState.RESULT)
        self.assertEqual(sm.current_state, SpeechState.RESULT)

        sm.transition_to(SpeechState.IDLE)
        self.assertEqual(sm.current_state, SpeechState.IDLE)

    def test_state_machine_cancellation_and_error(self):
        """Weryfikacja przejść anulowania i błędów."""
        # RECORDING -> CANCELLED -> IDLE
        sm = SpeechStateMachine()
        sm.transition_to(SpeechState.RECORDING)
        sm.transition_to(SpeechState.CANCELLED)
        self.assertEqual(sm.current_state, SpeechState.CANCELLED)
        sm.transition_to(SpeechState.IDLE)
        self.assertEqual(sm.current_state, SpeechState.IDLE)

        # RECORDING -> ERROR -> IDLE
        sm.transition_to(SpeechState.RECORDING)
        sm.transition_to(SpeechState.ERROR)
        self.assertEqual(sm.current_state, SpeechState.ERROR)
        sm.transition_to(SpeechState.IDLE)

        # PROCESSING -> ERROR
        sm.transition_to(SpeechState.RECORDING)
        sm.transition_to(SpeechState.PROCESSING)
        sm.transition_to(SpeechState.ERROR)
        self.assertEqual(sm.current_state, SpeechState.ERROR)

    def test_state_machine_illegal_transitions_rejected(self):
        """Odrzucenie nielegalnych przejść, np. PROCESSING -> RECORDING lub IDLE -> RESULT."""
        sm = SpeechStateMachine()

        # IDLE -> RESULT jest nielegalne
        with self.assertRaises(InvalidStateTransitionError):
            sm.transition_to(SpeechState.RESULT)

        # IDLE -> PROCESSING jest nielegalne
        with self.assertRaises(InvalidStateTransitionError):
            sm.transition_to(SpeechState.PROCESSING)

        sm.transition_to(SpeechState.RECORDING)
        sm.transition_to(SpeechState.PROCESSING)

        # PROCESSING -> RECORDING (próba podwójnego nagrania) jest nielegalna
        with self.assertRaises(InvalidStateTransitionError):
            sm.transition_to(SpeechState.RECORDING)

        # PROCESSING -> IDLE bez pośredniego RESULT/ERROR/CANCELLED jest nielegalne
        with self.assertRaises(InvalidStateTransitionError):
            sm.transition_to(SpeechState.IDLE)

    # -------------------------------------------------------------
    # 2. Key Handling (Enter vs Space vs Esc)
    # -------------------------------------------------------------
    def test_overlay_key_events_enter_and_esc(self):
        """Weryfikacja: Enter zatrzymuje i emituje wynik, Esc anuluje, Spacja nie zatrzymuje."""
        overlay = SpeechRecordingOverlay()
        
        stopped = []
        cancelled = []
        overlay.recording_finished.connect(lambda b: stopped.append(b))
        overlay.cancelled.connect(lambda: cancelled.append(True))

        # 1. Test klawisza Escape -> anulowanie
        mock_esc = MockKeyEvent(0x01000000)  # Qt.Key_Escape
        overlay.keyPressEvent(mock_esc)
        self.assertTrue(mock_esc.isAccepted())
        self.assertEqual(len(cancelled), 1)

        # 2. Test klawisza Enter -> zatrzymanie
        mock_enter = MockKeyEvent(0x01000004)  # Qt.Key_Return
        overlay.keyPressEvent(mock_enter)
        self.assertTrue(mock_enter.isAccepted())
        self.assertEqual(len(stopped), 1)

        # 3. Test klawisza Spacja -> NIE powinien zatrzymywać nagrania
        stopped.clear()
        mock_space = MockKeyEvent(0x20)  # Qt.Key_Space
        overlay.keyPressEvent(mock_space)
        self.assertFalse(mock_space.isAccepted())
        self.assertEqual(len(stopped), 0)

    # -------------------------------------------------------------
    # 3. MAX_RECORDING_SECONDS Limit Tests
    # -------------------------------------------------------------
    def test_max_recording_seconds_constant(self):
        """Potwierdzenie istnienia stałej MAX_RECORDING_SECONDS = 60."""
        self.assertEqual(MAX_RECORDING_SECONDS, 60)

    def test_overlay_auto_stops_at_max_seconds(self):
        """Po osiągnięciu limitu sekund nakładka automatycznie zatrzymuje nagranie."""
        overlay = SpeechRecordingOverlay(max_seconds=5)
        stopped = []
        overlay.recording_finished.connect(lambda b: stopped.append(b))

        # Symulacja 4 sekund - nagranie trwa
        for _ in range(4):
            overlay._on_timer_tick()
        self.assertEqual(len(stopped), 0)

        # 5. sekunda (osiągnięcie max_seconds) -> automatyczny stop
        overlay._on_timer_tick()
        self.assertEqual(len(stopped), 1)

    # -------------------------------------------------------------
    # 4. Audio Format Negotiation Tests
    # -------------------------------------------------------------
    def test_audio_format_negotiation_supported(self):
        """Gdy urządzenie obsługuje 16 kHz, negocjator wybiera żądany format 16 kHz mono."""
        rec = AudioRecorder(target_sample_rate=16000)
        device = MockDeviceSupported()
        fmt, rate, channels, width = rec._determine_audio_format(device)

        self.assertEqual(rate, 16000)
        self.assertEqual(channels, 1)
        self.assertEqual(width, 2)

    def test_audio_format_negotiation_unsupported_fallback(self):
        """Gdy urządzenie nie obsługuje 16 kHz, negocjator pobiera preferredFormat (48 kHz stereo)."""
        rec = AudioRecorder(target_sample_rate=16000)
        device = MockDeviceUnsupportedFallback()
        fmt, rate, channels, width = rec._determine_audio_format(device)

        self.assertEqual(rate, 48000)
        self.assertEqual(channels, 2)
        self.assertEqual(width, 2)

    # -------------------------------------------------------------
    # 5. Audio WAV Container Tests
    # -------------------------------------------------------------
    def test_build_wav_container_valid_header_16khz(self):
        """Weryfikacja tworzenia poprawnego nagłówka RIFF WAV 16 kHz mono."""
        raw_pcm = b"\x00\x00" * 16000
        wav_bytes = build_wav_container(raw_pcm, sample_rate=16000, channels=1, sample_width=2)

        self.assertTrue(wav_bytes.startswith(b"RIFF"))
        self.assertIn(b"WAVE", wav_bytes)

        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(wf.getframerate(), 16000)
            self.assertEqual(wf.getnframes(), 16000)

    def test_build_wav_container_custom_sample_rate_48khz(self):
        """Weryfikacja pakowania audio w natywnym formacie mikrofonu 48 kHz stereo."""
        raw_pcm = b"\x01\x00\x02\x00" * 48000
        wav_bytes = build_wav_container(raw_pcm, sample_rate=48000, channels=2, sample_width=2)

        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            self.assertEqual(wf.getnchannels(), 2)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(wf.getframerate(), 48000)
            self.assertEqual(wf.getnframes(), 48000)

    def test_build_wav_container_empty_returns_empty(self):
        """Puste dane PCM zwracają pusty bufor."""
        self.assertEqual(build_wav_container(b""), b"")

    # -------------------------------------------------------------
    # 6. Speech Providers & Gemini Integration Tests
    # -------------------------------------------------------------
    def test_gemini_speech_provider_transcription(self):
        """Weryfikacja działania GeminiSpeechProvider i instrukcji systemowej pl-PL."""
        mock_provider = FakeAudioProvider("Dzień dobry, testuję MyszkaHUD.")
        provider = GeminiSpeechProvider(audio_provider=mock_provider)

        test_audio = b"RIFF_FAKE_AUDIO_BYTES"
        result = provider.transcribe(test_audio, mime_type="audio/wav", language_tag="pl-PL")

        self.assertEqual(result, "Dzień dobry, testuję MyszkaHUD.")
        self.assertIn("pl-PL", mock_provider.last_prompt)
        self.assertIn("Speech-to-Text", mock_provider.last_system_instruction)
        self.assertEqual(mock_provider.last_models, DEFAULT_STT_MODELS)
        self.assertEqual(mock_provider.last_models[0], "gemini-3.5-transcribe")

    def test_gemini_speech_provider_empty_audio(self):
        """Pusty bufor audio nie wysyła zapytania."""
        mock_provider = FakeAudioProvider("Coś")
        provider = GeminiSpeechProvider(audio_provider=mock_provider)

        result = provider.transcribe(b"")
        self.assertEqual(result, "")
        self.assertEqual(mock_provider.last_prompt, "")

    def test_windows_speech_provider_on_unsupported_or_linux(self):
        """WindowsSpeechProvider poprawnie raportuje stan walidacji Windows."""
        provider = WindowsSpeechProvider(language_tag="pl-PL")
        with self.assertRaises(NotImplementedError) as ctx:
            provider.transcribe(b"FAKE_AUDIO")
        self.assertIn("OCZEKUJE NA WINDOWS VALIDATION", str(ctx.exception))

    def test_speech_service_delegation_and_switch(self):
        """Weryfikacja SpeechService i dynamicznego przełączania dostawcy."""
        mock_gemini = FakeAudioProvider("Transkrypcja z chmury")
        prov1 = GeminiSpeechProvider(audio_provider=mock_gemini)
        service = SpeechService(provider=prov1)

        self.assertEqual(service.transcribe(b"AUDIO"), "Transkrypcja z chmury")

        mock_local = FakeAudioProvider("Transkrypcja lokalna")
        prov2 = GeminiSpeechProvider(audio_provider=mock_local)
        service.set_provider(prov2)
        self.assertEqual(service.get_provider(), prov2)
        self.assertEqual(service.transcribe(b"AUDIO"), "Transkrypcja lokalna")

    def test_gemini_service_audio_fallback_chain(self):
        """Test automatycznego fallbacku w GeminiService.generate_audio_transcription."""
        calls = []

        def mock_client_call(model, prompt, audio_bytes, mime_type, system_instruction):
            calls.append(model)
            if model == "gemini-3.5-transcribe":
                # Symulacja przeciążenia / 429 dla dedykowanego modelu
                raise GeminiQuotaError("Model 3.5 transcribe przeciążony (429)")
            return "Odpowiedź z modelu fallback 3.7"

        gemini_svc = GeminiService(
            api_key="test_key",
            client=mock_client_call
        )

        result = gemini_svc.generate_audio_transcription(
            prompt="Transkrybuj",
            audio_bytes=b"AUDIO_DATA",
            models=["gemini-3.5-transcribe", "gemini-3.7-flash"]
        )

        self.assertEqual(result, "Odpowiedź z modelu fallback 3.7")
        self.assertEqual(calls, ["gemini-3.5-transcribe", "gemini-3.7-flash"])

    def test_speech_worker_signals_and_cancellation(self):
        """Weryfikacja SpeechWorker: sukces, błędy i anulowanie."""
        mock_provider = FakeAudioProvider("Pomyślna transkrypcja")
        speech_svc = SpeechService(provider=GeminiSpeechProvider(audio_provider=mock_provider))

        worker = SpeechWorker(service=speech_svc, audio_bytes=b"AUDIO")
        results = []
        worker.finished_success.connect(lambda t: results.append(t))
        worker.run()

        self.assertEqual(results, ["Pomyślna transkrypcja"])

        # Test anulowania
        worker_cancelled = SpeechWorker(service=speech_svc, audio_bytes=b"AUDIO")
        worker_cancelled.cancel()
        results_c = []
        worker_cancelled.finished_success.connect(lambda t: results_c.append(t))
        worker_cancelled.run()
        self.assertEqual(results_c, [])

    def test_speech_result_window_signals(self):
        """Weryfikacja sygnałów okna wyników transkrypcji."""
        win = SpeechResultWindow()
        win.set_text("Przykładowy tekst ze mowy")

        copied = []
        pasted = []
        pasted_enter = []
        translated = []

        win.copy_requested.connect(lambda t: copied.append(t))
        win.paste_requested.connect(lambda t: pasted.append(t))
        win.paste_enter_requested.connect(lambda t: pasted_enter.append(t))
        win.translate_requested.connect(lambda t: translated.append(t))

        win._on_copy_clicked()
        self.assertEqual(copied, ["Przykładowy tekst ze mowy"])

        win._on_paste_clicked()
        self.assertEqual(pasted, ["Przykładowy tekst ze mowy"])

        win._on_paste_enter_clicked()
        self.assertEqual(pasted_enter, ["Przykładowy tekst ze mowy"])

        win._on_translate_clicked()
        self.assertEqual(translated, ["Przykładowy tekst ze mowy"])


if __name__ == "__main__":
    unittest.main()
