"""Moduł Inteligentnego Schowka i Podręcznego Notesu dla MyszkaHUD."""

from .models import (
    ClipboardEntry,
    Note,
    DEFAULT_CLIPBOARD_HISTORY_LIMIT,
    MAX_ENTRY_LENGTH,
    SCHEMA_VERSION,
    utc_now,
)
from .clipboard_service import ClipboardService
from .notes_service import NotesService
from .monitor import (
    ClipboardWriteGuard,
    ClipboardMonitor,
    detect_source_application,
)

__all__ = [
    "ClipboardEntry",
    "Note",
    "DEFAULT_CLIPBOARD_HISTORY_LIMIT",
    "MAX_ENTRY_LENGTH",
    "SCHEMA_VERSION",
    "utc_now",
    "ClipboardService",
    "NotesService",
    "ClipboardWriteGuard",
    "ClipboardMonitor",
    "detect_source_application",
]
