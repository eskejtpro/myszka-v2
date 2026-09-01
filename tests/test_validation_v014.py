"""Zestaw testów automatycznych walidacji v0.14 dla Windows 10."""

import os
import tempfile
import unittest
from myszkahud.storage.paths import get_app_data_dir, get_database_path
from myszkahud.services.settings.settings_service import SettingsService
from myszkahud.services.autostart.autostart_service import AutostartService
from myszkahud.services.ram import RamService
from myszkahud.services.process import ProcessService
from myszkahud.services.clipboard import ClipboardService, NotesService
from myszkahud.core.single_instance import SingleInstanceGuard
from myszkahud.core.safe_logging import sanitize_text


class TestWindowsValidationSuite(unittest.TestCase):
    """Kompleksowa walidacja komponentów i integralności systemu."""

    def test_validation_script_exists(self):
        bat_path = os.path.join(os.getcwd(), "validate_windows.bat")
        self.assertTrue(os.path.exists(bat_path), "Brak pliku validate_windows.bat")

    def test_validation_doc_exists(self):
        doc_path = os.path.join(os.getcwd(), "WINDOWS_VALIDATION.md")
        self.assertTrue(os.path.exists(doc_path), "Brak pliku WINDOWS_VALIDATION.md")

    def test_settings_initialization_and_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings_path = os.path.join(tmpdir, "settings.json")
            settings_svc = SettingsService(custom_path=test_settings_path)
            cfg = settings_svc.current
            self.assertEqual(cfg.hud.opacity, 0.96)
            self.assertTrue(cfg.clipboard.enabled)
            self.assertEqual(cfg.clipboard.history_limit, 200)
            self.assertTrue(cfg.system.protect_critical_processes)

    def test_all_services_instantiation(self):
        ram_svc = RamService()
        proc_svc = ProcessService()
        autostart_svc = AutostartService()
        self.assertIsNotNone(ram_svc)
        self.assertIsNotNone(proc_svc)
        self.assertIsNotNone(autostart_svc)

    def test_safe_data_isolation(self):
        app_dir = get_app_data_dir()
        self.assertIn("MyszkaHUD", str(app_dir))
        db_path = get_database_path()
        self.assertIn("myszkahud.db", db_path)

    def test_single_instance_and_logging_guards(self):
        guard = SingleInstanceGuard(mutex_name="Local\\Test_Val_Mutex")
        self.assertTrue(guard.acquire())
        guard.release()
        
        redacted = sanitize_text("Secret: AIzaSyDUMMY1234567890ABCDEFabcdef12")
        self.assertNotIn("AIzaSyDUMMY", redacted)


if __name__ == "__main__":
    unittest.main()
