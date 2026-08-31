"""Repozytorium danych SQLite dla podręcznych notatek (Note)."""

import sqlite3
from datetime import datetime, timezone
from typing import List, Optional
from myszkahud.services.clipboard.models import Note, utc_now
from .database import create_connection, init_database, escape_like_query


class SQLiteNotesRepository:
    """Odpowiada za bezpieczne operacje bazy danych na notatkach użytkownika."""

    def __init__(self, db_path: Optional[str] = None, conn: Optional[sqlite3.Connection] = None):
        self.db_path = db_path
        if conn is not None:
            self._conn = conn
        else:
            self._conn = init_database(db_path)

    def _row_to_note(self, row: sqlite3.Row) -> Note:
        # Parsowanie ISO 8601 UTC
        def parse_iso(val: str) -> datetime:
            if isinstance(val, str):
                try:
                    dt = datetime.fromisoformat(val)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except Exception:
                    pass
            return datetime.now(timezone.utc)

        return Note(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            created_at=parse_iso(row["created_at"]),
            updated_at=parse_iso(row["updated_at"]),
            pinned=bool(row["pinned"]),
        )

    def add_note(self, note: Note) -> Note:
        """Dodaje nową notatkę i przypisuje wygenerowane ID."""
        iso_created = note.created_at.isoformat()
        iso_updated = note.updated_at.isoformat()
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO notes (title, content, created_at, updated_at, pinned)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    note.title,
                    note.content,
                    iso_created,
                    iso_updated,
                    1 if note.pinned else 0,
                ),
            )
            note.id = cursor.lastrowid
        return note

    def get_note_by_id(self, note_id: int) -> Optional[Note]:
        """Pobiera pojedynczą notatkę po ID."""
        cursor = self._conn.execute(
            """
            SELECT id, title, content, created_at, updated_at, pinned
            FROM notes
            WHERE id = ?
            """,
            (note_id,),
        )
        row = cursor.fetchone()
        return self._row_to_note(row) if row else None

    def list_notes(
        self,
        pinned_only: bool = False,
        search_query: Optional[str] = None,
    ) -> List[Note]:
        """
        Pobiera listę notatek posortowanych: najpierw przypięte, potem od najnowszej aktualizacji.
        Obsługuje bezpieczne wyszukiwanie parametryzowane LIKE w tytule oraz treści.
        """
        sql = """
            SELECT id, title, content, created_at, updated_at, pinned
            FROM notes
            WHERE 1=1
        """
        params = []

        if pinned_only:
            sql += " AND pinned = 1"

        if search_query:
            escaped_term = escape_like_query(search_query)
            sql += " AND (title LIKE ? ESCAPE '\\' OR content LIKE ? ESCAPE '\\')"
            params.extend([escaped_term, escaped_term])

        sql += " ORDER BY pinned DESC, updated_at DESC, id DESC"

        cursor = self._conn.execute(sql, params)
        return [self._row_to_note(row) for row in cursor.fetchall()]

    def update_note(self, note_id: int, title: str, content: str) -> bool:
        """Aktualizuje tytuł i treść notatki oraz odświeża updated_at."""
        now_iso = utc_now().isoformat()
        with self._conn:
            cursor = self._conn.execute(
                """
                UPDATE notes
                SET title = ?, content = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, content, now_iso, note_id),
            )
            return cursor.rowcount > 0

    def set_pinned(self, note_id: int, pinned: bool) -> bool:
        """Ustawia status przypięcia notatki."""
        with self._conn:
            cursor = self._conn.execute(
                "UPDATE notes SET pinned = ? WHERE id = ?",
                (1 if pinned else 0, note_id),
            )
            return cursor.rowcount > 0

    def delete_note(self, note_id: int) -> bool:
        """Usuwa notatkę po ID."""
        with self._conn:
            cursor = self._conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            return cursor.rowcount > 0

    def get_total_count(self, pinned_only: bool = False) -> int:
        """Zwraca łączną liczbę notatek."""
        if pinned_only:
            cur = self._conn.execute("SELECT COUNT(*) AS cnt FROM notes WHERE pinned = 1")
        else:
            cur = self._conn.execute("SELECT COUNT(*) AS cnt FROM notes")
        return cur.fetchone()["cnt"]
