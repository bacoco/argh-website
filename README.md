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

The home page is generated from the real dossier store. `data/taxonomy.json`
provides the explicit one-to-one Cuisine/Expert navigation vocabulary and assigns
the current dossiers to a place in the lifecycle. A dossier without an assignment
is not forced into a category: it is published immediately under the unclassified
section until the editorial taxonomy is revised.

`data/activity.json` is the public change receipt. On every synchronization the
site compares canonical entity hashes with the preceding projection. A new dossier
is labelled as new; a changed dossier keeps its route and is labelled as enriched.
The first projection is only a baseline, so it cannot manufacture 59 simultaneous
news items.

`Sync ARGH public projection` polls `bacoco/argh/main` hourly. It validates and
copies the complete `publication/argh/entities/` tree, rebuilds every generated
route, updates the public activity receipt, verifies the four authored modes and
the absence of the private product name, then commits the projection to this
repository. GitHub Pages serves `main`.
