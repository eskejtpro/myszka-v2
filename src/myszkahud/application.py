"""Główna klasa aplikacji MyszkaHUD (v0.12 — Stabilność, Ochrona Instancji i Bezpieczne Logowanie)."""

import sys
import time
import signal
import logging
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QObject
    from PySide6.QtGui import QGuiApplication
except ImportError:
    class MockApp:
        @staticmethod
        def instance():
            return None
        def setApplicationName(self, name): pass
        def setApplicationDisplayName(self, name): pass
        def setQuitOnLastWindowClosed(self, val): pass
        def exec(self): return 0
        def quit(self): pass
    
    QApplication = MockApp
    QObject = object
    class QGuiApplication:
        @staticmethod
        def clipboard():
            return None

from .ui.hud.radial_hud import RadialHUDWindow
from .ui.hud.text_actions_menu import TextActionsMenuWindow
from .ui.translation.translation_window import TranslationWindow
from .ui.ocr.snipping_overlay import ScreenSnippingOverlay
from .ui.ocr.ocr_window import OCRResultWindow
from .ui.speech.speech_overlay import SpeechRecordingOverlay
from .ui.speech.speech_result_window import SpeechResultWindow
from .ui.clipboard import ClipboardWindow
from .ui.process import ProcessWindow
from .ui.ram import RamWindow
from .ui.settings import SettingsWindow
from .ui.tray import TrayManager

from .core.hotkeys import WindowsHotkeyListener
from .core.windows import WindowManager, ClipboardFreshnessGuard
from .core.text_actions import TextActionExecutor, TextAction
from .core.single_instance import SingleInstanceGuard
from .core.safe_logging import setup_safe_logging

from .services.gemini.client import GeminiService
from .services.translation.translator import TranslationService
from .services.ocr.engine import OCRService, GeminiOCRProvider
from .services.speech import SpeechService, GeminiSpeechProvider
from .services.clipboard import (
    ClipboardService,
    NotesService,
    ClipboardMonitor,
    ClipboardWriteGuard,
)
from .services.process import ProcessService
from .services.ram import RamService
from .services.settings import SettingsService
from .services.autostart import AutostartService

# Inicjalizacja bezpiecznego loggera filtrującego dane wrażliwe
setup_safe_logging()
logger = logging.getLogger(__name__)


class MyszkaHUDApp(QObject):
    """Zarządca cyklu życia, integracji serwisów i okien interfejsu MyszkaHUD."""

    def __init__(self, argv=None):
        super().__init__()
        self.argv = argv or sys.argv
        self.single_instance_guard = SingleInstanceGuard()

        # Sprawdzenie ochrony przed wielokrotnym uruchomieniem
        if not self.single_instance_guard.acquire():
            logger.info("MyszkaHUD jest już uruchomiony w tle. Zamykanie drugiej instancji.")
            print("[MyszkaHUD] Aplikacja jest już aktywna w zasobniku systemowym.")
            self._is_duplicate = True
            return

        self._is_duplicate = False
        self.qt_app = QApplication.instance() or QApplication(self.argv)
        
        self.qt_app.setApplicationName("MyszkaHUD")
        self.qt_app.setApplicationDisplayName("MyszkaHUD")
        self.qt_app.setQuitOnLastWindowClosed(False)

        # 1. Usługi systemowe, konfiguracja i okna
        self.settings_service = SettingsService()
        self.autostart_service = AutostartService()
        self.window_manager = WindowManager()
        self.clipboard_guard = ClipboardFreshnessGuard(timeout_ms=350)
        self.clipboard_write_guard = ClipboardWriteGuard()
        self.text_executor = TextActionExecutor()
        
        # 2. Usługi AI (Gemini jako wspólne źródło prawdy)
        self.gemini_service = GeminiService()
        self.translation_service = TranslationService(ai_provider=self.gemini_service)
        self.gemini_ocr_provider = GeminiOCRProvider(vision_provider=self.gemini_service)
        self.ocr_service = OCRService(provider=self.gemini_ocr_provider)
        self.gemini_speech_provider = GeminiSpeechProvider(audio_provider=self.gemini_service)
        self.speech_service = SpeechService(provider=self.gemini_speech_provider)

        # 3. Moduły narzędziowe: Schowek, Procesy, RAM
        self.clipboard_service = ClipboardService()
        self.notes_service = NotesService()
        self.clipboard_monitor = ClipboardMonitor(
            service=self.clipboard_service,
            write_guard=self.clipboard_write_guard,
            window_manager=self.window_manager,
            parent=self,
        )
        self.process_service = ProcessService()
        self.ram_service = RamService()

        # 4. Inicjalizacja wszystkich okien interfejsu (PySide6)
        self.hud_window = RadialHUDWindow()
        self.text_actions_menu = TextActionsMenuWindow()
        self.translation_window = TranslationWindow(translation_service=self.translation_service)
        self.snipping_overlay = ScreenSnippingOverlay()
        self.ocr_result_window = OCRResultWindow(ocr_service=self.ocr_service)
        self.speech_overlay = SpeechRecordingOverlay()
        self.speech_result_window = SpeechResultWindow(speech_service=self.speech_service)
        self.clipboard_window = ClipboardWindow(
            clipboard_service=self.clipboard_service,
            notes_service=self.notes_service,
        )
        self.process_window = ProcessWindow(process_service=self.process_service)
        self.ram_window = RamWindow(ram_service=self.ram_service)
        self.settings_window = SettingsWindow(settings_service=self.settings_service)

        # 5. Menedżer zasobnika systemowego (Windows System Tray)
        self.tray_manager = TrayManager(autostart_service=self.autostart_service, parent=self)

        # Rejestracja uchwytów okien MyszkaHUD, by nie traktować ich jako aplikacji docelowej
        try:
            self.window_manager.set_app_hwnd(int(self.hud_window.winId()))
        except Exception:
            pass

        # 6. Połączenie sygnałów głównego HUD i Menu
        self.hud_window.action_selected.connect(self._on_hud_action_selected)
        self.text_actions_menu.action_triggered.connect(self._on_text_action_triggered)

        # Połączenie sygnałów okna schowka & notatek
        self.clipboard_window.copy_requested.connect(self._on_text_copy_requested)
        self.clipboard_window.paste_requested.connect(self._on_text_paste_requested)
        self.clipboard_window.paste_enter_requested.connect(self._on_text_paste_enter_requested)

        # Połączenie sygnałów okna tłumacza
        self.translation_window.copy_requested.connect(self._on_text_copy_requested)
        self.translation_window.paste_requested.connect(self._on_text_paste_requested)
        self.translation_window.paste_enter_requested.connect(self._on_text_paste_enter_requested)

        # Połączenie sygnałów nakładki OCR i okna wyników OCR
        self.snipping_overlay.image_captured.connect(self._on_ocr_image_captured)
        self.snipping_overlay.cancelled.connect(self._on_ocr_snipping_cancelled)
        self.ocr_result_window.copy_requested.connect(self._on_text_copy_requested)
        self.ocr_result_window.paste_requested.connect(self._on_text_paste_requested)
        self.ocr_result_window.paste_enter_requested.connect(self._on_text_paste_enter_requested)
        self.ocr_result_window.translate_requested.connect(self._on_ocr_translate_requested)

        # Połączenie sygnałów nakładki głosu i okna wyników mowy
        self.speech_overlay.recording_finished.connect(self._on_speech_recording_finished)
        self.speech_overlay.cancelled.connect(self._on_speech_recording_cancelled)
        self.speech_result_window.copy_requested.connect(self._on_text_copy_requested)
        self.speech_result_window.paste_requested.connect(self._on_text_paste_requested)
        self.speech_result_window.paste_enter_requested.connect(self._on_text_paste_enter_requested)
        self.speech_result_window.translate_requested.connect(self._on_speech_translate_requested)
        self.speech_result_window.retry_recording_requested.connect(self._handle_speech_action)

        # Połączenie sygnałów zasobnika systemowego Tray
        self.tray_manager.open_hud_requested.connect(self._on_hotkey_triggered)
        self.tray_manager.open_clipboard_requested.connect(self._open_clipboard)
        self.tray_manager.open_processes_requested.connect(self._open_processes)
        self.tray_manager.open_ram_requested.connect(self._open_ram)
        self.tray_manager.open_settings_requested.connect(self._open_settings)
        self.tray_manager.exit_requested.connect(self.shutdown)

        # Uruchomienie monitora schowka
        self.clipboard_monitor.start_monitoring()

        # Inicjalizacja globalnego nasłuchiwania skrótu Alt + Q
        self.hotkey_listener = WindowsHotkeyListener(key_code=ord('Q'), hotkey_id=1)
        self.hotkey_listener.triggered.connect(self._on_hotkey_triggered)

    def _hide_all_overlays(self):
        """Ukrywa wszystkie aktywne okna nakładkowe."""
        for win in (
            self.text_actions_menu,
            self.translation_window,
            self.snipping_overlay,
            self.ocr_result_window,
            self.speech_overlay,
            self.speech_result_window,
            self.clipboard_window,
            self.process_window,
            self.ram_window,
            self.settings_window,
        ):
            if hasattr(win, "isVisible") and win.isVisible():
                win.hide()

    def _on_hotkey_triggered(self):
        """Obsługa wyzwolenia globalnego skrótu Alt + Q."""
        self.window_manager.capture_foreground_window()
        self._hide_all_overlays()
        self.hud_window.show_at_cursor()

    def _open_clipboard(self):
        self.window_manager.capture_foreground_window()
        self._hide_all_overlays()
        self.hud_window.hide()
        self.clipboard_window._set_category("all")
        self.clipboard_window.show_at_cursor()

    def _open_processes(self):
        self.window_manager.capture_foreground_window()
        self._hide_all_overlays()
        self.hud_window.hide()
        self.process_window.show()

    def _open_ram(self):
        self.window_manager.capture_foreground_window()
        self._hide_all_overlays()
        self.hud_window.hide()
        self.ram_window.show()

    def _open_settings(self):
        self.window_manager.capture_foreground_window()
        self._hide_all_overlays()
        self.hud_window.hide()
        self.settings_window.show()

    def _on_hud_action_selected(self, item_id: str):
        """Obsługa wyboru kafelka z głównego radialnego HUD."""
        if item_id == "actions":
            self.text_actions_menu.show_at_cursor()
        elif item_id == "translate":
            self._handle_translate_action()
        elif item_id == "ocr":
            self._handle_ocr_action()
        elif item_id == "speech":
            self._handle_speech_action()
        elif item_id == "clipboard":
            self._open_clipboard()
        elif item_id == "notes":
            self.window_manager.capture_foreground_window()
            self._hide_all_overlays()
            self.hud_window.hide()
            self.clipboard_window._set_category("notes")
            self.clipboard_window.show_at_cursor()
        elif item_id == "processes":
            self._open_processes()
        elif item_id == "ram":
            self._open_ram()
        elif item_id == "settings":
            self._open_settings()
        else:
            logger.info(f"Wybrano moduł: {item_id}")

    def _handle_speech_action(self):
        self.hud_window.hide()
        if hasattr(self.speech_result_window, "isVisible") and self.speech_result_window.isVisible():
            self.speech_result_window.hide()
        self.speech_overlay.start_recording()

    def _on_speech_recording_finished(self, audio_bytes: bytes):
        if not audio_bytes or len(audio_bytes) == 0:
            logger.warning("Brak danych z nagrania głosu.")
            return

        self.speech_result_window.show_at_cursor()
        self.speech_result_window.start_transcription(
            audio_bytes=audio_bytes,
            mime_type="audio/wav",
            language_tag=self.settings_service.current.speech.language or "pl-PL",
        )

    def _on_speech_recording_cancelled(self):
        if self.window_manager.is_window_valid():
            self.window_manager.restore_focus(delay_ms=20)

    def _on_speech_translate_requested(self, text: str):
        self.speech_result_window.hide()
        self.translation_window.show_at_cursor()
        self.translation_window.set_source_text(text, auto_translate=True)

    def _handle_ocr_action(self):
        self.hud_window.hide()
        self.snipping_overlay.start_capture()

    def _on_ocr_image_captured(self, image_bytes: bytes):
        self.ocr_result_window.show_at_cursor()
        self.ocr_result_window.start_ocr(image_bytes=image_bytes)

    def _on_ocr_snipping_cancelled(self):
        if self.window_manager.is_window_valid():
            self.window_manager.restore_focus(delay_ms=20)

    def _on_ocr_translate_requested(self, text: str):
        self.ocr_result_window.hide()
        self.translation_window.show_at_cursor()
        self.translation_window.set_source_text(text, auto_translate=True)

    def _handle_translate_action(self):
        self.hud_window.hide()
        captured_text = ""

        if self.window_manager.is_window_valid():
            initial_seq = self.clipboard_guard.get_sequence_number()
            if self.window_manager.restore_focus(delay_ms=40):
                self.text_executor.execute_action(TextAction.COPY)
                changed = self.clipboard_guard.wait_for_clipboard_change(initial_seq)
                if changed:
                    clipboard = QGuiApplication.clipboard()
                    if clipboard:
                        captured_text = clipboard.text()

        self.translation_window.show_at_cursor()
        self.translation_window.set_source_text(captured_text, auto_translate=bool(captured_text.strip()))

    def _on_text_action_triggered(self, action: TextAction):
        self.hud_window.hide()
        self.text_actions_menu.hide()

        if not self.window_manager.is_window_valid():
            logger.warning("Brak poprawnego okna docelowego do wykonania akcji.")
            return

        restored = self.window_manager.restore_focus(delay_ms=45)
        if not restored:
            logger.error("Nie udało się przywrócić fokusu do okna docelowego.")
            return

        self.text_executor.execute_action(action)

    def _on_text_copy_requested(self, text: str):
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            with self.clipboard_write_guard.suppress(text):
                clipboard.setText(text)

    def _on_text_paste_requested(self, text: str):
        self._on_text_copy_requested(text)
        if self.window_manager.is_window_valid():
            self.window_manager.restore_focus(delay_ms=45)
            self.text_executor.execute_action(TextAction.PASTE)

    def _on_text_paste_enter_requested(self, text: str):
        self._on_text_copy_requested(text)
        if self.window_manager.is_window_valid():
            self.window_manager.restore_focus(delay_ms=45)
            self.text_executor.execute_action(TextAction.PASTE_ENTER)

    def run(self) -> int:
        """Uruchomienie pętli głównej aplikacji."""
        if getattr(self, "_is_duplicate", False):
            return 0

        print("[MyszkaHUD] Uruchomiono MyszkaHUD v0.12 (Stabilność, Single Instance, Bezpieczne Logowanie)")
        print("[MyszkaHUD] Skrót aktywacji: Alt + Q | Schowek: Alt + V")
        
        self.tray_manager.show()
        self.hotkey_listener.start()
        signal.signal(signal.SIGINT, lambda *args: self.shutdown())

        exit_code = self.qt_app.exec()
        self.cleanup()
        return exit_code

    def shutdown(self):
        """Zadanie bezpiecznego zamknięcia aplikacji."""
        print("\n[MyszkaHUD] Zamykanie aplikacji...")
        if hasattr(self, "qt_app"):
            self.qt_app.quit()

    def cleanup(self):
        """Zwalnianie zasobów i blokad."""
        if hasattr(self, 'tray_manager'):
            self.tray_manager.hide()
        if hasattr(self, 'hotkey_listener') and hasattr(self.hotkey_listener, 'isRunning') and self.hotkey_listener.isRunning():
            self.hotkey_listener.stop()
        if hasattr(self, 'clipboard_monitor'):
            self.clipboard_monitor.stop_monitoring()
        if hasattr(self, 'translation_window'):
            self.translation_window._cancel_current_worker()
        if hasattr(self, 'ocr_result_window'):
            self.ocr_result_window._cancel_current_worker()
        if hasattr(self, 'speech_result_window'):
            self.speech_result_window._cancel_current_worker()
        if hasattr(self, 'speech_overlay') and hasattr(self.speech_overlay, 'recorder'):
            if self.speech_overlay.recorder.is_recording():
                self.speech_overlay.recorder.stop_recording()
        if hasattr(self, 'single_instance_guard'):
            self.single_instance_guard.release()


def main():
    app = MyszkaHUDApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
