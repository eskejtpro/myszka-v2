"""Okno Menedżera Procesów i Aktywnych Aplikacji (ProcessWindow) w PySide6."""

import logging
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QScrollArea,
        QFrame,
        QMessageBox,
        QGraphicsDropShadowEffect,
    )
    from PySide6.QtCore import Qt, QTimer, QPoint, Signal
    from PySide6.QtGui import QColor, QCursor, QGuiApplication, QKeyEvent
except ImportError:
    class MockSignal:
        def connect(self, *args):
            pass
        def emit(self, *args):
            pass

    class MockWidget:
        def __init__(self, *args, **kwargs):
            self.clicked = MockSignal()
            self.textChanged = MockSignal()
            self.timeout = MockSignal()
        def count(self):
            return 0
        def takeAt(self, *args):
            return None
        def __getattr__(self, name):
            if name in ("clicked", "textChanged", "timeout"):
                return MockSignal()
            def _dummy(*args, **kwargs):
                return None
            return _dummy

    class MockTimer:
        def __init__(self, *args, **kwargs):
            self.timeout = MockSignal()
        def setInterval(self, *args):
            pass
        def start(self, *args):
            pass
        def stop(self):
            pass

    class MockQt:
        Window = 0x00000001
        FramelessWindowHint = 0x00000800
        WindowStaysOnTopHint = 0x00040000
        Tool = 0x00000008
        WA_TranslucentBackground = 120
        Key_Escape = 0x01000000
        AlignCenter = 0x0004

    class MockHelper:
        def __init__(self, *args, **kwargs):
            pass
        def __getattr__(self, name):
            def _dummy(*args, **kwargs):
                return None
            return _dummy

    Signal = lambda *args: MockSignal()
    QWidget = MockWidget
    QVBoxLayout = MockWidget
    QHBoxLayout = MockWidget
    QLabel = MockWidget
    QLineEdit = MockWidget
    QPushButton = MockWidget
    QScrollArea = MockWidget
    QFrame = MockWidget
    QMessageBox = MockWidget
    QGraphicsDropShadowEffect = MockWidget
    QTimer = MockTimer
    Qt = MockQt
    QPoint = MockHelper
    QColor = MockHelper
    QCursor = MockHelper
    QGuiApplication = MockHelper
    QKeyEvent = MockHelper

from myszkahud.services.process.process_service import ProcessService
from myszkahud.ui.process.process_item_card import ProcessItemCard

logger = logging.getLogger(__name__)


class ProcessWindow(QWidget):
    """Pływające okno zarządzania procesami i aktywnymi aplikacjami."""

    def __init__(self, process_service: Optional[ProcessService] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.service = process_service or ProcessService()
        self._filter_only_windows = False
        self._sort_by = "ram"
        self._search_text = ""

        self._init_ui()
        self._setup_auto_refresh()

    def _init_ui(self):
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(760, 520)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Główny kontener
        self.container = QFrame(self)
        self.container.setStyleSheet(
            "QFrame { background-color: #030712; border: 1.5px solid #0284C7; border-radius: 12px; }"
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 220))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 14, 16, 14)
        container_layout.setSpacing(10)

        # 1. Nagłówek
        header_layout = QHBoxLayout()
        header_title = QLabel("AKTYWNE APLIKACJE & PROCESY")
        header_title.setStyleSheet("color: #38BDF8; font-weight: 900; font-size: 13px; letter-spacing: 1px;")
        header_layout.addWidget(header_title)

        header_layout.addStretch()

        self.btn_refresh = QPushButton("Odśwież")
        self.btn_refresh.setFixedHeight(26)
        self.btn_refresh.setStyleSheet(
            "background-color: #0F172A; color: #38BDF8; border: 1px solid #0284C7; "
            "border-radius: 4px; font-size: 10px; font-weight: bold; padding: 2px 10px;"
        )
        self.btn_refresh.clicked.connect(self.refresh_list)
        header_layout.addWidget(self.btn_refresh)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 26)
        btn_close.setStyleSheet(
            "background-color: transparent; color: #94A3B8; font-weight: bold; font-size: 14px; border: none;"
        )
        btn_close.clicked.connect(self.hide)
        header_layout.addWidget(btn_close)

        container_layout.addLayout(header_layout)

        # 2. Pasek filtrów i wyszukiwarka
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Szukaj procesu po nazwie, PID lub tytule okna...")
        self.search_input.setFixedHeight(30)
        self.search_input.setStyleSheet(
            "QLineEdit { background-color: #0B1120; border: 1px solid #1E293B; border-radius: 6px; "
            "color: #F8FAFC; padding: 0 10px; font-size: 11px; } "
            "QLineEdit:focus { border: 1px solid #38BDF8; }"
        )
        self.search_input.textChanged.connect(self._on_search_changed)
        controls_layout.addWidget(self.search_input, stretch=3)

        self.btn_filter_all = QPushButton("Wszystkie")
        self.btn_filter_all.setFixedHeight(30)
        self.btn_filter_all.clicked.connect(lambda: self._set_window_filter(False))
        controls_layout.addWidget(self.btn_filter_all)

        self.btn_filter_windows = QPushButton("Tylko Okna")
        self.btn_filter_windows.setFixedHeight(30)
        self.btn_filter_windows.clicked.connect(lambda: self._set_window_filter(True))
        controls_layout.addWidget(self.btn_filter_windows)

        container_layout.addLayout(controls_layout)

        # 3. Lista procesów w ScrollArea
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(
            "QScrollArea { border: 1px solid #1E293B; border-radius: 8px; background-color: #050B14; } "
            "QScrollBar:vertical { background: #030712; width: 6px; } "
            "QScrollBar::handle:vertical { background: #1E293B; border-radius: 3px; }"
        )

        self.scroll_content = QWidget()
        self.list_layout = QVBoxLayout(self.scroll_content)
        self.list_layout.setContentsMargins(8, 8, 8, 8)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()

        self.scroll.setWidget(self.scroll_content)
        container_layout.addWidget(self.scroll, stretch=1)

        # 4. Stopka
        footer_layout = QHBoxLayout()
        self.stats_label = QLabel("Ładowanie procesów...")
        self.stats_label.setStyleSheet("color: #64748B; font-size: 10px; font-family: monospace;")
        footer_layout.addWidget(self.stats_label)

        footer_layout.addStretch()

        esc_label = QLabel("Esc: Zamknij")
        esc_label.setStyleSheet("color: #475569; font-size: 10px;")
        footer_layout.addWidget(esc_label)

        container_layout.addLayout(footer_layout)
        main_layout.addWidget(self.container)

        self._update_filter_button_styles()

    def _setup_auto_refresh(self):
        self._timer = QTimer(self)
        self._timer.setInterval(3000)  # Odświeżanie co 3 sekundy
        self._timer.timeout.connect(self.refresh_list)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_list()
        self._timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def _on_search_changed(self, text: str):
        self._search_text = text
        self.refresh_list()

    def _set_window_filter(self, only_windows: bool):
        self._filter_only_windows = only_windows
        self._update_filter_button_styles()
        self.refresh_list()

    def _update_filter_button_styles(self):
        active_style = (
            "background-color: #0284C7; color: white; font-weight: bold; "
            "border: none; border-radius: 6px; padding: 0 12px; font-size: 11px;"
        )
        inactive_style = (
            "background-color: #0B1120; color: #94A3B8; border: 1px solid #1E293B; "
            "border-radius: 6px; padding: 0 12px; font-size: 11px;"
        )
        if self._filter_only_windows:
            self.btn_filter_all.setStyleSheet(inactive_style)
            self.btn_filter_windows.setStyleSheet(active_style)
        else:
            self.btn_filter_all.setStyleSheet(active_style)
            self.btn_filter_windows.setStyleSheet(inactive_style)

    def refresh_list(self):
        procs = self.service.list_processes(
            search_query=self._search_text,
            only_with_windows=self._filter_only_windows,
            sort_by=self._sort_by,
        )

        # Wyczyść istniejące karty
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Dodaj nowe karty
        total_ram_mb = sum(p.ram_mb for p in procs)
        for p in procs:
            card = ProcessItemCard(p)
            card.activate_requested.connect(self._handle_activate)
            card.minimize_requested.connect(self._handle_minimize)
            card.close_requested.connect(self._handle_close)
            card.kill_requested.connect(self._handle_kill)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)

        self.stats_label.setText(
            f"Widoczne procesy: {len(procs)} | Łączny RAM: {round(total_ram_mb, 1)} MB"
        )

    def _handle_activate(self, pid: int):
        self.service.activate_window(pid)

    def _handle_minimize(self, pid: int):
        self.service.minimize_window(pid)

    def _handle_close(self, pid: int):
        self.service.close_process(pid)
        self.refresh_list()

    def _handle_kill(self, pid: int):
        reply = QMessageBox.question(
            self,
            "Wymuszenie zabicia procesu",
            f"Czy na pewno chcesz natychmiast ubić proces PID {pid}?\nNiezapisane dane zostaną utracone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.service.force_kill_process(pid)
            self.refresh_list()
