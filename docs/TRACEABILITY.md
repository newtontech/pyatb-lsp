# PyATB LSP Traceability

Issue: https://github.com/newtontech/pyatb-lsp/issues/50

PyATB LSP now carries the same staged docstring, LLM Wiki, and raw provenance
checker used by the rest of the scientific LSP fleet. The checker scans source
docstrings for `wiki/...md` links, scans wiki pages for `raw/assets/...`
evidence links, and validates those raw links against `raw/assets/manifest.json`.

Run the report-only gate:

```bash
make traceability
```

Run strict mode when closing historical coverage gaps:

```bash
python3 scripts/check_docstring_traceability.py --strict --write-report
```

The current CI wiring is intentionally report-only. Strict mode is available,
but the existing repository still needs follow-up PRs to link every historical
docstring and every wiki page to raw evidence before strict mode can become a
blocking gate.
