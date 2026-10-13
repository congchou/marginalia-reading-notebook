"""Conflict-aware synchronization between local SQLite cards and cloud cards."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .database import DuplicateEntryError, add_entry, delete_entry, list_entries, update_entry

FIELDS = ("kind", "word", "meaning", "sentence", "translation", "structure", "source", "tags", "status")
TABLES = {"word": "vocabulary", "sentence": "sentences"}


@dataclass
class SyncResult:
    uploaded: int = 0
    downloaded: int = 0
    conflicts: int = 0


def init_sync(db_path: str | Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sync_links (
                table_name TEXT NOT NULL,
                local_id INTEGER NOT NULL,
                cloud_id TEXT NOT NULL UNIQUE,
                version INTEGER NOT NULL,
                payload_hash TEXT NOT NULL,
                deleted INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (table_name, local_id)
            )
        """)


def bind_sync_owner(db_path: str | Path, user_id: str) -> None:
    """Prevent a second account from silently receiving this database's cards."""
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("SELECT value FROM metadata WHERE key = 'sync_owner'").fetchone()
        if row and row[0] != user_id:
            raise ValueError("本机资料库已关联另一同步账号；请先导出 CSV 备份，不要直接切换账号")
        if not row:
            connection.execute("INSERT INTO metadata(key, value) VALUES ('sync_owner', ?)", (user_id,))


def card_from_local(table: str, item: dict[str, Any], cloud_id: str) -> dict[str, Any]:
    return {"id": cloud_id, "kind": "word" if table == "vocabulary" else "sentence",
            **{field: str(item.get(field) or "") for field in FIELDS if field != "kind"}, "deleted": False}


def payload_hash(card: dict[str, Any]) -> str:
    content = {field: str(card.get(field) or "") for field in FIELDS}
    return hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def identity(card: dict[str, Any]) -> tuple[str, str]:
    main = card.get("word") if card.get("kind") == "word" else card.get("sentence")
    return (str(card.get("kind") or ""), str(main or "").strip().casefold())


def save_link(db_path: str | Path, table: str, local_id: int, cloud_id: str, version: int,
              content_hash: str, deleted: bool = False) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            INSERT INTO sync_links(table_name, local_id, cloud_id, version, payload_hash, deleted)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(table_name, local_id) DO UPDATE SET
              cloud_id=excluded.cloud_id, version=excluded.version,
              payload_hash=excluded.payload_hash, deleted=excluded.deleted
        """, (table, local_id, cloud_id, version, content_hash, int(deleted)))


def payload_for_table(table: str, card: dict[str, Any]) -> dict[str, str]:
    fields = ("word", "meaning", "sentence", "source", "tags", "status") if table == "vocabulary" else ("sentence", "translation", "structure", "source", "tags", "status")
    return {field: str(card.get(field) or "") for field in fields}


def sync_once(db_path: str | Path, cloud: Any) -> SyncResult:
    init_sync(db_path)
    result = SyncResult()
    remote = cloud.list_cards()
    remote_by_id = {card["id"]: card for card in remote}
    remote_by_identity = {identity(card): card for card in remote if not card.get("deleted")}
    local = {(table, item["id"]): item for table in ("vocabulary", "sentences") for item in list_entries(db_path, table)}
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        links = {(row["table_name"], row["local_id"]): dict(row) for row in connection.execute("SELECT * FROM sync_links")}
    mapped_cloud_ids = {link["cloud_id"] for link in links.values()}

    for (table, local_id), link in links.items():
        item = local.get((table, local_id))
        server = remote_by_id.get(link["cloud_id"])
        if item is None:
            if link["deleted"]:
                continue
            if not server or server["revision"] != link["version"]:
                result.conflicts += 1
                continue
            updated = cloud.update_card({**server, "deleted": True}, link["version"])
            if updated is None:
                result.conflicts += 1
                continue
            save_link(db_path, table, local_id, link["cloud_id"], updated["revision"], link["payload_hash"], True)
            result.uploaded += 1
            continue

        card = card_from_local(table, item, link["cloud_id"])
        current_hash = payload_hash(card)
        if current_hash != link["payload_hash"]:
            if not server or server["revision"] != link["version"]:
                result.conflicts += 1
                continue
            updated = cloud.update_card(card, link["version"])
            if updated is None:
                result.conflicts += 1
                continue
            save_link(db_path, table, local_id, link["cloud_id"], updated["revision"], current_hash)
            result.uploaded += 1
        elif server and server["revision"] > link["version"]:
            if server.get("deleted"):
                delete_entry(db_path, table, local_id)
                save_link(db_path, table, local_id, link["cloud_id"], server["revision"], current_hash, True)
                result.downloaded += 1
            else:
                try:
                    update_entry(db_path, table, local_id, payload_for_table(table, server))
                except (ValueError, DuplicateEntryError):
                    result.conflicts += 1
                    continue
                save_link(db_path, table, local_id, link["cloud_id"], server["revision"], payload_hash(server))
                result.downloaded += 1

    for (table, local_id), item in local.items():
        if (table, local_id) in links:
            continue
        new_id = str(uuid.uuid4())
        card = card_from_local(table, item, new_id)
        duplicate = remote_by_identity.get(identity(card))
        if duplicate:
            if payload_hash(duplicate) != payload_hash(card):
                result.conflicts += 1
                continue
            save_link(db_path, table, local_id, duplicate["id"], duplicate["revision"], payload_hash(card))
            mapped_cloud_ids.add(duplicate["id"])
            continue
        created = cloud.create_card(card)
        save_link(db_path, table, local_id, created["id"], created["revision"], payload_hash(card))
        mapped_cloud_ids.add(created["id"])
        result.uploaded += 1

    for card in remote:
        if card["id"] in mapped_cloud_ids or card.get("deleted"):
            continue
        table = TABLES[card["kind"]]
        if any(identity(card_from_local(local_table, item, "")) == identity(card) for (local_table, _), item in local.items()):
            result.conflicts += 1
            continue
        try:
            local_id = add_entry(db_path, table, payload_for_table(table, card))
        except (ValueError, DuplicateEntryError):
            result.conflicts += 1
            continue
        save_link(db_path, table, local_id, card["id"], card["revision"], payload_hash(card))
        result.downloaded += 1

    return result
