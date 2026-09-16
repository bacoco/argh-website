import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.sync_from_argh import SyncError, sync


def entity(kind, slug):
    plural = {"dossier": "dossiers", "project": "projects", "pattern": "patterns"}[kind]
    return {
        "schema": "argh/public-entity/v1", "id": f"{kind}:{slug}", "type": kind,
        "slug": slug, "route": f"/{plural}/{slug}/",
    }


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def source_store(root, values):
    entries = {}
    for value in values:
        plural = {"dossier": "dossiers", "project": "projects", "pattern": "patterns"}[
            value["type"]
        ]
        relative = f"{plural}/{value['slug']}.json"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
        path.write_bytes(raw)
        entries[relative] = blob(raw)
    (root / "README.md").write_text("public store\n")
    (root / "index.json").write_text(json.dumps({
        "schema": "argh/public-entity-index/v2", "generated_at": "now",
        "entries": entries,
    }, indent=2) + "\n")


class SyncTests(unittest.TestCase):
    def test_sync_replaces_complete_tree_and_writes_meta(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            website = root / "website"
            (website / "data/entities/dossiers").mkdir(parents=True)
            (website / "data/entities/dossiers/stale.json").write_text("{}")
            source_store(source, [entity("dossier", "one"), entity("project", "alpha")])
            result = sync(source, website, "a" * 40, "2026-09-16T12:00:00Z")
            self.assertEqual(result["dossier"], 1)
            self.assertEqual(result["project"], 1)
            self.assertFalse((website / "data/entities/dossiers/stale.json").exists())
            meta = json.loads((website / "data/meta.json").read_text())
            self.assertEqual(meta["source_head"], "a" * 40)
            activity = json.loads((website / "data/activity.json").read_text())
            self.assertEqual(activity["events"], [])

    def test_sync_records_new_and_enriched_dossiers_after_the_baseline(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            website = root / "website"
            first = entity("dossier", "one")
            source_store(source, [first])
            sync(source, website, "a" * 40, "2026-09-16T12:00:00Z")

            first["revision"] = "enriched"
            source_store(source, [first, entity("dossier", "two")])
            result = sync(source, website, "b" * 40, "2026-09-16T13:00:00Z")

            self.assertEqual(result["new_dossiers"], 1)
            self.assertEqual(result["updated_dossiers"], 1)
            activity = json.loads((website / "data/activity.json").read_text())
            by_path = {event["entity_path"]: event for event in activity["events"]}
            self.assertEqual(by_path["dossiers/one.json"]["kind"], "updated")
            self.assertEqual(by_path["dossiers/two.json"]["kind"], "new")

    def test_invalid_source_does_not_touch_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            website = root / "website"
            source_store(source, [entity("dossier", "one")])
            destination = website / "data/entities"
            destination.mkdir(parents=True)
            marker = destination / "keep.txt"
            marker.write_text("unchanged")
            target = source / "dossiers/one.json"
            target.write_text(target.read_text() + " ")
            with self.assertRaisesRegex(SyncError, "hash mismatch"):
                sync(source, website, "a" * 40, "2026-09-16T12:00:00Z")
            self.assertEqual(marker.read_text(), "unchanged")


if __name__ == "__main__":
    unittest.main()
