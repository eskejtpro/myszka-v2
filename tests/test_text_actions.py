"""Testy jednostkowe modułu operacji tekstowych i zarządzania oknami (MyszkaHUD 0.2)."""

import unittest
from myszkahud.core.text_actions import (
    TextAction,
    build_action_sequence,
    VK_CONTROL,
    VK_SHIFT,
    VK_RETURN,
    VK_A,
    VK_C,
    VK_V,
    VK_X,
    VK_Y,
    VK_Z,
    TextActionExecutor
)
from myszkahud.core.windows import WindowManager


class TestTextActionSequences(unittest.TestCase):
    """Weryfikacja symetrii i poprawności kodów klawiszy w generowanych sekwencjach."""

    def test_copy_sequence(self):
        seq = build_action_sequence(TextAction.COPY)
        expected = [
            (VK_CONTROL, False),
            (VK_C, False),
            (VK_C, True),
            (VK_CONTROL, True),
        ]
        self.assertEqual(seq, expected)

    def test_cut_sequence(self):
        seq = build_action_sequence(TextAction.CUT)
        expected = [
            (VK_CONTROL, False),
            (VK_X, False),
            (VK_X, True),
            (VK_CONTROL, True),
        ]
        self.assertEqual(seq, expected)

    def test_paste_sequence(self):
        seq = build_action_sequence(TextAction.PASTE)
        expected = [
            (VK_CONTROL, False),
            (VK_V, False),
            (VK_V, True),
            (VK_CONTROL, True),
        ]
        self.assertEqual(seq, expected)

    def test_paste_enter_sequence(self):
        seq = build_action_sequence(TextAction.PASTE_ENTER)
        expected = [
            (VK_CONTROL, False),
            (VK_V, False),
            (VK_V, True),
            (VK_CONTROL, True),
            (VK_RETURN, False),
            (VK_RETURN, True),
        ]
        self.assertEqual(seq, expected)

    def test_select_all_sequence(self):
        seq = build_action_sequence(TextAction.SELECT_ALL)
        expected = [
            (VK_CONTROL, False),
            (VK_A, False),
            (VK_A, True),
            (VK_CONTROL, True),
        ]
        self.assertEqual(seq, expected)

    def test_undo_sequence(self):
        seq = build_action_sequence(TextAction.UNDO)
        expected = [
            (VK_CONTROL, False),
            (VK_Z, False),
            (VK_Z, True),
            (VK_CONTROL, True),
        ]
        self.assertEqual(seq, expected)

    def test_redo_default_ctrl_y(self):
        seq = build_action_sequence(TextAction.REDO, redo_use_shift_z=False)
        expected = [
            (VK_CONTROL, False),
            (VK_Y, False),
            (VK_Y, True),
            (VK_CONTROL, True),
        ]
        self.assertEqual(seq, expected)

    def test_redo_ctrl_shift_z_variant(self):
        seq = build_action_sequence(TextAction.REDO, redo_use_shift_z=True)
        expected = [
            (VK_CONTROL, False),
            (VK_SHIFT, False),
            (VK_Z, False),
            (VK_Z, True),
            (VK_SHIFT, True),
            (VK_CONTROL, True),
        ]
        self.assertEqual(seq, expected)

    def test_key_balance_no_stuck_modifiers(self):
        """Wszystkie akcje muszą mieć równą liczbę zdarzeń key-down i key-up dla każdego klawisza."""
        for action in TextAction:
            for shift_variant in [False, True]:
                seq = build_action_sequence(action, redo_use_shift_z=shift_variant)
                key_counts = {}
                for vk, is_up in seq:
                    delta = -1 if is_up else 1
                    key_counts[vk] = key_counts.get(vk, 0) + delta
                
                # Każdy wciśnięty klawisz musi zostać zwolniony (bilans == 0)
                for vk, balance in key_counts.items():
                    self.assertEqual(balance, 0, f"Klawisz 0x{vk:02X} w akcji {action} ma niesymetryczny stan!")


class TestWindowManager(unittest.TestCase):
    """Testy stanu i logiki bezpieczeństwa WindowManager."""

    def test_initial_state_empty(self):
        wm = WindowManager()
        self.assertIsNone(wm.target_hwnd)
        self.assertFalse(wm.is_window_valid())
        self.assertFalse(wm.restore_focus())

    def test_clear_target_window(self):
        wm = WindowManager()
        wm._target_hwnd = 12345
        self.assertEqual(wm.target_hwnd, 12345)
        wm.clear()
        self.assertIsNone(wm.target_hwnd)

    def test_invalid_target_hwnd_refusal(self):
        wm = WindowManager()
        wm._target_hwnd = 0
        self.assertFalse(wm.is_window_valid())
        self.assertFalse(wm.restore_focus())


if __name__ == "__main__":
    unittest.main()
