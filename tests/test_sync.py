import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from marginalia.database import add_entry, delete_entry, init_db, list_entries, update_entry
from marginalia.sync import init_sync, sync_once, bind_sync_owner


class FakeCloud:
    def __init__(self, rows=()):
        self.rows = {row["id"]: dict(row) for row in rows}

    def list_cards(self):
        return list(self.rows.values())

    def create_card(self, card):
        row = {**card, "revision": 1, "deleted": False}
        self.rows[row["id"]] = row
        return row

    def update_card(self, card, version):
        previous = self.rows.get(card["id"])
        if previous is None or previous["revision"] != version:
            return None
        row = {**previous, **card, "revision": version + 1}
        self.rows[row["id"]] = row
        return row


def remote_word(card_id="11111111-1111-4111-8111-111111111111", **changes):
    return {"id": card_id, "kind": "word", "word": "criterion", "meaning": "标准", "sentence": "", "translation": "", "structure": "", "source": "", "tags": "", "status": "待复习", "deleted": False, "revision": 1, **changes}


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.db = Path(self.temp.name) / "test.db"
        init_db(self.db)
        init_sync(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_uploads_existing_local_card_then_changed_content(self):
        local_id = add_entry(self.db, "vocabulary", {"word": "criterion", "meaning": "标准"})
        cloud = FakeCloud()
        first = sync_once(self.db, cloud)
        self.assertEqual(first.uploaded, 1)
        cloud_id = next(iter(cloud.rows))
        update_entry(self.db, "vocabulary", local_id, {"word": "criterion", "meaning": "准则"})
        second = sync_once(self.db, cloud)
        self.assertEqual(second.uploaded, 1)
        self.assertEqual(cloud.rows[cloud_id]["revision"], 2)
        self.assertEqual(cloud.rows[cloud_id]["meaning"], "准则")

    def test_downloads_cloud_card_and_later_remote_edit(self):
        cloud = FakeCloud([remote_word()])
        first = sync_once(self.db, cloud)
        self.assertEqual(first.downloaded, 1)
        self.assertEqual(list_entries(self.db, "vocabulary")[0]["meaning"], "标准")
        cloud.rows[next(iter(cloud.rows))]["meaning"] = "标准；准则"
        cloud.rows[next(iter(cloud.rows))]["revision"] = 2
        second = sync_once(self.db, cloud)
        self.assertEqual(second.downloaded, 1)
        self.assertEqual(list_entries(self.db, "vocabulary")[0]["meaning"], "标准；准则")

    def test_local_delete_uploads_tombstone(self):
        local_id = add_entry(self.db, "vocabulary", {"word": "criterion", "meaning": "标准"})
        cloud = FakeCloud()
        sync_once(self.db, cloud)
        delete_entry(self.db, "vocabulary", local_id)
        result = sync_once(self.db, cloud)
        self.assertEqual(result.uploaded, 1)
        self.assertTrue(next(iter(cloud.rows.values()))["deleted"])

    def test_conflict_keeps_both_local_and_remote_edits(self):
        local_id = add_entry(self.db, "vocabulary", {"word": "criterion", "meaning": "标准"})
        cloud = FakeCloud()
        sync_once(self.db, cloud)
        update_entry(self.db, "vocabulary", local_id, {"word": "criterion", "meaning": "本地修改"})
        remote = next(iter(cloud.rows.values()))
        remote["meaning"] = "手机修改"
        remote["revision"] = 2
        result = sync_once(self.db, cloud)
        self.assertEqual(result.conflicts, 1)
        self.assertEqual(list_entries(self.db, "vocabulary")[0]["meaning"], "本地修改")
        self.assertEqual(remote["meaning"], "手机修改")

    def test_local_database_cannot_be_bound_to_a_different_account(self):
        bind_sync_owner(self.db, "user-1")
        bind_sync_owner(self.db, "user-1")
        with self.assertRaises(ValueError):
            bind_sync_owner(self.db, "user-2")


if __name__ == "__main__":
    unittest.main()
