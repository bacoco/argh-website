#!/usr/bin/env python3
"""Verify the complete generated GitHub Pages projection."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLURAL = {"dossier": "dossiers", "project": "projects", "pattern": "patterns"}
MODES = ("argh-fr-cuisine", "argh-fr-specialist", "argh-en-kitchen", "argh-en-specialist")


def main() -> int:
    index = json.loads((ROOT / "data/entities/index.json").read_text(encoding="utf-8"))
    expected = {kind: set() for kind in PLURAL}
    for relative in index["entries"]:
        entity = json.loads((ROOT / "data/entities" / relative).read_text(encoding="utf-8"))
        expected[entity["type"]].add(entity["slug"])
        output = ROOT / PLURAL[entity["type"]] / entity["slug"] / "index.html"
        html = output.read_text(encoding="utf-8")
        if any(mode not in html for mode in MODES):
            raise SystemExit(f"missing authored mode in {output}")

    for kind, plural in PLURAL.items():
        actual = {path.parent.name for path in (ROOT / plural).glob("*/index.html")}
        if actual != expected[kind]:
            raise SystemExit(
                f"stale or missing generated routes for {plural}: "
                f"missing={sorted(expected[kind] - actual)}, stale={sorted(actual - expected[kind])}"
            )
    for required in ("index.html", "dossiers/index.html", "projects/index.html",
                     "patterns/index.html", "atlas/index.html", "about/index.html", "404.html"):
        (ROOT / required).read_text(encoding="utf-8")
    taxonomy = json.loads((ROOT / "data/taxonomy.json").read_text(encoding="utf-8"))
    place_ids = {place["id"] for place in taxonomy["places"]}
    if len(place_ids) != len(taxonomy["places"]):
        raise SystemExit("duplicate place in public navigation")
    for place_id in place_ids:
        (ROOT / "places" / place_id / "index.html").read_text(encoding="utf-8")
    activity = json.loads((ROOT / "data/activity.json").read_text(encoding="utf-8"))
    if activity.get("schema") != "argh/public-activity/v1":
        raise SystemExit("wrong public activity schema")
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    for required in ("argh-home-hero", "argh-updates", "argh-map", "/assets/logo-imagine.png"):
        if required not in home:
            raise SystemExit(f"missing generated home feature: {required}")
    if "Un nouvel endroit" in home:
        raise SystemExit("an unclassified incident must not be rendered as a permanent place")
    for path in ROOT.rglob("*.html"):
        if re.search(r"loriq", path.read_text(encoding="utf-8"), re.I):
            raise SystemExit(f"forbidden product name in generated page: {path}")
    print(json.dumps({kind: len(slugs) for kind, slugs in expected.items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
