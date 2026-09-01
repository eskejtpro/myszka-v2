"""Zestaw testów jednostkowych dla modułu Monitora RAM i Bezpiecznego Zwalniania (MyszkaHUD v0.8)."""

import unittest
from myszkahud.services.process.models import ProcessInfo
from myszkahud.services.ram.models import RamStats, RamReleaseResult
from myszkahud.services.ram.providers.mock_provider import MockRamProvider
from myszkahud.services.ram.ram_service import RamService
from myszkahud.ui.ram.ram_window import RamWindow


class TestRamModels(unittest.TestCase):
    """Testy modeli danych RAM."""

    def test_ram_stats_gb_mb_calculations(self):
        stats = RamStats(
            total_bytes=16 * (1024 ** 3),
            used_bytes=8 * (1024 ** 3),
            available_bytes=8 * (1024 ** 3),
            percent=50.0,
        )
        self.assertEqual(stats.total_gb, 16.0)
        self.assertEqual(stats.used_gb, 8.0)
        self.assertEqual(stats.available_gb, 8.0)
        self.assertEqual(stats.percent, 50.0)

    def test_ram_release_result_calculations(self):
        res = RamReleaseResult(
            before_used_bytes=8 * (1024 ** 3),
            after_used_bytes=int(7.5 * (1024 ** 3)),
            released_bytes=int(0.5 * (1024 ** 3)),
            trimmed_processes_count=4,
        )
        self.assertEqual(res.released_mb, 512.0)
        self.assertEqual(res.trimmed_processes_count, 4)
        self.assertTrue(res.success)


class TestRamService(unittest.TestCase):
    """Testy logiki biznesowej serwisu RAM i bezpiecznego zwalniania."""

    def setUp(self):
        self.mock_provider = MockRamProvider(
            total_gb=16.0,
            used_gb=8.0,
            release_gain_mb=300.0,
            top_processes=[
                ProcessInfo(pid=1001, name="chrome.exe", ram_bytes=800 * 1024 * 1024),
                ProcessInfo(pid=1000, name="Code.exe", ram_bytes=450 * 1024 * 1024),
            ],
        )
        self.service = RamService(provider=self.mock_provider)

    def test_get_stats(self):
        stats = self.service.get_stats()
        self.assertEqual(stats.total_gb, 16.0)
        self.assertEqual(stats.used_gb, 8.0)
        self.assertEqual(len(stats.top_processes), 2)

    def test_safe_memory_release(self):
        """Bezpieczne zwalnianie pamięci poprawnie mierzy stan przed i po i oblicza realną różnicę."""
        res = self.service.release_memory_safe()
        self.assertEqual(self.mock_provider.trim_calls_count, 1)
        self.assertEqual(res.released_mb, 300.0)
        self.assertEqual(res.before_used_mb, 8192.0)
        self.assertEqual(res.after_used_mb, 7892.0)
        self.assertIn("Zwolniono bezpiecznie 300.0 MB", res.details)


class TestRamUI(unittest.TestCase):
    """Testy inicjalizacji okna RamWindow."""

    def test_window_creation(self):
        mock_provider = MockRamProvider()
        service = RamService(provider=mock_provider)
        win = RamWindow(ram_service=service)
        self.assertIsNotNone(win)
        win.refresh_stats()
        self.assertIsNotNone(win.service)


if __name__ == "__main__":
    unittest.main()
