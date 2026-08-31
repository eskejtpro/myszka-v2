"""Zestaw testów jednostkowych dla modułu Smart Clipboard & Notes (MyszkaHUD v0.6)."""

import os
import tempfile
import unittest
from datetime import datetime, timezone

from myszkahud.services.clipboard.models import (
    ClipboardEntry,
    Note,
    DEFAULT_CLIPBOARD_HISTORY_LIMIT,
    MAX_ENTRY_LENGTH,
    utc_now,
)
from myszkahud.storage.paths import get_app_data_dir, get_database_path
from myszkahud.storage.database import init_database, create_connection, escape_like_query
from myszkahud.storage.clipboard_repo import SQLiteClipboardRepository
from myszkahud.storage.notes_repo import SQLiteNotesRepository
from myszkahud.services.clipboard.clipboard_service import ClipboardService
from myszkahud.services.clipboard.notes_service import NotesService
from myszkahud.services.clipboard.monitor import (
    ClipboardWriteGuard,
    ClipboardMonitor,
    detect_source_application,
)
from myszkahud.ui.clipboard.clipboard_card import ClipboardCard
from myszkahud.ui.clipboard.note_dialog import NoteDialog
from myszkahud.ui.clipboard.clipboard_window import ClipboardWindow


class MockClipboard:
    """Mock schowka Qt (QClipboard) do testów zdarzeniowych monitora."""

    def __init__(self, initial_text: str = ""):
        self._text = initial_text
        self.dataChanged = self._MockSignal()

    class _MockSignal:
        def __init__(self):
            self.handlers = []

        def connect(self, h):
            self.handlers.append(h)

        def disconnect(self, h=None):
            if h and h in self.handlers:
                self.handlers.remove(h)
            else:
                self.handlers.clear()

        def emit(self):
            for h in list(self.handlers):
                h()

    def text(self) -> str:
        return self._text

    def setText(self, text: str):
        self._text = text
        self.dataChanged.emit()


class TestClipboardModels(unittest.TestCase):
    """Testy modeli danych schowka i notatek."""

    def test_char_count_property(self):
        """Weryfikacja wyliczania char_count jako właściwości dynamicznej."""
        entry = ClipboardEntry(id=1, text="Testowy tekst")
        self.assertEqual(entry.char_count, 13)

        note = Note(id=1, title="Tytuł", content="Treść notatki o długości 24")
        self.assertEqual(note.char_count, 27)

    def test_timezone_aware_utc(self):
        """Weryfikacja strefy czasowej UTC dla znaczników czasu."""
        now = utc_now()
        self.assertIsNotNone(now.tzinfo)
        self.assertEqual(now.tzinfo, timezone.utc)

        entry = ClipboardEntry(text="Tekst")
        self.assertIsNotNone(entry.created_at.tzinfo)
        self.assertEqual(entry.created_at.tzinfo, timezone.utc)


class TestStoragePathsAndDatabase(unittest.TestCase):
    """Testy warstwy ścieżek i bazy SQLite."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_myszkahud.db")
        self.conn = init_database(db_path=self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_database_initialization(self):
        """Weryfikacja tworzenia schematu tabel w SQLite."""
        cur = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row["name"] for row in cur.fetchall()]
        self.assertIn("clipboard_entries", tables)
        self.assertIn("notes", tables)
        self.assertIn("schema_meta", tables)

    def test_paths_resolution(self):
        """Weryfikacja poprawnego generowania ścieżek danych aplikacji."""
        app_dir = get_app_data_dir()
        self.assertTrue(os.path.isabs(app_dir))
        db_path = get_database_path()
        self.assertTrue(db_path.endswith(".db") or db_path.endswith(".sqlite"))


class TestClipboardRepository(unittest.TestCase):
    """Testy operacji CRUD dla repozytorium schowka."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_repo.db")
        self.repo = SQLiteClipboardRepository(db_path=self.db_path)

    def tearDown(self):
        self.repo._conn.close()
        self.temp_dir.cleanup()

    def test_insert_and_get(self):
        entry = ClipboardEntry(text="Klucz API: 12345", source_app="VSCode")
        saved = self.repo.add_entry(entry)
        self.assertIsNotNone(saved.id)

        fetched = self.repo.get_entry_by_id(saved.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.text, "Klucz API: 12345")
        self.assertEqual(fetched.source_app, "VSCode")
        self.assertFalse(fetched.pinned)

    def test_pin_toggle_clipboard(self):
        entry = self.repo.add_entry(ClipboardEntry(text="Ważna notatka schowka"))
        self.assertFalse(entry.pinned)

        self.repo.set_pinned(entry.id, True)
        self.assertTrue(self.repo.get_entry_by_id(entry.id).pinned)

        self.repo.set_pinned(entry.id, False)
        self.assertFalse(self.repo.get_entry_by_id(entry.id).pinned)

    def test_search_clipboard(self):
        self.repo.add_entry(ClipboardEntry(text="Pierwszy wpis Python"))
        self.repo.add_entry(ClipboardEntry(text="Drugi wpis TypeScript"))
        self.repo.add_entry(ClipboardEntry(text="Trzeci wpis Python i PySide6"))

        results = self.repo.list_entries(search_query="Python")
        self.assertEqual(len(results), 2)

    def test_trim_history_preserves_pinned(self):
        """Sprawdzenie czy czyszczenie limitu historii nie usuwa przypiętych wpisów."""
        # Wstawiamy 5 wpisów, z czego wpis 1 i 2 są przypięte
        e1 = self.repo.add_entry(ClipboardEntry(text="Wpis 1 (pinned)", pinned=True))
        e2 = self.repo.add_entry(ClipboardEntry(text="Wpis 2 (pinned)", pinned=True))
        e3 = self.repo.add_entry(ClipboardEntry(text="Wpis 3 (unpinned)"))
        e4 = self.repo.add_entry(ClipboardEntry(text="Wpis 4 (unpinned)"))
        e5 = self.repo.add_entry(ClipboardEntry(text="Wpis 5 (unpinned)"))

        # Obcinamy historię do limitu 2
        trimmed_count = self.repo.trim_history(max_unpinned_limit=2)
        self.assertEqual(trimmed_count, 1)  # Wpis 3 został usunięty

        all_entries = self.repo.list_entries(limit=10)
        all_ids = [e.id for e in all_entries]
        self.assertIn(e1.id, all_ids)
        self.assertIn(e2.id, all_ids)
        self.assertIn(e5.id, all_ids)
        self.assertIn(e4.id, all_ids)
        self.assertNotIn(e3.id, all_ids)


class TestNotesRepository(unittest.TestCase):
    """Testy operacji CRUD dla repozytorium notatek."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_notes.db")
        self.repo = SQLiteNotesRepository(db_path=self.db_path)

    def tearDown(self):
        self.repo._conn.close()
        self.temp_dir.cleanup()

    def test_notes_crud(self):
        # Create
        note = self.repo.add_note(Note(title="Lista zakupów", content="Mleko, Kawa, Chleb"))
        self.assertIsNotNone(note.id)

        # Read
        fetched = self.repo.get_note_by_id(note.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Lista zakupów")

        # Update
        self.assertTrue(self.repo.update_note(note.id, "Lista zakupów (zaktualizowana)", "Mleko, Kawa, Cukier"))

        updated = self.repo.get_note_by_id(note.id)
        self.assertEqual(updated.title, "Lista zakupów (zaktualizowana)")
        self.assertEqual(updated.content, "Mleko, Kawa, Cukier")

        # Pin toggle
        self.repo.set_pinned(note.id, True)
        self.assertTrue(self.repo.get_note_by_id(note.id).pinned)

        # Delete
        self.assertTrue(self.repo.delete_note(note.id))
        self.assertIsNone(self.repo.get_note_by_id(note.id))

    def test_search_notes(self):
        self.repo.add_note(Note(title="Plan projektu", content="Architektura Windows i PySide6"))
        self.repo.add_note(Note(title="Podsumowanie dnia", content="Wszystko ukończone"))

        results = self.repo.list_notes(search_query="Architektura")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Plan projektu")


class TestClipboardService(unittest.TestCase):
    """Testy logiki biznesowej ClipboardService."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_srv.db")
        self.repo = SQLiteClipboardRepository(db_path=self.db_path)
        self.service = ClipboardService(repository=self.repo, history_limit=5)

    def tearDown(self):
        self.repo._conn.close()
        self.temp_dir.cleanup()

    def test_duplicate_consecutive_texts_not_recorded(self):
        """Zabezpieczenie przed zapisem identycznego tekstu dwa razy z rzędu."""
        e1 = self.service.add_clipboard_text("Identyczny tekst")
        self.assertIsNotNone(e1)

        # Próba dodania tego samego tekstu zaraz po nim - powinno zostać odrzucone
        e2 = self.service.add_clipboard_text("Identyczny tekst")
        self.assertIsNone(e2)

        all_entries = self.service.list_entries()
        self.assertEqual(len(all_entries), 1)

    def test_whitespace_only_not_recorded(self):
        """Ignorowanie pustych i białych znaków."""
        self.assertIsNone(self.service.add_clipboard_text(""))
        self.assertIsNone(self.service.add_clipboard_text("   \n\t  "))
        self.assertEqual(len(self.service.list_entries()), 0)

    def test_history_paused(self):
        """Pauzowanie rejestrowania historii schowka."""
        self.assertFalse(self.service.is_paused)
        self.service.set_paused(True)
        self.assertTrue(self.service.is_paused)

        entry = self.service.add_clipboard_text("Nowy tekst podczas pauzy")
        self.assertIsNone(entry)
        self.assertEqual(len(self.service.list_entries()), 0)

        self.service.set_paused(False)
        entry_after = self.service.add_clipboard_text("Tekst po wznowieniu")
        self.assertIsNotNone(entry_after)
        self.assertEqual(len(self.service.list_entries()), 1)


class TestClipboardMonitor(unittest.TestCase):
    """Testy zdarzeniowego monitora schowka i zabezpieczeń Self-Change Suppression."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_mon.db")
        self.repo = SQLiteClipboardRepository(db_path=self.db_path)
        self.service = ClipboardService(repository=self.repo)
        self.guard = ClipboardWriteGuard()
        self.monitor = ClipboardMonitor(
            service=self.service,
            write_guard=self.guard,
            window_manager=None
        )

    def tearDown(self):
        self.monitor.stop_monitoring()
        self.repo._conn.close()
        self.temp_dir.cleanup()

    def test_monitor_startup_does_not_capture_stale_clipboard(self):
        """Startup nie zapisuje starego tekstu znajdującego się już w schowku."""
        mock_clip = MockClipboard(initial_text="Stary tekst ze schowka sprzed startu")
        self.monitor.start_monitoring(clipboard_instance=mock_clip)

        # Brak wpisów w bazie
        self.assertEqual(len(self.service.list_entries()), 0)

        # Nowe zdarzenie schowka
        mock_clip.setText("Świeżo skopiowany tekst")
        self.assertEqual(len(self.service.list_entries()), 1)
        self.assertEqual(self.service.list_entries()[0].text, "Świeżo skopiowany tekst")

    def test_internal_clipboard_write_not_recorded(self):
        """Self-Change Suppression: wewnętrzny zapis MyszkaHUD nie trafia ponownie do historii."""
        mock_clip = MockClipboard(initial_text="")
        self.monitor.start_monitoring(clipboard_instance=mock_clip)

        text_to_paste = "Tekst wybrany z MyszkaHUD do wklejenia"
        with self.guard.suppress(text_to_paste):
            mock_clip.setText(text_to_paste)

        # Zapis został zablokowany przez guard
        self.assertEqual(len(self.service.list_entries()), 0)

        # Zwykłe zewnętrzne skopiowanie powinno działać normalnie
        mock_clip.setText("Zewnętrzny tekst")
        self.assertEqual(len(self.service.list_entries()), 1)
        self.assertEqual(self.service.list_entries()[0].text, "Zewnętrzny tekst")

    def test_source_app_best_effort(self):
        """Bezpieczne wykrywanie aplikacji źródłowej bez rzucania wyjątków."""
        source = detect_source_application(window_manager=None)
        # Na maszynie testowej (Linux / headless) powinno bezpiecznie zwrócić None
        self.assertIsNone(source)


class TestClipboardUIComponents(unittest.TestCase):
    """Testy inicjalizacji i struktury komponentów interfejsu."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_ui.db")
        self.clip_repo = SQLiteClipboardRepository(db_path=self.db_path)
        self.notes_repo = SQLiteNotesRepository(db_path=self.db_path)
        self.clip_service = ClipboardService(repository=self.clip_repo)
        self.notes_service = NotesService(repository=self.notes_repo)

    def tearDown(self):
        self.clip_repo._conn.close()
        self.notes_repo._conn.close()
        self.temp_dir.cleanup()

    def test_clipboard_card_and_window_creation(self):
        entry = ClipboardEntry(id=1, text="Testowy wpis schowka", source_app="Explorer")
        card = ClipboardCard(entry)
        self.assertIsNotNone(card)

        note = Note(id=1, title="Tytuł", content="Treść")
        note_card = ClipboardCard(note)
        self.assertIsNotNone(note_card)

        dialog = NoteDialog(title="Nowa notatka", content="Treść testowa")
        self.assertIsNotNone(dialog)

        window = ClipboardWindow(
            clipboard_service=self.clip_service,
            notes_service=self.notes_service
        )
        self.assertIsNotNone(window)
        self.assertEqual(window.width(), 780)
        self.assertEqual(window.height(), 540)


if __name__ == "__main__":
    unittest.main()
