"""Tests for the universal generated-input preflight (#32).

Mirrors the abacus/qe/gaussian fleet preflight test contract: each of the four
capabilities (version-aware-keywords, cross-artifact-graph, code-actions,
fleet-regression-fixtures) is exercised against a real fixture directory so the
parent bohrium_skills probe can consume the same evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pyatb_lsp import tool
from pyatb_lsp.preflight import (
    ALL_ROLES,
    CODE_CONFIG_PARSE,
    CODE_KEYWORD_VERSION_MISMATCH,
    CODE_KPATH_TOO_COARSE,
    CODE_MISSING_ARTIFACT,
    CODE_TB_HAMILTONIAN_MISSING,
    CODE_UNKNOWN_PYATB_KEYWORD,
    CODE_UNRESOLVED_ARTIFACT,
    CODE_VERSION_ASSUMPTION,
    ArtifactGraph,
    build_artifact_graph,
    fleet_manifest,
    parse_workflow,
    resolve_version_assumption,
)
from pyatb_lsp.tool import (
    _looks_like_workspace,
    check_path,
    manifest_path,
    preflight_path,
)

FIXTURES = Path(__file__).parent / "fixtures" / "preflight"

# Envelope fields the issue acceptance criteria require on failing fixtures.
REQUIRED_FAILING_FIELDS = {
    "code",
    "severity",
    "path",
    "range",
    "blocking",
    "category",
    "source_provenance",
}


def _envelope_codes(payload: dict[str, Any]) -> set[str]:
    return {item["code"] for item in payload["diagnostics"]}


# --- Envelope shape --------------------------------------------------------


def test_agent_check_payload_carries_diagnostic_envelope_v1(capsys) -> None:
    # exercise the real CLI path so the capabilities block is attached
    rc = tool.main(["check", str(FIXTURES / "valid_boltzmann")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["diagnostic_envelope"] == "v1"
    # legacy engine label preserved for existing consumers
    assert payload["diagnostic_engine"] == "1.0"
    assert payload["software"] == "pyatb"
    # capabilities block is attached by the CLI wrapper
    assert payload["capabilities"]["operation"] == "check"
    # version assumption is surfaced at top level so the parent probe can branch
    assert "version_assumption" in payload
    assert payload["version_assumption"]["software"] == "pyatb"
    # cross-artifact graph is serialized for the fleet report workflow
    assert isinstance(payload.get("artifacts"), list)
    assert payload["artifacts"]


def test_legacy_diagnostic_engine_label_is_preserved() -> None:
    # Existing consumers assert diagnostic_engine == "1.0"; the envelope is
    # additive and must not break that contract.
    assumption = resolve_version_assumption(None)
    assert assumption["software"] == "pyatb"
    assert assumption["exact_runtime_known"] is False
    assert assumption["declared_by"] == "fallback"


# --- valid fixture ---------------------------------------------------------


def test_valid_boltzmann_fixture_is_clean() -> None:
    payload = preflight_path(FIXTURES / "valid_boltzmann")
    blocking = [item for item in payload["diagnostics"] if item["blocking"]]
    assert blocking == [], f"valid fixture should not emit blocking findings; got {blocking}"


def test_valid_fixture_version_assumption_is_declared_by_intent() -> None:
    payload = preflight_path(FIXTURES / "valid_boltzmann")
    assert payload["version_assumption"]["declared_by"] == "intent"
    assert payload["version_assumption"]["exact_runtime_known"] is True
    assert payload["version_assumption"]["software_version"] == "pyatb >=1.3.3"


# --- cross-artifact-graph (PYATB6xx) ---------------------------------------


def test_missing_hr_emits_blocking_tb_hamiltonian_finding() -> None:
    payload = preflight_path(FIXTURES / "missing_hr")
    failing = [
        item for item in payload["diagnostics"] if item["code"] == CODE_TB_HAMILTONIAN_MISSING
    ]
    assert failing, "missing_hr fixture must emit PYATB602"
    item = failing[0]
    for field in REQUIRED_FAILING_FIELDS:
        assert field in item, f"PYATB602 diagnostic missing required field {field}"
    assert item["severity"] == "error"
    assert item["blocking"] is True
    assert item["category"] == "cross-file reference"
    assert "tb-hamiltonian" in item["artifact_roles"]
    assert item["fix_hints"]
    assert item["source_provenance"]["role"] == "tb-hamiltonian"


def test_missing_config_emits_blocking_missing_artifact_finding() -> None:
    payload = preflight_path(FIXTURES / "missing_config")
    failing = [item for item in payload["diagnostics"] if item["code"] == CODE_MISSING_ARTIFACT]
    assert failing, "missing_config fixture must emit PYATB601"
    item = failing[0]
    assert item["blocking"] is True
    assert item["source_provenance"]["role"] == "config"
    assert any(action.get("role") == "config" for action in item.get("actions", []))


def test_bad_config_emits_blocking_config_parse_finding() -> None:
    payload = preflight_path(FIXTURES / "bad_config")
    failing = [item for item in payload["diagnostics"] if item["code"] == CODE_CONFIG_PARSE]
    assert failing, "bad_config fixture must emit PYATB604"
    item = failing[0]
    assert item["severity"] == "error"
    assert item["blocking"] is True
    assert item["category"] == "syntax"


def test_unresolved_overlap_is_a_non_blocking_warning(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "workflow.py").write_text(
        "import pyatb\n"
        "abf = pyatb.ABFunc(hr_file='HR.dat', sr_file='SR.dat')\n"
        "tb = pyatb.TightBinding(abf)\n",
        encoding="utf-8",
    )
    (case / "HR.dat").write_text("0 0 0 1.0\n", encoding="utf-8")
    # SR.dat intentionally absent so the overlap role is unresolved
    payload = preflight_path(case)
    unresolved = [
        item for item in payload["diagnostics"] if item["code"] == CODE_UNRESOLVED_ARTIFACT
    ]
    assert unresolved, "absent SR.dat must emit PYATB603"
    assert unresolved[0]["blocking"] is False
    assert unresolved[0]["source_provenance"]["role"] == "tb-overlap"


def test_empty_directory_emits_blocking_missing_artifact(tmp_path: Path) -> None:
    payload = preflight_path(tmp_path)
    failing = [item for item in payload["diagnostics"] if item["code"] == CODE_MISSING_ARTIFACT]
    assert failing
    assert failing[0]["blocking"] is True


# --- version-aware-keywords ------------------------------------------------


def test_calculation_without_required_kwargs_is_blocking() -> None:
    payload = preflight_path(FIXTURES / "ntype_keyword_mismatch")
    failing = [
        item for item in payload["diagnostics"] if item["code"] == CODE_KEYWORD_VERSION_MISMATCH
    ]
    assert failing, "ntype_keyword_mismatch fixture must emit PYATB608"
    item = failing[0]
    assert item["blocking"] is True
    assert item["category"] == "schema"
    assert "version_assumption" in item
    assert "mu_min" in item["facts"]["missing_kwargs"]
    assert item["domain_tags"] and "version-aware" in item["domain_tags"]


def test_coarse_kmesh_emits_runtime_risk_warning() -> None:
    payload = preflight_path(FIXTURES / "coarse_kmesh")
    failing = [item for item in payload["diagnostics"] if item["code"] == CODE_KPATH_TOO_COARSE]
    assert failing, "coarse_kmesh fixture must emit PYATB606"
    item = failing[0]
    assert item["blocking"] is False
    assert item["severity"] == "warning"
    assert item["category"] == "preflight/runtime-risk"


def test_unknown_pyatb_kwarg_is_warned(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "workflow.py").write_text(
        "import pyatb\ntb = pyatb.TightBinding(hr_file='HR.dat', bogus_option=42)\n",
        encoding="utf-8",
    )
    (case / "HR.dat").write_text("0 0 0 1.0\n", encoding="utf-8")
    payload = preflight_path(case)
    unknown = [
        item for item in payload["diagnostics"] if item["code"] == CODE_UNKNOWN_PYATB_KEYWORD
    ]
    assert unknown
    assert unknown[0]["severity"] == "warning"
    assert unknown[0]["facts"]["keyword"] == "bogus_option"


def test_version_assumption_diagnostic_emitted_when_intent_absent(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "workflow.py").write_text(
        "import pyatb\ntb = pyatb.TightBinding(hr_file='HR.dat')\n", encoding="utf-8"
    )
    (case / "HR.dat").write_text("0 0 0 1.0\n", encoding="utf-8")
    payload = preflight_path(case)
    info = [item for item in payload["diagnostics"] if item["code"] == CODE_VERSION_ASSUMPTION]
    assert info
    assert info[0]["severity"] == "information"
    assert info[0]["version_assumption"]["exact_runtime_known"] is False


# --- code-actions: blocking gate ------------------------------------------


def test_check_fail_on_blocking_returns_nonzero_for_failing_case(capsys) -> None:
    rc = tool.main(["check", str(FIXTURES / "missing_hr"), "--fail-on-blocking"])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False


def test_check_fail_on_blocking_returns_zero_for_valid_case(capsys) -> None:
    rc = tool.main(["check", str(FIXTURES / "valid_boltzmann"), "--fail-on-blocking"])
    assert rc == 0


def test_preflight_subcommand_returns_nonzero_on_blocking(capsys) -> None:
    rc = tool.main(["preflight", str(FIXTURES / "missing_hr"), "--fail-on-blocking"])
    assert rc == 1


# --- cross-artifact-graph model -------------------------------------------


def test_build_artifact_graph_records_generic_roles() -> None:
    case_dir = (FIXTURES / "valid_boltzmann").resolve()
    workflow = parse_workflow(case_dir / "workflow.py")
    graph = build_artifact_graph(case_dir, workflow)
    roles = {node.role for node in graph.nodes}
    assert "primary-input" in roles
    assert "config" in roles
    assert "tb-hamiltonian" in roles
    assert "tb-overlap" in roles
    # serialized graph is stable / sortable
    payload = graph.to_json()
    assert isinstance(payload, list)
    assert all({"role", "path", "exists", "source"} <= set(node) for node in payload)


def test_all_roles_are_exposed_in_manifest() -> None:
    manifest = fleet_manifest()
    assert set(manifest["artifact_roles"]) == set(ALL_ROLES)


def test_parse_workflow_captures_kwargs_and_literals() -> None:
    case_dir = (FIXTURES / "valid_boltzmann").resolve()
    workflow = parse_workflow(case_dir / "workflow.py")
    assert workflow.has_pyatb_import is True
    assert "calculation" in workflow.kwargs
    assert any(name.endswith("HR.dat") for name, _ in workflow.file_literals)
    assert any(name == "config.json" for name, _ in workflow.config_refs)


def test_parse_workflow_records_syntax_error_for_bad_script(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("def (\n", encoding="utf-8")
    workflow = parse_workflow(bad)
    assert workflow.syntax_error is not None


# --- fleet-regression-fixtures --------------------------------------------


def test_fleet_manifest_describes_all_capabilities_and_codes() -> None:
    manifest = fleet_manifest()
    assert manifest["software"] == "pyatb"
    assert manifest["preflight_envelope"] == "DiagnosticEnvelope/v1"
    caps = manifest["capabilities"]
    for capability in (
        "version-aware-keywords",
        "cross-artifact-graph",
        "code-actions",
        "fleet-regression-fixtures",
    ):
        assert capability in caps
        assert caps[capability]["status"] == "available"
    expected_codes = {
        CODE_MISSING_ARTIFACT,
        CODE_TB_HAMILTONIAN_MISSING,
        CODE_UNRESOLVED_ARTIFACT,
        CODE_CONFIG_PARSE,
        CODE_UNKNOWN_PYATB_KEYWORD,
        CODE_KEYWORD_VERSION_MISMATCH,
        CODE_KPATH_TOO_COARSE,
        CODE_VERSION_ASSUMPTION,
    }
    assert expected_codes <= set(manifest["codes"])
    # every code is mapped back to the capability that evidences it
    for _code, entry in manifest["codes"].items():
        assert entry["capability"] in caps
        assert "summary" in entry


def test_manifest_path_merges_fixture_expectations() -> None:
    manifest = manifest_path(FIXTURES / "valid_boltzmann")
    fixtures = manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"]
    assert any(item["name"] == "valid_boltzmann" for item in fixtures)


@pytest.mark.parametrize(
    "fixture,expected_code",
    [
        ("missing_hr", CODE_TB_HAMILTONIAN_MISSING),
        ("missing_config", CODE_MISSING_ARTIFACT),
        ("bad_config", CODE_CONFIG_PARSE),
        ("ntype_keyword_mismatch", CODE_KEYWORD_VERSION_MISMATCH),
        ("coarse_kmesh", CODE_KPATH_TOO_COARSE),
    ],
)
def test_failing_fixture_emits_expected_code(fixture: str, expected_code: str) -> None:
    payload = preflight_path(FIXTURES / fixture)
    assert expected_code in _envelope_codes(payload), (
        f"{fixture} should emit {expected_code}; got {_envelope_codes(payload)}"
    )


# --- workspace detection ---------------------------------------------------


def test_looks_like_workspace_true_for_valid_fixture() -> None:
    assert _looks_like_workspace(FIXTURES / "valid_boltzmann") is True


def test_looks_like_workspace_false_for_bare_dir(tmp_path: Path) -> None:
    assert _looks_like_workspace(tmp_path) is False


def test_check_path_on_single_file_keeps_legacy_behavior(tmp_path: Path) -> None:
    # Single-file lint path must not inject a missing-artifact blocking
    # finding just because the directory is not a full pyatb workspace. A
    # plain Python file that does not import pyatb is treated as a lone
    # script, not a generated-input workspace, so no PYATB6xx code fires.
    p = tmp_path / "plain.py"
    p.write_text("x = 1\n", encoding="utf-8")
    payload = check_path(p)
    assert not any(item["code"].startswith("PYATB6") for item in payload["diagnostics"])


# --- regression: ArtifactGraph dataclass -----------------------------------


def test_artifact_graph_by_role_and_to_json_round_trip() -> None:
    graph = ArtifactGraph(case_dir=Path("/tmp"))
    assert graph.to_json() == []
    assert graph.by_role("config") == []
