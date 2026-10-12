import unittest

from marginalia.ui import display_tags, excerpt, normalize_tags


class UiHelpersTests(unittest.TestCase):
    def test_normalize_tags_deduplicates_and_trims(self):
        self.assertEqual(normalize_tags(" methods，ecology, methods "), "methods, ecology")

    def test_display_tags_escapes_user_content(self):
        html = display_tags("methods, <script>alert(1)</script>")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_excerpt_handles_empty_and_long_text(self):
        self.assertEqual(excerpt(None), "—")
        self.assertEqual(excerpt("abcdefgh", 6), "abcde…")


if __name__ == "__main__":
    unittest.main()
