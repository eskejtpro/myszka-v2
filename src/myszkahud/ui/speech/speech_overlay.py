"""Kompaktowa pływająca nakładka nagrywania głosu (SpeechRecordingOverlay).

Wyświetla:
- status nagrywania z pulsującą diodą,
- licznik czasu nagrania (np. 00:03),
- prostą animację poziomu audio,
- przycisk [Zakończ] (lub Spacja/Enter) oraz [Anuluj] (lub Esc).
"""

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QGraphicsDropShadowEffect, QProgressBar
    )
    from PySide6.QtCore import Qt, Signal, QTimer, QPoint
    from PySide6.QtGui import QColor, QCursor, QGuiApplication
except ImportError:
    class QWidget:
        def __init__(self, parent=None):
            pass
        def setWindowFlags(self, *args):
            pass
        def setAttribute(self, *args):
            pass
        def setFixedSize(self, *args):
            pass
        def show(self):
            pass
        def hide(self):
            pass
        def move(self, *args):
            pass
        def raise_(self):
            pass
        def activateWindow(self):
            pass
        def width(self):
            return 360
        def height(self):
            return 110
        def keyPressEvent(self, e):
            pass

    class Signal:
        def __init__(self, *types):
            self._callbacks = []
        def connect(self, callback):
            self._callbacks.append(callback)
        def emit(self, *args):
            for cb in self._callbacks:
                cb(*args)

    class QTimer:
        def __init__(self, parent=None):
            self.timeout = Signal()
        def setInterval(self, ms):
            pass
        def start(self):
            pass
        def stop(self):
            pass

    class MockWidget:
        def __init__(self, *args, **kwargs):
            self._text = ""
            self.clicked = Signal()
        def setText(self, text):
            self._text = text
        def text(self):
            return self._text
        def width(self):
            return 360
        def height(self):
            return 110
        def __getattr__(self, name):
            def _dummy_method(*args, **kwargs):
                return None
            return _dummy_method

    class QWidget(MockWidget):
        pass

    class MockQt:
        FramelessWindowHint = 0x00000800
        WindowStaysOnTopHint = 0x00040000
        Tool = 0x00000008
        WA_TranslucentBackground = 120
        Key_Return = 0x01000004
        Key_Enter = 0x01000005
        Key_Space = 0x20
        Key_Escape = 0x01000000

    class MockColor:
        def __init__(self, *args, **kwargs):
            pass

    class MockPoint:
        def __init__(self, *args, **kwargs):
            pass

    class MockCursor:
        def __init__(self, *args, **kwargs):
            pass
        @staticmethod
        def pos():
            return MockPoint()

    QPoint = MockPoint
    QVBoxLayout = MockWidget
    QHBoxLayout = MockWidget
    QLabel = MockWidget
    QPushButton = MockWidget
    QGraphicsDropShadowEffect = MockWidget
    QProgressBar = MockWidget
    Qt = MockQt
    QColor = MockColor
    QCursor = MockCursor
    QGuiApplication = object

from myszkahud.services.speech.audio_recorder import (
    AudioRecorder,
    AudioDeviceNotFoundError
)
from myszkahud.services.speech.service import MAX_RECORDING_SECONDS


class SpeechRecordingOverlay(QWidget):
    """
    Pływająca, podręczna nakładka nagrywania głosu pod kursorem.
    """

    recording_finished = Signal(bytes)  # Emituje spakowane bajty WAV
    cancelled = Signal()                # Emituje anulowanie nagrania
    error_occurred = Signal(str)        # Emituje błąd urządzenia

    def __init__(self, recorder: Optional[AudioRecorder] = None, max_seconds: int = MAX_RECORDING_SECONDS, parent=None):
        super().__init__(parent)
        self.recorder = recorder or AudioRecorder(parent=self)
        self.max_seconds = max_seconds
        self._elapsed_seconds = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_timer_tick)

        self._pulse_state = False
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(500)
        self._pulse_timer.timeout.connect(self._on_pulse_tick)

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(360, 110)
        self._init_ui()


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        self.card = QWidget(self)
        self.card.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 15, 29, 0.96);
                border: 1.5px solid #0284C7;
                border-radius: 12px;
            }
        """)

        card_shadow = QGraphicsDropShadowEffect(self.card)
        card_shadow.setBlurRadius(24)
        card_shadow.setColor(QColor(0, 0, 0, 220))
        card_shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(card_shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(6)

        # 1. Pasek statusu nagrywania
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.lbl_rec_dot = QLabel("●", self.card)
        self.lbl_rec_dot.setStyleSheet("font-size: 14px; color: #EF4444; background: transparent; border: none;")
        header_layout.addWidget(self.lbl_rec_dot)

        self.lbl_title = QLabel("NAGRYWANIE MOWY (pl-PL)", self.card)
        self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px; background: transparent; border: none;")
        header_layout.addWidget(self.lbl_title)

        header_layout.addStretch()

        self.lbl_timer = QLabel("00:00", self.card)
        self.lbl_timer.setStyleSheet("font-size: 12px; font-weight: 700; font-family: 'Consolas', monospace; color: #F8FAFC; background: transparent; border: none;")
        header_layout.addWidget(self.lbl_timer)

        card_layout.addLayout(header_layout)

        # 2. Pasek wizualizacji audio (animowany wave bar)
        self.audio_bar = QProgressBar(self.card)
        self.audio_bar.setRange(0, 100)
        self.audio_bar.setValue(50)
        self.audio_bar.setFixedHeight(4)
        self.audio_bar.setTextVisible(False)
        self.audio_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #0284C7;
                border-radius: 2px;
            }
        """)
        card_layout.addWidget(self.audio_bar)

        # 3. Przyciski akcji
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        self.btn_stop = QPushButton("✔ Zakończ i transkrybuj", self.card)
        self.btn_stop.setStyleSheet("""
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
            QPushButton:pressed { background-color: #075985; }
        """)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        actions_layout.addWidget(self.btn_stop)

        self.btn_cancel = QPushButton("Anuluj", self.card)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 600;
                padding: 6px 10px;
            }
            QPushButton:hover { background-color: #334155; color: #F8FAFC; }
            QPushButton:pressed { background-color: #0F172A; }
        """)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        actions_layout.addWidget(self.btn_cancel)

        actions_layout.addStretch()

        lbl_hint = QLabel("Enter: Zakończ | Esc: Anuluj", self.card)
        lbl_hint.setStyleSheet("font-size: 9px; color: #64748B; background: transparent; border: none;")
        actions_layout.addWidget(lbl_hint)

        card_layout.addLayout(actions_layout)
        main_layout.addWidget(self.card)

    def start_recording(self, target_pos: Optional[QPoint] = None) -> bool:
        """Rozpoczyna nagrywanie i wyświetla nakładkę pod kursorem."""
        self._elapsed_seconds = 0
        self.lbl_timer.setText("00:00")
        self.lbl_title.setText("NAGRYWANIE MOWY (pl-PL)")
        self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px; background: transparent; border: none;")
        self.btn_stop.setEnabled(True)

        try:
            success = self.recorder.start_recording()
            if not success:
                return False
        except AudioDeviceNotFoundError as e:
            self.error_occurred.emit(str(e))
            self.lbl_title.setText("BŁĄD: Brak mikrofonu")
            self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #EF4444; background: transparent; border: none;")
            self.show_at_cursor(target_pos)
            return False
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.lbl_title.setText(f"BŁĄD: {e}")
            self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #EF4444; background: transparent; border: none;")
            self.show_at_cursor(target_pos)
            return False

        self._timer.start()
        self._pulse_timer.start()
        self.show_at_cursor(target_pos)
        return True

    def _on_timer_tick(self):
        self._elapsed_seconds += 1
        mins = self._elapsed_seconds // 60
        secs = self._elapsed_seconds % 60
        self.lbl_timer.setText(f"{mins:02d}:{secs:02d}")

        # Automatyczne zakończenie nagrania po osiągnięciu limitu MAX_RECORDING_SECONDS
        if self._elapsed_seconds >= self.max_seconds:
            self._on_stop_clicked()

    def _on_pulse_tick(self):
        self._pulse_state = not self._pulse_state
        if self._pulse_state:
            self.lbl_rec_dot.setStyleSheet("font-size: 14px; color: #EF4444; background: transparent; border: none;")
            self.audio_bar.setValue(85)
        else:
            self.lbl_rec_dot.setStyleSheet("font-size: 14px; color: #7F1D1D; background: transparent; border: none;")
            self.audio_bar.setValue(35)

    def _on_stop_clicked(self):
        self._timer.stop()
        self._pulse_timer.stop()
        self.hide()
        wav_bytes = self.recorder.stop_recording()
        self.recording_finished.emit(wav_bytes)

    def _on_cancel_clicked(self):
        self._timer.stop()
        self._pulse_timer.stop()
        self.hide()
        self.recorder.stop_recording()
        self.cancelled.emit()

    def show_at_cursor(self, target_pos: Optional[QPoint] = None):
        """Wyświetla nakładkę pod wskazaną pozycją lub pod kursorem."""
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
        # Esc -> Anulowanie nagrania
        if event.key() == Qt.Key_Escape:
            self._on_cancel_clicked()
            event.accept()
        # Enter -> Zakończenie nagrania TYLKO gdy nakładka posiada aktywny fokus
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._on_stop_clicked()
            event.accept()
        else:
            # Spacja i inne klawisze NIE są skrótem zakończenia nagrywania
            if hasattr(super(), "keyPressEvent"):
                super().keyPressEvent(event)


