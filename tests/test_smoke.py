from pathlib import Path
import tempfile
import unittest

from marginalia.database import init_db


class SmokeTests(unittest.TestCase):
    def test_python_sources_compile_and_database_initializes(self):
        for source in [Path("app.py"), *Path("marginalia").glob("*.py")]:
            compile(source.read_text(encoding="utf-8"), str(source), "exec")
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "app.db"
            init_db(db_path)
            self.assertTrue(db_path.exists())


if __name__ == "__main__":
    unittest.main()
