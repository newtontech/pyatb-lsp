---
name: pyatb
description: "PyATB workflow preflight for generated input scripts."
---

# PyATB LSP Skill

Use this skill when preparing, repairing, or reviewing PyATB input files before a run. It provides an installable language server and an agent-facing CLI that reports machine-readable diagnostics.

## Scope

- Input patterns: *.pyatb.py, run_pyatb.py
- Server command: `pyatb-lsp`
- Agent CLI: `pyatb-lsp-tool`
- Diagnostic contract: `DiagnosticEnvelope/v1`

## Installing the checker

```bash
pip install pyatb-lsp
```

This installs the `pyatb-lsp` language server and the `pyatb-lsp-tool` agent CLI from the `pyatb-lsp` Python package.

## Useful inspection commands

```bash
pyatb-lsp-tool capabilities
pyatb-lsp-tool skill-spec --format json
pyatb-lsp-tool skill-export --output ./skill
pyatb-lsp-tool check <input-file-or-dir> --format json
pyatb-lsp-tool context <input-file-or-dir> --line 0 --character 0 --format json
pyatb-lsp-tool hover <input-file-or-dir> --line 0 --character 0 --format json
pyatb-lsp-tool complete <input-file-or-dir> --line 0 --character 0 --format json
pyatb-lsp-tool symbols <input-file-or-dir> --format json
pyatb-lsp-tool fix <input-file-or-dir> --line 0 --character 0 --format json
```

`fix` is advisory and must be treated as a preview. Do not blindly apply a repair without preserving the user's scientific intent.

## Validation gate

Before saying generated inputs are ready, run:

```bash
pyatb-lsp-tool check <input-file-or-dir> --format json --fail-on-blocking
```

Report `commands`, `files_checked`, `tool_available`, `diagnostics`, `blocking_findings`, `readiness`, and `reason`.

## Repair rules

1. Validate first and identify the smallest blocking issue.
2. Fix syntax or schema errors with minimal edits.
3. Preserve scientific settings unless the user explicitly asks to redesign them.
4. Re-run the checker after every edit.
5. Separate syntax, schema, semantic, and runtime-log diagnostics in the final report.
