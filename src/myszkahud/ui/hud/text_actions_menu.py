"""Podręczne menu wyboru akcji tekstowych (MyszkaHUD 0.2)."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGraphicsDropShadowEffect, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QEvent, QPoint
from PySide6.QtGui import QColor, QCursor, QGuiApplication

from myszkahud.core.text_actions import TextAction


class TextActionButton(QPushButton):
    """Przycisk pojedynczej operacji tekstowej."""
    
    def __init__(self, action: TextAction, title: str, shortcut_text: str, parent=None):
        super().__init__(parent)
        self.action = action
        self.setFixedSize(148, 42)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 8px;
                text-align: left;
                padding-left: 10px;
                padding-right: 8px;
            }
            QPushButton:hover {
                background-color: #1E293B;
                border: 1px solid #38BDF8;
            }
            QPushButton:pressed {
                background-color: #0F172A;
                border: 1px solid #60A5FA;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        self.lbl_title = QLabel(title, self)
        self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #F8FAFC; background: transparent; border: none;")
        self.lbl_title.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_title)

        layout.addStretch()

        self.lbl_shortcut = QLabel(shortcut_text, self)
        self.lbl_shortcut.setStyleSheet("font-size: 9px; font-weight: 600; color: #94A3B8; background: transparent; border: none;")
        self.lbl_shortcut.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_shortcut)


class TextActionsMenuWindow(QWidget):
    """Kompaktowe okno podmenu akcji tekstowych."""
    
    action_triggered = Signal(TextAction)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        
        self.setFixedSize(330, 260)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Główny kontener
        self.card = QWidget(self)
        self.card.setStyleSheet("""
            QWidget {
                background-color: #0B1120;
                border: 1.5px solid #2563EB;
                border-radius: 12px;
            }
        """)
        
        card_shadow = QGraphicsDropShadowEffect(self.card)
        card_shadow.setBlurRadius(20)
        card_shadow.setColor(QColor(0, 0, 0, 200))
        card_shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(card_shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(8)

        # Nagłówek
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        lbl_icon = QLabel("⚡", self.card)
        lbl_icon.setStyleSheet("font-size: 13px; color: #38BDF8; background: transparent; border: none;")
        header_layout.addWidget(lbl_icon)

        lbl_header = QLabel("AKCJE TEKSTOWE", self.card)
        lbl_header.setStyleSheet("font-size: 11px; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px; background: transparent; border: none;")
        header_layout.addWidget(lbl_header)

        header_layout.addStretch()

        lbl_esc = QLabel("Esc: Zamknij", self.card)
        lbl_esc.setStyleSheet("font-size: 9px; color: #64748B; background: transparent; border: none;")
        header_layout.addWidget(lbl_esc)

        card_layout.addLayout(header_layout)

        # Siatka akcji 2 kolumny x 4 wiersze
        grid = QGridLayout()
        grid.setSpacing(6)

        actions = [
            (TextAction.COPY, "Kopiuj", "Ctrl+C", 0, 0),
            (TextAction.CUT, "Wytnij", "Ctrl+X", 0, 1),
            (TextAction.PASTE, "Wklej", "Ctrl+V", 1, 0),
            (TextAction.PASTE_ENTER, "Wklej + Enter", "Ctrl+V, Enter", 1, 1),
            (TextAction.PASTE_PLAIN, "Wklej czysty tekst", "Plain Text", 2, 0),
            (TextAction.SELECT_ALL, "Zaznacz wszystko", "Ctrl+A", 2, 1),
            (TextAction.UNDO, "Cofnij", "Ctrl+Z", 3, 0),
            (TextAction.REDO, "Ponów", "Ctrl+Y", 3, 1),
        ]

        for action_type, title, shortcut, row, col in actions:
            btn = TextActionButton(action_type, title, shortcut, self.card)
            btn.clicked.connect(lambda checked=False, a=action_type: self._on_action_click(a))
            grid.addWidget(btn, row, col)

        card_layout.addLayout(grid)
        main_layout.addWidget(self.card)

    def _on_action_click(self, action: TextAction):
        self.action_triggered.emit(action)
        self.hide()

    def show_at_cursor(self, target_pos: QPoint = None):
        """Wyświetla okno akcji pod kursorem z ochroną ekranu."""
        if target_pos is None:
            target_pos = QCursor.pos()

        screen = QGuiApplication.screenAt(target_pos)
        if not screen:
            screen = QGuiApplication.primaryScreen()

        geom = screen.availableGeometry()

        x = target_pos.x() - self.width() // 2
        y = target_pos.y() - self.height() // 2

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
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow():
                self.hide()
        super().changeEvent(event)
