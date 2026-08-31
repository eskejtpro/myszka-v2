"""Moduł nagrywania dźwięku z mikrofonu przy użyciu PySide6.QtMultimedia.

Obsługuje:
- Bezpieczną detekcję dostępności mikrofonu przez QMediaDevices (brak crasha przy braku urządzenia),
- Sprawdzanie i negocjację formatu audio (isFormatSupported / preferredFormat),
- Zapis strumienia PCM do bufora w pamięci (io.BytesIO),
- Pakowanie surowych próbek PCM do standardowego kontenera RIFF WAV z prawidłowymi metadanymi próbkowania.
"""

import io
import struct
import wave
from typing import Optional, Tuple

try:
    from PySide6.QtCore import QObject, Signal, QByteArray, QIODevice, QBuffer
    from PySide6.QtMultimedia import (
        QMediaDevices,
        QAudioSource,
        QAudioFormat,
        QAudioDevice
    )
except ImportError:
    QObject = object
    Signal = lambda *args: None
    QByteArray = bytes
    QIODevice = object
    QBuffer = object
    QMediaDevices = None
    QAudioSource = None
    QAudioFormat = None
    QAudioDevice = None


class AudioDeviceNotFoundError(RuntimeError):
    """Wyjątek rzucany w przypadku braku dostępnego mikrofonu w systemie."""
    def __init__(self, message: str = "Nie wykryto urządzenia wejściowego audio."):
        super().__init__(message)


def build_wav_container(
    pcm_data: bytes,
    sample_rate: int = 16000,
    channels: int = 1,
    sample_width: int = 2
) -> bytes:
    """
    Pakuje surowe bajty PCM do standardowego bufora RIFF WAV w pamięci RAM.
    
    :param pcm_data: Surowe próbki PCM (np. 16-bit signed integer little-endian).
    :param sample_rate: Częstotliwość próbkowania w Hz (np. 16000, 44100, 48000).
    :param channels: Liczba kanałów (1 = mono, 2 = stereo).
    :param sample_width: Szerokość próbki w bajtach (2 = 16-bit).
    :return: Kompletne bajty pliku WAV gotowe do przesłania do API.
    """
    if not pcm_data:
        return b""

    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)

    return out_buf.getvalue()


class AudioRecorder(QObject):
    """
    Asynchroniczny rejestrator audio z mikrofonu oparty na QAudioSource.
    """

    state_changed = Signal(bool)  # True = recording, False = stopped
    error_occurred = Signal(str)   # Komunikat błędu

    def __init__(self, target_sample_rate: int = 16000, parent=None):
        if QObject is object:
            self._is_recording = False
            self.target_sample_rate = target_sample_rate
            self.actual_sample_rate = target_sample_rate
            self.actual_channels = 1
            self.actual_sample_width = 2
            return

        super().__init__(parent)
        self.target_sample_rate = target_sample_rate
        self.actual_sample_rate = target_sample_rate
        self.actual_channels = 1
        self.actual_sample_width = 2

        self.audio_source: Optional[QAudioSource] = None
        self.io_device: Optional[QIODevice] = None
        self.raw_pcm_buffer = bytearray()
        self._is_recording = False

    @staticmethod
    def get_default_input_device() -> Optional[object]:
        """Sprawdza i zwraca domyślne urządzenie wejściowe audio."""
        if QMediaDevices is None:
            return None
        
        inputs = QMediaDevices.audioInputs()
        if not inputs or len(inputs) == 0:
            return None

        default_device = QMediaDevices.defaultAudioInput()
        if default_device.isNull():
            return None

        return default_device

    @staticmethod
    def is_microphone_available() -> bool:
        """Szybkie sprawdzenie czy w systemie jest dostępny sprawny mikrofon."""
        device = AudioRecorder.get_default_input_device()
        return device is not None

    def _determine_audio_format(self, device: object) -> Tuple[object, int, int, int]:
        """
        Negocjuje format audio z urządzeniem.
        Nie wymusza na siłę 16 kHz jeśli mikrofon go nie obsługuje,
        lecz pobiera preferredFormat().
        """
        if QAudioFormat is None:
            return None, 16000, 1, 2

        desired_format = QAudioFormat()
        desired_format.setSampleRate(self.target_sample_rate)
        desired_format.setChannelCount(1)  # Mono
        desired_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        if hasattr(device, "isFormatSupported") and device.isFormatSupported(desired_format):
            return desired_format, self.target_sample_rate, 1, 2

        # Fallback do natywnego formatu mikrofonu
        pref_format = device.preferredFormat()
        sample_rate = pref_format.sampleRate() if pref_format.sampleRate() > 0 else 44100
        channels = pref_format.channelCount() if pref_format.channelCount() > 0 else 1
        
        sample_fmt = pref_format.sampleFormat()
        if sample_fmt == QAudioFormat.SampleFormat.Int16:
            sample_width = 2
        elif sample_fmt == QAudioFormat.SampleFormat.Int32 or sample_fmt == QAudioFormat.SampleFormat.Float:
            sample_width = 4
        elif sample_fmt == QAudioFormat.SampleFormat.UInt8:
            sample_width = 1
        else:
            sample_width = 2

        return pref_format, sample_rate, channels, sample_width

    def start_recording(self) -> bool:
        """
        Rozpoczyna nagrywanie audio.
        Zwraca True przy powodzeniu lub False/rzuca wyjątek przy braku mikrofonu.
        """
        if self._is_recording:
            return True

        device = self.get_default_input_device()
        if device is None:
            msg = "Nie wykryto urządzenia wejściowego audio."
            self.error_occurred.emit(msg)
            raise AudioDeviceNotFoundError(msg)

        try:
            audio_format, rate, channels, width = self._determine_audio_format(device)
            self.actual_sample_rate = rate
            self.actual_channels = channels
            self.actual_sample_width = width

            self.raw_pcm_buffer.clear()
            self.audio_source = QAudioSource(device, audio_format, self)
            self.io_device = self.audio_source.start()

            if self.io_device is None:
                raise RuntimeError("Nie udało się otworzyć strumienia audio ze źródła QAudioSource.")

            self.io_device.readyRead.connect(self._on_audio_data_ready)
            self._is_recording = True
            self.state_changed.emit(True)
            return True

        except Exception as e:
            self._is_recording = False
            self.error_occurred.emit(str(e))
            raise RuntimeError(f"Błąd podczas uruchamiania nagrywania: {e}")

    def _on_audio_data_ready(self):
        """Odbiera surowe klastry próbek z urządzenia i dopisuje do bufora."""
        if self.io_device and self.io_device.isOpen():
            data = self.io_device.readAll()
            if data:
                # Konwersja QByteArray -> bytes
                self.raw_pcm_buffer.extend(bytes(data))

    def stop_recording(self) -> bytes:
        """
        Zatrzymuje nagrywanie i zwraca spakowane bajty WAV z prawidłowymi nagłówkami.
        """
        if not self._is_recording:
            if self.raw_pcm_buffer:
                return build_wav_container(
                    bytes(self.raw_pcm_buffer),
                    sample_rate=self.actual_sample_rate,
                    channels=self.actual_channels,
                    sample_width=self.actual_sample_width
                )
            return b""

        self._is_recording = False

        if self.audio_source:
            # Odczytujemy resztki z bufora
            if self.io_device and self.io_device.isOpen():
                remaining = self.io_device.readAll()
                if remaining:
                    self.raw_pcm_buffer.extend(bytes(remaining))
            self.audio_source.stop()
            self.audio_source = None
            self.io_device = None

        self.state_changed.emit(False)

        # Tworzymy gotowy plik WAV
        wav_bytes = build_wav_container(
            bytes(self.raw_pcm_buffer),
            sample_rate=self.actual_sample_rate,
            channels=self.actual_channels,
            sample_width=self.actual_sample_width
        )
        return wav_bytes

    def is_recording(self) -> bool:
        return self._is_recording

    def get_recorded_duration_seconds(self) -> float:
        """Szacuje długość nagranego dźwięku w sekundach na podstawie liczby próbek."""
        if not self.raw_pcm_buffer:
            return 0.0
        bytes_per_second = self.actual_sample_rate * self.actual_channels * self.actual_sample_width
        if bytes_per_second <= 0:
            return 0.0
        return len(self.raw_pcm_buffer) / bytes_per_second
