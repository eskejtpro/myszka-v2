"""Główne okno panelu Inteligentnego Schowka i Podręcznych Notatek (MyszkaHUD v0.6)."""

from typing import Optional, List, Union

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QScrollArea, QFrame, QGraphicsDropShadowEffect,
        QButtonGroup
    )
    from PySide6.QtCore import Qt, Signal, QPoint
    from PySide6.QtGui import QColor, QCursor, QGuiApplication
except ImportError:
    class MockWidget:
        def __init__(self, *args, **kwargs):
            self._text = ""
            self.clicked = Signal()
            self.textChanged = Signal()
        def setText(self, t):
            self._text = t
        def text(self):
            return self._text
        def width(self):
            return 780
        def height(self):
            return 540
        def __getattr__(self, name):
            def _dummy(*args, **kwargs):
                return None
            return _dummy

    class QWidget(MockWidget):
        pass

    class Signal:
        def __init__(self, *types):
            self._handlers = []
        def connect(self, h):
            self._handlers.append(h)
        def emit(self, *args):
            for h in self._handlers:
                h(*args)

    class MockQt:
        FramelessWindowHint = 0x00000800
        WindowStaysOnTopHint = 0x00040000
        Tool = 0x00000008
        WA_TranslucentBackground = 120
        Key_Escape = 0x01000000
        AlignCenter = 0x0004

    QVBoxLayout = MockWidget
    QHBoxLayout = MockWidget
    QLabel = MockWidget
    QLineEdit = MockWidget
    QPushButton = MockWidget
    QScrollArea = MockWidget
    QFrame = MockWidget
    QGraphicsDropShadowEffect = MockWidget
    QButtonGroup = MockWidget
    Qt = MockQt
    QPoint = object
    QColor = object
    QCursor = object
    QGuiApplication = object

from myszkahud.services.clipboard.clipboard_service import ClipboardService
from myszkahud.services.clipboard.notes_service import NotesService
from myszkahud.services.clipboard.models import ClipboardEntry, Note
from .clipboard_card import ClipboardCard
from .note_dialog import NoteDialog


class ClipboardWindow(QWidget):
    """
    Panel Inteligentnego Schowka & Podręcznego Notesu.
    Pozwala na przeglądanie, wyszukiwanie, przypinanie, kopiowanie i wklejanie.
    """

    copy_requested = Signal(str)
    paste_requested = Signal(str)
    paste_enter_requested = Signal(str)

    def __init__(
        self,
        clipboard_service: Optional[ClipboardService] = None,
        notes_service: Optional[NotesService] = None,
        parent=None
    ):
        if QWidget is not object:
            super().__init__(parent)

        self.clipboard_service = clipboard_service or ClipboardService()
        self.notes_service = notes_service or NotesService()
        self.current_category = "all"  # "all", "pinned", "clipboard", "notes"
        self._note_dialog: Optional[NoteDialog] = None

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(780, 540)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Główny kontener Dark Navy
        self.card = QWidget(self)
        self.card.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 15, 29, 0.98);
                border: 1.5px solid #0284C7;
                border-radius: 12px;
            }
        """)

        card_shadow = QGraphicsDropShadowEffect(self.card)
        card_shadow.setBlurRadius(24)
        card_shadow.setColor(QColor(0, 0, 0, 220))
        card_shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(card_shadow)

        layout = QHBoxLayout(self.card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ==========================================
        # 1. LEWY SIDEBAR
        # ==========================================
        self.sidebar = QWidget(self.card)
        self.sidebar.setFixedWidth(190)
        self.sidebar.setStyleSheet("""
            QWidget {
                background-color: #070A13;
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
                border-right: 1px solid #1E293B;
                border-top: none;
                border-left: none;
                border-bottom: none;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 14, 12, 14)
        sidebar_layout.setSpacing(6)

        # Tytuł modułu
        lbl_brand = QLabel("📋 SCHOWEK & NOTES", self.sidebar)
        lbl_brand.setStyleSheet("font-size: 11px; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px; background: transparent; border: none;")
        sidebar_layout.addWidget(lbl_brand)
        sidebar_layout.addSpacing(10)

        # Przyciski kategorii
        nav_btn_style = """
            QPushButton {
                background-color: transparent;
                color: #94A3B8;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                text-align: left;
                padding: 7px 10px;
            }
            QPushButton:hover { background-color: #0E1626; color: #F8FAFC; }
            QPushButton:checked { background-color: #0284C7; color: #FFFFFF; font-weight: 700; }
        """

        self.btn_all = QPushButton("🗂 Wszystkie", self.sidebar)
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self.btn_all.setStyleSheet(nav_btn_style)
        self.btn_all.clicked.connect(lambda: self._set_category("all"))
        sidebar_layout.addWidget(self.btn_all)

        self.btn_pinned = QPushButton("📌 Przypięte", self.sidebar)
        self.btn_pinned.setCheckable(True)
        self.btn_pinned.setStyleSheet(nav_btn_style)
        self.btn_pinned.clicked.connect(lambda: self._set_category("pinned"))
        sidebar_layout.addWidget(self.btn_pinned)

        self.btn_clip = QPushButton("🕒 Schowek", self.sidebar)
        self.btn_clip.setCheckable(True)
        self.btn_clip.setStyleSheet(nav_btn_style)
        self.btn_clip.clicked.connect(lambda: self._set_category("clipboard"))
        sidebar_layout.addWidget(self.btn_clip)

        self.btn_notes = QPushButton("📝 Notatki", self.sidebar)
        self.btn_notes.setCheckable(True)
        self.btn_notes.setStyleSheet(nav_btn_style)
        self.btn_notes.clicked.connect(lambda: self._set_category("notes"))
        sidebar_layout.addWidget(self.btn_notes)

        sidebar_layout.addStretch()

        # Przełącznik pauzy historii
        self.btn_pause = QPushButton("⏸ Pauza historii", self.sidebar)
        self.btn_pause.setStyleSheet("""
            QPushButton {
                background-color: #0E1626;
                color: #CBD5E1;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 600;
                padding: 6px;
            }
            QPushButton:hover { background-color: #1E293B; border-color: #38BDF8; }
        """)
        self.btn_pause.clicked.connect(self._toggle_pause_history)
        sidebar_layout.addWidget(self.btn_pause)

        # Przycisk czyszczenia historii (usuwa tylko nieprzypięte ze schowka)
        self.btn_clear = QPushButton("🗑 Wyczyść schowek", self.sidebar)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #EF4444;
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 6px;
                font-size: 10px;
                font-weight: 600;
                padding: 6px;
            }
            QPushButton:hover { background-color: rgba(239, 68, 68, 0.15); border-color: #EF4444; }
        """)
        self.btn_clear.clicked.connect(self._on_clear_history_clicked)
        sidebar_layout.addWidget(self.btn_clear)

        layout.addWidget(self.sidebar)

        # ==========================================
        # 2. PRAWA CZĘŚĆ GŁÓWNA (GÓRA + LISTA KART)
        # ==========================================
        content_widget = QWidget(self.card)
        content_widget.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(10)

        # Górny pasek wyszukiwania i dodawania
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.edit_search = QLineEdit(content_widget)
        self.edit_search.setPlaceholderText("🔍 Szukaj w schowku i notatkach...")
        self.edit_search.setStyleSheet("""
            QLineEdit {
                background-color: #0E1626;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
            }
            QLineEdit:focus { border: 1px solid #38BDF8; }
        """)
        self.edit_search.textChanged.connect(self.refresh_list)
        top_bar.addWidget(self.edit_search)

        self.btn_new_note = QPushButton("＋ Nowa notatka", content_widget)
        self.btn_new_note.setStyleSheet("""
            QPushButton {
                background-color: #0284C7;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 700;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #0369A1; }
        """)
        self.btn_new_note.clicked.connect(self._on_new_note_clicked)
        top_bar.addWidget(self.btn_new_note)

        content_layout.addLayout(top_bar)

        # Obszar przewijania kart
        self.scroll_area = QScrollArea(content_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #070A13;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0284C7;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent; border: none;")
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 0, 4, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)
        content_layout.addWidget(self.scroll_area)

        # Dolny pasek informacyjny
        footer = QHBoxLayout()
        self.lbl_stats = QLabel("0 elementów", content_widget)
        self.lbl_stats.setStyleSheet("font-size: 10px; color: #64748B; background: transparent; border: none;")
        footer.addWidget(self.lbl_stats)

        footer.addStretch()

        lbl_hint = QLabel("Esc: Zamknij  |  Kliknij Wklej, aby wysłać do okna", content_widget)
        lbl_hint.setStyleSheet("font-size: 9px; color: #64748B; background: transparent; border: none;")
        footer.addWidget(lbl_hint)

        content_layout.addLayout(footer)
        layout.addWidget(content_widget)
        main_layout.addWidget(self.card)

    def _set_category(self, cat: str):
        self.current_category = cat
        self.btn_all.setChecked(cat == "all")
        self.btn_pinned.setChecked(cat == "pinned")
        self.btn_clip.setChecked(cat == "clipboard")
        self.btn_notes.setChecked(cat == "notes")
        self.refresh_list()

    def _toggle_pause_history(self):
        is_paused = self.clipboard_service.toggle_pause()
        if is_paused:
            self.btn_pause.setText("▶ Wznów historię")
            self.btn_pause.setStyleSheet("""
                QPushButton {
                    background-color: #7C2D12;
                    color: #FED7AA;
                    border: 1px solid #F97316;
                    border-radius: 6px;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 6px;
                }
            """)
        else:
            self.btn_pause.setText("⏸ Pauza historii")
            self.btn_pause.setStyleSheet("""
                QPushButton {
                    background-color: #0E1626;
                    color: #CBD5E1;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 6px;
                }
                QPushButton:hover { background-color: #1E293B; border-color: #38BDF8; }
            """)

    def _on_clear_history_clicked(self):
        self.clipboard_service.clear_history(preserve_pinned=True)
        self.refresh_list()

    def _on_new_note_clicked(self):
        self._note_dialog = NoteDialog(parent=self)
        self._note_dialog.saved.connect(self._on_note_saved)
        self._note_dialog.show()

    def _on_note_saved(self, title: str, content: str, pinned: bool, note_id: Optional[int]):
        if note_id is not None:
            self.notes_service.update_note(note_id, title, content)
            self.notes_service.set_pinned(note_id, pinned)
        else:
            self.notes_service.create_note(title, content, pinned=pinned)
        self.refresh_list()

    def _on_edit_note_requested(self, note_id: int):
        note = self.notes_service.get_note(note_id)
        if note:
            self._note_dialog = NoteDialog(
                note_id=note.id,
                title=note.title,
                content=note.content,
                pinned=note.pinned,
                parent=self
            )
            self._note_dialog.saved.connect(self._on_note_saved)
            self._note_dialog.show()

    def _on_pin_toggled(self, item_id: int, is_note: bool):
        if is_note:
            self.notes_service.toggle_pin(item_id)
        else:
            self.clipboard_service.toggle_pin(item_id)
        self.refresh_list()

    def _on_delete_requested(self, item_id: int, is_note: bool):
        if is_note:
            self.notes_service.delete_note(item_id)
        else:
            self.clipboard_service.delete_entry(item_id)
        self.refresh_list()

    def refresh_list(self):
        """Pobiera elementy z bazy i odświeża widok kart."""
        # Usuwamy dotychczasowe karty
        while self.cards_layout.count() > 1:
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        query = self.edit_search.text().strip() or None
        items: List[Union[ClipboardEntry, Note]] = []

        if self.current_category == "all":
            clips = self.clipboard_service.list_entries(search_query=query)
            notes = self.notes_service.list_notes(search_query=query)
            # Łączenie i sortowanie: najpierw pinned, potem od najnowszych
            items = sorted(
                clips + notes,
                key=lambda x: (not x.pinned, -(x.created_at.timestamp() if hasattr(x, "created_at") else 0))
            )
        elif self.current_category == "pinned":
            clips = self.clipboard_service.list_entries(pinned_only=True, search_query=query)
            notes = self.notes_service.list_notes(pinned_only=True, search_query=query)
            items = sorted(
                clips + notes,
                key=lambda x: -(x.created_at.timestamp() if hasattr(x, "created_at") else 0)
            )
        elif self.current_category == "clipboard":
            items = self.clipboard_service.list_entries(search_query=query)
        elif self.current_category == "notes":
            items = self.notes_service.list_notes(search_query=query)

        # Tworzenie kart
        for item in items:
            card = ClipboardCard(item, parent=self.scroll_content)
            card.copy_requested.connect(self._on_copy)
            card.paste_requested.connect(self._on_paste)
            card.paste_enter_requested.connect(self._on_paste_enter)
            card.pin_toggled.connect(self._on_pin_toggled)
            card.delete_requested.connect(self._on_delete_requested)
            card.edit_requested.connect(self._on_edit_note_requested)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        self.lbl_stats.setText(f"{len(items)} elementów")

    def _on_copy(self, text: str):
        self.copy_requested.emit(text)

    def _on_paste(self, text: str):
        self.paste_requested.emit(text)
        self.hide()

    def _on_paste_enter(self, text: str):
        self.paste_enter_requested.emit(text)
        self.hide()

    def show_at_cursor(self, target_pos: Optional[QPoint] = None):
        """Wyświetla okno na środku lub pod kursorem."""
        self.refresh_list()

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
            if hasattr(super(), "keyPressEvent"):
                super().keyPressEvent(event)
