"""Komponent centralnej karty MyszkaHUD.

Wyświetla nazwę aplikacji, skrót aktywacyjny oraz wizualny wskaźnik gotowości,
pozostawiając subtelną widoczność punktu kotwiczenia kursora myszy.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen

from .hud_theme import DEFAULT_HUD_THEME, HUDColorPalette


class CenterHUDCard(QWidget):
    """Centralna karta informacji i statusu w menu radialnym."""

    def __init__(self, theme: HUDColorPalette = DEFAULT_HUD_THEME, parent=None):
        super().__init__(parent)
        self.theme = theme
        
        self.setFixedSize(136, 76)
        self._init_ui()

    def _init_ui(self):
        # Stylizacja karty głównej
        self.setStyleSheet(f"""
            QWidget#CenterCardRoot {{
                background-color: {self.theme.bg_center_rgba};
                border: 1.5px solid {self.theme.border_center};
                border-radius: {self.theme.border_radius_center}px;
            }}
        """)
        self.setObjectName("CenterCardRoot")

        # Subtelny glow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(37, 99, 235, 130))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        # Nazwa aplikacji
        self.lbl_app_name = QLabel("MyszkaHUD", self)
        self.lbl_app_name.setAlignment(Qt.AlignCenter)
        self.lbl_app_name.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 800;
            color: {self.theme.accent_primary};
            background: transparent;
            border: none;
            letter-spacing: 0.6px;
        """)
        layout.addWidget(self.lbl_app_name)

        # Kontener statusu i skrótu (ALT + Q | ● GOTOWY)
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(5)
        status_row.setAlignment(Qt.AlignCenter)

        self.lbl_hotkey = QLabel("ALT + Q", self)
        self.lbl_hotkey.setStyleSheet(f"""
            font-size: 9px;
            font-weight: 700;
            color: {self.theme.text_secondary};
            background: transparent;
            border: none;
            letter-spacing: 0.8px;
        """)
        status_row.addWidget(self.lbl_hotkey)

        lbl_sep = QLabel("•", self)
        lbl_sep.setStyleSheet(f"font-size: 8px; color: {self.theme.text_muted}; background: transparent; border: none;")
        status_row.addWidget(lbl_sep)

        self.lbl_status = QLabel("GOTOWY", self)
        self.lbl_status.setStyleSheet(f"""
            font-size: 9px;
            font-weight: 700;
            color: {self.theme.status_ready};
            background: transparent;
            border: none;
            letter-spacing: 0.5px;
        """)
        status_row.addWidget(self.lbl_status)

        layout.addLayout(status_row)
