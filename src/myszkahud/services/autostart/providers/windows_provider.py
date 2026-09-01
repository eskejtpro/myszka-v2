"""Dostawca autostartu Windows w rejestrze HKCU (Current User - bez praw administratora)."""

import os
import sys
import logging
from myszkahud.services.autostart.providers.base import BaseAutostartProvider

logger = logging.getLogger(__name__)

REG_RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


class WindowsRegistryAutostartProvider(BaseAutostartProvider):
    """Zarządza wpisem autostartu w HKCU (HKEY_CURRENT_USER)."""

    def is_enabled(self, app_name: str = "MyszkaHUD") -> bool:
        if sys.platform != "win32":
            return False

        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_READ) as key:
                try:
                    val, _ = winreg.QueryValueEx(key, app_name)
                    return bool(val)
                except FileNotFoundError:
                    return False
        except Exception as e:
            logger.warning(f"Błąd odczytu autostartu z rejestru: {e}")
            return False

    def enable(self, app_name: str = "MyszkaHUD", exec_path: str = "") -> bool:
        if sys.platform != "win32":
            logger.info("Autostart w rejestrze jest wspierany tylko w systemie Windows.")
            return False

        if not exec_path:
            exec_path = sys.executable

        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exec_path}"')
                logger.info(f"Włączono autostart Windows dla {app_name} ({exec_path})")
                return True
        except Exception as e:
            logger.error(f"Błąd zapisu do rejestru autostartu: {e}")
            return False

    def disable(self, app_name: str = "MyszkaHUD") -> bool:
        if sys.platform != "win32":
            return False

        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_SET_VALUE) as key:
                try:
                    winreg.DeleteValue(key, app_name)
                    logger.info(f"Wyłączono autostart Windows dla {app_name}")
                    return True
                except FileNotFoundError:
                    return True
        except Exception as e:
            logger.error(f"Błąd usuwania wpisu autostartu z rejestru: {e}")
            return False
