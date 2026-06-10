"""Tests for the LSP server module."""

from __future__ import annotations

from pathlib import Path

# Import will fail until server.py is created — that's expected in TDD
from pyatb_lsp.server import (
    PyATBServer,
    complete_keywords,
    create_server,
    diagnose_document,
    format_document,
    hover_info,
)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


class TestCreateServer:
    def test_create_returns_pyatb_server(self):
        server = create_server()
        assert isinstance(server, PyATBServer)


class TestDiagnoseDocument:
    def test_valid_document_no_errors(self):
        content = 'import pyatb\nhr_file = "HR.dat"\n'
        diags = diagnose_document("file:///test.py", content)
        errors = [d for d in diags if d.severity == 1]  # Error=1
        assert not errors

    def test_syntax_error_returns_error(self):
        content = "def broken(\n"
        diags = diagnose_document("file:///test.py", content)
        assert len(diags) >= 1

    def test_missing_import_returns_warning(self):
        content = 'hr_file = "HR.dat"\n'
        diags = diagnose_document("file:///test.py", content)
        # Warning = 2
        warnings = [d for d in diags if d.severity == 2]
        assert len(warnings) >= 1

    def test_empty_content(self):
        diags = diagnose_document("file:///test.py", "")
        assert isinstance(diags, list)


class TestFormatDocument:
    def test_formats_key_value(self):
        content = "key=value\n"
        result = format_document(content)
        assert "key" in result
        assert "=" in result

    def test_idempotent(self):
        content = 'import pyatb\nhr_file = "HR.dat"\n'
        assert format_document(format_document(content)) == format_document(content)


class TestCompleteKeywords:
    def test_returns_completions(self):
        items = complete_keywords("imp")
        assert len(items) > 0

    def test_empty_prefix_returns_all(self):
        items = complete_keywords("")
        assert len(items) > 0

    def test_completion_has_label(self):
        items = complete_keywords("py")
        for item in items:
            assert item.label


class TestHoverInfo:
    def test_hover_for_import(self):
        info = hover_info("import pyatb", 0, 7)
        assert info is not None
        assert "pyatb" in info.lower() or "PyATB" in info

    def test_hover_for_unknown(self):
        info = hover_info("unknown_token", 0, 3)
        assert info is None or isinstance(info, str)
