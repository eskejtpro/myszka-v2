"""Pakiet usług Speech-to-Text (STT) dla MyszkaHUD."""

from .service import SpeechService
from .audio_recorder import (
    AudioRecorder,
    AudioDeviceNotFoundError,
    build_wav_container
)
from .providers import (
    SpeechProvider,
    GeminiSpeechProvider,
    WindowsSpeechProvider
)

__all__ = [
    "SpeechService",
    "SpeechProvider",
    "GeminiSpeechProvider",
    "WindowsSpeechProvider",
    "AudioRecorder",
    "AudioDeviceNotFoundError",
    "build_wav_container"
]
