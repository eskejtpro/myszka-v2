"""Główna klasa aplikacji MyszkaHUD."""

import sys
import time
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject
from PySide6.QtGui import QGuiApplication

from .ui.hud.radial_hud import RadialHUDWindow
from .ui.hud.text_actions_menu import TextActionsMenuWindow
from .ui.translation.translation_window import TranslationWindow
from .ui.ocr.snipping_overlay import ScreenSnippingOverlay
from .ui.ocr.ocr_window import OCRResultWindow
from .ui.speech.speech_overlay import SpeechRecordingOverlay
from .ui.speech.speech_result_window import SpeechResultWindow
from .core.hotkeys import WindowsHotkeyListener
from .core.windows import WindowManager, ClipboardFreshnessGuard
from .core.text_actions import TextActionExecutor, TextAction
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
from .ui.clipboard import ClipboardWindow


class MyszkaHUDApp(QObject):
    """Zarządca cyklu życia aplikacji MyszkaHUD."""

    def __init__(self, argv=None):
        super().__init__()
        self.argv = argv or sys.argv
        self.qt_app = QApplication.instance() or QApplication(self.argv)
        
        self.qt_app.setApplicationName("MyszkaHUD")
        self.qt_app.setApplicationDisplayName("MyszkaHUD")
        self.qt_app.setQuitOnLastWindowClosed(False)

        # Usługi systemowe i AI (Gemini jako wspólne źródło prawdy)
        self.window_manager = WindowManager()
        self.clipboard_guard = ClipboardFreshnessGuard(timeout_ms=350)
        self.clipboard_write_guard = ClipboardWriteGuard()
        self.text_executor = TextActionExecutor()
        
        self.gemini_service = GeminiService()
        self.translation_service = TranslationService(ai_provider=self.gemini_service)
        self.gemini_ocr_provider = GeminiOCRProvider(vision_provider=self.gemini_service)
        self.ocr_service = OCRService(provider=self.gemini_ocr_provider)
        self.gemini_speech_provider = GeminiSpeechProvider(audio_provider=self.gemini_service)
        self.speech_service = SpeechService(provider=self.gemini_speech_provider)

        # Moduł v0.6: Inteligentny Schowek & Podręczny Notes
        self.clipboard_service = ClipboardService()
        self.notes_service = NotesService()
        self.clipboard_monitor = ClipboardMonitor(
            service=self.clipboard_service,
            write_guard=self.clipboard_write_guard,
            window_manager=self.window_manager,
            parent=self,
        )

        # Inicjalizacja okien interfejsu
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

        # Rejestracja uchwytów okien MyszkaHUD, by nie traktować ich jako aplikacji docelowej
        self.window_manager.set_app_hwnd(int(self.hud_window.winId()))

        # Połączenie sygnałów głównego HUD
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

        # Uruchomienie monitora schowka
        self.clipboard_monitor.start_monitoring()

        # Inicjalizacja globalnego nasłuchiwania skrótu Alt + Q
        self.hotkey_listener = WindowsHotkeyListener(key_code=ord('Q'), hotkey_id=1)
        self.hotkey_listener.triggered.connect(self._on_hotkey_triggered)

    def _on_hotkey_triggered(self):
        """Obsługa wyzwolenia globalnego skrótu Alt + Q."""
        # 1. ZAWSZE przed pokazaniem HUD zapamiętujemy aktywne okno użytkownika
        captured_hwnd = self.window_manager.capture_foreground_window()
        
        # 2. Jeśli otwarte są podokna, chowamy je
        if self.text_actions_menu.isVisible():
            self.text_actions_menu.hide()
        if self.translation_window.isVisible():
            self.translation_window.hide()
        if self.snipping_overlay.isVisible():
            self.snipping_overlay.hide()
        if self.ocr_result_window.isVisible():
            self.ocr_result_window.hide()
        if self.speech_overlay.isVisible():
            self.speech_overlay.hide()
        if self.speech_result_window.isVisible():
            self.speech_result_window.hide()
        if self.clipboard_window.isVisible():
            self.clipboard_window.hide()

        # 3. Pokazujemy główny radialny HUD pod kursorem
        self.hud_window.show_at_cursor()

    def _on_hud_action_selected(self, item_id: str):
        """Obsługa wyboru kafelka z głównego radialnego HUD."""
        if item_id == "actions":
            # Otwórz podmenu akcji tekstowych dokładnie w miejscu kursora
            self.text_actions_menu.show_at_cursor()
        elif item_id == "translate":
            # Uruchom procedurę pobierania zaznaczonego tekstu i otwarcie tłumacza
            self._handle_translate_action()
        elif item_id == "ocr":
            # Uruchom tryb zaznaczania obszaru OCR
            self._handle_ocr_action()
        elif item_id == "speech":
            # Uruchom tryb nagrywania mowy (Speech-to-Text)
            self._handle_speech_action()
        elif item_id == "clipboard":
            # Otwórz panel schowka & notatek
            self.hud_window.hide()
            self.clipboard_window._set_category("all")
            self.clipboard_window.show_at_cursor()
        elif item_id == "notes":
            # Otwórz panel z filtrem na notatki
            self.hud_window.hide()
            self.clipboard_window._set_category("notes")
            self.clipboard_window.show_at_cursor()
        else:
            print(f"[MyszkaHUD] Wybrano moduł: {item_id} (oczekuje na swój etap roadmapy)")

    def _handle_speech_action(self):
        """
        Uruchamia procedurę dyktowania mowy (STT):
        1. Ukrycie HUD.
        2. Wyświetlenie nakładki nagrywania i rozpoczęcie rejestracji audio.
        """
        self.hud_window.hide()
        if self.speech_result_window.isVisible():
            self.speech_result_window.hide()

        self.speech_overlay.start_recording()

    def _on_speech_recording_finished(self, audio_bytes: bytes):
        """Obsługa zakończenia nagrania głosu – otwarcie okna wyników i uruchomienie SpeechWorker."""
        if not audio_bytes or len(audio_bytes) == 0:
            print("[MyszkaHUD] Brak danych z nagrania głosu.")
            return

        self.speech_result_window.show_at_cursor()
        self.speech_result_window.start_transcription(
            audio_bytes=audio_bytes,
            mime_type="audio/wav",
            language_tag="pl-PL"
        )

    def _on_speech_recording_cancelled(self):
        """Obsługa anulowania nagrywania głosu – przywrócenie fokusu do poprzedniego okna."""
        if self.window_manager.is_window_valid():
            self.window_manager.restore_focus(delay_ms=20)

    def _on_speech_translate_requested(self, text: str):
        """
        Płynne przekazanie tekstu z transkrypcji głosu do okna Tłumacza.
        Używa istniejącego TranslationService / TranslationWindow.
        """
        self.speech_result_window.hide()
        self.translation_window.show_at_cursor()
        self.translation_window.set_source_text(text, auto_translate=True)

    def _handle_ocr_action(self):
        """
        Uruchamia procedurę wycinania ekranu dla OCR:
        1. Ukrycie HUD.
        2. Uruchomienie nakładki na wirtualnym pulpicie.
        """
        self.hud_window.hide()
        self.snipping_overlay.start_capture()

    def _on_ocr_image_captured(self, image_bytes: bytes):
        """Obsługa przechwycenia wycinka ekranu – uruchamia okno wyników i OCRWorker."""
        self.ocr_result_window.show_at_cursor()
        self.ocr_result_window.start_ocr(image_bytes=image_bytes)

    def _on_ocr_snipping_cancelled(self):
        """Obsługa anulowania zrzutu ekranu – przywrócenie fokusu do poprzedniego okna."""
        if self.window_manager.is_window_valid():
            self.window_manager.restore_focus(delay_ms=20)

    def _on_ocr_translate_requested(self, text: str):
        """
        Płynne przekazanie tekstu z OCR do okna Tłumacza.
        Używa istniejącego TranslationService / TranslationWindow.
        """
        self.ocr_result_window.hide()
        self.translation_window.show_at_cursor()
        self.translation_window.set_source_text(text, auto_translate=True)

    def _handle_translate_action(self):

        """
        Pobiera zaznaczony tekst z aktywnego okna i otwiera panel tłumacza:
        1. Ukrycie HUD.
        2. Zapamiętanie numeru sekwencji schowka (ClipboardFreshnessGuard).
        3. Przywrócenie okna docelowego i wysłanie Ctrl+C.
        4. Oczekiwanie na zmianę numeru sekwencji schowka.
        5. Jeśli pojawił się nowy tekst -> używamy go. Jeśli nie -> otwieramy z pustym polem.
        """
        self.hud_window.hide()

        captured_text = ""

        if self.window_manager.is_window_valid():
            # Zapamiętujemy początkowy numer sekwencji schowka
            initial_seq = self.clipboard_guard.get_sequence_number()

            # Przywracamy fokus do aplikacji użytkownika
            if self.window_manager.restore_focus(delay_ms=40):
                # Wysyłamy Ctrl+C do aplikacji
                self.text_executor.execute_action(TextAction.COPY)

                # Czekamy na zarejestrowanie nowego schowka przez system (krótki polling z timeoutem 350ms)
                changed = self.clipboard_guard.wait_for_clipboard_change(initial_seq)
                if changed:
                    clipboard = QGuiApplication.clipboard()
                    if clipboard:
                        captured_text = clipboard.text()

        # Otwieramy okno tłumacza pod kursorem
        self.translation_window.show_at_cursor()
        self.translation_window.set_source_text(captured_text, auto_translate=bool(captured_text.strip()))

    def _on_text_action_triggered(self, action: TextAction):
        """Obsługa wykonania akcji tekstowej."""
        print(f"[MyszkaHUD] Wykonywanie akcji tekstowej: {action.value}")
        
        self.hud_window.hide()
        self.text_actions_menu.hide()

        if not self.window_manager.is_window_valid():
            print("[MyszkaHUD] OSTRZEŻENIE: Brak poprawnego okna docelowego do wykonania akcji.")
            return

        restored = self.window_manager.restore_focus(delay_ms=45)
        if not restored:
            print("[MyszkaHUD] BŁĄD: Nie udało się przywrócić fokusu do okna docelowego.")
            return

        success = self.text_executor.execute_action(action)
        if not success:
            print(f"[MyszkaHUD] BŁĄD: Niepowodzenie wysłania sekwencji dla akcji {action.value}")

    def _on_text_copy_requested(self, text: str):
        """Kopiuje tekst do schowka z zabezpieczeniem Self-Change Suppression."""
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            with self.clipboard_write_guard.suppress(text):
                clipboard.setText(text)
            print("[MyszkaHUD] Skopiowano tekst do schowka.")

    def _on_text_paste_requested(self, text: str):
        """Kopiuje tekst i wkleja go do poprzedniego aktywnego okna użytkownika."""
        self._on_text_copy_requested(text)
        if self.window_manager.is_window_valid():
            self.window_manager.restore_focus(delay_ms=45)
            self.text_executor.execute_action(TextAction.PASTE)

    def _on_text_paste_enter_requested(self, text: str):
        """Kopiuje tekst i wkleja go z Enterem do poprzedniego okna."""
        self._on_text_copy_requested(text)
        if self.window_manager.is_window_valid():
            self.window_manager.restore_focus(delay_ms=45)
            self.text_executor.execute_action(TextAction.PASTE_ENTER)

    def run(self) -> int:
        """Uruchomienie pętli głównej aplikacji."""
        print("[MyszkaHUD] Uruchomiono MyszkaHUD v0.6 (Smart Clipboard & Notes, STT pl-PL, Vision OCR, Translation)")
        print("[MyszkaHUD] Skrót aktywacji: Alt + Q")
        
        self.hotkey_listener.start()
        signal.signal(signal.SIGINT, lambda *args: self.shutdown())

        exit_code = self.qt_app.exec()
        self.cleanup()
        return exit_code

    def shutdown(self):
        """Zadanie zamknięcia aplikacji."""
        print("\n[MyszkaHUD] Zamykanie aplikacji...")
        self.qt_app.quit()

    def cleanup(self):
        """Zwalnianie zasobów."""
        if hasattr(self, 'hotkey_listener') and self.hotkey_listener.isRunning():
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



def main():
    app = MyszkaHUDApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
