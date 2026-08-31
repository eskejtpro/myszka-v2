"""Definicje motywu, kolorów i stylów wizualnych dla MyszkaHUD.

Centralne miejsce zarządzania paletą barw (Dark Navy / HUD / AI Overlay),
obramowaniami, zaokrągleniami, typografią i kolorami akcentów modułów.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class HUDColorPalette:
    # Główne tła
    bg_base_rgba: str = "rgba(10, 15, 29, 0.94)"       # Głęboki granat / dark navy
    bg_card_rgba: str = "rgba(15, 23, 42, 0.96)"       # Karta kafelka
    bg_card_hover_rgba: str = "rgba(30, 41, 59, 0.98)" # Karta hover
    bg_card_pressed_rgba: str = "rgba(15, 23, 42, 1.0)" # Karta wciśnięta
    bg_center_rgba: str = "rgba(13, 20, 36, 0.95)"     # Karta centralna
    
    # Obramowania
    border_default: str = "rgba(51, 65, 85, 0.65)"     # Cienkie niebiesko-szare obramowanie
    border_hover: str = "#38BDF8"                      # Domyślny hover border
    border_center: str = "#2563EB"                     # Obramowanie centrum
    
    # Kolory funkcyjne i akcenty modułów
    accent_primary: str = "#38BDF8"                    # Błękitny / niebieski główny
    accent_ai: str = "#2DD4BF"                         # Cyan / Teal dla funkcji AI (Tłumacz / Asystent)
    accent_vision: str = "#38BDF8"                     # Błękitny dla OCR / Vision
    accent_speech: str = "#0284C7"                     # Głęboki błękit dla mikrofonu
    accent_tools: str = "#F59E0B"                      # Bursztynowy / pomarańczowy dla narzędzi (Notatki / Akcje)
    accent_actions: str = "#818CF8"                    # Indygo dla akcji systemowych
    
    # Statusy modułów
    status_ready: str = "#10B981"                      # Zielony (GOTOWY / READY)
    status_working: str = "#38BDF8"                    # Błękitny pulsujący (WORKING)
    status_disabled: str = "#64748B"                   # Szary (DISABLED)
    status_error: str = "#EF4444"                      # Czerwony (ERROR)
    
    # Typografia
    text_primary: str = "#F8FAFC"                      # Jasny główny tekst
    text_secondary: str = "#94A3B8"                    # Szary pomocniczy podtytuł
    text_muted: str = "#64748B"                        # Przygaszony tekst statusu / skrótu
    
    # Linie pomocnicze i glow
    ring_line_rgba: str = "rgba(56, 189, 248, 0.25)"   # Subtelny okrąg radialny
    spoke_line_rgba: str = "rgba(51, 65, 85, 0.40)"    # Linie łączące środek z kafelkami
    center_glow_rgba: str = "rgba(37, 99, 235, 100)"   # Subtelny glow centrum
    cursor_reticle_rgba: str = "rgba(56, 189, 248, 0.5)" # Celownik pozycji kursora
    
    # Geometria
    border_radius_tile: int = 12
    border_radius_center: int = 14


# Globalna instancja domyślnego motywu
DEFAULT_HUD_THEME = HUDColorPalette()


# Konfiguracja 6 modułów radialnego HUD (kąty, ikony, akcenty, podtytuły)
# Kąty w układzie ekranowym: 270° = Góra, 330° = Prawa-Góra, 30° = Prawa-Dół, 
# 90° = Dół, 150° = Lewa-Dół, 210° = Lewa-Góra
HUD_MODULES_CONFIG = [
    {
        "id": "speech",
        "title": "MIKROFON",
        "icon": "🎙",
        "subtitle": "Mowa → Tekst",
        "angle_deg": 270,
        "accent_color": "#0284C7",
        "status": "READY",
    },
    {
        "id": "translate",
        "title": "TŁUMACZ",
        "icon": "🌐",
        "subtitle": "AI Translation",
        "angle_deg": 330,
        "accent_color": "#2DD4BF",
        "status": "READY",
    },
    {
        "id": "ocr",
        "title": "OCR",
        "icon": "👁",
        "subtitle": "Tekst z ekranu",
        "angle_deg": 30,
        "accent_color": "#38BDF8",
        "status": "READY",
    },
    {
        "id": "clipboard",
        "title": "SCHOWEK",
        "icon": "📋",
        "subtitle": "Historia",
        "angle_deg": 90,
        "accent_color": "#10B981",
        "status": "READY",
    },
    {
        "id": "notes",
        "title": "NOTATKI",
        "icon": "📝",
        "subtitle": "Szybkie notatki",
        "angle_deg": 150,
        "accent_color": "#F59E0B",
        "status": "READY",
    },
    {
        "id": "actions",
        "title": "AKCJE",
        "icon": "⚡",
        "subtitle": "Tekst / Windows",
        "angle_deg": 210,
        "accent_color": "#818CF8",
        "status": "READY",
    },
]
