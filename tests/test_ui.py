import re
import unittest

from marginalia.ui import APP_CSS, display_tags, excerpt, normalize_tags


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

    def test_main_content_clears_fixed_streamlit_header(self):
        match = re.search(r"\.block-container\{[^}]*padding-top:([0-9.]+)rem", APP_CSS)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(float(match.group(1)), 4.5)

    def test_streamlit_header_is_removed_to_prevent_browser_dependent_overlap(self):
        compact_css = re.sub(r"\s+", "", APP_CSS)
        self.assertIn('[data-testid="stHeader"]{display:none!important}', compact_css)


if __name__ == "__main__":
    unittest.main()
