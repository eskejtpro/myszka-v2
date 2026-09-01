"""Dialog tworzenia i edycji podręcznej notatki w MyszkaHUD (Dark Navy theme)."""

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QTextEdit, QPushButton, QCheckBox, QGraphicsDropShadowEffect
    )
    from PySide6.QtCore import Qt, Signal, QPoint
    from PySide6.QtGui import QColor, QCursor, QGuiApplication
except ImportError:
    class MockWidget:
        def __init__(self, *args, **kwargs):
            self._text = ""
            self.clicked = Signal()
        def setText(self, text):
            self._text = text
        def text(self):
            return self._text
        def setPlainText(self, text):
            self._text = text
        def toPlainText(self):
            return self._text
        def isChecked(self):
            return False
        def setChecked(self, val):
            pass
        def width(self):
            return 450
        def height(self):
            return 320
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

    class MockQt:
        FramelessWindowHint = 0x00000800
        WindowStaysOnTopHint = 0x00040000
        Tool = 0x00000008
        WA_TranslucentBackground = 120
        Key_Escape = 0x01000000

    class MockHelper:
        def __init__(self, *args, **kwargs):
            pass
        def __getattr__(self, name):
            def _dummy(*args, **kwargs):
                return None
            return _dummy

    QVBoxLayout = MockWidget
    QHBoxLayout = MockWidget
    QLabel = MockWidget
    QLineEdit = MockWidget
    QTextEdit = MockWidget
    QPushButton = MockWidget
    QCheckBox = MockWidget
    QGraphicsDropShadowEffect = MockWidget
    Qt = MockQt
    QPoint = MockHelper
    QColor = MockHelper
    QCursor = MockHelper
    QGuiApplication = MockHelper


class NoteDialog(QWidget):
    """Kompaktowy edytor notatki w stylistyce Dark Navy."""

    saved = Signal(str, str, bool, object)  # title, content, pinned, note_id

    def __init__(self, note_id: Optional[int] = None, title: str = "", content: str = "", pinned: bool = False, parent=None):
        if QWidget is not object:
            super().__init__(parent)
        self.note_id = note_id
        self._initial_title = title
        self._initial_content = content
        self._initial_pinned = pinned

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(450, 320)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

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

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        lbl_title = QLabel("📝 NOWA NOTATKA" if not self.note_id else "📝 EDYTUJ NOTATKĘ", self.card)
        lbl_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px; background: transparent; border: none;")
        header.addWidget(lbl_title)
        header.addStretch()

        self.chk_pin = QCheckBox("Przypnij na górze", self.card)
        self.chk_pin.setChecked(self._initial_pinned)
        self.chk_pin.setStyleSheet("color: #94A3B8; font-size: 10px; background: transparent; border: none;")
        header.addWidget(self.chk_pin)
        layout.addLayout(header)

        # Tytuł notatki
        self.edit_title = QLineEdit(self.card)
        self.edit_title.setPlaceholderText("Tytuł notatki...")
        self.edit_title.setText(self._initial_title)
        self.edit_title.setStyleSheet("""
            QLineEdit {
                background-color: #0E1626;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QLineEdit:focus { border: 1px solid #38BDF8; }
        """)
        layout.addWidget(self.edit_title)

        # Treść notatki
        self.edit_content = QTextEdit(self.card)
        self.edit_content.setPlaceholderText("Treść notatki...")
        self.edit_content.setPlainText(self._initial_content)
        self.edit_content.setStyleSheet("""
            QTextEdit {
                background-color: #0E1626;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
            QTextEdit:focus { border: 1px solid #38BDF8; }
        """)
        layout.addWidget(self.edit_content)

        # Przyciski
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.btn_cancel = QPushButton("Anuluj", self.card)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 600;
                padding: 5px 12px;
            }
            QPushButton:hover { background-color: #334155; color: #FFFFFF; }
        """)
        self.btn_cancel.clicked.connect(self.hide)
        btn_box.addWidget(self.btn_cancel)

        btn_box.addStretch()

        self.btn_save = QPushButton("Zapisz notatkę", self.card)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #0284C7;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 700;
                padding: 5px 16px;
            }
            QPushButton:hover { background-color: #0369A1; }
            QPushButton:pressed { background-color: #075985; }
        """)
        self.btn_save.clicked.connect(self._on_save_clicked)
        btn_box.addWidget(self.btn_save)

        layout.addLayout(btn_box)
        main_layout.addWidget(self.card)

    def _on_save_clicked(self):
        title = self.edit_title.text()
        content = self.edit_content.toPlainText()
        pinned = self.chk_pin.isChecked()
        self.saved.emit(title, content, pinned, self.note_id)
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            if hasattr(super(), "keyPressEvent"):
                super().keyPressEvent(event)
