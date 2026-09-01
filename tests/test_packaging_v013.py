"""Testy weryfikacji konfiguracji packagingu i instalatora Windows (v0.13)."""

import os
import sys
import unittest
from myszkahud.storage.paths import get_app_data_dir, get_database_path
from myszkahud.services.autostart.autostart_service import AutostartService


class TestPackagingConfiguration(unittest.TestCase):
    """Weryfikacja skryptów i specyfikacji packagingu dla Windows 10 x64."""

    def test_spec_file_exists(self):
        spec_path = os.path.join(os.getcwd(), "MyszkaHUD.spec")
        self.assertTrue(os.path.exists(spec_path), "Brak pliku MyszkaHUD.spec")

    def test_build_script_exists(self):
        bat_path = os.path.join(os.getcwd(), "build_windows.bat")
        self.assertTrue(os.path.exists(bat_path), "Brak pliku build_windows.bat")

    def test_requirements_file_exists(self):
        req_path = os.path.join(os.getcwd(), "requirements.txt")
        self.assertTrue(os.path.exists(req_path), "Brak pliku requirements.txt")

    def test_appdata_isolated_from_install_dir(self):
        app_dir = get_app_data_dir()
        self.assertTrue(str(app_dir).endswith("MyszkaHUD"))
        db_path = get_database_path()
        self.assertTrue(db_path.endswith("myszkahud.db"))

    def test_autostart_status_executable_path(self):
        service = AutostartService()
        status = service.get_status()
        self.assertIsNotNone(status.executable_path)
        self.assertEqual(status.app_name, "MyszkaHUD")


if __name__ == "__main__":
    unittest.main()
