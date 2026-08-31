"""Repozytorium danych SQLite dla historii schowka (ClipboardEntry)."""

import sqlite3
from datetime import datetime, timezone
from typing import List, Optional
from myszkahud.services.clipboard.models import ClipboardEntry, DEFAULT_CLIPBOARD_HISTORY_LIMIT
from .database import create_connection, init_database, escape_like_query


class SQLiteClipboardRepository:
    """Odpowiada za bezpieczne operacje bazy danych na wpisach schowka."""

    def __init__(self, db_path: Optional[str] = None, conn: Optional[sqlite3.Connection] = None):
        self.db_path = db_path
        if conn is not None:
            self._conn = conn
        else:
            self._conn = init_database(db_path)

    def _row_to_entry(self, row: sqlite3.Row) -> ClipboardEntry:
        # Parsowanie ISO 8601 UTC
        raw_created = row["created_at"]
        if isinstance(raw_created, str):
            try:
                created_dt = datetime.fromisoformat(raw_created)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
            except Exception:
                created_dt = datetime.now(timezone.utc)
        else:
            created_dt = datetime.now(timezone.utc)

        return ClipboardEntry(
            id=row["id"],
            text=row["text"],
            created_at=created_dt,
            source_app=row["source_app"],
            pinned=bool(row["pinned"]),
            entry_type=row["entry_type"] or "text",
        )

    def add_entry(self, entry: ClipboardEntry) -> ClipboardEntry:
        """Dodaje nowy wpis do schowka i przypisuje wygenerowane ID."""
        iso_created = entry.created_at.isoformat()
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO clipboard_entries (text, created_at, source_app, pinned, entry_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entry.text,
                    iso_created,
                    entry.source_app,
                    1 if entry.pinned else 0,
                    entry.entry_type,
                ),
            )
            entry.id = cursor.lastrowid
        return entry

    def get_latest_entry(self) -> Optional[ClipboardEntry]:
        """Pobiera ostatnio dodany wpis schowka."""
        cursor = self._conn.execute(
            """
            SELECT id, text, created_at, source_app, pinned, entry_type
            FROM clipboard_entries
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        return self._row_to_entry(row) if row else None

    def get_entry_by_id(self, entry_id: int) -> Optional[ClipboardEntry]:
        """Pobiera pojedynczy wpis po ID."""
        cursor = self._conn.execute(
            """
            SELECT id, text, created_at, source_app, pinned, entry_type
            FROM clipboard_entries
            WHERE id = ?
            """,
            (entry_id,),
        )
        row = cursor.fetchone()
        return self._row_to_entry(row) if row else None

    def list_entries(
        self,
        limit: int = DEFAULT_CLIPBOARD_HISTORY_LIMIT,
        pinned_only: bool = False,
        search_query: Optional[str] = None,
    ) -> List[ClipboardEntry]:
        """
        Zwraca listę wpisów schowka posortowanych od najnowszych.
        Obsługuje filtrowanie po przypięciu oraz parametryzowane wyszukiwanie LIKE.
        """
        sql = """
            SELECT id, text, created_at, source_app, pinned, entry_type
            FROM clipboard_entries
            WHERE 1=1
        """
        params = []

        if pinned_only:
            sql += " AND pinned = 1"

        if search_query:
            escaped_term = escape_like_query(search_query)
            sql += " AND text LIKE ? ESCAPE '\\'"
            params.append(escaped_term)

        sql += " ORDER BY pinned DESC, created_at DESC, id DESC LIMIT ?"
        params.append(limit)

        cursor = self._conn.execute(sql, params)
        return [self._row_to_entry(row) for row in cursor.fetchall()]

    def set_pinned(self, entry_id: int, pinned: bool) -> bool:
        """Ustawia status przypięcia wpisu."""
        with self._conn:
            cursor = self._conn.execute(
                "UPDATE clipboard_entries SET pinned = ? WHERE id = ?",
                (1 if pinned else 0, entry_id),
            )
            return cursor.rowcount > 0

    def delete_entry(self, entry_id: int) -> bool:
        """Usuwa pojedynczy wpis schowka po ID."""
        with self._conn:
            cursor = self._conn.execute(
                "DELETE FROM clipboard_entries WHERE id = ?", (entry_id,)
            )
            return cursor.rowcount > 0

    def clear_history(self, preserve_pinned: bool = True) -> int:
        """
        Czyści historię schowka.
        Domyślnie usuwa tylko nieprzypięte elementy (pinned = 0).
        """
        with self._conn:
            if preserve_pinned:
                cursor = self._conn.execute(
                    "DELETE FROM clipboard_entries WHERE pinned = 0"
                )
            else:
                cursor = self._conn.execute("DELETE FROM clipboard_entries")
            return cursor.rowcount

    def trim_history(self, max_unpinned_limit: int = DEFAULT_CLIPBOARD_HISTORY_LIMIT) -> int:
        """
        Automatycznie przycina najstarsze NIEPRZYPIĘTE wpisy,
        jeśli ich liczba przekracza max_unpinned_limit.
        Wpisy przypięte (pinned=1) są zawsze chronione.
        """
        with self._conn:
            # Pobieramy ID wpisów unpinned przekraczających limit
            sql = """
                DELETE FROM clipboard_entries
                WHERE id IN (
                    SELECT id FROM clipboard_entries
                    WHERE pinned = 0
                    ORDER BY created_at DESC, id DESC
                    LIMIT -1 OFFSET ?
                )
            """
            cursor = self._conn.execute(sql, (max_unpinned_limit,))
            return cursor.rowcount

    def get_total_count(self, pinned_only: bool = False) -> int:
        """Zwraca całkowitą liczbę wpisów."""
        if pinned_only:
            cur = self._conn.execute(
                "SELECT COUNT(*) AS cnt FROM clipboard_entries WHERE pinned = 1"
            )
        else:
            cur = self._conn.execute("SELECT COUNT(*) AS cnt FROM clipboard_entries")
        return cur.fetchone()["cnt"]
