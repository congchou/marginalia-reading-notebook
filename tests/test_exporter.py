import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from marginalia.database import add_entry, init_db
from marginalia.exporter import export_entries_csv
from marginalia.importer import parse_csv_upload


class ExporterTests(unittest.TestCase):
    def test_desktop_export_import_round_trip(self):
        with TemporaryDirectory() as folder:
            db_path = Path(folder) / "marginalia.db"
            init_db(db_path)
            add_entry(db_path, "vocabulary", {"word": "criterion", "meaning": "标准, 准则", "sentence": "A key criterion.", "source": "论文 A", "tags": "methods, ecology", "status": "学习中"})
            add_entry(db_path, "sentences", {"sentence": "Although results vary, the trend remains.", "translation": "尽管结果不同，趋势仍在。", "structure": "让步从句", "source": "论文 B", "tags": "syntax", "status": "待复习"})
            exported = export_entries_csv(db_path)
            self.assertTrue(exported.startswith(b"\xef\xbb\xbf"))
            parsed = parse_csv_upload(exported)
            self.assertEqual(parsed.errors, [])
            self.assertEqual(len(parsed.entries), 2)
            self.assertEqual({item.table for item in parsed.entries}, {"vocabulary", "sentences"})
            self.assertIn("标准, 准则", [item.payload.get("meaning") for item in parsed.entries])


if __name__ == "__main__":
    unittest.main()
