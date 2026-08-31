"""Zarządzanie połączeniem SQLite, schematem i migracjami MyszkaHUD."""

import sqlite3
from typing import Optional
from .paths import get_database_path
from myszkahud.services.clipboard.models import SCHEMA_VERSION


def escape_like_query(text: str) -> str:
    """
    Bezpiecznie escapuje znaki specjalne LIKE ('%' oraz '_') za pomocą backslasha.
    Należy używać w zapytaniach z klauzulą `LIKE ? ESCAPE '\\'`.
    """
    if not text:
        return ""
    # Najpierw escapujemy sam backslash, potem % i _
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def create_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Tworzy i konfiguruje nowe połączenie z bazą SQLite.
    Każdy wątek/repozytorium tworzy lub otrzymuje własne dedykowane połączenie.
    """
    target_path = db_path if db_path is not None else get_database_path()
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row

    # Optymalizacje SQLite
    if target_path != ":memory:":
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
        except Exception:
            pass
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Inicjalizuje schemat bazy danych i tworzy tabele, jeśli nie istnieją.
    Zwraca aktywne połączenie z zainicjalizowaną bazą.
    """
    conn = create_connection(db_path)
    with conn:
        # Tabela metadanych wersji schematu
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        # Tabela wpisów schowka
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                source_app TEXT,
                pinned INTEGER NOT NULL DEFAULT 0,
                entry_type TEXT NOT NULL DEFAULT 'text'
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_clipboard_created 
            ON clipboard_entries (created_at DESC);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_clipboard_pinned 
            ON clipboard_entries (pinned);
        """)

        # Tabela notatek
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                pinned INTEGER NOT NULL DEFAULT 0
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_updated 
            ON notes (updated_at DESC);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_pinned 
            ON notes (pinned);
        """)

        # Ustawienie wersji schematu
        conn.execute("""
            INSERT OR REPLACE INTO schema_meta (key, value)
            VALUES ('schema_version', ?);
        """, (str(SCHEMA_VERSION),))

    return conn


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Odczytuje aktualną wersję schematu bazy."""
    try:
        cur = conn.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'")
        row = cur.fetchone()
        return int(row["value"]) if row else 0
    except Exception:
        return 0
