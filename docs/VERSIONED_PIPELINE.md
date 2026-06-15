# Versioned PyATB LSP Pipeline

Tracking issues: https://github.com/newtontech/pyatb-lsp/issues/34 and #35

This repository keeps PyATB diagnostics reproducible by treating the
documentation and provenance layer as checked-in build artifacts:

1. Mirror official PyATB documentation under `raw/assets`.
2. Index wiki entities, concepts, and synthesis pages.
3. Map diagnostic codes to wiki pages and source provenance.
4. Run tests and static checks.
5. Verify the LSP runtime and OpenQC integration.

## Source of Truth

- `src/pyatb_lsp/schema/pyatb_rules.json` is the runtime rule/provenance index.
- `raw/assets/pyatb-official-docs.json` records local asset and wiki checksums.
- `raw/assets/source-provenance.json` maps rule sources to checksums and retrieval dates.
- `lsp-capabilities.json` exposes the agent/OpenQC manifest surface.

## Refresh

```bash
python3 scripts/update_official_pipeline.py
python3 scripts/update_official_pipeline.py --offline
python3 scripts/update_official_pipeline.py --fetch-official
```

The default offline refresh recomputes checksums for mirrored assets and wiki
pages without network access. Use `--fetch-official` to record upstream landing
page checksums when network is available.

## Verification

```bash
make test
python3 scripts/update_official_pipeline.py --offline
pyatb-lsp-tool capabilities
```

## Runtime Contract

The capabilities manifest exposes:

- `pipeline`: `official-docs-fetch -> raw-assets-index -> wiki-entities -> structured-schema-rules -> source-provenance -> tests -> lsp-runtime`
- `sourceProvenance`: official docs plus mirrored reference pages used by diagnostics
- `provenanceUpdatedAt`: timestamp matching `raw/assets/source-provenance.json`

This does not claim full grammar or version-rule coverage across every PyATB
input surface; it provides traceable provenance for the enforced diagnostic set.
