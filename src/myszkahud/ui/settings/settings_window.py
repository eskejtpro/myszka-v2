"""Okno Centrum Ustawień (SettingsWindow v0.9) w PySide6."""

import logging
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QLineEdit,
        QCheckBox,
        QComboBox,
        QSpinBox,
        QDoubleSpinBox,
        QScrollArea,
        QFrame,
        QStackedWidget,
        QGraphicsDropShadowEffect,
        QMessageBox,
    )
    from PySide6.QtCore import Qt, Signal
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
            self.textChanged = MockSignal()
            self.currentTextChanged = MockSignal()
            self.toggled = MockSignal()
            self.valueChanged = MockSignal()
        def count(self):
            return 0
        def takeAt(self, *args):
            return None
        def __getattr__(self, name):
            if name in ("clicked", "textChanged", "currentTextChanged", "toggled", "valueChanged"):
                return MockSignal()
            def _dummy(*args, **kwargs):
                return None
            return _dummy

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
    QLineEdit = MockWidget
    QCheckBox = MockWidget
    QComboBox = MockWidget
    QSpinBox = MockWidget
    QDoubleSpinBox = MockWidget
    QScrollArea = MockWidget
    QFrame = MockWidget
    QStackedWidget = MockWidget
    QGraphicsDropShadowEffect = MockWidget
    QMessageBox = MockWidget
    Qt = MockQt
    QColor = MockHelper
    QFont = MockHelper
    QKeyEvent = MockHelper

from myszkahud.services.settings.settings_service import SettingsService
from myszkahud.services.settings.models import AppSettings

logger = logging.getLogger(__name__)


class SettingsWindow(QWidget):
    """Pływające okno Centrum Ustawień MyszkaHUD."""

    settings_saved = Signal(object)  # AppSettings

    def __init__(self, settings_service: Optional[SettingsService] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.service = settings_service or SettingsService()
        self.current_settings = self.service.current

        self._init_ui()
        self._load_values_into_ui()

    def _init_ui(self):
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(680, 500)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Główny kontener
        self.container = QFrame(self)
        self.container.setStyleSheet(
            "QFrame { background-color: #030712; border: 1.5px solid #38BDF8; border-radius: 12px; }"
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
        header_title = QLabel("CENTRUM USTAWIEŃ (v0.9)")
        header_title.setStyleSheet("color: #38BDF8; font-weight: 900; font-size: 13px; letter-spacing: 1px;")
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

        # 2. Główny podział (Sidebar + Strony)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(12)

        # Sidebar kategorii
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setSpacing(4)

        categories = [
            ("Skróty Klawiszowe", 0),
            ("Wygląd & HUD", 1),
            ("Mowa (STT)", 2),
            ("OCR (Vision)", 3),
            ("Schowek & Notes", 4),
            ("System & Bezpieczeństwo", 5),
            ("Monitor RAM", 6),
        ]
        self.cat_buttons = []
        for name, idx in categories:
            btn = QPushButton(name)
            btn.setFixedHeight(32)
            btn.setStyleSheet(
                "background-color: #0B1120; color: #94A3B8; border: 1px solid #1E293B; "
                "border-radius: 6px; text-align: left; padding-left: 10px; font-size: 11px;"
            )
            btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
            self.sidebar_layout.addWidget(btn)
            self.cat_buttons.append(btn)

        self.sidebar_layout.addStretch()
        body_layout.addLayout(self.sidebar_layout, stretch=1)

        # Strony ustawień w StackedWidget
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background-color: #0B1120; border: 1px solid #1E293B; border-radius: 8px; padding: 12px;")

        # Page 0: Skróty
        p0 = QWidget()
        l0 = QVBoxLayout(p0)
        l0.setSpacing(8)
        l0.addWidget(QLabel("Skrót wywołania HUD (Alt+Q):"))
        self.inp_hotkey_hud = QLineEdit("Alt+Q")
        l0.addWidget(self.inp_hotkey_hud)
        l0.addWidget(QLabel("Skrót otwarcia Schowka (Alt+V):"))
        self.inp_hotkey_clip = QLineEdit("Alt+V")
        l0.addWidget(self.inp_hotkey_clip)
        l0.addStretch()
        self.pages.addWidget(p0)

        # Page 1: HUD & Wygląd
        p1 = QWidget()
        l1 = QVBoxLayout(p1)
        l1.setSpacing(8)
        self.chk_hud_anim = QCheckBox("Włącz płynne animacje HUD")
        l1.addWidget(self.chk_hud_anim)
        self.chk_hud_autoclose = QCheckBox("Automatycznie zamykaj HUD po wybraniu akcji")
        l1.addWidget(self.chk_hud_autoclose)
        l1.addStretch()
        self.pages.addWidget(p1)

        # Page 2: Mowa STT
        p2 = QWidget()
        l2 = QVBoxLayout(p2)
        l2.setSpacing(8)
        l2.addWidget(QLabel("Język rozpoznawania mowy:"))
        self.cmb_speech_lang = QComboBox()
        self.cmb_speech_lang.addItems(["pl-PL", "en-US", "de-DE", "uk-UA"])
        l2.addWidget(self.cmb_speech_lang)
        self.chk_speech_paste = QCheckBox("Automatycznie wklejaj transkrypcję pod kursor")
        l2.addWidget(self.chk_speech_paste)
        l2.addStretch()
        self.pages.addWidget(p2)

        # Page 3: OCR
        p3 = QWidget()
        l3 = QVBoxLayout(p3)
        l3.setSpacing(8)
        l3.addWidget(QLabel("Główny silnik OCR:"))
        self.cmb_ocr_engine = QComboBox()
        self.cmb_ocr_engine.addItems(["gemini_vision", "windows_ocr"])
        l3.addWidget(self.cmb_ocr_engine)
        self.chk_ocr_copy = QCheckBox("Automatycznie kopiuj odczytany tekst do schowka")
        l3.addWidget(self.chk_ocr_copy)
        l3.addStretch()
        self.pages.addWidget(p3)

        # Page 4: Schowek
        p4 = QWidget()
        l4 = QVBoxLayout(p4)
        l4.setSpacing(8)
        self.chk_clip_enabled = QCheckBox("Włącz rejestrowanie historii schowka")
        l4.addWidget(self.chk_clip_enabled)
        l4.addWidget(QLabel("Limit historii (liczba wpisów):"))
        self.spn_clip_limit = QSpinBox()
        self.spn_clip_limit.setRange(20, 1000)
        self.spn_clip_limit.setValue(200)
        l4.addWidget(self.spn_clip_limit)
        l4.addStretch()
        self.pages.addWidget(p4)

        # Page 5: System
        p5 = QWidget()
        l5 = QVBoxLayout(p5)
        l5.setSpacing(8)
        self.chk_autostart = QCheckBox("Uruchamiaj MyszkaHUD przy starcie systemu Windows")
        l5.addWidget(self.chk_autostart)
        self.chk_protect_procs = QCheckBox("Chroń krytyczne procesy systemowe w Process Managerze")
        l5.addWidget(self.chk_protect_procs)
        l5.addStretch()
        self.pages.addWidget(p5)

        # Page 6: RAM
        p6 = QWidget()
        l6 = QVBoxLayout(p6)
        l6.setSpacing(8)
        l6.addWidget(QLabel("Interwał odświeżania statystyk RAM (ms):"))
        self.spn_ram_interval = QSpinBox()
        self.spn_ram_interval.setRange(500, 10000)
        self.spn_ram_interval.setValue(2000)
        l6.addWidget(self.spn_ram_interval)
        l6.addStretch()
        self.pages.addWidget(p6)

        body_layout.addWidget(self.pages, stretch=2)
        container_layout.addLayout(body_layout, stretch=1)

        # 3. Pasek przycisków dolnych (Zapisz / Przywróć domyślne)
        footer_layout = QHBoxLayout()
        btn_defaults = QPushButton("Przywróć domyślne")
        btn_defaults.setFixedHeight(30)
        btn_defaults.setStyleSheet(
            "background-color: #1E293B; color: #94A3B8; border: 1px solid #334155; "
            "border-radius: 6px; padding: 0 12px; font-size: 11px;"
        )
        btn_defaults.clicked.connect(self._handle_restore_defaults)
        footer_layout.addWidget(btn_defaults)

        footer_layout.addStretch()

        btn_save = QPushButton("Zapisz ustawienia")
        btn_save.setFixedHeight(30)
        btn_save.setStyleSheet(
            "background-color: #0284C7; color: white; font-weight: bold; border: none; "
            "border-radius: 6px; padding: 0 16px; font-size: 11px;"
        )
        btn_save.clicked.connect(self._handle_save)
        footer_layout.addWidget(btn_save)

        container_layout.addLayout(footer_layout)
        main_layout.addWidget(self.container)

        self._switch_page(0)

    def _switch_page(self, index: int):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.cat_buttons):
            if i == index:
                btn.setStyleSheet(
                    "background-color: #0284C7; color: white; font-weight: bold; border: none; "
                    "border-radius: 6px; text-align: left; padding-left: 10px; font-size: 11px;"
                )
            else:
                btn.setStyleSheet(
                    "background-color: #0B1120; color: #94A3B8; border: 1px solid #1E293B; "
                    "border-radius: 6px; text-align: left; padding-left: 10px; font-size: 11px;"
                )

    def _load_values_into_ui(self):
        s = self.current_settings
        self.inp_hotkey_hud.setText(s.hotkeys.hud_hotkey)
        self.inp_hotkey_clip.setText(s.hotkeys.clipboard_hotkey)
        self.chk_hud_anim.setChecked(s.hud.animations_enabled)
        self.chk_hud_autoclose.setChecked(s.hud.auto_close_on_action)
        self.cmb_speech_lang.setCurrentText(s.speech.language)
        self.chk_speech_paste.setChecked(s.speech.auto_paste_result)
        self.cmb_ocr_engine.setCurrentText(s.ocr.preferred_provider)
        self.chk_ocr_copy.setChecked(s.ocr.auto_copy_result)
        self.chk_clip_enabled.setChecked(s.clipboard.enabled)
        self.spn_clip_limit.setValue(s.clipboard.history_limit)
        self.chk_autostart.setChecked(s.system.autostart_with_windows)
        self.chk_protect_procs.setChecked(s.system.protect_critical_processes)
        self.spn_ram_interval.setValue(s.ram.refresh_interval_ms)

    def _handle_save(self):
        s = self.current_settings
        s.hotkeys.hud_hotkey = self.inp_hotkey_hud.text() if hasattr(self.inp_hotkey_hud, 'text') else "Alt+Q"
        s.hotkeys.clipboard_hotkey = self.inp_hotkey_clip.text() if hasattr(self.inp_hotkey_clip, 'text') else "Alt+V"
        s.hud.animations_enabled = self.chk_hud_anim.isChecked() if hasattr(self.chk_hud_anim, 'isChecked') else True
        s.hud.auto_close_on_action = self.chk_hud_autoclose.isChecked() if hasattr(self.chk_hud_autoclose, 'isChecked') else True
        s.speech.language = self.cmb_speech_lang.currentText() if hasattr(self.cmb_speech_lang, 'currentText') else "pl-PL"
        s.speech.auto_paste_result = self.chk_speech_paste.isChecked() if hasattr(self.chk_speech_paste, 'isChecked') else True
        s.ocr.preferred_provider = self.cmb_ocr_engine.currentText() if hasattr(self.cmb_ocr_engine, 'currentText') else "gemini_vision"
        s.ocr.auto_copy_result = self.chk_ocr_copy.isChecked() if hasattr(self.chk_ocr_copy, 'isChecked') else True
        s.clipboard.enabled = self.chk_clip_enabled.isChecked() if hasattr(self.chk_clip_enabled, 'isChecked') else True
        s.clipboard.history_limit = self.spn_clip_limit.value() if hasattr(self.spn_clip_limit, 'value') else 200
        s.system.autostart_with_windows = self.chk_autostart.isChecked() if hasattr(self.chk_autostart, 'isChecked') else False
        s.system.protect_critical_processes = self.chk_protect_procs.isChecked() if hasattr(self.chk_protect_procs, 'isChecked') else True
        s.ram.refresh_interval_ms = self.spn_ram_interval.value() if hasattr(self.spn_ram_interval, 'value') else 2000

        self.service.save_settings(s)
        self.settings_saved.emit(s)
        self.hide()

    def _handle_restore_defaults(self):
        self.current_settings = self.service.reset_to_defaults()
        self._load_values_into_ui()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
