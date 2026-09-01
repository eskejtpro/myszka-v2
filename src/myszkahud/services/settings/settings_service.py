"""Serwis zarządzania konfiguracją aplikacji (SettingsService v0.9)."""

import os
import json
import logging
import tempfile
from typing import Optional

from myszkahud.services.settings.models import AppSettings
from myszkahud.storage.paths import get_app_data_dir

logger = logging.getLogger(__name__)


class SettingsService:
    """Odczytuje i zapisuje konfigurację aplikacji w formacie JSON z obsługą błędów."""

    def __init__(self, custom_path: Optional[str] = None):
        if custom_path:
            self._settings_path = custom_path
        else:
            app_dir = get_app_data_dir()
            self._settings_path = os.path.join(app_dir, "settings.json")
        self._current_settings: AppSettings = self.load_settings()

    @property
    def current(self) -> AppSettings:
        """Zwraca aktualnie załadowane ustawienia."""
        return self._current_settings

    def load_settings(self) -> AppSettings:
        """Wczytuje ustawienia z dysku lub tworzy domyślne, jeśli plik nie istnieje lub jest uszkodzony."""
        if not os.path.exists(self._settings_path):
            logger.info(f"Plik ustawień nie istnieje ({self._settings_path}), tworzenie domyślnych.")
            default_settings = AppSettings()
            self.save_settings(default_settings)
            return default_settings

        try:
            with open(self._settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                settings = AppSettings.from_dict(data)
                self._current_settings = settings
                return settings
        except (json.JSONDecodeError, OSError, ValueError) as e:
            logger.warning(f"Uszkodzony plik ustawień ({e}). Przywracanie domyślnych wartości.")
            default_settings = AppSettings()
            self._current_settings = default_settings
            return default_settings

    def save_settings(self, settings: Optional[AppSettings] = None) -> bool:
        """Atomowo zapisuje konfigurację do pliku JSON."""
        if settings is not None:
            self._current_settings = settings

        target_dir = os.path.dirname(self._settings_path)
        if target_dir and not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
            except OSError as e:
                logger.error(f"Nie udało się utworzyć katalogu ustawień: {e}")
                return False

        data = self._current_settings.to_dict()
        try:
            # Bezpieczny zapis atomowy przez plik tymczasowy
            temp_fd, temp_path = tempfile.mkstemp(dir=target_dir or None, prefix="settings_", suffix=".tmp")
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Zamień atomowo plik docelowy
            if os.path.exists(self._settings_path):
                os.replace(temp_path, self._settings_path)
            else:
                os.rename(temp_path, self._settings_path)
            return True
        except Exception as e:
            logger.error(f"Błąd zapisu pliku ustawień ({self._settings_path}): {e}")
            return False

    def reset_to_defaults(self) -> AppSettings:
        """Przywraca i zapisuje domyślne ustawienia."""
        self._current_settings = AppSettings()
        self.save_settings(self._current_settings)
        return self._current_settings
