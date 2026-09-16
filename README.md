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

`Sync ARGH public projection` polls `bacoco/argh/main` hourly. It validates and
copies the complete `publication/argh/entities/` tree, rebuilds every generated
route, verifies the four authored modes and the absence of the private product
name, then commits the projection to this repository. GitHub Pages serves `main`.
