"""Tests for the Diagnostic dataclass."""

from __future__ import annotations

from pyatb_lsp.diagnostics import Diagnostic


def test_diagnostic_defaults():
    d = Diagnostic(code="PYATB001", severity="warning", message="test", file="a.py", line=5)
    assert d.column == 1
    assert d.evidence == []
    assert d.suggested_fix is None
    assert d.confidence == 1.0


def test_diagnostic_to_json():
    d = Diagnostic(
        code="PYATB010",
        severity="error",
        message="bad",
        file="x.py",
        line=3,
        column=10,
        evidence=["line1"],
        suggested_fix={"kind": "replace"},
        confidence=0.9,
    )
    j = d.to_json()
    assert j["code"] == "PYATB010"
    assert j["severity"] == "error"
    assert j["line"] == 3
    assert j["column"] == 10
    assert j["evidence"] == ["line1"]
    assert j["suggested_fix"] == {"kind": "replace"}
    assert j["confidence"] == 0.9


def test_diagnostic_frozen():
    d = Diagnostic(code="X", severity="warning", message="m", file="f", line=1)
    try:
        d.code = "Y"
        raise AssertionError("should be frozen")
    except AttributeError:
        pass


def test_diagnostic_all_fields():
    d = Diagnostic(
        code="PYATB001",
        severity="info",
        message="note",
        file="test.py",
        line=1,
        column=1,
        evidence=["a", "b"],
        suggested_fix={"kind": "add"},
        confidence=0.5,
    )
    j = d.to_json()
    assert set(j.keys()) == {
        "code",
        "severity",
        "message",
        "file",
        "line",
        "column",
        "evidence",
        "suggested_fix",
        "confidence",
    }
