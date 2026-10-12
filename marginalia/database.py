"""SQLite persistence for Marginalia."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any, Mapping

STATUSES = ("待复习", "学习中", "已掌握")
DEFAULT_STATUS = STATUSES[0]
TABLES = {"vocabulary", "sentences"}
FIELDS = {
    "vocabulary": ("word", "meaning", "sentence", "source", "tags", "status"),
    "sentences": ("sentence", "structure", "translation", "source", "tags", "status"),
}
REQUIRED = {"vocabulary": ("word", "meaning"), "sentences": ("sentence", "translation")}


class DuplicateEntryError(ValueError):
    """Raised when an entry with the same primary text already exists."""


def _table(name: str) -> str:
    if name not in TABLES:
        raise ValueError(f"Unsupported table: {name}")
    return name


def _connect(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = """
    CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL COLLATE NOCASE UNIQUE,
        meaning TEXT NOT NULL,
        sentence TEXT NOT NULL DEFAULT '',
        source TEXT NOT NULL DEFAULT '',
        tags TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT '待复习',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS sentences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sentence TEXT NOT NULL COLLATE NOCASE UNIQUE,
        structure TEXT NOT NULL DEFAULT '',
        translation TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT '',
        tags TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT '待复习',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """
    with _connect(path) as connection:
        connection.executescript(schema)
        for table in TABLES:
            connection.execute(f"UPDATE {table} SET source = '' WHERE lower(trim(source)) IN ('null', 'nan', 'none')")


def _clean_payload(table: str, payload: Mapping[str, Any]) -> dict[str, str]:
    result = {field: str(payload.get(field) or "").strip() for field in FIELDS[table]}
    result["status"] = result["status"] or DEFAULT_STATUS
    if result["status"] not in STATUSES:
        raise ValueError("无效的学习状态")
    missing = [field for field in REQUIRED[table] if not result[field]]
    if missing:
        raise ValueError(f"请填写必填项：{', '.join(missing)}")
    return result


def add_entry(db_path: str | Path, table: str, payload: Mapping[str, Any]) -> int:
    table = _table(table)
    data = _clean_payload(table, payload)
    fields = FIELDS[table]
    placeholders = ", ".join("?" for _ in fields)
    try:
        with _connect(db_path) as connection:
            cursor = connection.execute(
                f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})",
                [data[field] for field in fields],
            )
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise DuplicateEntryError("这条内容已经存在于资料库中") from exc


def update_entry(db_path: str | Path, table: str, entry_id: int, payload: Mapping[str, Any]) -> None:
    table = _table(table)
    data = _clean_payload(table, payload)
    fields = FIELDS[table]
    assignments = ", ".join(f"{field} = ?" for field in fields)
    try:
        with _connect(db_path) as connection:
            cursor = connection.execute(
                f"UPDATE {table} SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                [*[data[field] for field in fields], entry_id],
            )
            if cursor.rowcount == 0:
                raise KeyError(f"Entry {entry_id} does not exist")
    except sqlite3.IntegrityError as exc:
        raise DuplicateEntryError("修改后的内容与已有条目重复") from exc


def delete_entry(db_path: str | Path, table: str, entry_id: int) -> None:
    table = _table(table)
    with _connect(db_path) as connection:
        connection.execute(f"DELETE FROM {table} WHERE id = ?", (entry_id,))


def list_entries(
    db_path: str | Path,
    table: str,
    *,
    search: str = "",
    source: str = "",
    status: str = "",
    tag: str = "",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    table = _table(table)
    clauses: list[str] = []
    params: list[Any] = []
    searchable = FIELDS[table][:-1]
    if search.strip():
        token = f"%{search.strip()}%"
        clauses.append("(" + " OR ".join(f"{field} LIKE ?" for field in searchable) + ")")
        params.extend([token] * len(searchable))
    if source:
        clauses.append("source = ?")
        params.append(source)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if tag:
        clauses.append("tags LIKE ?")
        params.append(f"%{tag}%")
    query = f"SELECT * FROM {table}"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC, id DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(int(limit))
    with _connect(db_path) as connection:
        return [dict(row) for row in connection.execute(query, params).fetchall()]


def get_sources(db_path: str | Path) -> list[str]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT source FROM vocabulary WHERE source <> '' UNION SELECT source FROM sentences WHERE source <> '' ORDER BY source"
        ).fetchall()
    return [str(row[0]) for row in rows]


def get_stats(db_path: str | Path) -> dict[str, int]:
    with _connect(db_path) as connection:
        vocabulary = connection.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0]
        sentences = connection.execute("SELECT COUNT(*) FROM sentences").fetchone()[0]
        pending = connection.execute(
            "SELECT (SELECT COUNT(*) FROM vocabulary WHERE status <> '已掌握') + (SELECT COUNT(*) FROM sentences WHERE status <> '已掌握')"
        ).fetchone()[0]
        mastered = connection.execute(
            "SELECT (SELECT COUNT(*) FROM vocabulary WHERE status = '已掌握') + (SELECT COUNT(*) FROM sentences WHERE status = '已掌握')"
        ).fetchone()[0]
        sources = len(get_sources(db_path))
    return {"vocabulary": vocabulary, "sentences": sentences, "pending": pending, "mastered": mastered, "sources": sources}


def import_legacy_csv(db_path: str | Path, csv_path: str | Path) -> int:
    csv_path = Path(csv_path)
    marker = f"legacy_import:{csv_path.resolve()}"
    if not csv_path.exists():
        return 0
    with _connect(db_path) as connection:
        if connection.execute("SELECT 1 FROM metadata WHERE key = ?", (marker,)).fetchone():
            return 0
    imported = 0
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            cleaned_row = {
                key: ("" if str(value or "").strip().lower() in {"null", "nan", "none"} else value)
                for key, value in row.items()
            }
            try:
                add_entry(db_path, "vocabulary", {**cleaned_row, "tags": "", "status": DEFAULT_STATUS})
                imported += 1
            except (DuplicateEntryError, ValueError):
                continue
    with _connect(db_path) as connection:
        connection.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", (marker, str(imported)))
    return imported
