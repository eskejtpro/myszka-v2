"""Serwis logiki biznesowej dla Inteligentnego Schowka (ClipboardService)."""

from typing import List, Optional
from myszkahud.storage.clipboard_repo import SQLiteClipboardRepository
from .models import (
    ClipboardEntry,
    DEFAULT_CLIPBOARD_HISTORY_LIMIT,
    MAX_ENTRY_LENGTH,
    utc_now,
)


class ClipboardService:
    """Zarządza historią schowka, filtrowaniem duplikatów, limitami i prywatnością."""

    def __init__(
        self,
        repository: Optional[SQLiteClipboardRepository] = None,
        history_limit: int = DEFAULT_CLIPBOARD_HISTORY_LIMIT,
        max_entry_length: int = MAX_ENTRY_LENGTH,
    ):
        self.repo = repository or SQLiteClipboardRepository()
        self.history_limit = history_limit
        self.max_entry_length = max_entry_length
        self._is_paused = False
        self._is_enabled = True

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    def pause_history(self) -> None:
        """Tymczasowo wstrzymuje rejestrowanie nowych wpisów schowka."""
        self._is_paused = True

    def resume_history(self) -> None:
        """Wznawia rejestrowanie nowych wpisów schowka."""
        self._is_paused = False

    def set_paused(self, paused: bool) -> None:
        """Ustawia stan wstrzymania rejestrowania schowka."""
        self._is_paused = bool(paused)

    def toggle_pause(self) -> bool:
        """Przełącza stan wstrzymania (zwraca nowy stan is_paused)."""
        self._is_paused = not self._is_paused
        return self._is_paused

    def set_enabled(self, enabled: bool) -> None:
        """Całkowicie włącza lub wyłącza moduł historii."""
        self._is_enabled = enabled

    def add_clipboard_text(
        self,
        text: str,
        source_app: Optional[str] = None,
        pinned: bool = False,
        entry_type: str = "text",
    ) -> Optional[ClipboardEntry]:
        """
        Główna metoda rejestracji tekstu ze schowka:
        - Sprawdza czy historia nie jest wyłączona lub wstrzymana,
        - Ignoruje puste ciągi i whitespace-only (zachowując spacje w prawidłowych tekstach),
        - Przycina tekst do MAX_ENTRY_LENGTH,
        - Ignoruje natychmiastowe duplikaty z ostatnim wpisem,
        - Zapisuje do SQLite i uruchamia trimowanie unpinned.
        """
        if not self._is_enabled or self._is_paused:
            return None

        if not text or not text.strip():
            return None

        # Ochrona przed gigantycznymi buforami
        safe_text = text[: self.max_entry_length]

        # Tłumienie duplikatów względem ostatniego wpisu
        latest = self.repo.get_latest_entry()
        if latest and latest.text == safe_text:
            return None

        entry = ClipboardEntry(
            id=None,
            text=safe_text,
            created_at=utc_now(),
            source_app=source_app,
            pinned=pinned,
            entry_type=entry_type,
        )

        saved_entry = self.repo.add_entry(entry)

        # Automatyczne trimowanie nieprzypiętych wpisów powyżej limitu
        self.repo.trim_history(self.history_limit)

        return saved_entry

    def list_entries(
        self,
        limit: Optional[int] = None,
        pinned_only: bool = False,
        search_query: Optional[str] = None,
    ) -> List[ClipboardEntry]:
        """Pobiera listę wpisów schowka."""
        effective_limit = limit if limit is not None else self.history_limit
        return self.repo.list_entries(
            limit=effective_limit,
            pinned_only=pinned_only,
            search_query=search_query,
        )

    def get_latest_entry(self) -> Optional[ClipboardEntry]:
        """Zwraca ostatni wpis schowka."""
        return self.repo.get_latest_entry()

    def set_pinned(self, entry_id: int, pinned: bool) -> bool:
        """Przypina lub odpina wpis."""
        return self.repo.set_pinned(entry_id, pinned)

    def toggle_pin(self, entry_id: int) -> bool:
        """Przełącza status przypięcia wpisu."""
        entry = self.repo.get_entry_by_id(entry_id)
        if not entry:
            return False
        new_pinned = not entry.pinned
        return self.repo.set_pinned(entry_id, new_pinned)

    def delete_entry(self, entry_id: int) -> bool:
        """Usuwa wpis schowka po ID."""
        return self.repo.delete_entry(entry_id)

    def clear_history(self, preserve_pinned: bool = True) -> int:
        """Czyści historię schowka (domyślnie chroni wpisy przypięte)."""
        return self.repo.clear_history(preserve_pinned=preserve_pinned)

    def get_total_count(self, pinned_only: bool = False) -> int:
        """Zwraca łączną liczbę wpisów."""
        return self.repo.get_total_count(pinned_only=pinned_only)
