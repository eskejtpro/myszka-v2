"""Podręczne okno podglądu i akcji dla wyniku OCR (MyszkaHUD v0.4).

Zgodne ze stylistyką MyszkaHUD v0.3.1 (Dark Navy, subtelny błękitny akcent, zaokrąglenia 12px, brak ciężkiego blura).
Pozwala użytkownikowi na:
- edycję rozpoznanego tekstu w edytorze,
- Kopiuj do schowka,
- Wklej do poprzedniego aktywnego okna,
- Wklej + Enter,
- Tłumacz (przekazanie do istniejącego TranslationService / TranslationWindow),
- Ponów OCR (w razie błędu sieci/API z zachowanym zrzutem ekranu),
- Wskaźnik statusu z czytelnym raportowaniem błędów.
"""

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QPushButton, QGraphicsDropShadowEffect, QProgressBar
    )
    from PySide6.QtCore import Qt, Signal, QEvent, QPoint
    from PySide6.QtGui import QColor, QCursor, QGuiApplication
except ImportError:
    QWidget = object
    QPoint = object
    Signal = lambda *args: None

from myszkahud.services.ocr.service import OCRService
from myszkahud.ui.ocr.worker import OCRWorker


class OCRResultWindow(QWidget):
    """
    Okno podglądu wyniku OCR z możliwością edycji i akcjami systemowymi.
    """

    copy_requested = Signal(str)
    paste_requested = Signal(str)
    paste_enter_requested = Signal(str)
    translate_requested = Signal(str)
    retry_requested = Signal()

    def __init__(self, ocr_service: Optional[OCRService] = None, parent=None):
        if QWidget is object:
            return
        super().__init__(parent)
        self.ocr_service = ocr_service
        self.current_worker: Optional[OCRWorker] = None
        self._last_image_bytes: Optional[bytes] = None
        self._last_mime_type: str = "image/png"

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(500, 370)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        self.card = QWidget(self)
        self.card.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 15, 29, 0.96);
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

        # 1. Pasek tytułu i statusu
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        lbl_icon = QLabel("🔍", self.card)
        lbl_icon.setStyleSheet("font-size: 13px; background: transparent; border: none;")
        header_layout.addWidget(lbl_icon)

        lbl_title = QLabel("ROZPOZNANY TEKST (OCR)", self.card)
        lbl_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px; background: transparent; border: none;")
        header_layout.addWidget(lbl_title)

        header_layout.addStretch()

        self.lbl_status = QLabel("Gotowy", self.card)
        self.lbl_status.setStyleSheet("font-size: 10px; color: #94A3B8; background: transparent; border: none;")
        header_layout.addWidget(self.lbl_status)

        card_layout.addLayout(header_layout)

        # 2. Pasek postępu
        self.progress_bar = QProgressBar(self.card)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #38BDF8;
            }
        """)
        self.progress_bar.hide()
        card_layout.addWidget(self.progress_bar)

        # 3. Pole edycji tekstu rozpoznanego
        self.txt_result = QTextEdit(self.card)
        self.txt_result.setPlaceholderText("Trwa przetwarzanie wycinka ekranu...")
        self.txt_result.setStyleSheet("""
            QTextEdit {
                background-color: #0E1626;
                color: #F8FAFC;
                border: 1px solid rgba(51, 65, 85, 0.7);
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: 1px solid #38BDF8;
            }
        """)
        card_layout.addWidget(self.txt_result)

        # 4. Pasek przycisków akcji
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
            QPushButton:disabled { background-color: #1E293B; color: #64748B; border-color: #1E293B; }
        """

        self.btn_copy = QPushButton("Kopiuj", self.card)
        self.btn_copy.setStyleSheet(btn_style)
        self.btn_copy.clicked.connect(self._on_copy_clicked)
        actions_layout.addWidget(self.btn_copy)

        self.btn_paste = QPushButton("Wklej", self.card)
        self.btn_paste.setStyleSheet(btn_style)
        self.btn_paste.clicked.connect(self._on_paste_clicked)
        actions_layout.addWidget(self.btn_paste)

        self.btn_paste_enter = QPushButton("Wklej + Enter", self.card)
        self.btn_paste_enter.setStyleSheet(btn_style)
        self.btn_paste_enter.clicked.connect(self._on_paste_enter_clicked)
        actions_layout.addWidget(self.btn_paste_enter)

        # Przycisk "Tłumacz" ze specjalnym wyróżnieniem (akcent #2DD4BF / #2563EB)
        self.btn_translate = QPushButton("🌐 Tłumacz", self.card)
        self.btn_translate.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 700;
                padding: 5px 10px;
            }
            QPushButton:hover { background-color: #3B82F6; }
            QPushButton:pressed { background-color: #1D4ED8; }
            QPushButton:disabled { background-color: #334155; color: #64748B; }
        """)
        self.btn_translate.clicked.connect(self._on_translate_clicked)
        actions_layout.addWidget(self.btn_translate)

        # Przycisk "Ponów OCR" (ukryty domyślnie, widoczny przy błędzie lub na życzenie)
        self.btn_retry = QPushButton("Ponów", self.card)
        self.btn_retry.setStyleSheet(btn_style)
        self.btn_retry.clicked.connect(self._on_retry_clicked)
        self.btn_retry.hide()
        actions_layout.addWidget(self.btn_retry)

        actions_layout.addStretch()

        lbl_esc = QLabel("Esc: Zamknij", self.card)
        lbl_esc.setStyleSheet("font-size: 9px; color: #64748B; background: transparent; border: none;")
        actions_layout.addWidget(lbl_esc)

        card_layout.addLayout(actions_layout)
        main_layout.addWidget(self.card)

    def start_ocr(self, image_bytes: bytes, mime_type: str = "image/png"):
        """Uruchamia asynchroniczny proces rozpoznawania tekstu z przekazanego obrazu."""
        if not image_bytes:
            self.lbl_status.setText("Brak danych obrazu.")
            return

        if not self.ocr_service:
            self.lbl_status.setText("Błąd: Usługa OCR nie jest skonfigurowana.")
            return

        self._last_image_bytes = image_bytes
        self._last_mime_type = mime_type
        self._cancel_current_worker()

        self.btn_retry.hide()
        self.txt_result.clear()
        self.txt_result.setPlaceholderText("Trwa analiza obrazu przez Gemini Vision OCR...")
        self.progress_bar.show()
        self.lbl_status.setText("Analiza obrazu...")
        self.lbl_status.setStyleSheet("font-size: 10px; color: #38BDF8; background: transparent; border: none;")

        self._set_buttons_enabled(False)

        self.current_worker = OCRWorker(
            service=self.ocr_service,
            image_bytes=image_bytes,
            mime_type=mime_type,
            parent=self
        )
        self.current_worker.finished_success.connect(self._on_ocr_success)
        self.current_worker.finished_error.connect(self._on_ocr_error)
        self.current_worker.start()

    def set_text(self, text: str):
        """Ręczne ustawienie tekstu w polu wyników."""
        self.progress_bar.hide()
        self.txt_result.setPlainText(text)
        self.lbl_status.setText("Gotowe.")
        self.lbl_status.setStyleSheet("font-size: 10px; color: #10B981; background: transparent; border: none;")
        self._set_buttons_enabled(True)

    def _set_buttons_enabled(self, enabled: bool):
        self.btn_copy.setEnabled(enabled)
        self.btn_paste.setEnabled(enabled)
        self.btn_paste_enter.setEnabled(enabled)
        self.btn_translate.setEnabled(enabled)

    def _on_ocr_success(self, text: str):
        self.progress_bar.hide()
        self._set_buttons_enabled(True)
        self.btn_retry.hide()
        self.txt_result.setPlainText(text)
        if text.strip():
            self.lbl_status.setText("Rozpoznano pomyślnie.")
            self.lbl_status.setStyleSheet("font-size: 10px; color: #10B981; background: transparent; border: none;")
        else:
            self.lbl_status.setText("Nie wykryto tekstu na zaznaczonym obszarze.")
            self.lbl_status.setStyleSheet("font-size: 10px; color: #F59E0B; background: transparent; border: none;")

    def _on_ocr_error(self, message: str, error_code: str):
        self.progress_bar.hide()
        self._set_buttons_enabled(True)
        self.btn_retry.show()
        self.lbl_status.setText(f"Błąd ({error_code}): {message}")
        self.lbl_status.setStyleSheet("font-size: 10px; color: #EF4444; background: transparent; border: none;")

    def _on_copy_clicked(self):
        text = self.txt_result.toPlainText()
        if text:
            self.copy_requested.emit(text)

    def _on_paste_clicked(self):
        text = self.txt_result.toPlainText()
        if text:
            self.paste_requested.emit(text)
            self.hide()

    def _on_paste_enter_clicked(self):
        text = self.txt_result.toPlainText()
        if text:
            self.paste_enter_requested.emit(text)
            self.hide()

    def _on_translate_clicked(self):
        text = self.txt_result.toPlainText()
        if text:
            self.translate_requested.emit(text)
            self.hide()

    def _on_retry_clicked(self):
        if self._last_image_bytes:
            self.start_ocr(self._last_image_bytes, self._last_mime_type)
            self.retry_requested.emit()

    def _cancel_current_worker(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker = None

    def show_at_cursor(self, target_pos: Optional[QPoint] = None):
        """Wyświetla okno pod kursorem z ochroną przed wyjściem poza ekran."""
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
        else:
            super().keyPressEvent(event)
