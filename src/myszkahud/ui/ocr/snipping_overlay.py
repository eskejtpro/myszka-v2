"""Nakładka zrzutu ekranu dla wielu monitorów (Snipping Tool Overlay)."""

from typing import List, Optional, Tuple

try:
    from PySide6.QtWidgets import QWidget, QApplication
    from PySide6.QtCore import Qt, Signal, QRect, QPoint, QBuffer, QIODevice
    from PySide6.QtGui import (
        QPainter, QColor, QPen, QBrush, QGuiApplication,
        QCursor, QPixmap, QScreen
    )
except ImportError:
    QWidget = object
    QPoint = object
    QRect = object
    Signal = lambda *args: None

from myszkahud.core.geometry import (
    ScreenRect,
    normalize_selection_rect,
    is_valid_selection,
    calculate_virtual_desktop_geometry,
    map_logical_to_screen_crop
)


class ScreenSnippingOverlay(QWidget):
    """
    Pojedyncza nakładka na dany ekran (lub cały virtual desktop).
    Pozwala użytkownikowi na zaznaczenie obszaru prostokątnego.
    
    Gwarantuje:
    - Esc anuluje i emituje cancelled,
    - Prawidłowe ukrycie nakładki PRZED zrzutem ekranu, aby overlay nie znalazł się na obrazie,
    - Zwrócenie bajtów obrazu PNG (image_captured) lub anulowanie.
    """

    area_selected = Signal(int, int, int, int)  # x, y, width, height (logiczne)
    image_captured = Signal(bytes)             # surowe bajty PNG
    cancelled = Signal()

    def __init__(self, parent=None):
        if QWidget is object:
            return
        super().__init__(parent)

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setMouseTracking(True)

        self._is_selecting = False
        self._start_pos: Optional[QPoint] = None
        self._current_pos: Optional[QPoint] = None

    def start_capture(self):
        """
        Inicjalizuje nakładkę na całym wirtualnym pulpicie (wszystkie monitory).
        """
        screens = QGuiApplication.screens()
        screen_rects = []
        for s in screens:
            geom = s.geometry()
            dpr = s.devicePixelRatio()
            screen_rects.append(ScreenRect(
                x=geom.x(),
                y=geom.y(),
                width=geom.width(),
                height=geom.height(),
                device_pixel_ratio=dpr,
                name=s.name()
            ))

        vx, vy, vw, vh = calculate_virtual_desktop_geometry(screen_rects)

        self.setGeometry(vx, vy, vw, vh)
        self._is_selecting = False
        self._start_pos = None
        self._current_pos = None
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Półprzezroczyste tło na całym obszarze (Dark HUD tint)
        dim_color = QColor(0, 0, 0, 140)
        painter.fillRect(self.rect(), dim_color)

        # 2. Rysowanie zaznaczonego prostokąta
        if self._is_selecting and self._start_pos and self._current_pos:
            x, y, w, h = normalize_selection_rect(
                self._start_pos.x(),
                self._start_pos.y(),
                self._current_pos.x(),
                self._current_pos.y()
            )

            # Rysowanie "okna" - wyczyszczenie tła wewnątrz zaznaczenia
            selection_rect = QRect(x, y, w, h)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.transparent)

            # Ramka zaznaczenia w kolorze niebieskim HUD (#38BDF8)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(QColor(56, 189, 248), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(selection_rect)

            # Informacja o rozmiarze
            if w > 40 and h > 20:
                painter.setPen(QColor(255, 255, 255, 220))
                painter.drawText(x + 6, y + 16, f"{w} x {h} px")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_selecting = True
            self._start_pos = event.pos()
            self._current_pos = event.pos()
            self.update()
        elif event.button() == Qt.RightButton:
            # Prawy przycisk anuluje
            self._cancel()

    def mouseMoveEvent(self, event):
        if self._is_selecting:
            self._current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._is_selecting:
            self._is_selecting = False
            if not self._start_pos or not self._current_pos:
                self._cancel()
                return

            # Współrzędne w układzie lokalnym nakładki (względem jej geometrii)
            lx, ly, lw, lh = normalize_selection_rect(
                self._start_pos.x(),
                self._start_pos.y(),
                self._current_pos.x(),
                self._current_pos.y()
            )

            # Współrzędne w układzie globalnym wirtualnego pulpitu
            gx = self.x() + lx
            gy = self.y() + ly

            if not is_valid_selection(lw, lh, min_width=8, min_height=8):
                # Za mały obszar - anulujemy
                self._cancel()
                return

            # 1. KROK KRYTYCZNY: Ukrywamy overlay przed wykonaniem zrzutu ekranu!
            self.hide()
            QApplication.processEvents()

            # 2. Wykonujemy właściwy zrzut ekranu z uwzględnieniem monitora i DPI
            image_bytes = self._capture_screen_region(gx, gy, lw, lh)

            if image_bytes:
                self.area_selected.emit(gx, gy, lw, lh)
                self.image_captured.emit(image_bytes)
            else:
                self._cancel()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._cancel()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _cancel(self):
        self._is_selecting = False
        self.hide()
        self.cancelled.emit()

    def _capture_screen_region(
        self, global_x: int, global_y: int, width: int, height: int
    ) -> Optional[bytes]:
        """
        Pobiera zrzut ekranu zaznaczonego fragmentu z uwzględnieniem DPI i właściwego monitora.
        """
        # Znalezienie monitora na którym znajduje się środek zaznaczenia
        center_x = global_x + width // 2
        center_y = global_y + height // 2
        target_point = QPoint(center_x, center_y)

        screen = QGuiApplication.screenAt(target_point)
        if not screen:
            screen = QGuiApplication.primaryScreen()
        if not screen:
            return None

        # Geometria ekranu
        s_geom = screen.geometry()
        dpr = screen.devicePixelRatio()
        s_rect = ScreenRect(
            x=s_geom.x(),
            y=s_geom.y(),
            width=s_geom.width(),
            height=s_geom.height(),
            device_pixel_ratio=dpr,
            name=screen.name()
        )

        # Przeliczenie do współrzędnych fizycznych ekranu
        px, py, pw, ph = map_logical_to_screen_crop(
            crop_x=global_x,
            crop_y=global_y,
            crop_w=width,
            crop_h=height,
            screen_rect=s_rect
        )

        # Wykonanie zrzutu ekranu danego monitora
        pixmap = screen.grabWindow(0, px, py, pw, ph)
        if pixmap.isNull():
            return None

        # Konwersja QPixmap do surowych bajtów PNG
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, "PNG")
        raw_bytes = bytes(buffer.data().data())
        buffer.close()

        return raw_bytes
