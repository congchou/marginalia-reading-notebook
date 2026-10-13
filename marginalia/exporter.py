"""Portable CSV backup shared by the desktop app and iPhone PWA."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from .database import list_entries
from .importer import CSV_COLUMNS


def export_entries_csv(db_path: str | Path) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for table in ("vocabulary", "sentences"):
        for entry in list_entries(db_path, table):
            writer.writerow({
                "type": "生词" if table == "vocabulary" else "难句",
                "word": entry.get("word", ""),
                "meaning": entry.get("meaning", ""),
                "sentence": entry.get("sentence", ""),
                "translation": entry.get("translation", ""),
                "structure": entry.get("structure", ""),
                "source": entry.get("source", ""),
                "tags": entry.get("tags", ""),
                "status": entry.get("status", ""),
            })
    return output.getvalue().encode("utf-8-sig")
