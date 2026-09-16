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
remain in `bacoco/argh` and are never copied here.

The home page is generated from the real dossier store. `/harness/` explains the
complete path with the same Cuisine/Expert and FR/EN switches, using the compressed
illustrations versioned under `assets/illustrations/`.

`data/taxonomy.json` and `data/visual-taxonomy.json` are synchronized from
`bacoco/argh/publication/argh/navigation/`. They provide the explicit one-to-one
Cuisine/Expert vocabulary and the authored classifications. A new dossier, pattern
or project without an assignment is never hidden or forced into a category: it is
published in an explicit unclassified group until the LLM-authored taxonomy is
revised.

`data/activity.json` is the public change receipt. On every synchronization the
site compares canonical entity hashes with the preceding projection. A new dossier
is labelled as new; a changed dossier keeps its route and is labelled as enriched.
The first projection is only a baseline, so it cannot manufacture 59 simultaneous
news items.

`Sync ARGH public projection` polls private `bacoco/argh/main` hourly through the
read-only deploy key stored as `ARGH_SOURCE_DEPLOY_KEY`. It validates and copies
the complete `publication/argh/entities/` tree and public navigation,
rebuilds every generated route, updates the public activity receipt, verifies the
four authored modes and the absence of the private product name, then commits the
projection to this repository. GitHub Pages serves `main`.
