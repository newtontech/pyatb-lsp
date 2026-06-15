"""Closed-loop fixture tests for DiagnosticEnvelope/v1 stability.

Verifies that the agent CLI produces stable, correct DiagnosticEnvelope/v1 JSON
when run against valid, invalid, and log fixtures. Uses tmp_path isolation to
avoid preflight workspace detection on shared fixture directories.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from pyatb_lsp.tool import main as tool_main

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_DIR = FIXTURES_DIR / "valid"
INVALID_DIR = FIXTURES_DIR / "invalid"
LOGS_DIR = FIXTURES_DIR / "logs"


def _run_check(path: Path, fail_on_blocking: bool = False) -> dict:
    """Run pyatb-lsp-tool check and return parsed JSON."""
    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        args = ["check", str(path)]
        if fail_on_blocking:
            args.append("--fail-on-blocking")
        tool_main(args)
    finally:
        sys.stdout = old_stdout
    return json.loads(buffer.getvalue())


def _run_check_isolated(tmp_path: Path, fixture_path: Path, fail_on_blocking: bool = False) -> dict:
    """Copy fixture to isolated tmp_path, then run check.

    This avoids preflight workspace detection when multiple .py files
    share a directory.
    """
    dest = tmp_path / fixture_path.name
    shutil.copy2(fixture_path, dest)
    return _run_check(dest, fail_on_blocking=fail_on_blocking)


def _run_parse_log(path: Path) -> dict:
    """Run pyatb-lsp-tool parse-log and return parsed JSON."""
    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        tool_main(["parse-log", str(path)])
    finally:
        sys.stdout = old_stdout
    return json.loads(buffer.getvalue())


def _assert_envelope_v1(payload: dict) -> None:
    """Assert the payload follows DiagnosticEnvelope/v1 structure."""
    assert "uri" in payload, "Missing 'uri' in envelope"
    assert "operation" in payload, "Missing 'operation' in envelope"
    assert "ok" in payload, "Missing 'ok' in envelope"
    assert "version" in payload, "Missing 'version' in envelope"
    assert "software" in payload, "Missing 'software' in envelope"
    assert "diagnostic_engine" in payload, "Missing 'diagnostic_engine' in envelope"
    assert "diagnostic_envelope" in payload, "Missing 'diagnostic_envelope' in envelope"
    assert "diagnostics" in payload, "Missing 'diagnostics' in envelope"
    assert "summary" in payload, "Missing 'summary' in envelope"

    assert payload["diagnostic_envelope"] == "v1"
    assert payload["software"] == "pyatb"

    summary = payload["summary"]
    assert "count" in summary
    assert "blocking" in summary
    assert "errors" in summary
    assert "warnings" in summary

    for diag in payload["diagnostics"]:
        _assert_diagnostic_v1(diag)


def _assert_diagnostic_v1(diag: dict) -> None:
    """Assert a single diagnostic follows DiagnosticEnvelope/v1 structure."""
    required_fields = [
        "code",
        "severity",
        "category",
        "confidence",
        "source",
        "range",
        "software",
        "file_type",
        "path",
        "fix_hints",
        "blocking",
        "message",
    ]
    for field in required_fields:
        assert field in diag, f"Missing '{field}' in diagnostic"

    assert diag["severity"] in ("error", "warning", "information", "hint")

    valid_categories = [
        "syntax",
        "schema",
        "type/value",
        "cross-file reference",
        "semantic consistency",
        "preflight/runtime-risk",
        "style/deprecation",
    ]
    assert diag["category"] in valid_categories

    assert 0.0 <= diag["confidence"] <= 1.0

    assert "start" in diag["range"]
    assert "end" in diag["range"]
    assert "line" in diag["range"]["start"]
    assert "character" in diag["range"]["start"]
    assert "line" in diag["range"]["end"]
    assert "character" in diag["range"]["end"]


class TestValidFixtures:
    """Tests that valid fixtures produce no legacy blocking diagnostics.

    Each fixture is copied to tmp_path to avoid preflight workspace detection
    on the shared fixtures/valid/ directory.
    """

    def test_minimal_valid(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, VALID_DIR / "minimal_valid.py")
        _assert_envelope_v1(payload)
        legacy_codes = {d["code"] for d in payload["diagnostics"]}
        blocking_legacy = legacy_codes & {"PYATB-E070", "PYATB-E071", "PYATB-E072", "PYATB-E073"}
        assert not blocking_legacy, f"Unexpected legacy blocking codes: {blocking_legacy}"

    def test_with_sr_dat(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, VALID_DIR / "with_sr_dat.py")
        _assert_envelope_v1(payload)
        legacy_codes = {d["code"] for d in payload["diagnostics"]}
        blocking_legacy = legacy_codes & {"PYATB-E070", "PYATB-E071", "PYATB-E072", "PYATB-E073"}
        assert not blocking_legacy

    def test_with_tightbinding(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, VALID_DIR / "with_tightbinding.py")
        _assert_envelope_v1(payload)
        legacy_codes = {d["code"] for d in payload["diagnostics"]}
        blocking_legacy = legacy_codes & {"PYATB-E070", "PYATB-E071", "PYATB-E072", "PYATB-E073"}
        assert not blocking_legacy

    def test_with_tb_alias(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, VALID_DIR / "with_tb_alias.py")
        _assert_envelope_v1(payload)
        legacy_codes = {d["code"] for d in payload["diagnostics"]}
        blocking_legacy = legacy_codes & {"PYATB-E070", "PYATB-E071", "PYATB-E072", "PYATB-E073"}
        assert not blocking_legacy

    def test_with_output_path(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, VALID_DIR / "with_output_path.py")
        _assert_envelope_v1(payload)
        legacy_codes = {d["code"] for d in payload["diagnostics"]}
        blocking_legacy = legacy_codes & {"PYATB-E070", "PYATB-E071", "PYATB-E072", "PYATB-E073"}
        assert not blocking_legacy


class TestInvalidFixtures:
    """Tests that invalid fixtures produce expected blocking errors.

    Each fixture is copied to tmp_path to ensure single-file analysis mode.
    """

    def test_syntax_error(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, INVALID_DIR / "syntax_error.py")
        _assert_envelope_v1(payload)
        assert payload["ok"] is False
        assert payload["summary"]["blocking"] > 0
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-E070" in codes

    def test_missing_import(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, INVALID_DIR / "missing_import.py")
        _assert_envelope_v1(payload)
        assert payload["ok"] is False
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-E071" in codes

    def test_empty_file(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, INVALID_DIR / "empty_file.py")
        _assert_envelope_v1(payload)
        assert payload["summary"]["count"] > 0

    def test_just_print(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, INVALID_DIR / "just_print.py")
        _assert_envelope_v1(payload)
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-E071" in codes


class TestLogFixtures:
    """Tests that log fixtures are parsed correctly."""

    def test_clean_log(self):
        payload = _run_parse_log(LOGS_DIR / "clean.log")
        _assert_envelope_v1(payload)
        assert payload["ok"] is True
        assert payload["summary"]["count"] == 0

    def test_runtime_error_log(self):
        payload = _run_parse_log(LOGS_DIR / "runtime_error.log")
        _assert_envelope_v1(payload)
        assert payload["ok"] is False
        assert payload["summary"]["count"] >= 1
        severities = [d["severity"] for d in payload["diagnostics"]]
        assert "error" in severities

    def test_file_not_found_log(self):
        payload = _run_parse_log(LOGS_DIR / "file_not_found.log")
        _assert_envelope_v1(payload)
        assert payload["ok"] is False
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-E074" in codes

    def test_import_error_log(self):
        payload = _run_parse_log(LOGS_DIR / "import_error.log")
        _assert_envelope_v1(payload)
        assert payload["ok"] is False
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-E071" in codes

    def test_segfault_log(self):
        payload = _run_parse_log(LOGS_DIR / "segfault.log")
        _assert_envelope_v1(payload)
        assert payload["ok"] is False
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-E075" in codes

    def test_multiple_errors_log(self):
        payload = _run_parse_log(LOGS_DIR / "multiple_errors.log")
        _assert_envelope_v1(payload)
        assert payload["ok"] is False
        assert payload["summary"]["count"] >= 3


class TestDiagnosticEnvelopeV1Fields:
    """Tests that verify DiagnosticEnvelope/v1 field completeness."""

    def test_all_envelope_fields_present(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, VALID_DIR / "minimal_valid.py")
        _assert_envelope_v1(payload)
        assert isinstance(payload["uri"], str)
        assert isinstance(payload["operation"], str)
        assert isinstance(payload["ok"], bool)
        assert isinstance(payload["version"], str)
        assert isinstance(payload["software"], str)
        assert isinstance(payload["diagnostic_engine"], str)
        assert isinstance(payload["diagnostic_envelope"], str)
        assert isinstance(payload["diagnostics"], list)
        assert isinstance(payload["summary"], dict)

    def test_all_diagnostic_fields_present(self, tmp_path: Path):
        payload = _run_check_isolated(tmp_path, VALID_DIR / "minimal_valid.py")
        _assert_envelope_v1(payload)
        if payload["diagnostics"]:
            diag = payload["diagnostics"][0]
            assert isinstance(diag["code"], str)
            assert isinstance(diag["severity"], str)
            assert isinstance(diag["category"], str)
            assert isinstance(diag["confidence"], float)
            assert isinstance(diag["source"], str)
            assert isinstance(diag["range"], dict)
            assert isinstance(diag["software"], str)
            assert isinstance(diag["file_type"], str)
            assert isinstance(diag["path"], str)
            assert isinstance(diag["fix_hints"], list)
            assert isinstance(diag["blocking"], bool)
            assert isinstance(diag["message"], str)


class TestBlockingPolicy:
    """Tests that verify blocking policy is enforced correctly."""

    def test_syntax_error_is_blocking(self, tmp_path: Path):
        payload = _run_check_isolated(
            tmp_path, INVALID_DIR / "syntax_error.py", fail_on_blocking=True
        )
        assert payload["ok"] is False

    def test_missing_import_is_blocking(self, tmp_path: Path):
        payload = _run_check_isolated(
            tmp_path, INVALID_DIR / "missing_import.py", fail_on_blocking=True
        )
        assert payload["ok"] is False


# ---------------------------------------------------------------------------
# Fix-preview tests (#40)
# ---------------------------------------------------------------------------


def _run_fix(path: Path) -> dict:
    """Run pyatb-lsp-tool fix and return parsed JSON."""
    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        tool_main(["fix", str(path)])
    finally:
        sys.stdout = old_stdout
    return json.loads(buffer.getvalue())


def _run_fix_isolated(tmp_path: Path, fixture_path: Path) -> dict:
    """Copy fixture to isolated tmp_path, then run fix."""
    dest = tmp_path / fixture_path.name
    shutil.copy2(fixture_path, dest)
    return _run_fix(dest)


class TestFixOperation:
    """Tests for the fix operation with fix-preview envelopes (#40)."""

    def test_fix_returns_envelope_v1(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, INVALID_DIR / "missing_import.py")
        _assert_envelope_v1(payload)
        assert payload["operation"] == "fix"

    def test_fix_valid_file_has_no_error_fix_previews(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, VALID_DIR / "minimal_valid.py")
        _assert_envelope_v1(payload)
        assert payload["ok"] is True
        for diag in payload["diagnostics"]:
            if diag["severity"] == "error":
                assert "fix_preview" not in diag

    def test_fix_missing_import_has_add_import_preview(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, INVALID_DIR / "missing_import.py")
        _assert_envelope_v1(payload)
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-E071" in codes
        e071 = [d for d in payload["diagnostics"] if d["code"] == "PYATB-E071"][0]
        assert "fix_preview" in e071
        preview = e071["fix_preview"]
        assert preview["kind"] == "quickfix"
        assert preview["diagnostic_code"] == "PYATB-E071"
        assert preview["safe_to_auto_apply"] is True
        assert "edit" in preview
        assert "changes" in preview["edit"]
        assert len(preview["edit"]["changes"]) > 0

    def test_fix_missing_hr_dat_has_add_symbol_reference_preview(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, INVALID_DIR / "missing_hr_dat.py")
        _assert_envelope_v1(payload)
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-E072" in codes
        e072 = [d for d in payload["diagnostics"] if d["code"] == "PYATB-E072"][0]
        assert "fix_preview" in e072
        preview = e072["fix_preview"]
        assert preview["kind"] == "quickfix"
        assert preview["diagnostic_code"] == "PYATB-E072"
        assert preview["safe_to_auto_apply"] is False
        assert "edit" in preview

    def test_fix_missing_structure_ref_has_add_symbol_reference_preview(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, INVALID_DIR / "missing_structure_ref.py")
        _assert_envelope_v1(payload)
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-E072" in codes
        e072 = [d for d in payload["diagnostics"] if d["code"] == "PYATB-E072"][0]
        assert "fix_preview" in e072
        preview = e072["fix_preview"]
        assert preview["kind"] == "quickfix"
        assert preview["diagnostic_code"] == "PYATB-E072"
        assert preview["safe_to_auto_apply"] is False

    def test_fix_no_output_path_has_add_output_path_preview(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, INVALID_DIR / "no_output_path.py")
        _assert_envelope_v1(payload)
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-W070" in codes
        w070 = [d for d in payload["diagnostics"] if d["code"] == "PYATB-W070"][0]
        assert "fix_preview" in w070
        preview = w070["fix_preview"]
        assert preview["kind"] == "quickfix"
        assert preview["safe_to_auto_apply"] is True

    def test_fix_syntax_error_returns_no_auto_fix(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, INVALID_DIR / "syntax_error.py")
        _assert_envelope_v1(payload)
        codes = {d["code"] for d in payload["diagnostics"]}
        assert "PYATB-E070" in codes
        e070 = [d for d in payload["diagnostics"] if d["code"] == "PYATB-E070"][0]
        assert "fix_preview" in e070
        preview = e070["fix_preview"]
        assert preview["safe_to_auto_apply"] is False
        assert preview["edit"] is None

    def test_fix_summary_fields_present(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, INVALID_DIR / "missing_import.py")
        _assert_envelope_v1(payload)
        summary = payload["summary"]
        assert "count" in summary
        assert "blocking" in summary
        assert "errors" in summary
        assert "warnings" in summary
        assert isinstance(summary["count"], int)
        assert isinstance(summary["blocking"], int)
        assert summary["count"] > 0

    def test_fix_valid_file_ok_is_true(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, VALID_DIR / "minimal_valid.py")
        assert payload["ok"] is True

    def test_fix_invalid_file_ok_is_false(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, INVALID_DIR / "missing_import.py")
        assert payload["ok"] is False

    def test_fix_preview_has_required_fields(self, tmp_path: Path):
        payload = _run_fix_isolated(tmp_path, INVALID_DIR / "missing_import.py")
        e071 = [d for d in payload["diagnostics"] if d["code"] == "PYATB-E071"][0]
        preview = e071["fix_preview"]
        required = ["title", "kind", "diagnostic_code", "confidence", "safe_to_auto_apply"]
        for field in required:
            assert field in preview, f"Missing '{field}' in fix_preview"
