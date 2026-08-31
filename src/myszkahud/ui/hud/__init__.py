"""HUD package for MyszkaHUD."""
from .hud_theme import HUDColorPalette, DEFAULT_HUD_THEME, HUD_MODULES_CONFIG
from .hud_status import ModuleStatus

try:
    from .radial_hud import RadialHUDWindow
    from .text_actions_menu import TextActionsMenuWindow
    from .hud_item import HUDItemButton
    from .center_card import CenterHUDCard
except ImportError:
    # Środowisko headless / testowe bez PySide6
    RadialHUDWindow = None  # type: ignore
    TextActionsMenuWindow = None  # type: ignore
    HUDItemButton = None  # type: ignore
    CenterHUDCard = None  # type: ignore

__all__ = [
    "RadialHUDWindow",
    "TextActionsMenuWindow",
    "HUDItemButton",
    "ModuleStatus",
    "CenterHUDCard",
    "HUDColorPalette",
    "DEFAULT_HUD_THEME",
    "HUD_MODULES_CONFIG",
]
