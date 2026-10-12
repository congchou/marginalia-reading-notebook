import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from marginalia.database import (
    DuplicateEntryError,
    add_entry,
    delete_entry,
    get_stats,
    import_legacy_csv,
    init_db,
    list_entries,
    update_entry,
)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Path(self.temp_dir.name) / "marginalia.db"
        init_db(self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_db_creates_expected_tables(self):
        with sqlite3.connect(self.db) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"vocabulary", "sentences", "metadata"}.issubset(tables))

    def test_vocabulary_crud_and_search(self):
        entry_id = add_entry(self.db, "vocabulary", {"word": "  Criterion ", "meaning": "标准", "sentence": "A key criterion.", "source": "Paper A", "tags": "methods, ecology"})
        rows = list_entries(self.db, "vocabulary", search="criterion", source="Paper A", status="待复习")
        self.assertEqual(rows[0]["id"], entry_id)
        self.assertEqual(rows[0]["word"], "Criterion")
        update_entry(self.db, "vocabulary", entry_id, {**rows[0], "meaning": "标准；准则", "status": "已掌握"})
        self.assertEqual(list_entries(self.db, "vocabulary", status="已掌握")[0]["meaning"], "标准；准则")
        delete_entry(self.db, "vocabulary", entry_id)
        self.assertEqual(list_entries(self.db, "vocabulary"), [])

    def test_sentence_stats_and_duplicate_rejection(self):
        payload = {"sentence": "Although results vary, the trend remains.", "structure": "让步状语从句", "translation": "尽管结果不同，趋势仍然存在。", "source": "Paper B", "tags": "syntax"}
        add_entry(self.db, "sentences", payload)
        with self.assertRaises(DuplicateEntryError):
            add_entry(self.db, "sentences", payload)
        self.assertEqual(get_stats(self.db), {"vocabulary": 0, "sentences": 1, "pending": 1, "mastered": 0, "sources": 1})

    def test_legacy_csv_import_is_idempotent(self):
        csv_path = Path(self.temp_dir.name) / "vocabulary.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["word", "meaning", "sentence", "source"])
            writer.writeheader()
            writer.writerow({"word": "prevailing", "meaning": "盛行的", "sentence": "A prevailing wind.", "source": "C11"})
            writer.writerow({"word": "criterion", "meaning": "标准", "sentence": "A criterion.", "source": "Null"})
        self.assertEqual(import_legacy_csv(self.db, csv_path), 2)
        self.assertEqual(import_legacy_csv(self.db, csv_path), 0)
        imported = list_entries(self.db, "vocabulary")
        self.assertEqual(len(imported), 2)
        self.assertEqual(imported[0]["source"], "")


if __name__ == "__main__":
    unittest.main()
