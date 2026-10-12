import unittest

from marginalia.importer import CSV_COLUMNS, parse_csv_upload


class CsvImporterTests(unittest.TestCase):
    def test_parses_mixed_vocabulary_and_sentence_rows(self):
        content = (
            "type,word,meaning,sentence,translation,structure,source,tags,status\n"
            "生词,criterion,标准,A key criterion.,,,,Paper A,methods,待复习\n"
        )
        # Use quoted fields to exercise a valid nine-column CSV row.
        content = (
            "type,word,meaning,sentence,translation,structure,source,tags,status\n"
            '生词,criterion,标准,"A key criterion.",,,Paper A,methods,待复习\n'
            '难句,,,"Although results vary, the trend remains.","尽管结果不同，趋势仍然存在。",让步状语从句,Paper B,syntax,学习中\n'
        )
        result = parse_csv_upload(content.encode("utf-8"))
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.entries), 2)
        self.assertEqual(result.entries[0].table, "vocabulary")
        self.assertEqual(result.entries[1].payload["status"], "学习中")

    def test_accepts_utf8_bom_and_english_type_aliases(self):
        content = "type,word,meaning,sentence,translation,structure,source,tags,status\nword,prevailing,盛行的,,,,C11,,\n"
        result = parse_csv_upload(content.encode("utf-8-sig"))
        self.assertEqual(result.errors, [])
        self.assertEqual(result.entries[0].payload["status"], "待复习")

    def test_reports_missing_columns_and_invalid_rows(self):
        missing = parse_csv_upload(b"type,word\nword,test\n")
        self.assertIn("缺少列", missing.errors[0])
        content = (
            "type,word,meaning,sentence,translation,structure,source,tags,status\n"
            "unknown,test,,,,,,,,\n"
            "生词,word,,,,,,,,\n"
        )
        result = parse_csv_upload(content.encode())
        self.assertEqual(len(result.errors), 2)
        self.assertIn("第 2 行", result.errors[0])
        self.assertIn("第 3 行", result.errors[1])

    def test_template_columns_are_stable(self):
        self.assertEqual(CSV_COLUMNS[0], "type")
        self.assertEqual(CSV_COLUMNS[-1], "status")


if __name__ == "__main__":
    unittest.main()
