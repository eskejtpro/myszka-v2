"""Maszyna stanów dla przepływu nagrywania i transkrypcji mowy (Speech-to-Text).

Dozwolone stany:
IDLE -> RECORDING -> PROCESSING -> RESULT
oraz:
RECORDING -> CANCELLED -> IDLE
RECORDING -> ERROR -> IDLE
PROCESSING -> ERROR -> IDLE
RESULT -> IDLE
"""

import enum
from typing import Set, Tuple


class SpeechState(str, enum.Enum):
    IDLE = "IDLE"
    RECORDING = "RECORDING"
    PROCESSING = "PROCESSING"
    RESULT = "RESULT"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


# Zdefiniowane legalne przejścia stanów
VALID_TRANSITIONS: Set[Tuple[SpeechState, SpeechState]] = {
    (SpeechState.IDLE, SpeechState.RECORDING),
    (SpeechState.RECORDING, SpeechState.PROCESSING),
    (SpeechState.RECORDING, SpeechState.CANCELLED),
    (SpeechState.RECORDING, SpeechState.ERROR),
    (SpeechState.PROCESSING, SpeechState.RESULT),
    (SpeechState.PROCESSING, SpeechState.ERROR),
    (SpeechState.PROCESSING, SpeechState.CANCELLED),
    (SpeechState.RESULT, SpeechState.IDLE),
    (SpeechState.RESULT, SpeechState.RECORDING),  # Retry / nowe nagranie
    (SpeechState.CANCELLED, SpeechState.IDLE),
    (SpeechState.CANCELLED, SpeechState.RECORDING),
    (SpeechState.ERROR, SpeechState.IDLE),
    (SpeechState.ERROR, SpeechState.RECORDING),
}


class InvalidStateTransitionError(RuntimeError):
    """Błąd nielegalnego przejścia w maszynie stanów."""
    def __init__(self, current_state: SpeechState, target_state: SpeechState):
        super().__init__(
            f"Nielegalne przejście stanu mowy: {current_state.value} -> {target_state.value}"
        )
        self.current_state = current_state
        self.target_state = target_state


class SpeechStateMachine:
    """
    Jawna, lekka maszyna stanów dla modułu mowy MyszkaHUD.
    Chroni przed jednoczesnym uruchomieniem wielu nagrań lub nielegalnymi sekwencjami.
    """

    def __init__(self, initial_state: SpeechState = SpeechState.IDLE):
        self._state = initial_state

    @property
    def current_state(self) -> SpeechState:
        return self._state

    def is_idle(self) -> bool:
        return self._state == SpeechState.IDLE

    def is_recording(self) -> bool:
        return self._state == SpeechState.RECORDING

    def is_processing(self) -> bool:
        return self._state == SpeechState.PROCESSING

    def can_transition_to(self, target_state: SpeechState) -> bool:
        """Sprawdza, czy przejście ze stanu bieżącego do target_state jest dozwolone."""
        return (self._state, target_state) in VALID_TRANSITIONS

    def transition_to(self, target_state: SpeechState) -> SpeechState:
        """
        Zmienia stan na target_state lub rzuca InvalidStateTransitionError.
        """
        if not self.can_transition_to(target_state):
            raise InvalidStateTransitionError(self._state, target_state)

        self._state = target_state
        return self._state

    def reset(self) -> None:
        """Resetuje maszynę stanów do stanu początkowego IDLE."""
        self._state = SpeechState.IDLE
