"""Modele danych dla Centrum Ustawień (Settings Center v1.0.0)."""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional


@dataclass
class HotkeySettings:
    hud_hotkey: str = "Alt+Q"
    clipboard_hotkey: str = "Alt+V"
    ocr_hotkey: str = "Alt+S"
    speech_hotkey: str = "Alt+R"


@dataclass
class HudSettings:
    size_diameter: int = 520
    opacity: float = 0.96
    animations_enabled: bool = True
    auto_close_on_action: bool = True


@dataclass
class AppearanceSettings:
    theme: str = "Dark Navy"
    accent_color: str = "#38BDF8"  # Sky Blue
    compact_mode: bool = False


@dataclass
class SpeechSettings:
    language: str = "pl-PL"
    max_recording_seconds: int = 60
    preferred_provider: str = "gemini"
    auto_paste_result: bool = True


@dataclass
class OcrSettings:
    preferred_provider: str = "gemini_vision"
    auto_copy_result: bool = True


@dataclass
class ClipboardSettings:
    enabled: bool = True
    history_limit: int = 200
    max_entry_length: int = 100000
    is_paused: bool = False


@dataclass
class SystemSettings:
    autostart_with_windows: bool = False
    minimize_to_tray: bool = True
    protect_critical_processes: bool = True


@dataclass
class RamSettings:
    refresh_interval_ms: int = 2000
    top_processes_count: int = 5


@dataclass
class AppSettings:
    """Główna konfiguracja aplikacji MyszkaHUD."""

    schema_version: int = 1
    hotkeys: HotkeySettings = field(default_factory=HotkeySettings)
    hud: HudSettings = field(default_factory=HudSettings)
    appearance: AppearanceSettings = field(default_factory=AppearanceSettings)
    speech: SpeechSettings = field(default_factory=SpeechSettings)
    ocr: OcrSettings = field(default_factory=OcrSettings)
    clipboard: ClipboardSettings = field(default_factory=ClipboardSettings)
    system: SystemSettings = field(default_factory=SystemSettings)
    ram: RamSettings = field(default_factory=RamSettings)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        if not isinstance(data, dict):
            return cls()

        def extract_sub(sub_cls, key):
            val = data.get(key, {})
            if isinstance(val, dict):
                # Filtruj tylko znane pola
                known_fields = sub_cls.__dataclass_fields__.keys()
                filtered = {k: v for k, v in val.items() if k in known_fields}
                return sub_cls(**filtered)
            return sub_cls()

        return cls(
            schema_version=data.get("schema_version", 1),
            hotkeys=extract_sub(HotkeySettings, "hotkeys"),
            hud=extract_sub(HudSettings, "hud"),
            appearance=extract_sub(AppearanceSettings, "appearance"),
            speech=extract_sub(SpeechSettings, "speech"),
            ocr=extract_sub(OcrSettings, "ocr"),
            clipboard=extract_sub(ClipboardSettings, "clipboard"),
            system=extract_sub(SystemSettings, "system"),
            ram=extract_sub(RamSettings, "ram"),
        )
