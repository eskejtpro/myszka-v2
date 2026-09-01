"""Zestaw testów jednostkowych dla Centrum Ustawień (MyszkaHUD v0.9)."""

import os
import tempfile
import unittest
from myszkahud.services.settings.models import (
    AppSettings,
    HotkeySettings,
    HudSettings,
    AppearanceSettings,
    SpeechSettings,
    OcrSettings,
    ClipboardSettings,
    SystemSettings,
    RamSettings,
)
from myszkahud.services.settings.settings_service import SettingsService
from myszkahud.ui.settings.settings_window import SettingsWindow


class TestSettingsModels(unittest.TestCase):
    """Testy modeli i serializacji ustawień."""

    def test_default_values(self):
        s = AppSettings()
        self.assertEqual(s.hotkeys.hud_hotkey, "Alt+Q")
        self.assertEqual(s.hotkeys.clipboard_hotkey, "Alt+V")
        self.assertEqual(s.speech.language, "pl-PL")
        self.assertEqual(s.clipboard.history_limit, 200)
        self.assertTrue(s.system.protect_critical_processes)

    def test_serialization_roundtrip(self):
        s = AppSettings()
        s.speech.language = "en-US"
        s.clipboard.history_limit = 500
        d = s.to_dict()

        restored = AppSettings.from_dict(d)
        self.assertEqual(restored.speech.language, "en-US")
        self.assertEqual(restored.clipboard.history_limit, 500)


class TestSettingsService(unittest.TestCase):
    """Testy odczytu, zapisu i odporności na błędy serwisu ustawień."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.settings_path = os.path.join(self.test_dir, "settings.json")
        self.service = SettingsService(custom_path=self.settings_path)

    def tearDown(self):
        if os.path.exists(self.settings_path):
            os.remove(self.settings_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_save_and_load_persistence(self):
        s = self.service.current
        s.hotkeys.hud_hotkey = "Ctrl+Space"
        s.appearance.theme = "Dark Navy Pro"
        self.service.save_settings(s)

        # Nowa instancja powinna wczytać zapisany stan
        new_svc = SettingsService(custom_path=self.settings_path)
        self.assertEqual(new_svc.current.hotkeys.hud_hotkey, "Ctrl+Space")
        self.assertEqual(new_svc.current.appearance.theme, "Dark Navy Pro")

    def test_corrupt_file_recovery(self):
        """Uszkodzony plik JSON powinien zostać obsłużony z powrotem do wartości domyślnych bez błędu."""
        with open(self.settings_path, "w", encoding="utf-8") as f:
            f.write("CORRUPT_JSON_DATA{{}}")

        s = self.service.load_settings()
        self.assertIsNotNone(s)
        self.assertEqual(s.hotkeys.hud_hotkey, "Alt+Q")

    def test_reset_to_defaults(self):
        s = self.service.current
        s.hotkeys.hud_hotkey = "Ctrl+Shift+K"
        self.service.save_settings(s)

        reset_s = self.service.reset_to_defaults()
        self.assertEqual(reset_s.hotkeys.hud_hotkey, "Alt+Q")


class TestSettingsUI(unittest.TestCase):
    """Testy okna graficznego SettingsWindow."""

    def test_window_creation(self):
        test_dir = tempfile.mkdtemp()
        settings_path = os.path.join(test_dir, "settings.json")
        svc = SettingsService(custom_path=settings_path)
        win = SettingsWindow(settings_service=svc)
        self.assertIsNotNone(win)
        win._handle_save()
        if os.path.exists(settings_path):
            os.remove(settings_path)
        if os.path.exists(test_dir):
            os.rmdir(test_dir)


if __name__ == "__main__":
    unittest.main()
