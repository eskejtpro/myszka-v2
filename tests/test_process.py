"""Zestaw testów jednostkowych dla modułu Zarządzania Procesami (MyszkaHUD v0.7)."""

import os
import unittest
from myszkahud.services.process.models import ProcessInfo, CRITICAL_SYSTEM_PROCESSES
from myszkahud.services.process.providers.mock_provider import MockProcessProvider
from myszkahud.services.process.process_service import ProcessService
from myszkahud.ui.process.process_item_card import ProcessItemCard
from myszkahud.ui.process.process_window import ProcessWindow


class TestProcessModels(unittest.TestCase):
    """Testy modeli danych procesów."""

    def test_ram_mb_calculation(self):
        p = ProcessInfo(pid=123, name="test.exe", ram_bytes=104857600)  # 100 MB
        self.assertEqual(p.ram_mb, 100.0)

    def test_display_name_prefers_window_title(self):
        p_with_title = ProcessInfo(pid=1, name="Code.exe", window_title="App.tsx - Code")
        self.assertEqual(p_with_title.display_name, "App.tsx - Code")

        p_no_title = ProcessInfo(pid=2, name="cmd.exe", window_title="")
        self.assertEqual(p_no_title.display_name, "cmd.exe")


class TestProcessServiceAndSecurity(unittest.TestCase):
    """Testy logiki biznesowej i zabezpieczeń procesów krytycznych."""

    def setUp(self):
        self.mock_provider = MockProcessProvider()
        self.service = ProcessService(provider=self.mock_provider)

    def test_list_and_sorting(self):
        # Sort by RAM
        procs = self.service.list_processes(sort_by="ram", reverse=True)
        self.assertGreater(len(procs), 0)
        self.assertEqual(procs[0].name, "chrome.exe")  # Highest RAM in mock

        # Search filter
        filtered = self.service.list_processes(search_query="chrome")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "chrome.exe")

    def test_critical_processes_are_protected(self):
        """Krytyczne procesy systemowe i sam MyszkaHUD są chronione przed zamknięciem i ubiciem."""
        # System PID 4
        self.assertTrue(self.service.is_protected(4, "System"))
        # explorer.exe
        self.assertTrue(self.service.is_protected(100, "explorer.exe"))
        # csrss.exe
        self.assertTrue(self.service.is_protected(999, "csrss.exe"))

        # Próba zamknięcia procesu chronionego
        result_close = self.service.close_process(4)
        self.assertFalse(result_close)
        self.assertNotIn(4, self.mock_provider.closed_pids)

        # Próba ubicia procesu chronionego
        result_kill = self.service.force_kill_process(4)
        self.assertFalse(result_kill)
        self.assertNotIn(4, self.mock_provider.killed_pids)

    def test_user_process_close_and_kill(self):
        """Zwykłe procesy użytkownika mogą być bezpiecznie zamykane lub ubijane."""
        # Zamknięcie Code.exe (PID 1000)
        self.assertTrue(self.service.close_process(1000))
        self.assertIn(1000, self.mock_provider.closed_pids)

        # Ubicie chrome.exe (PID 1001)
        self.assertTrue(self.service.force_kill_process(1001))
        self.assertIn(1001, self.mock_provider.killed_pids)

    def test_window_actions(self):
        """Aktywacja i minimalizacja okna."""
        self.assertTrue(self.service.activate_window(1000))
        self.assertIn(1000, self.mock_provider.activated_pids)

        self.assertTrue(self.service.minimize_window(1000))
        self.assertIn(1000, self.mock_provider.minimized_pids)


class TestProcessUIComponents(unittest.TestCase):
    """Testy inicjalizacji widoków PySide6."""

    def setUp(self):
        self.mock_provider = MockProcessProvider()
        self.service = ProcessService(provider=self.mock_provider)

    def test_card_and_window_creation(self):
        proc = ProcessInfo(pid=1000, name="Code.exe", window_title="Visual Studio Code", ram_bytes=50000000)
        card = ProcessItemCard(proc)
        self.assertIsNotNone(card)

        win = ProcessWindow(process_service=self.service)
        self.assertIsNotNone(win)
        win.refresh_list()
        self.assertIsNotNone(win.service)


if __name__ == "__main__":
    unittest.main()
