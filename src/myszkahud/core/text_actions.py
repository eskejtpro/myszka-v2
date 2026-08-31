"""Moduł bezpiecznej symulacji operacji tekstowych i klawiaturowych (Windows SendInput)."""

import sys
import time
import ctypes
from ctypes import wintypes
from enum import Enum
from typing import List, Tuple, Optional

try:
    from PySide6.QtGui import QGuiApplication
except ImportError:
    QGuiApplication = None


class TextAction(Enum):
    COPY = "copy"
    CUT = "cut"
    PASTE = "paste"
    PASTE_ENTER = "paste_enter"
    PASTE_PLAIN = "paste_plain"
    SELECT_ALL = "select_all"
    UNDO = "undo"
    REDO = "redo"


# Win32 Virtual Key Codes
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_RETURN = 0x0D
VK_A = 0x41
VK_C = 0x43
VK_V = 0x56
VK_X = 0x58
VK_Y = 0x59
VK_Z = 0x5A

# SendInput Constants
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", INPUT_UNION),
    ]


def build_key_event(vk_code: int, key_up: bool = False) -> Tuple[int, bool]:
    """Generuje parę (kod_klawisza, czy_up)."""
    return vk_code, key_up


def build_action_sequence(action: TextAction, redo_use_shift_z: bool = False) -> List[Tuple[int, bool]]:
    """
    Buduje poprawną sekwencję wciśnięć i zwolnień klawiszy (key down / key up)
    dla danej akcji tekstowej. Gwarantuje symetryczne zwalnianie modyfikatorów.
    """
    seq: List[Tuple[int, bool]] = []

    if action == TextAction.COPY:
        seq.append((VK_CONTROL, False))
        seq.append((VK_C, False))
        seq.append((VK_C, True))
        seq.append((VK_CONTROL, True))

    elif action == TextAction.CUT:
        seq.append((VK_CONTROL, False))
        seq.append((VK_X, False))
        seq.append((VK_X, True))
        seq.append((VK_CONTROL, True))

    elif action in (TextAction.PASTE, TextAction.PASTE_PLAIN):
        seq.append((VK_CONTROL, False))
        seq.append((VK_V, False))
        seq.append((VK_V, True))
        seq.append((VK_CONTROL, True))

    elif action == TextAction.PASTE_ENTER:
        seq.append((VK_CONTROL, False))
        seq.append((VK_V, False))
        seq.append((VK_V, True))
        seq.append((VK_CONTROL, True))
        seq.append((VK_RETURN, False))
        seq.append((VK_RETURN, True))

    elif action == TextAction.SELECT_ALL:
        seq.append((VK_CONTROL, False))
        seq.append((VK_A, False))
        seq.append((VK_A, True))
        seq.append((VK_CONTROL, True))

    elif action == TextAction.UNDO:
        seq.append((VK_CONTROL, False))
        seq.append((VK_Z, False))
        seq.append((VK_Z, True))
        seq.append((VK_CONTROL, True))

    elif action == TextAction.REDO:
        if redo_use_shift_z:
            seq.append((VK_CONTROL, False))
            seq.append((VK_SHIFT, False))
            seq.append((VK_Z, False))
            seq.append((VK_Z, True))
            seq.append((VK_SHIFT, True))
            seq.append((VK_CONTROL, True))
        else:
            seq.append((VK_CONTROL, False))
            seq.append((VK_Y, False))
            seq.append((VK_Y, True))
            seq.append((VK_CONTROL, True))

    return seq


class TextActionExecutor:
    """Wykonawca operacji tekstowych z bezpieczną obsługą schowka i SendInput."""

    def __init__(self, redo_use_shift_z: bool = False):
        self.redo_use_shift_z = redo_use_shift_z

    def send_input_sequence(self, sequence: List[Tuple[int, bool]]) -> bool:
        """
        Wysyła sekwencję zdarzeń klawiatury przez Win32 SendInput.
        W przypadku błędu wymusza wyzerowanie modyfikatorów.
        """
        if not sequence:
            return False

        if sys.platform != "win32":
            return True

        n_events = len(sequence)
        input_array = (INPUT * n_events)()

        for i, (vk_code, is_up) in enumerate(sequence):
            flags = KEYEVENTF_KEYUP if is_up else 0
            input_array[i].type = INPUT_KEYBOARD
            input_array[i].u.ki = KEYBDINPUT(
                wVk=vk_code,
                wScan=0,
                dwFlags=flags,
                time=0,
                dwExtraInfo=None
            )

        user32 = ctypes.windll.user32
        sent = user32.SendInput(n_events, ctypes.byref(input_array), ctypes.sizeof(INPUT))
        
        if sent != n_events:
            # Awaryjne zwolnienie modyfikatorów w razie niepełnego wysłania
            self._emergency_release_modifiers()
            return False

        return True

    def _emergency_release_modifiers(self):
        """Zwalnia klawisze Ctrl, Shift i Alt, zapobiegając 'zablokowaniu klawisza'."""
        if sys.platform != "win32":
            return
        user32 = ctypes.windll.user32
        modifiers = [VK_CONTROL, VK_SHIFT, 0x12]  # VK_MENU (Alt) = 0x12
        arr = (INPUT * len(modifiers))()
        for i, vk in enumerate(modifiers):
            arr[i].type = INPUT_KEYBOARD
            arr[i].u.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=None)
        user32.SendInput(len(modifiers), ctypes.byref(arr), ctypes.sizeof(INPUT))

    def prepare_plain_text_clipboard(self) -> Optional[str]:
        """
        Konwertuje aktualną zawartość schowka na czysty tekst (plain text).
        Zwraca wyodrębniony tekst lub None.
        """
        clipboard = QGuiApplication.clipboard()
        if not clipboard:
            return None

        text = clipboard.text()
        if text:
            # Ponowne ustawienie jako czysty tekst bez znaczników HTML/RTF
            clipboard.setText(text)
            return text
        return None

    def execute_action(self, action: TextAction) -> bool:
        """
        Wykonuje pełną akcję tekstową.
        Dla PASTE_PLAIN najpierw konwertuje schowek na czysty tekst.
        """
        if action == TextAction.PASTE_PLAIN:
            self.prepare_plain_text_clipboard()

        seq = build_action_sequence(action, redo_use_shift_z=self.redo_use_shift_z)
        return self.send_input_sequence(seq)
