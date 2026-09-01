"""Karta pojedynczego procesu dla widoku Process Manager w PySide6."""

from typing import Optional, Callable

try:
    from PySide6.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QVBoxLayout,
        QLabel,
        QPushButton,
        QFrame,
        QMessageBox,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont, QColor
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
        def __getattr__(self, name):
            if name in ("clicked", "textChanged"):
                return MockSignal()
            def _dummy(*args, **kwargs):
                return None
            return _dummy

    Signal = lambda *args: MockSignal()
    QWidget = MockWidget
    QHBoxLayout = MockWidget
    QVBoxLayout = MockWidget
    QLabel = MockWidget
    QPushButton = MockWidget
    QFrame = MockWidget
    QMessageBox = MockWidget
    Qt = MockWidget
    QFont = MockWidget
    QColor = MockWidget

from myszkahud.services.process.models import ProcessInfo


class ProcessItemCard(QWidget):
    """Karta reprezentująca pojedynczy proces w menedżerze procesów."""

    activate_requested = Signal(int)  # PID
    minimize_requested = Signal(int)  # PID
    close_requested = Signal(int)     # PID
    kill_requested = Signal(int)      # PID

    def __init__(self, process_info: ProcessInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.proc = process_info
        self._init_ui()

    def _init_ui(self):
        self.setFixedHeight(54)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        # Lewa strona: Nazwa, Tytuł okna, PID
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        name_label = QLabel(self.proc.display_name)
        name_label.setStyleSheet("color: #F8FAFC; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(name_label)

        if self.proc.is_protected:
            prot_badge = QLabel("CHRONIONY" if not self.proc.is_current_app else "MYSZKAHUD")
            prot_badge.setStyleSheet(
                "background-color: #1E293B; color: #94A3B8; font-size: 9px; "
                "font-weight: bold; padding: 1px 4px; border-radius: 3px; border: 1px solid #334155;"
            )
            header_layout.addWidget(prot_badge)

        header_layout.addStretch()
        info_layout.addLayout(header_layout)

        sub_label = QLabel(f"PID: {self.proc.pid} | {self.proc.name}")
        sub_label.setStyleSheet("color: #64748B; font-size: 10px; font-family: monospace;")
        info_layout.addWidget(sub_label)

        layout.addLayout(info_layout, stretch=2)

        # Środek: RAM i CPU
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(2)
        ram_label = QLabel(f"{self.proc.ram_mb} MB")
        ram_label.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11px; font-family: monospace;")
        stats_layout.addWidget(ram_label)

        cpu_label = QLabel(f"CPU: {self.proc.cpu_percent:.1f}%")
        cpu_label.setStyleSheet("color: #94A3B8; font-size: 10px; font-family: monospace;")
        stats_layout.addWidget(cpu_label)

        layout.addLayout(stats_layout, stretch=1)

        # Prawa strona: Akcje
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        if self.proc.window_title:
            btn_act = QPushButton("Aktywuj")
            btn_act.setFixedHeight(26)
            btn_act.setStyleSheet(
                "background-color: #0F172A; color: #38BDF8; border: 1px solid #0284C7; "
                "border-radius: 4px; font-size: 10px; font-weight: bold; padding: 2px 8px;"
            )
            btn_act.clicked.connect(lambda: self.activate_requested.emit(self.proc.pid))
            actions_layout.addWidget(btn_act)

            btn_min = QPushButton("Min")
            btn_min.setFixedHeight(26)
            btn_min.setStyleSheet(
                "background-color: #0F172A; color: #94A3B8; border: 1px solid #334155; "
                "border-radius: 4px; font-size: 10px; padding: 2px 6px;"
            )
            btn_min.clicked.connect(lambda: self.minimize_requested.emit(self.proc.pid))
            actions_layout.addWidget(btn_min)

        if not self.proc.is_protected:
            btn_close = QPushButton("Zamknij")
            btn_close.setFixedHeight(26)
            btn_close.setStyleSheet(
                "background-color: #1E293B; color: #F1F5F9; border: 1px solid #475569; "
                "border-radius: 4px; font-size: 10px; padding: 2px 8px;"
            )
            btn_close.clicked.connect(lambda: self.close_requested.emit(self.proc.pid))
            actions_layout.addWidget(btn_close)

            btn_kill = QPushButton("Kill")
            btn_kill.setFixedHeight(26)
            btn_kill.setStyleSheet(
                "background-color: #450A0A; color: #FCA5A5; border: 1px solid #DC2626; "
                "border-radius: 4px; font-size: 10px; font-weight: bold; padding: 2px 8px;"
            )
            btn_kill.clicked.connect(self._on_kill_clicked)
            actions_layout.addWidget(btn_kill)

        layout.addLayout(actions_layout)

        # Styl tła karty
        self.setStyleSheet(
            "ProcessItemCard { background-color: #0B1120; border: 1px solid #1E293B; border-radius: 6px; } "
            "ProcessItemCard:hover { background-color: #0F172A; border-color: #0284C7; }"
        )

    def _on_kill_clicked(self):
        self.kill_requested.emit(self.proc.pid)
