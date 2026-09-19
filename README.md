# ARGH public site

Static GitHub Pages projection of ARGH public intelligence.

The site mirrors the complete public entity store and exposes the same four authored
reader modes on `/dossiers/`, `/projects/`, `/patterns/` and `/atlas/`:

- French / Cuisine;
- French / Technical;
- English / Kitchen;
- English / Technical.

The browser selects an authored string from the entity JSON. It never translates,
simplifies or rewrites editorial text.

Private evidence, source acquisition, scheduler state and operational provenance
remain in `bacoco/loriq-argh` and are never copied here.

The home page is generated from the real dossier store. `/harness/` explains the
complete path with the same Cuisine/Expert and FR/EN switches, using the compressed
illustrations versioned under `assets/illustrations/`.

`data/taxonomy.json` and `data/visual-taxonomy.json` are synchronized from
`bacoco/loriq-argh/publication/argh/navigation/`. They provide the explicit one-to-one
Cuisine/Expert vocabulary and the authored classifications. A new dossier, pattern
or project without an assignment is never hidden or forced into a category: it is
published in an explicit unclassified group until the LLM-authored taxonomy is
revised.

`data/activity.json` is the public change receipt. On every synchronization the
site compares canonical entity hashes with the preceding projection. A new dossier
is labelled as new; a changed dossier keeps its route and is labelled as enriched.
The first projection is only a baseline, so it cannot manufacture 59 simultaneous
news items.

The primary delivery path is the scheduled ChatGPT `CONSUME_BUNDLE` action in
`bacoco/loriq-argh`. After the validated ARGH commit, that action pins this repository,
runs `scripts/sync_from_argh.py`, the site tests, `build.py` and
`scripts/verify_projection.py`, then commits the generated projection to `main`.
The sync also imports validated generated teaching-card images from ARGH visual briefs.
A dossier-specific asset named `dossier-<slug>-640.*` takes precedence over the
generic taxonomy illustration on that dossier page. Teaching-card assets are rendered
full-width below the dossier introduction so their problem, solution and final rule
remain legible; they are never squeezed into the ordinary 300 px decorative thumbnail. It may write no other public
repository and never authors editorial prose here.

The ARGH scheduler performs the deterministic projection directly from the active
ChatGPT invocation and writes the verified result to `main` through the GitHub
connector. GitHub Actions is not used for synchronization, recovery, validation,
build or publication. No file may be added under `.github/workflows/`; a future
workflow would violate this repository contract. GitHub Pages serves `main`.
