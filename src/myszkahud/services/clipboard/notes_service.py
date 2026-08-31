"""Serwis logiki biznesowej dla Podręcznych Notatek (NotesService)."""

from typing import List, Optional
from myszkahud.storage.notes_repo import SQLiteNotesRepository
from .models import Note, utc_now


class NotesService:
    """Zarządza notatkami użytkownika, operacjami CRUD i wyszukiwaniem."""

    def __init__(self, repository: Optional[SQLiteNotesRepository] = None):
        self.repo = repository or SQLiteNotesRepository()

    def create_note(
        self,
        title: str,
        content: str,
        pinned: bool = False,
    ) -> Optional[Note]:
        """Tworzy nową notatkę (wymaga niepustego tytułu lub treści)."""
        clean_title = title.strip() if title else ""
        clean_content = content.strip() if content else ""

        if not clean_title and not clean_content:
            return None

        display_title = clean_title or "Bez tytułu"
        now = utc_now()
        note = Note(
            id=None,
            title=display_title,
            content=content,  # zachowujemy oryginalne formatowanie treści
            created_at=now,
            updated_at=now,
            pinned=pinned,
        )
        return self.repo.add_note(note)

    def get_note(self, note_id: int) -> Optional[Note]:
        """Pobiera pojedynczą notatkę po ID."""
        return self.repo.get_note_by_id(note_id)

    def list_notes(
        self,
        pinned_only: bool = False,
        search_query: Optional[str] = None,
    ) -> List[Note]:
        """Zwraca listę notatek z opcją wyszukiwania i filtrowania po przypięciu."""
        return self.repo.list_notes(
            pinned_only=pinned_only,
            search_query=search_query,
        )

    def update_note(self, note_id: int, title: str, content: str) -> bool:
        """Aktualizuje istniejącą notatkę."""
        clean_title = title.strip() if title else "Bez tytułu"
        return self.repo.update_note(note_id, clean_title, content)

    def set_pinned(self, note_id: int, pinned: bool) -> bool:
        """Ustawia status przypięcia notatki."""
        return self.repo.set_pinned(note_id, pinned)

    def toggle_pin(self, note_id: int) -> bool:
        """Przełącza status przypięcia notatki."""
        note = self.repo.get_note_by_id(note_id)
        if not note:
            return False
        return self.repo.set_pinned(note_id, not note.pinned)

    def delete_note(self, note_id: int) -> bool:
        """Usuwa notatkę po ID."""
        return self.repo.delete_note(note_id)

    def get_total_count(self, pinned_only: bool = False) -> int:
        """Zwraca łączną liczbę notatek."""
        return self.repo.get_total_count(pinned_only=pinned_only)
