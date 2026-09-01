"""Moduł zarządzania procesami i aplikacjami dla MyszkaHUD."""

from .models import ProcessInfo, CRITICAL_SYSTEM_PROCESSES
from .process_service import ProcessService
from .providers.base import BaseProcessProvider
from .providers.psutil_provider import PsutilProcessProvider
from .providers.mock_provider import MockProcessProvider

__all__ = [
    "ProcessInfo",
    "CRITICAL_SYSTEM_PROCESSES",
    "ProcessService",
    "BaseProcessProvider",
    "PsutilProcessProvider",
    "MockProcessProvider",
]
