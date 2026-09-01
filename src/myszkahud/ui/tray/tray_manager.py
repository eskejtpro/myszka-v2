"""Menedżer zasobnika systemowego Windows (QSystemTrayIcon v0.10) dla MyszkaHUD."""

import logging
from typing import Optional, Callable

try:
    from PySide6.QtWidgets import (
        QSystemTrayIcon,
        QMenu,
        QApplication,
        QWidget,
    )
    from PySide6.QtGui import QIcon, QAction, QPixmap, QColor, QPainter
    from PySide6.QtCore import QObject, Signal
except ImportError:
    class MockSignal:
        def connect(self, *args):
            pass
        def emit(self, *args):
            pass

    class MockAction:
        def __init__(self, text="", parent=None):
            self.text = text
            self.triggered = MockSignal()
            self.toggled = MockSignal()
            self._checked = False
        def setCheckable(self, val):
            pass
        def setChecked(self, val):
            self._checked = val
        def isChecked(self):
            return self._checked

    class MockMenu:
        def __init__(self, *args, **kwargs):
            self.actions = []
        def addAction(self, text_or_action, *args):
            if isinstance(text_or_action, str):
                act = MockAction(text_or_action)
                self.actions.append(act)
                return act
            self.actions.append(text_or_action)
            return text_or_action
        def addSeparator(self):
            pass

    class MockTrayIcon:
        Information = 1
        Warning = 2
        Critical = 3
        Trigger = 1
        DoubleClick = 2
        def __init__(self, *args, **kwargs):
            self.activated = MockSignal()
            self.messageClicked = MockSignal()
        def setContextMenu(self, menu):
            self.menu = menu
        def setIcon(self, icon):
            pass
        def setToolTip(self, tip):
            self.tooltip = tip
        def show(self):
            pass
        def hide(self):
            pass
        def isVisible(self):
            return True
        def showMessage(self, title, msg, icon=1, msecs=5000):
            pass

    class MockHelper:
        def __init__(self, *args, **kwargs):
            pass
        def __getattr__(self, name):
            def _dummy(*args, **kwargs):
                return None
            return _dummy

    QObject = MockHelper
    Signal = lambda *args: MockSignal()
    QSystemTrayIcon = MockTrayIcon
    QMenu = MockMenu
    QAction = MockAction
    QIcon = MockHelper
    QPixmap = MockHelper
    QColor = MockHelper
    QPainter = MockHelper
    QWidget = MockHelper
    QApplication = MockHelper

from myszkahud.services.autostart.autostart_service import AutostartService

logger = logging.getLogger(__name__)


class TrayManager(QObject):
    """Zarządza ikoną w zasobniku systemowym (Windows Tray) i powiązanymi akcjami."""

    open_hud_requested = Signal()
    open_clipboard_requested = Signal()
    open_processes_requested = Signal()
    open_ram_requested = Signal()
    open_settings_requested = Signal()
    exit_requested = Signal()

    def __init__(
        self,
        autostart_service: Optional[AutostartService] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.autostart_service = autostart_service or AutostartService()
        self._init_tray()

    def _create_default_icon(self) -> QIcon:
        """Generuje programową ikonę zasobnika w kolorze Sky Blue."""
        try:
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pixmap)
            painter.setBrush(QColor("#0284C7"))
            painter.setPen(QColor("#38BDF8"))
            painter.drawEllipse(4, 4, 24, 24)
            painter.end()
            return QIcon(pixmap)
        except Exception:
            return QIcon()

    def _init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self._create_default_icon())
        self.tray_icon.setToolTip("MyszkaHUD (v0.10) — Aktywny pod kursor (Alt+Q)")

        # Tworzenie menu kontekstowego
        self.menu = QMenu()

        # 1. Główne akcje okien
        self.act_hud = self.menu.addAction("Otwórz MyszkaHUD (Alt+Q)")
        self.act_hud.triggered.connect(self.open_hud_requested.emit)

        self.act_clip = self.menu.addAction("Historia Schowka & Notes (Alt+V)")
        self.act_clip.triggered.connect(self.open_clipboard_requested.emit)

        self.act_proc = self.menu.addAction("Menedżer Procesów")
        self.act_proc.triggered.connect(self.open_processes_requested.emit)

        self.act_ram = self.menu.addAction("Monitor RAM & Zwalnianie")
        self.act_ram.triggered.connect(self.open_ram_requested.emit)

        self.menu.addSeparator()

        # 2. Ustawienia i Autostart
        self.act_settings = self.menu.addAction("Centrum Ustawień...")
        self.act_settings.triggered.connect(self.open_settings_requested.emit)

        self.act_autostart = QAction("Uruchamiaj z Windows", self)
        self.act_autostart.setCheckable(True)
        self.act_autostart.setChecked(self.autostart_service.is_autostart_enabled())
        self.act_autostart.triggered.connect(self._toggle_autostart)
        self.menu.addAction(self.act_autostart)

        self.menu.addSeparator()

        # 3. Wyjście
        self.act_exit = self.menu.addAction("Zakończ MyszkaHUD")
        self.act_exit.triggered.connect(self.exit_requested.emit)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

    def show(self):
        """Wyświetla ikonę w zasobniku systemowym."""
        self.tray_icon.show()

    def hide(self):
        """Ukrywa ikonę w zasobniku systemowym."""
        self.tray_icon.hide()

    def show_notification(self, title: str, message: str, is_warning: bool = False):
        """Wyświetla powiadomienie dymkowe w zasobniku Windows."""
        try:
            icon_type = (
                QSystemTrayIcon.Warning if is_warning else QSystemTrayIcon.Information
            )
            self.tray_icon.showMessage(title, message, icon_type, 3000)
        except Exception as e:
            logger.debug(f"Powiadomienie tray: {e}")

    def _toggle_autostart(self):
        is_on = self.autostart_service.toggle_autostart()
        self.act_autostart.setChecked(is_on)
        state_str = "włączony" if is_on else "wyłączony"
        self.show_notification(
            "Autostart Windows",
            f"Autostart MyszkaHUD został {state_str}.",
        )

    def _on_tray_activated(self, reason):
        # Pojedynczy lub podwójny klik lewym przyciskiem myszy otwiera HUD
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.open_hud_requested.emit()
