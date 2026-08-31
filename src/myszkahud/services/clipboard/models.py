"""Modele danych dla Inteligentnego Schowka i Podręcznego Notesu w MyszkaHUD."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# Stałe konfiguracyjne dla schowka
DEFAULT_CLIPBOARD_HISTORY_LIMIT: int = 200
MAX_ENTRY_LENGTH: int = 100_000
SCHEMA_VERSION: int = 1


def utc_now() -> datetime:
    """Zwraca bieżący czas w formacie timezone-aware UTC."""
    return datetime.now(timezone.utc)


@dataclass
class ClipboardEntry:
    """Reprezentuje pojedynczy wpis w historii schowka."""

    text: str
    id: Optional[int] = None
    created_at: datetime = field(default_factory=utc_now)
    source_app: Optional[str] = None
    pinned: bool = False
    entry_type: str = "text"

    @property
    def char_count(self) -> int:
        """Dynamicznie wyliczana liczba znaków, gwarantująca spójność z treścią."""
        return len(self.text) if self.text else 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
            "source_app": self.source_app,
            "pinned": self.pinned,
            "entry_type": self.entry_type,
            "char_count": self.char_count,
        }


@dataclass
class Note:
    """Reprezentuje podręczną notatkę użytkownika."""

    title: str
    content: str
    id: Optional[int] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    pinned: bool = False

    @property
    def char_count(self) -> int:
        """Dynamicznie wyliczana liczba znaków w treści notatki."""
        return len(self.content) if self.content else 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "pinned": self.pinned,
            "char_count": self.char_count,
        }
