"""Moduł geometrii ekranu i transformacji współrzędnych dla wielomonitorowości i DPI."""

from dataclasses import dataclass
from typing import Tuple, List, Optional


@dataclass(frozen=True)
class ScreenRect:
    """Reprezentuje prostokąt ekranu w logicznych pikselach Qt."""
    x: int
    y: int
    width: int
    height: int
    device_pixel_ratio: float = 1.0
    name: str = ""

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height


def normalize_selection_rect(
    start_x: int, start_y: int, end_x: int, end_y: int
) -> Tuple[int, int, int, int]:
    """
    Normalizuje dowolne dwa punkty przeciągania myszy do postaci (x, y, width, height),
    gdzie width >= 0 i height >= 0.
    
    Poprawnie obsługuje:
    - przeciąganie od prawej do lewej,
    - przeciąganie z dołu do góry,
    - współrzędne ujemne (monitory po lewej stronie głównego).
    """
    min_x = min(start_x, end_x)
    max_x = max(start_x, end_x)
    min_y = min(start_y, end_y)
    max_y = max(start_y, end_y)

    width = max_x - min_x
    height = max_y - min_y

    return (min_x, min_y, width, height)


def is_valid_selection(
    width: int, height: int, min_width: int = 5, min_height: int = 5
) -> bool:
    """
    Sprawdza, czy zaznaczony obszar ma wystarczający rozmiar dla operacji OCR.
    Odrzuca puste kliknięcia i mikroskopijne przesunięcia.
    """
    return width >= min_width and height >= min_height


def calculate_virtual_desktop_geometry(
    screens: List[ScreenRect]
) -> Tuple[int, int, int, int]:
    """
    Oblicza globalne granice wirtualnego pulpitu (bounding box wszystkich monitorów).
    Obsługuje monitory po lewej stronie (ujemny X) lub u góry (ujemny Y).
    """
    if not screens:
        return (0, 0, 1920, 1080)

    min_x = min(s.left for s in screens)
    min_y = min(s.top for s in screens)
    max_x = max(s.right for s in screens)
    max_y = max(s.bottom for s in screens)

    return (min_x, min_y, max_x - min_x, max_y - min_y)


def map_logical_to_screen_crop(
    crop_x: int,
    crop_y: int,
    crop_w: int,
    crop_h: int,
    screen_rect: ScreenRect
) -> Tuple[int, int, int, int]:
    """
    Przelicza współrzędne logiczne zaznaczenia leżącego na danym ekranie
    do współrzędnych lokalnych zrzutu ekranu z uwzględnieniem Device Pixel Ratio (DPI).
    
    DPI scaling w Qt:
    Piksele logiczne * device_pixel_ratio = piksele fizyczne obrazu.
    """
    # 1. Obliczenie współrzędnych relatywnych względem lewego górnego rogu monitora
    rel_x = crop_x - screen_rect.left
    rel_y = crop_y - screen_rect.top

    dpr = screen_rect.device_pixel_ratio

    # 2. Skalowanie do pikseli fizycznych
    phys_x = int(round(rel_x * dpr))
    phys_y = int(round(rel_y * dpr))
    phys_w = int(round(crop_w * dpr))
    phys_h = int(round(crop_h * dpr))

    return (phys_x, phys_y, phys_w, phys_h)
