# ARGH public entity store

This directory is the canonical public editorial store after the entity-store migration.

```text
publication/argh/entities/
  index.json
  dossiers/<slug>.json
  projects/<slug>.json
  patterns/<slug>.json
```

Rules:

- one JSON file = one public entity;
- each entity uses `argh/public-entity/v1`;
- every slot contains FR/Cuisine, FR/Expert, EN/Kitchen and EN/Expert;
- Cuisine/Kitchen is independently authored from meaning, never lexically transformed from Expert;
- exact source/provenance stays private and is forbidden in this tree;
- `index.json` uses `argh/public-entity-index/v2` and binds each entity to its exact Git blob identity; it contains no editorial prose;
- Git history is the editorial history; do not duplicate the site into a monolithic editorial JSON;
- WordPress mirrors this tree under `wp-content/uploads/argh/entities/` and renders it through the shared renderer.

The repository corpus is complete and canonical. Live activation is a separate deployment gate: the WordPress mirror, renderer 1.4+ and all four reader/language modes must be read back successfully before `entity_store_target.status` is changed to `active`.
