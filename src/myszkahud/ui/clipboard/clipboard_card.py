"""Komponent pojedynczej karty wpisu schowka lub notatki w MyszkaHUD."""

from typing import Optional, Union

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
    )
    from PySide6.QtCore import Qt, Signal
except ImportError:
    class MockWidget:
        def __init__(self, *args, **kwargs):
            self.clicked = Signal()
        def setText(self, text):
            pass
        def setStyleSheet(self, s):
            pass
        def __getattr__(self, name):
            def _dummy(*args, **kwargs):
                return None
            return _dummy

    class QWidget(MockWidget):
        pass

    class Signal:
        def __init__(self, *types):
            self._handlers = []
        def connect(self, handler):
            self._handlers.append(handler)
        def emit(self, *args):
            for h in self._handlers:
                h(*args)

    QVBoxLayout = MockWidget
    QHBoxLayout = MockWidget
    QLabel = MockWidget
    QPushButton = MockWidget
    QFrame = MockWidget

from myszkahud.services.clipboard.models import ClipboardEntry, Note


class ClipboardCard(QWidget):
    """Karta reprezentująca pojedynczy element schowka lub notatkę."""

    copy_requested = Signal(str)
    paste_requested = Signal(str)
    paste_enter_requested = Signal(str)
    pin_toggled = Signal(int, bool)     # (id, is_note)
    delete_requested = Signal(int, bool) # (id, is_note)
    edit_requested = Signal(int)         # (note_id)

    def __init__(self, item: Union[ClipboardEntry, Note], parent=None):
        if QWidget is not object:
            super().__init__(parent)
        self.item = item
        self.is_note = isinstance(item, Note)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Kontener karty z ramką
        self.frame = QFrame(self)
        pinned_border = "border: 1px solid #0284C7;" if self.item.pinned else "border: 1px solid #1E293B;"
        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: #0E1626;
                {pinned_border}
                border-radius: 8px;
            }}
            QFrame:hover {{
                border: 1px solid #38BDF8;
                background-color: #111C30;
            }}
        """)

        card_layout = QVBoxLayout(self.frame)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(6)

        # 1. Pasek metadanych (Źródło / Data / Rozmiar / Pin)
        header = QHBoxLayout()
        header.setSpacing(6)

        if self.is_note:
            badge_text = "📝 NOTATKA"
            badge_color = "#3B82F6"
        else:
            source = getattr(self.item, "source_app", None)
            badge_text = f"💻 {source}" if source else "📋 SCHOWEK"
            badge_color = "#0284C7"

        lbl_badge = QLabel(badge_text, self.frame)
        lbl_badge.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(2, 132, 199, 0.2);
                color: {badge_color};
                font-size: 9px;
                font-weight: 700;
                border-radius: 4px;
                padding: 2px 5px;
                border: none;
            }}
        """)
        header.addWidget(lbl_badge)

        # Data utworzenia (konwersja UTC do czytelnego stringa)
        dt = getattr(self.item, "created_at", None)
        time_str = dt.strftime("%H:%M:%S  %d.%m") if dt else ""
        lbl_time = QLabel(time_str, self.frame)
        lbl_time.setStyleSheet("font-size: 9px; color: #64748B; background: transparent; border: none;")
        header.addWidget(lbl_time)

        # Długość tekstu
        char_count = self.item.char_count
        lbl_len = QLabel(f"{char_count} zn.", self.frame)
        lbl_len.setStyleSheet("font-size: 9px; color: #64748B; background: transparent; border: none;")
        header.addWidget(lbl_len)

        header.addStretch()

        # Przycisk przypięcia (PIN)
        pin_icon = "📌" if self.item.pinned else "📍"
        self.btn_pin = QPushButton(pin_icon, self.frame)
        self.btn_pin.setToolTip("Przypnij / Odepnij")
        self.btn_pin.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 11px;
                padding: 2px 4px;
            }
            QPushButton:hover { background-color: #1E293B; border-radius: 4px; }
        """)
        self.btn_pin.clicked.connect(self._on_pin_clicked)
        header.addWidget(self.btn_pin)

        # Przycisk usunięcia
        self.btn_delete = QPushButton("✕", self.frame)
        self.btn_delete.setToolTip("Usuń wpis")
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #EF4444;
                border: none;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 4px;
            }
            QPushButton:hover { background-color: rgba(239, 68, 68, 0.2); border-radius: 4px; }
        """)
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        header.addWidget(self.btn_delete)

        card_layout.addLayout(header)

        # 2. Treść wpisu / Tytuł notatki
        if self.is_note:
            lbl_title = QLabel(self.item.title, self.frame)
            lbl_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #F8FAFC; background: transparent; border: none;")
            card_layout.addWidget(lbl_title)

        # Skrócony podgląd tekstu
        raw_text = self.item.content if self.is_note else self.item.text
        preview = raw_text[:280] + ("..." if len(raw_text) > 280 else "")
        lbl_preview = QLabel(preview, self.frame)
        lbl_preview.setWordWrap(True)
        lbl_preview.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #CBD5E1;
                font-family: 'Segoe UI', sans-serif;
                background: transparent;
                border: none;
                line-height: 1.3;
            }
        """)
        card_layout.addWidget(lbl_preview)

        # 3. Pasek akcji
        actions = QHBoxLayout()
        actions.setSpacing(6)

        btn_action_style = """
            QPushButton {
                background-color: #1E293B;
                color: #E2E8F0;
                border: 1px solid #334155;
                border-radius: 4px;
                font-size: 9px;
                font-weight: 600;
                padding: 3px 7px;
            }
            QPushButton:hover { background-color: #334155; border: 1px solid #38BDF8; }
            QPushButton:pressed { background-color: #0F172A; }
        """

        self.btn_copy = QPushButton("Kopiuj", self.frame)
        self.btn_copy.setStyleSheet(btn_action_style)
        self.btn_copy.clicked.connect(self._on_copy_clicked)
        actions.addWidget(self.btn_copy)

        self.btn_paste = QPushButton("Wklej", self.frame)
        self.btn_paste.setStyleSheet(btn_action_style)
        self.btn_paste.clicked.connect(self._on_paste_clicked)
        actions.addWidget(self.btn_paste)

        self.btn_paste_enter = QPushButton("+ Enter", self.frame)
        self.btn_paste_enter.setStyleSheet(btn_action_style)
        self.btn_paste_enter.clicked.connect(self._on_paste_enter_clicked)
        actions.addWidget(self.btn_paste_enter)

        if self.is_note:
            self.btn_edit = QPushButton("Edytuj", self.frame)
            self.btn_edit.setStyleSheet(btn_action_style)
            self.btn_edit.clicked.connect(self._on_edit_clicked)
            actions.addWidget(self.btn_edit)

        actions.addStretch()
        card_layout.addLayout(actions)

        layout.addWidget(self.frame)

    def _get_target_text(self) -> str:
        return self.item.content if self.is_note else self.item.text

    def _on_copy_clicked(self):
        self.copy_requested.emit(self._get_target_text())

    def _on_paste_clicked(self):
        self.paste_requested.emit(self._get_target_text())

    def _on_paste_enter_clicked(self):
        self.paste_enter_requested.emit(self._get_target_text())

    def _on_pin_clicked(self):
        if self.item.id is not None:
            self.pin_toggled.emit(self.item.id, self.is_note)

    def _on_delete_clicked(self):
        if self.item.id is not None:
            self.delete_requested.emit(self.item.id, self.is_note)

    def _on_edit_clicked(self):
        if self.is_note and self.item.id is not None:
            self.edit_requested.emit(self.item.id)
