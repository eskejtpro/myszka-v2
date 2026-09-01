"""Okno Monitora Pamięci RAM i Bezpiecznego Zwalniania (RamWindow) w PySide6."""

import logging
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QProgressBar,
        QFrame,
        QGraphicsDropShadowEffect,
    )
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QColor, QFont, QKeyEvent
except ImportError:
    class MockSignal:
        def connect(self, *args):
            pass
        def emit(self, *args):
            pass

    class MockWidget:
        def __init__(self, *args, **kwargs):
            self.clicked = MockSignal()
            self.timeout = MockSignal()
        def count(self):
            return 0
        def takeAt(self, *args):
            return None
        def __getattr__(self, name):
            if name in ("clicked", "timeout"):
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
    QPushButton = MockWidget
    QProgressBar = MockWidget
    QFrame = MockWidget
    QGraphicsDropShadowEffect = MockWidget
    QTimer = MockTimer
    Qt = MockQt
    QColor = MockHelper
    QFont = MockHelper
    QKeyEvent = MockHelper

from myszkahud.services.ram.ram_service import RamService

logger = logging.getLogger(__name__)


class RamWindow(QWidget):
    """Pływające okno monitoringu i bezpiecznego zwalniania pamięci RAM."""

    def __init__(self, ram_service: Optional[RamService] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.service = ram_service or RamService()

        self._init_ui()
        self._setup_auto_refresh()

    def _init_ui(self):
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(540, 440)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Główny kontener
        self.container = QFrame(self)
        self.container.setStyleSheet(
            "QFrame { background-color: #030712; border: 1.5px solid #6366F1; border-radius: 12px; }"
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 220))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 14, 16, 14)
        container_layout.setSpacing(12)

        # 1. Nagłówek
        header_layout = QHBoxLayout()
        header_title = QLabel("MONITOR PAMIĘCI RAM (v0.8)")
        header_title.setStyleSheet("color: #818CF8; font-weight: 900; font-size: 13px; letter-spacing: 1px;")
        header_layout.addWidget(header_title)

        header_layout.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 26)
        btn_close.setStyleSheet(
            "background-color: transparent; color: #94A3B8; font-weight: bold; font-size: 14px; border: none;"
        )
        btn_close.clicked.connect(self.hide)
        header_layout.addWidget(btn_close)

        container_layout.addLayout(header_layout)

        # 2. Główny wskaźnik zużycia RAM
        gauge_box = QFrame()
        gauge_box.setStyleSheet("background-color: #0B1120; border: 1px solid #1E293B; border-radius: 8px; padding: 10px;")
        gauge_layout = QVBoxLayout(gauge_box)

        gauge_header = QHBoxLayout()
        self.lbl_usage_percent = QLabel("Zużycie: 0%")
        self.lbl_usage_percent.setStyleSheet("color: #F8FAFC; font-weight: bold; font-size: 15px;")
        gauge_header.addWidget(self.lbl_usage_percent)

        gauge_header.addStretch()

        self.lbl_usage_bytes = QLabel("0.0 GB / 0.0 GB")
        self.lbl_usage_bytes.setStyleSheet("color: #818CF8; font-weight: bold; font-size: 12px; font-family: monospace;")
        gauge_header.addWidget(self.lbl_usage_bytes)

        gauge_layout.addLayout(gauge_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(50)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #030712; border-radius: 6px; } "
            "QProgressBar::chunk { background-color: #6366F1; border-radius: 6px; }"
        )
        gauge_layout.addWidget(self.progress_bar)

        container_layout.addWidget(gauge_box)

        # 3. Sekcja Top Procesów RAM
        top_title = QLabel("TOP PROCESY WG RAM")
        top_title.setStyleSheet("color: #64748B; font-weight: bold; font-size: 10px; letter-spacing: 0.5px;")
        container_layout.addWidget(top_title)

        self.top_list_box = QFrame()
        self.top_list_box.setStyleSheet("background-color: #0B1120; border: 1px solid #1E293B; border-radius: 8px; padding: 6px;")
        self.top_list_layout = QVBoxLayout(self.top_list_box)
        self.top_list_layout.setSpacing(4)

        self.lbl_top_empty = QLabel("Brak danych o procesach")
        self.lbl_top_empty.setStyleSheet("color: #475569; font-size: 10px;")
        self.top_list_layout.addWidget(self.lbl_top_empty)

        container_layout.addWidget(self.top_list_box, stretch=1)

        # 4. Sekcja Akcji: Bezpieczne Zwolnienie RAM
        action_box = QHBoxLayout()

        self.btn_release = QPushButton("Zwolnij pamięć (Bezpieczne)")
        self.btn_release.setFixedHeight(34)
        self.btn_release.setStyleSheet(
            "background-color: #4F46E5; color: white; font-weight: bold; font-size: 11px; "
            "border: none; border-radius: 6px; padding: 0 16px;"
        )
        self.btn_release.clicked.connect(self._handle_release_memory)
        action_box.addWidget(self.btn_release)

        self.lbl_release_status = QLabel("Gotowy do optymalizacji")
        self.lbl_release_status.setStyleSheet("color: #94A3B8; font-size: 10px;")
        action_box.addWidget(self.lbl_release_status)

        action_box.addStretch()

        container_layout.addLayout(action_box)

        # 5. Stopka
        footer_layout = QHBoxLayout()
        safe_badge = QLabel("Zabezpieczenie: Bez zamykania programów | Realny pomiar")
        safe_badge.setStyleSheet("color: #475569; font-size: 9px; font-family: monospace;")
        footer_layout.addWidget(safe_badge)

        footer_layout.addStretch()

        esc_label = QLabel("Esc: Zamknij")
        esc_label.setStyleSheet("color: #475569; font-size: 9px;")
        footer_layout.addWidget(esc_label)

        container_layout.addLayout(footer_layout)
        main_layout.addWidget(self.container)

    def _setup_auto_refresh(self):
        self._timer = QTimer(self)
        self._timer.setInterval(2000)  # Odświeżanie co 2 sekundy
        self._timer.timeout.connect(self.refresh_stats)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_stats()
        self._timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def refresh_stats(self):
        stats = self.service.get_stats()
        self.lbl_usage_percent.setText(f"Zużycie: {stats.percent}%")
        self.lbl_usage_bytes.setText(f"{stats.used_gb} GB / {stats.total_gb} GB")
        self.progress_bar.setValue(int(stats.percent))

        # Zaktualizuj Top procesy
        while self.top_list_layout.count() > 0:
            it = self.top_list_layout.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        if not stats.top_processes:
            lbl = QLabel("Brak danych o procesach")
            lbl.setStyleSheet("color: #475569; font-size: 10px;")
            self.top_list_layout.addWidget(lbl)
        else:
            for p in stats.top_processes[:5]:
                row = QHBoxLayout()
                name_lbl = QLabel(p.display_name)
                name_lbl.setStyleSheet("color: #E2E8F0; font-size: 11px; font-weight: bold;")
                row.addWidget(name_lbl)

                row.addStretch()

                ram_lbl = QLabel(f"{p.ram_mb} MB")
                ram_lbl.setStyleSheet("color: #818CF8; font-size: 11px; font-family: monospace;")
                row.addWidget(ram_lbl)

                w_row = QWidget()
                w_row.setLayout(row)
                self.top_list_layout.addWidget(w_row)

    def _handle_release_memory(self):
        self.lbl_release_status.setText("Zwalnianie pamięci...")
        result = self.service.release_memory_safe()
        self.refresh_stats()
        self.lbl_release_status.setText(
            f"Odzyskano: {result.released_mb} MB (procesy: {result.trimmed_processes_count})"
        )
