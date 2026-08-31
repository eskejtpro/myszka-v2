"""Pakiet usług Speech-to-Text (STT) dla MyszkaHUD."""

from .service import SpeechService, MAX_RECORDING_SECONDS
from .state_machine import SpeechState, SpeechStateMachine, InvalidStateTransitionError
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
    "MAX_RECORDING_SECONDS",
    "SpeechState",
    "SpeechStateMachine",
    "InvalidStateTransitionError",
    "SpeechProvider",
    "GeminiSpeechProvider",
    "WindowsSpeechProvider",
    "AudioRecorder",
    "AudioDeviceNotFoundError",
    "build_wav_container"
]
