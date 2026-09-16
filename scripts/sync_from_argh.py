#!/usr/bin/env python3
"""Synchronize the validated ARGH entity store into the static projection."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


INDEX_SCHEMA = "argh/public-entity-index/v2"
ENTITY_SCHEMA = "argh/public-entity/v1"
RELATIVE_ENTITY = re.compile(r"(dossiers|projects|patterns)/[a-z0-9]+(?:-[a-z0-9]+)*\.json")
SHA = re.compile(r"[a-f0-9]{40}")
FORBIDDEN_NAME = re.compile(r"loriq", re.I)


class SyncError(ValueError):
    pass


def _blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def validate_source(source: Path) -> dict[str, int]:
    try:
        index = json.loads((source / "index.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncError("source index is not valid JSON") from exc
    if not isinstance(index, dict) or index.get("schema") != INDEX_SCHEMA:
        raise SyncError("wrong source index schema")
    if set(index) != {"schema", "generated_at", "entries"} or not isinstance(index["entries"], dict):
        raise SyncError("source index fields mismatch")

    expected = set(index["entries"])
    actual = {
        path.relative_to(source).as_posix()
        for plural in ("dossiers", "projects", "patterns")
        for path in (source / plural).glob("*.json")
    }
    if expected != actual:
        raise SyncError(
            f"source entity/index mismatch: missing={sorted(expected - actual)}, "
            f"unindexed={sorted(actual - expected)}"
        )

    counts = {"dossier": 0, "project": 0, "pattern": 0}
    seen_ids: set[str] = set()
    seen_routes: set[str] = set()
    for relative, expected_hash in index["entries"].items():
        if not RELATIVE_ENTITY.fullmatch(relative) or not SHA.fullmatch(expected_hash):
            raise SyncError(f"invalid source index entry: {relative}")
        raw = (source / relative).read_bytes()
        if _blob_sha1(raw) != expected_hash:
            raise SyncError(f"source entity hash mismatch: {relative}")
        if FORBIDDEN_NAME.search(raw.decode("utf-8")):
            raise SyncError(f"forbidden product name in public entity: {relative}")
        try:
            entity = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SyncError(f"invalid source entity JSON: {relative}") from exc
        if not isinstance(entity, dict) or entity.get("schema") != ENTITY_SCHEMA:
            raise SyncError(f"wrong source entity schema: {relative}")
        kind = entity.get("type")
        if kind not in counts:
            raise SyncError(f"invalid source entity type: {relative}")
        if entity.get("id") in seen_ids or entity.get("route") in seen_routes:
            raise SyncError(f"duplicate source entity identity: {relative}")
        seen_ids.add(entity.get("id"))
        seen_routes.add(entity.get("route"))
        counts[kind] += 1
    return counts


def _same_tree(left: Path, right: Path) -> bool:
    left_files = {path.relative_to(left) for path in left.rglob("*") if path.is_file()}
    right_files = {path.relative_to(right) for path in right.rglob("*") if path.is_file()}
    return left_files == right_files and all(
        (left / relative).read_bytes() == (right / relative).read_bytes()
        for relative in left_files
    )


def sync(source: Path, website: Path, source_head: str, generated_at: str) -> dict[str, object]:
    if not SHA.fullmatch(source_head):
        raise SyncError("source_head must be a full Git SHA")
    if not generated_at.strip():
        raise SyncError("generated_at is required")
    counts = validate_source(source)
    destination = website / "data" / "entities"
    changed = not destination.exists() or not _same_tree(source, destination)
    if changed:
        staged = website / "data" / ".entities-sync"
        backup = website / "data" / ".entities-backup"
        if staged.exists() or backup.exists():
            raise SyncError("stale synchronization directory exists")
        shutil.copytree(source, staged)
        try:
            if destination.exists():
                destination.rename(backup)
            staged.rename(destination)
        except BaseException:
            if not destination.exists() and backup.exists():
                backup.rename(destination)
            raise
        finally:
            shutil.rmtree(staged, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)

    meta_path = website / "data" / "meta.json"
    previous = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    if previous.get("source_head") == source_head:
        projection_generated_at = previous.get("generated_at", generated_at)
    else:
        projection_generated_at = generated_at
    meta = {
        "schema": "argh/static-projection/v1",
        "generated_at": projection_generated_at,
        "source_repository": "bacoco/argh",
        "source_head": source_head,
        "dossier_count": counts["dossier"],
        "project_count": counts["project"],
        "pattern_count": counts["pattern"],
        "publication_mode": "static_github_pages",
    }
    raw_meta = json.dumps(meta, ensure_ascii=False, indent=2) + "\n"
    meta_changed = not meta_path.exists() or meta_path.read_text(encoding="utf-8") != raw_meta
    if meta_changed:
        meta_path.write_text(raw_meta, encoding="utf-8")
    return {"source_head": source_head, "data_changed": changed,
            "meta_changed": meta_changed, **counts}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--website", type=Path, default=Path("."))
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--generated-at", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(sync(args.source, args.website, args.source_head, args.generated_at),
                         ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "REFUSED", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
