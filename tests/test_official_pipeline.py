"""Tests for the official-docs -> wiki -> provenance pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from pyatb_lsp.preflight import (
    CODE_CONFIG_PARSE,
    CODE_KEYWORD_VERSION_MISMATCH,
    CODE_KPATH_TOO_COARSE,
    CODE_MISSING_ARTIFACT,
    CODE_TB_HAMILTONIAN_MISSING,
    CODE_UNKNOWN_PYATB_KEYWORD,
    CODE_UNRESOLVED_ARTIFACT,
    CODE_VERSION_ASSUMPTION,
    fleet_manifest,
)
from pyatb_lsp.schema.official_rules import (
    diagnostic_rules,
    pipeline_steps,
    provenance_for_code,
    source_provenance,
)
from pyatb_lsp.tool import _capabilities_payload

ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_steps_match_rule_index():
    assert pipeline_steps()[-1] == "lsp-runtime"
    assert "source-provenance" in pipeline_steps()


def test_all_preflight_codes_have_provenance():
    manifest = fleet_manifest()
    for code in manifest["codes"]:
        rule = diagnostic_rules().get(code)
        assert rule is not None, f"missing diagnostic rule for {code}"
        assert rule.get("source_id"), f"missing source_id for {code}"
        provenance = provenance_for_code(code)
        assert provenance is not None
        assert provenance.get("wiki_ref")


def test_capabilities_include_pipeline_and_provenance():
    payload = _capabilities_payload()
    assert payload["software"] == "pyatb"
    assert "pipeline" in payload
    assert "source-provenance" in payload["capabilities"]
    assert len(payload["sourceProvenance"]) >= 4
    assert payload.get("provenanceUpdatedAt")


def test_source_provenance_manifest_exists():
    manifest = json.loads((ROOT / "raw" / "assets" / "source-provenance.json").read_text())
    assert manifest["schema"] == "SourceProvenance/v1"
    source_ids = {item["id"] for item in source_provenance()}
    manifest_ids = {item["id"] for item in manifest["sources"]}
    assert source_ids <= manifest_ids


def test_local_assets_indexed_with_checksums():
    snapshot = json.loads((ROOT / "raw" / "assets" / "pyatb-official-docs.json").read_text())
    assets = snapshot["local_assets"]
    assert any(item["path"] == "raw/assets/pyatb-input-reference.md" for item in assets)
    assert all(len(item["sha256"]) == 64 for item in assets)


def test_wiki_pages_indexed():
    snapshot = json.loads((ROOT / "raw" / "assets" / "pyatb-official-docs.json").read_text())
    wiki_paths = {item["path"] for item in snapshot["wiki_pages"]}
    assert "wiki/entities/hr-sr-files.md" in wiki_paths
    assert "wiki/synthesis/diagnostic-codes.md" in wiki_paths


def test_offline_pipeline_script():
    import subprocess

    result = subprocess.run(
        ["python3", "scripts/update_official_pipeline.py", "--offline"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_known_preflight_codes_map_to_wiki_entities():
    mapping = {
        CODE_MISSING_ARTIFACT: "wiki/synthesis/diagnostic-codes.md",
        CODE_TB_HAMILTONIAN_MISSING: "wiki/entities/hr-sr-files.md",
        CODE_UNRESOLVED_ARTIFACT: "wiki/entities/hr-sr-files.md",
        CODE_CONFIG_PARSE: "wiki/entities/output-config.md",
        CODE_UNKNOWN_PYATB_KEYWORD: "wiki/entities/tightbinding.md",
        CODE_KPATH_TOO_COARSE: "wiki/entities/kmesh-kpath.md",
        CODE_VERSION_ASSUMPTION: "wiki/synthesis/diagnostic-codes.md",
        CODE_KEYWORD_VERSION_MISMATCH: "wiki/entities/tightbinding.md",
    }
    for code, wiki_ref in mapping.items():
        assert diagnostic_rules()[code]["wiki_ref"] == wiki_ref
