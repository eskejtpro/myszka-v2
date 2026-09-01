"""Zestaw testów jednostkowych dla modułu System Tray i Autostartu (MyszkaHUD v0.10)."""

import unittest
from myszkahud.services.autostart.models import AutostartStatus
from myszkahud.services.autostart.providers.mock_provider import MockAutostartProvider
from myszkahud.services.autostart.autostart_service import AutostartService
from myszkahud.ui.tray.tray_manager import TrayManager


class TestAutostartService(unittest.TestCase):
    """Testy logiki włączania, wyłączania i przełączania autostartu."""

    def setUp(self):
        self.mock_provider = MockAutostartProvider(initial_enabled=False)
        self.service = AutostartService(provider=self.mock_provider, app_name="MyszkaHUD")

    def test_enable_and_disable(self):
        self.assertFalse(self.service.is_autostart_enabled())

        # Włącz
        success = self.service.enable_autostart("C:\\MyszkaHUD.exe")
        self.assertTrue(success)
        self.assertTrue(self.service.is_autostart_enabled())

        # Wyłącz
        success = self.service.disable_autostart()
        self.assertTrue(success)
        self.assertFalse(self.service.is_autostart_enabled())

    def test_toggle(self):
        self.assertFalse(self.service.is_autostart_enabled())

        # Toggle 1 -> True
        res = self.service.toggle_autostart()
        self.assertTrue(res)
        self.assertTrue(self.service.is_autostart_enabled())

        # Toggle 2 -> False
        res = self.service.toggle_autostart()
        self.assertFalse(res)
        self.assertFalse(self.service.is_autostart_enabled())

    def test_get_status(self):
        status = self.service.get_status()
        self.assertIsInstance(status, AutostartStatus)
        self.assertEqual(status.app_name, "MyszkaHUD")


class TestTrayManager(unittest.TestCase):
    """Testy menedżera ikony zasobnika i menu kontekstowego."""

    def test_tray_initialization(self):
        mock_provider = MockAutostartProvider(initial_enabled=True)
        autostart_service = AutostartService(provider=mock_provider)
        tray = TrayManager(autostart_service=autostart_service)

        self.assertIsNotNone(tray)
        self.assertIsNotNone(tray.menu)
        self.assertEqual(len(tray.menu.actions), 7)

        # Sprawdź przełączanie autostartu z menu
        tray._toggle_autostart()
        self.assertFalse(autostart_service.is_autostart_enabled())


if __name__ == "__main__":
    unittest.main()
