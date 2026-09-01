"""Komponent pojedynczego kafelka radialnego menu HUD.

Obsługuje:
- Stylizację Gaming HUD / Utility HUD (ciemny granat, cienka ramka, zaokrąglone narożniki),
- Wektorowe symbole / ikony, tytuł i podtytuł,
- Wskaźnik stanu modułu (READY, WORKING, ERROR, DISABLED),
- Płynny wizualny hover i pressed state z zachowaniem niskiego narzutu CPU,
- Akcenty kolorystyczne spójne z HUDColorPalette.
"""

from PySide6.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect, QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QCursor

from .hud_theme import DEFAULT_HUD_THEME, HUDColorPalette
from .hud_status import ModuleStatus


class HUDItemButton(QPushButton):
    """Kafelek pojedynczego modułu w radialnym HUD."""
    
    action_triggered = Signal(str)

    def __init__(
        self,
        item_id: str,
        title: str,
        icon_text: str,
        subtitle: str = "",
        accent_color: str = "#38BDF8",
        status: ModuleStatus = ModuleStatus.READY,
        theme: HUDColorPalette = DEFAULT_HUD_THEME,
        parent=None
    ):
        super().__init__(parent)
        self.item_id = item_id
        self.title_text = title
        self.icon_text = icon_text
        self.subtitle_text = subtitle
        self.accent_color = accent_color
        self.module_status = status
        self.theme = theme
        
        # Wymiary kafelka
        self.setFixedSize(100, 64)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_Hover, True)
        
        self._setup_style()
        self._init_ui()
        self.clicked.connect(self._on_clicked)

    def _setup_style(self):
        """Ustawia arkusz stylów uwzględniający hover, pressed i dedykowany akcent."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.bg_card_rgba};
                border: 1px solid {self.theme.border_default};
                border-radius: {self.theme.border_radius_tile}px;
                text-align: center;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.bg_card_hover_rgba};
                border: 1.5px solid {self.accent_color};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.bg_card_pressed_rgba};
                border: 1.5px solid {self.accent_color};
            }}
        """)

        # Subtelny cień kafelka
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

    def _init_ui(self):
        """Budowa wewnętrznego układu kafelka."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        # 1. Górny rząd: Ikona + mały wskaźnik statusu
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(4)
        top_row.setAlignment(Qt.AlignCenter)

        self.lbl_icon = QLabel(self.icon_text, self)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet(f"""
            font-size: 15px;
            color: {self.accent_color};
            background: transparent;
            border: none;
        """)
        self.lbl_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        top_row.addWidget(self.lbl_icon)

        layout.addLayout(top_row)

        # 2. Nazwa modułu
        self.lbl_title = QLabel(self.title_text, self)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 700;
            color: {self.theme.text_primary};
            background: transparent;
            border: none;
            letter-spacing: 0.4px;
        """)
        self.lbl_title.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_title)

        # 3. Podtytuł / Opis
        if self.subtitle_text:
            self.lbl_subtitle = QLabel(self.subtitle_text, self)
            self.lbl_subtitle.setAlignment(Qt.AlignCenter)
            self.lbl_subtitle.setStyleSheet(f"""
                font-size: 9px;
                color: {self.theme.text_secondary};
                background: transparent;
                border: none;
            """)
            self.lbl_subtitle.setAttribute(Qt.WA_TransparentForMouseEvents)
            layout.addWidget(self.lbl_subtitle)

    def set_status(self, status: ModuleStatus):
        """Aktualizuje stan modułu."""
        self.module_status = status

    def _on_clicked(self):
        """Obsługa kliknięcia kafelka."""
        self.action_triggered.emit(self.item_id)
