"""Testy logiki pozycjonowania, geometrii i konfiguracji modułów MyszkaHUD."""

import math
import unittest
from myszkahud.ui.hud.hud_theme import (
    HUDColorPalette,
    DEFAULT_HUD_THEME,
    HUD_MODULES_CONFIG
)
from myszkahud.ui.hud.hud_status import ModuleStatus


def calculate_clamped_position(cursor_x: int, cursor_y: int, win_w: int, win_h: int,
                               screen_left: int, screen_top: int, screen_right: int, screen_bottom: int):
    """Czysta funkcja obliczania pozycji HUD w obrębie ekranu."""
    target_x = cursor_x - win_w // 2
    target_y = cursor_y - win_h // 2
    
    min_x = screen_left
    max_x = screen_right - win_w + 1
    min_y = screen_top
    max_y = screen_bottom - win_h + 1
    
    clamped_x = max(min_x, min(target_x, max_x))
    clamped_y = max(min_y, min(target_y, max_y))
    return clamped_x, clamped_y


class TestHUDGeometry(unittest.TestCase):
    def test_center_screen_position(self):
        """Kursor na środku ekranu 1920x1080 -> okno 430x430 wycentrowane pod kursorem."""
        cx, cy = calculate_clamped_position(960, 540, 430, 430, 0, 0, 1919, 1079)
        self.assertEqual(cx, 960 - 215)
        self.assertEqual(cy, 540 - 215)

    def test_top_left_corner_clamping(self):
        """Kursor w lewym górnym rogu (0, 0) nie powinien powodować wyjścia okna za ekran."""
        cx, cy = calculate_clamped_position(0, 0, 430, 430, 0, 0, 1919, 1079)
        self.assertEqual(cx, 0)
        self.assertEqual(cy, 0)

    def test_bottom_right_corner_clamping(self):
        """Kursor w prawym dolnym rogu (1919, 1079) nie powinien ucinać okna."""
        cx, cy = calculate_clamped_position(1919, 1079, 430, 430, 0, 0, 1919, 1079)
        self.assertEqual(cx, 1920 - 430)
        self.assertEqual(cy, 1080 - 430)

    def test_radial_item_angles(self):
        """Weryfikacja 6 pozycji radialnych (co 60 stopni) w konfiguracji HUD."""
        angles = [m["angle_deg"] for m in HUD_MODULES_CONFIG]
        self.assertEqual(len(angles), 6)
        expected_angles = [270, 330, 30, 90, 150, 210]
        self.assertEqual(angles, expected_angles)
        
        # Różnica kątowa między sąsiednimi elementami wynosi 60 stopni
        for i in range(len(angles)):
            diff = (angles[(i + 1) % 6] - angles[i]) % 360
            self.assertEqual(diff, 60)

    def test_hud_modules_unique_ids(self):
        """Wszystkie moduły muszą mieć unikalne identyfikatory."""
        ids = [m["id"] for m in HUD_MODULES_CONFIG]
        self.assertEqual(len(ids), len(set(ids)))
        expected_ids = {"speech", "translate", "ocr", "clipboard", "notes", "actions"}
        self.assertEqual(set(ids), expected_ids)

    def test_hud_modules_structure_and_status(self):
        """Weryfikacja poprawności pól każdego z 6 modułów HUD."""
        for mod in HUD_MODULES_CONFIG:
            self.assertIn("id", mod)
            self.assertIn("title", mod)
            self.assertIn("icon", mod)
            self.assertIn("subtitle", mod)
            self.assertIn("angle_deg", mod)
            self.assertIn("accent_color", mod)
            self.assertIn("status", mod)
            # Sprawdzenie czy status mapuje się na enum ModuleStatus
            self.assertIn(mod["status"], [s.value for s in ModuleStatus])

    def test_theme_palette_integrity(self):
        """Weryfikacja kompletności palety barw HUD."""
        palette = DEFAULT_HUD_THEME
        self.assertTrue(palette.bg_base_rgba.startswith("rgba"))
        self.assertTrue(palette.bg_card_rgba.startswith("rgba"))
        self.assertTrue(palette.border_default.startswith("rgba") or palette.border_default.startswith("#"))
        self.assertTrue(palette.accent_ai.startswith("#"))
        self.assertTrue(palette.status_ready.startswith("#"))


if __name__ == "__main__":
    unittest.main()
