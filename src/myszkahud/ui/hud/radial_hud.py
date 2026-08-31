"""Główne okno radialnego menu HUD MyszkaHUD (v0.3.1 - Final HUD UI).

Komponent łączy:
- Rozmieszczenie 6 modułów wokół centrum na okręgu co 60°,
- Wizualny reticle pozycji kursora oraz subtelny okrąg i linie promieniste (QPainter),
- Centralną kartę z informacją o stanie gotowości (CenterHUDCard),
- Ochronę wielomonitorową (Screen Clamping / Multi-Monitor),
- Lekkie, natywne renderowanie bez ciężkiego blura i zbędnych bibliotek.
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, QEvent, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen

from .hud_theme import DEFAULT_HUD_THEME, HUD_MODULES_CONFIG, HUDColorPalette
from .hud_status import ModuleStatus
from .center_card import CenterHUDCard
from .hud_item import HUDItemButton


class RadialHUDWindow(QWidget):
    """Główne okno radialnego HUD wyświetlane przy kursorze myszy."""
    
    action_selected = Signal(str)

    def __init__(self, theme: HUDColorPalette = DEFAULT_HUD_THEME, parent=None):
        super().__init__(parent)
        self.theme = theme
        
        # Konfiguracja okna: Frameless, Always On Top, Tool window, przezroczyste tło
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        
        # Całkowity wymiar radialnego obszaru
        self.hud_size = 430
        self.setFixedSize(self.hud_size, self.hud_size)
        
        # Promień rozmieszczenia kafelków
        self.orbit_radius = 142
        
        self._init_ui()

    def _init_ui(self):
        """Inicjalizacja i pozycjonowanie komponentów HUD."""
        cx = self.hud_size // 2
        cy = self.hud_size // 2

        # 1. Centralna karta aplikacji
        self.center_card = CenterHUDCard(theme=self.theme, parent=self)
        self.center_card.move(
            cx - self.center_card.width() // 2,
            cy - self.center_card.height() // 2
        )

        # 2. Utworzenie 6 kafelków modularnych
        self.buttons = []
        for mod in HUD_MODULES_CONFIG:
            status_enum = ModuleStatus[mod.get("status", "READY")]
            btn = HUDItemButton(
                item_id=mod["id"],
                title=mod["title"],
                icon_text=mod["icon"],
                subtitle=mod["subtitle"],
                accent_color=mod["accent_color"],
                status=status_enum,
                theme=self.theme,
                parent=self
            )
            
            # Obliczenie współrzędnych radialnych
            rad = math.radians(mod["angle_deg"])
            btn_x = int(cx + self.orbit_radius * math.cos(rad) - btn.width() / 2)
            btn_y = int(cy + self.orbit_radius * math.sin(rad) - btn.height() / 2)
            btn.move(btn_x, btn_y)
            
            btn.action_triggered.connect(self._handle_action)
            self.buttons.append(btn)

    def paintEvent(self, event):
        """
        Natywne rysowanie subtelnych elementów graficznych:
        - Delikatny radialny pierścień w tle,
        - Subtelne linie promieniste łączące centrum z modułami,
        - Znacznik pozycji kursora (reticle).
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx = self.hud_size / 2.0
        cy = self.hud_size / 2.0
        center_pt = QPoint(int(cx), int(cy))

        # 1. Linie promieniste łączące środek z modułami
        spoke_pen = QPen(QColor(51, 65, 85, 90), 1, Qt.SolidLine)
        painter.setPen(spoke_pen)
        for mod in HUD_MODULES_CONFIG:
            rad = math.radians(mod["angle_deg"])
            # Rysujemy od brzegu karty środkowej do kafelka
            start_dist = 42
            end_dist = self.orbit_radius - 36
            x1 = cx + start_dist * math.cos(rad)
            y1 = cy + start_dist * math.sin(rad)
            x2 = cx + end_dist * math.cos(rad)
            y2 = cy + end_dist * math.sin(rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # 2. Subtelny radialny pierścień
        ring_pen = QPen(QColor(56, 189, 248, 45), 1, Qt.DashLine)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center_pt, self.orbit_radius, self.orbit_radius)

        # 3. Zewnętrzny bardzo delikatny okrąg tła
        outer_pen = QPen(QColor(30, 41, 59, 70), 1, Qt.SolidLine)
        painter.setPen(outer_pen)
        painter.drawEllipse(center_pt, self.orbit_radius + 40, self.orbit_radius + 40)

    def _handle_action(self, item_id: str):
        """Obsługa wyboru kafelka przez użytkownika."""
        self.action_selected.emit(item_id)
        self.hide()

    def show_at_cursor(self, target_pos: QPoint = None):
        """
        Wyświetla HUD zakotwiczony przy kursorze myszy z uwzględnieniem
        wielu monitorów i ochroną krawędzi ekranu (clamping).
        """
        if target_pos is None:
            target_pos = QCursor.pos()

        screen = QGuiApplication.screenAt(target_pos)
        if not screen:
            screen = QGuiApplication.primaryScreen()

        geom = screen.availableGeometry()

        x = target_pos.x() - self.width() // 2
        y = target_pos.y() - self.height() // 2

        # Screen clamping
        min_x = geom.left()
        max_x = geom.right() - self.width() + 1
        min_y = geom.top()
        max_y = geom.bottom() - self.height() + 1

        clamped_x = max(min_x, min(x, max_x))
        clamped_y = max(min_y, min(y, max_y))

        self.move(clamped_x, clamped_y)
        self.show()
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, event):
        """Zamknięcie HUD klawiszem Esc."""
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)

    def changeEvent(self, event):
        """Zamknięcie HUD po utracie fokusu (kliknięcie poza aplikacją)."""
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow():
                self.hide()
        super().changeEvent(event)

    def mousePressEvent(self, event):
        """Kliknięcie w tło HUD zamyka okno."""
        child = self.childAt(event.pos())
        if child is None or child == self:
            self.hide()
            event.accept()
        else:
            super().mousePressEvent(event)
