"""Podręczne okno tłumacza tekstu (MyszkaHUD 0.3)."""

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QPushButton, QComboBox, QGraphicsDropShadowEffect, QProgressBar
    )
    from PySide6.QtCore import Qt, Signal, QEvent, QPoint
    from PySide6.QtGui import QColor, QCursor, QGuiApplication
except ImportError:
    # Stubs dla środowiska testowego
    QWidget = object
    QPoint = object
    Signal = lambda *args: None

from myszkahud.services.translation.translator import TranslationService, SUPPORTED_LANGUAGES
from myszkahud.ui.translation.worker import TranslationWorker


class TranslationWindow(QWidget):
    """
    Kompaktowe okno dialogowe tłumaczenia tekstu w stylistyce Dark HUD.
    """

    copy_requested = Signal(str)
    paste_requested = Signal(str)
    paste_enter_requested = Signal(str)

    def __init__(self, translation_service: Optional[TranslationService] = None, parent=None):
        if QWidget is object:
            return
        super().__init__(parent)
        self.translation_service = translation_service
        self.current_worker: Optional[TranslationWorker] = None

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(460, 420)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        self.card = QWidget(self)
        self.card.setStyleSheet("""
            QWidget {
                background-color: #0B1120;
                border: 1.5px solid #38BDF8;
                border-radius: 12px;
            }
        """)

        card_shadow = QGraphicsDropShadowEffect(self.card)
        card_shadow.setBlurRadius(24)
        card_shadow.setColor(QColor(0, 0, 0, 220))
        card_shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(card_shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        # 1. Pasek tytułu i wybór języków
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        lbl_icon = QLabel("🌐", self.card)
        lbl_icon.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        header_layout.addWidget(lbl_icon)

        lbl_title = QLabel("TŁUMACZ GEMINI", self.card)
        lbl_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px; background: transparent; border: none;")
        header_layout.addWidget(lbl_title)

        header_layout.addStretch()

        # Wybór języka źródłowego i docelowego
        self.combo_source = QComboBox(self.card)
        self.combo_target = QComboBox(self.card)
        
        combo_style = """
            QComboBox {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: 600;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #0F172A;
                color: #F8FAFC;
                selection-background-color: #2563EB;
            }
        """
        self.combo_source.setStyleSheet(combo_style)
        self.combo_target.setStyleSheet(combo_style)

        for code, name in SUPPORTED_LANGUAGES.items():
            self.combo_source.addItem(name, code)
            if code != "auto":
                self.combo_target.addItem(name, code)

        self.combo_source.setCurrentText("Automatyczny")
        self.combo_target.setCurrentText("Angielski")

        header_layout.addWidget(self.combo_source)
        lbl_arrow = QLabel("➔", self.card)
        lbl_arrow.setStyleSheet("color: #64748B; background: transparent; border: none;")
        header_layout.addWidget(lbl_arrow)
        header_layout.addWidget(self.combo_target)

        card_layout.addLayout(header_layout)

        # 2. Pole tekstu źródłowego
        self.txt_source = QTextEdit(self.card)
        self.txt_source.setPlaceholderText("Wpisz lub zaznacz tekst do przetłumaczenia...")
        self.txt_source.setFixedHeight(95)
        self.txt_source.setStyleSheet("""
            QTextEdit {
                background-color: #0F172A;
                color: #F1F5F9;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px;
                font-size: 11px;
            }
            QTextEdit:focus {
                border: 1px solid #38BDF8;
            }
        """)
        card_layout.addWidget(self.txt_source)

        # 3. Pasek akcji tłumaczenia i status
        mid_layout = QHBoxLayout()
        self.btn_translate = QPushButton("Przetłumacz (Ctrl+Enter)", self.card)
        self.btn_translate.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_translate.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
                padding: 5px 12px;
            }
            QPushButton:hover { background-color: #3B82F6; }
            QPushButton:pressed { background-color: #1D4ED8; }
            QPushButton:disabled { background-color: #334155; color: #64748B; }
        """)
        self.btn_translate.clicked.connect(self._start_translation)
        mid_layout.addWidget(self.btn_translate)

        self.lbl_status = QLabel("", self.card)
        self.lbl_status.setStyleSheet("font-size: 10px; color: #94A3B8; background: transparent; border: none;")
        mid_layout.addWidget(self.lbl_status)
        mid_layout.addStretch()

        card_layout.addLayout(mid_layout)

        # 4. Pasek postępu (ukryty domyślnie)
        self.progress_bar = QProgressBar(self.card)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { background-color: #1E293B; border: none; } QProgressBar::chunk { background-color: #38BDF8; }")
        self.progress_bar.hide()
        card_layout.addWidget(self.progress_bar)

        # 5. Pole wyniku tłumaczenia
        self.txt_target = QTextEdit(self.card)
        self.txt_target.setPlaceholderText("Wynik tłumaczenia...")
        self.txt_target.setFixedHeight(115)
        self.txt_target.setStyleSheet("""
            QTextEdit {
                background-color: #0F172A;
                color: #38BDF8;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px;
                font-size: 11px;
                font-weight: 500;
            }
            QTextEdit:focus {
                border: 1px solid #60A5FA;
            }
        """)
        card_layout.addWidget(self.txt_target)

        # 6. Przyciski akcji docelowych
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        btn_style = """
            QPushButton {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 600;
                padding: 5px 8px;
            }
            QPushButton:hover { background-color: #334155; border: 1px solid #38BDF8; }
            QPushButton:pressed { background-color: #0F172A; }
        """

        self.btn_copy = QPushButton("Kopiuj wynik", self.card)
        self.btn_copy.setStyleSheet(btn_style)
        self.btn_copy.clicked.connect(self._on_copy_clicked)
        actions_layout.addWidget(self.btn_copy)

        self.btn_paste = QPushButton("Wklej do okna", self.card)
        self.btn_paste.setStyleSheet(btn_style)
        self.btn_paste.clicked.connect(self._on_paste_clicked)
        actions_layout.addWidget(self.btn_paste)

        self.btn_paste_enter = QPushButton("Wklej + Enter", self.card)
        self.btn_paste_enter.setStyleSheet(btn_style)
        self.btn_paste_enter.clicked.connect(self._on_paste_enter_clicked)
        actions_layout.addWidget(self.btn_paste_enter)

        actions_layout.addStretch()

        lbl_esc = QLabel("Esc: Zamknij", self.card)
        lbl_esc.setStyleSheet("font-size: 9px; color: #64748B; background: transparent; border: none;")
        actions_layout.addWidget(lbl_esc)

        card_layout.addLayout(actions_layout)
        main_layout.addWidget(self.card)

    def set_source_text(self, text: str, auto_translate: bool = True):
        """Ustawia tekst wejściowy i opcjonalnie od razu wyzwala tłumaczenie."""
        self.txt_source.setPlainText(text)
        self.txt_target.clear()
        self.lbl_status.setText("")

        if text.strip() and auto_translate:
            self._start_translation()
        elif not text.strip():
            self.lbl_status.setText("Brak zaznaczonego tekstu. Wpisz tekst ręcznie.")

    def _start_translation(self):
        text = self.txt_source.toPlainText().strip()
        if not text:
            self.lbl_status.setText("Wpisz tekst do przetłumaczenia.")
            return

        if not self.translation_service:
            self.lbl_status.setText("Błąd: Usługa tłumaczenia nie jest podłączona.")
            return

        # Anulowanie poprzedniego workera jeśli trwał
        self._cancel_current_worker()

        src_code = self.combo_source.currentData()
        tgt_code = self.combo_target.currentData()

        self.btn_translate.setEnabled(False)
        self.progress_bar.show()
        self.lbl_status.setText("Tłumaczenie przez Gemini...")
        self.lbl_status.setStyleSheet("font-size: 10px; color: #38BDF8; background: transparent; border: none;")

        self.current_worker = TranslationWorker(
            service=self.translation_service,
            text=text,
            source_lang=src_code,
            target_lang=tgt_code,
            parent=self
        )
        self.current_worker.finished_success.connect(self._on_translation_success)
        self.current_worker.finished_error.connect(self._on_translation_error)
        self.current_worker.start()

    def _on_translation_success(self, result: str):
        self.progress_bar.hide()
        self.btn_translate.setEnabled(True)
        self.txt_target.setPlainText(result)
        self.lbl_status.setText("Gotowe.")
        self.lbl_status.setStyleSheet("font-size: 10px; color: #10B981; background: transparent; border: none;")

    def _on_translation_error(self, message: str, error_code: str):
        self.progress_bar.hide()
        self.btn_translate.setEnabled(True)
        self.lbl_status.setText(f"Błąd ({error_code}): {message}")
        self.lbl_status.setStyleSheet("font-size: 10px; color: #EF4444; background: transparent; border: none;")

    def _on_copy_clicked(self):
        text = self.txt_target.toPlainText()
        if text:
            self.copy_requested.emit(text)

    def _on_paste_clicked(self):
        text = self.txt_target.toPlainText()
        if text:
            self.paste_requested.emit(text)
            self.hide()

    def _on_paste_enter_clicked(self):
        text = self.txt_target.toPlainText()
        if text:
            self.paste_enter_requested.emit(text)
            self.hide()

    def _cancel_current_worker(self):
        """Bezpiecznie anuluje bieżący wątek (bez terminate)."""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker = None

    def show_at_cursor(self, target_pos: Optional[QPoint] = None):
        """Wyświetla okno pod kursorem z zabezpieczeniem przed ucinaniem ekranu."""
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

    def closeEvent(self, event):
        self._cancel_current_worker()
        super().closeEvent(event)

    def hideEvent(self, event):
        self._cancel_current_worker()
        super().hideEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() & Qt.ControlModifier:
            self._start_translation()
            event.accept()
        else:
            super().keyPressEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow():
                # Przy utracie fokusu nie zamykamy natychmiast, jeśli użytkownik zaznacza tekst,
                # ale można ukryć jeśli kliknięto poza
                pass
        super().changeEvent(event)
