"""Global hotkey manager for Windows 10 using native Win32 API."""

import sys
import ctypes
from ctypes import wintypes

try:
    from PySide6.QtCore import QThread, Signal
except ImportError:
    class QThread:
        def __init__(self, parent=None):
            self.parent = parent
        def start(self):
            pass
        def isRunning(self):
            return False
        def quit(self):
            pass
        def wait(self, msecs=None):
            pass

    class Signal:
        def __init__(self, *types):
            self._callbacks = []
        def connect(self, callback):
            self._callbacks.append(callback)
        def emit(self, *args):
            for cb in self._callbacks:
                cb(*args)

# Win32 Modifier Constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

# Win32 Messages
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012


class WindowsHotkeyListener(QThread):
    """Watkowy nasluchiwacz globalnych skrotow klawiszowych dla Windows."""
    
    triggered = Signal()

    def __init__(self, key_code: int = ord('Q'), modifiers: int = MOD_ALT, hotkey_id: int = 1, parent=None):
        super().__init__(parent)
        self.key_code = key_code
        self.modifiers = modifiers
        self.hotkey_id = hotkey_id
        self._running = True
        self._thread_id = None

    def run(self):
        if sys.platform != "win32":
            print("[MyszkaHUD] Global hotkey jest aktywny tylko na systemie Windows.")
            return

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()

        # Rejestracja globalnego skrotu w petli komunikatow tego watku
        mod = self.modifiers | MOD_NOREPEAT
        success = user32.RegisterHotKey(None, self.hotkey_id, mod, self.key_code)
        if not success:
            # Fallback bez MOD_NOREPEAT
            success = user32.RegisterHotKey(None, self.hotkey_id, self.modifiers, self.key_code)

        if not success:
            print(f"[MyszkaHUD] OSTRZEZENIE: Nie udalo sie zarejestrowac globalnego skrotu (ID={self.hotkey_id}).")
            return

        msg = wintypes.MSG()
        while self._running:
            # GetMessageW czeka w stanie uspienia na komunikat, nie zuzywajac CPU
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            if msg.message == WM_HOTKEY and msg.wParam == self.hotkey_id:
                self.triggered.emit()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        user32.UnregisterHotKey(None, self.hotkey_id)

    def stop(self):
        """Bezpieczne zatrzymanie watku i wyrejestrowanie skrotu."""
        self._running = False
        if sys.platform == "win32" and self._thread_id:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        self.quit()
        self.wait(1000)
