"""Comprehensive tests for the analyzer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from pyatb_lsp.analyzer import (
    _collect_files,
    _is_supported,
    _meaningful_lines,
    analyze_file,
    analyze_path,
    format_text,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# analyze_path — directory-level
# ---------------------------------------------------------------------------


class TestAnalyzePathDirectory:
    def test_valid_fixture_dir_no_errors(self, tmp_path: Path):
        _write(tmp_path, "run.py", 'import pyatb\nhr_file = "HR.dat"\n')
        diag = analyze_path(tmp_path)
        errors = [d for d in diag if d.severity == "error"]
        assert not errors

    def test_empty_directory_reports_no_files_error(self, tmp_path: Path):
        diag = analyze_path(tmp_path)
        assert len(diag) == 1
        assert diag[0].code == "PYATB201"
        assert diag[0].severity == "error"

    def test_no_py_files_reports_no_files_error(self, tmp_path: Path):
        _write(tmp_path, "README.md", "# hello")
        diag = analyze_path(tmp_path)
        assert len(diag) == 1
        assert diag[0].code == "PYATB201"

    def test_multiple_files_aggregates_diagnostics(self, tmp_path: Path):
        _write(tmp_path, "good.py", 'import pyatb\nhr_file = "HR.dat"\n')
        _write(tmp_path, "bad.py", 'print("no import")\n')
        diag = analyze_path(tmp_path)
        # good.py: no errors, possibly warnings for SR.dat etc.
        # bad.py: at least missing import warning
        files = {d.file for d in diag}
        assert any("bad.py" in f for f in files)

    def test_single_file_mode(self, tmp_path: Path):
        p = _write(tmp_path, "single.py", 'import pyatb\nhr_file = "HR.dat"\n')
        diag = analyze_path(p)
        assert isinstance(diag, list)

    def test_results_are_sorted(self, tmp_path: Path):
        _write(tmp_path, "a.py", 'import pyatb\nhr_file = "HR.dat"\n')
        _write(tmp_path, "b.py", 'import pyatb\nhr_file = "HR.dat"\n')
        diag = analyze_path(tmp_path)
        for i in range(len(diag) - 1):
            key_curr = (diag[i].file, diag[i].line, diag[i].code)
            key_next = (diag[i + 1].file, diag[i + 1].line, diag[i + 1].code)
            assert key_curr <= key_next


# ---------------------------------------------------------------------------
# analyze_file — single-file edge cases
# ---------------------------------------------------------------------------


class TestAnalyzeFile:
    def test_syntax_error_reports_diagnostic(self, tmp_path: Path):
        p = _write(tmp_path, "bad.py", "def broken(\n")
        diag = analyze_file(p)
        assert len(diag) >= 1
        assert diag[0].severity == "error"
        assert diag[0].code == "PYATB001"

    def test_non_utf8_file(self, tmp_path: Path):
        p = tmp_path / "binary.py"
        p.write_bytes(b"\x80\x81\x82")
        diag = analyze_file(p)
        assert len(diag) == 1
        assert diag[0].code == "PYATB202"
        assert diag[0].severity == "error"

    def test_missing_pyatb_import(self, tmp_path: Path):
        p = _write(tmp_path, "no_import.py", 'hr_file = "HR.dat"\nprint(hr_file)\n')
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB101" in codes

    def test_missing_hr_dat_symbol(self, tmp_path: Path):
        p = _write(tmp_path, "no_hr.py", "import pyatb\nprint(pyatb)\n")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB102" in codes

    def test_valid_script_minimal_warnings(self, tmp_path: Path):
        p = _write(tmp_path, "ok.py", 'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\n')
        diag = analyze_file(p)
        errors = [d for d in diag if d.severity == "error"]
        assert not errors

    def test_pyatb_specific_check_missing_hr_reference(self, tmp_path: Path):
        p = _write(tmp_path, "no_ref.py", "import pyatb\nresult = pyatb.compute()\n")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB010" in codes

    def test_pyatb_with_hr_file_in_content_no_warning(self, tmp_path: Path):
        p = _write(tmp_path, "has_hr.py", 'import pyatb\npath = "HR.dat"\nprint(path)\n')
        diag = analyze_file(p)
        pyatb010 = [d for d in diag if d.code == "PYATB010"]
        assert not pyatb010

    def test_pyatb_with_hr_file_keyword_in_content(self, tmp_path: Path):
        p = _write(tmp_path, "has_hr_kw.py", 'import pyatb\ntb = pyatb.TB(hr_file="HR.dat")\n')
        diag = analyze_file(p)
        pyatb010 = [d for d in diag if d.code == "PYATB010"]
        assert not pyatb010

    def test_from_import_pyatb(self, tmp_path: Path):
        content = 'from pyatb import TightBinding\nhr_file = "HR.dat"\n'
        p = _write(tmp_path, "from_import.py", content)
        diag = analyze_file(p)
        pyatb101 = [d for d in diag if d.code == "PYATB101"]
        assert not pyatb101

    def test_fixture_syntax_error_file(self):
        p = FIXTURES / "syntax_error.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        assert any(d.severity == "error" for d in diag)

    def test_fixture_missing_import(self):
        p = FIXTURES / "missing_import.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB101" in codes

    def test_fixture_missing_symbols(self):
        p = FIXTURES / "missing_symbols.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB010" in codes

    def test_fixture_valid(self):
        p = FIXTURES / "valid_pyatb.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        errors = [d for d in diag if d.severity == "error"]
        assert not errors


# ---------------------------------------------------------------------------
# _collect_files and _is_supported
# ---------------------------------------------------------------------------


class TestFileCollection:
    def test_collects_py_files(self, tmp_path: Path):
        _write(tmp_path, "a.py", "")
        _write(tmp_path, "b.py", "")
        _write(tmp_path, "c.txt", "")
        files = _collect_files(tmp_path)
        names = {f.name for f in files}
        assert names == {"a.py", "b.py"}

    def test_single_file_returns_list(self, tmp_path: Path):
        p = _write(tmp_path, "x.py", "")
        files = _collect_files(p)
        assert files == [p]

    def test_non_supported_file_returns_empty(self, tmp_path: Path):
        p = _write(tmp_path, "x.txt", "")
        files = _collect_files(p)
        assert files == []

    def test_is_supported_py(self, tmp_path: Path):
        assert _is_supported(tmp_path / "test.py") is True

    def test_is_supported_txt(self, tmp_path: Path):
        assert _is_supported(tmp_path / "test.txt") is False

    def test_nested_py_files(self, tmp_path: Path):
        sub = tmp_path / "sub"
        sub.mkdir()
        _write(sub, "nested.py", "")
        _write(tmp_path, "top.py", "")
        files = _collect_files(tmp_path)
        names = {f.name for f in files}
        assert names == {"top.py", "nested.py"}


# ---------------------------------------------------------------------------
# _meaningful_lines
# ---------------------------------------------------------------------------


class TestMeaningfulLines:
    def test_skips_blanks_and_comments(self):
        content = "# comment\n\nkey = val\n!bang\n;semi\n  \nresult\n"
        lines = _meaningful_lines(content)
        text_values = [text for _, text in lines]
        assert text_values == ["key = val", "result"]

    def test_empty_content(self):
        assert _meaningful_lines("") == []

    def test_only_comments(self):
        assert _meaningful_lines("# a\n# b\n") == []

    def test_preserves_line_numbers(self):
        content = "first\n\nthird\n"
        lines = _meaningful_lines(content)
        assert lines == [(1, "first"), (3, "third")]


# ---------------------------------------------------------------------------
# format_text
# ---------------------------------------------------------------------------


class TestFormatText:
    def test_idempotent_simple(self):
        src = 'import pyatb\nhr_file = "HR.dat"\n'
        assert format_text(format_text(src)) == format_text(src)

    def test_key_value_alignment(self):
        src = "key=value\n"
        result = format_text(src)
        assert "key" in result
        assert "=" in result
        # Key should be left-aligned to column 24
        assert result.startswith("key")

    def test_comment_preservation(self):
        src = "# this is a comment\nkey = val\n"
        result = format_text(src)
        lines = result.splitlines()
        assert lines[0] == "# this is a comment"

    def test_blank_line_preservation(self):
        src = "a = 1\n\nb = 2\n"
        result = format_text(src)
        assert "\n\n" in result

    def test_trailing_newline(self):
        assert format_text("a = 1\n").endswith("\n")

    def test_keyword_line_alignment(self):
        src = "ENCUT 500\n"
        result = format_text(src)
        # keyword should be left-aligned to col 24
        assert result.splitlines()[0].startswith("ENCUT")

    def test_empty_input(self):
        result = format_text("")
        assert result == "\n"

    def test_already_formatted_is_stable(self):
        src = "key                      = value\n"
        result = format_text(src)
        assert result == src

    def test_comment_only(self):
        src = "# just a comment\n"
        result = format_text(src)
        assert result == "# just a comment\n"

    def test_plain_text_passthrough(self):
        """Lines that look like keyword-value get aligned; all words preserved."""
        src = "some random text without structure\n"
        result = format_text(src)
        # "some" matches the keyword pattern, so line gets alignment spacing
        assert "some" in result
        assert "random text without structure" in result

    def test_multiple_key_values(self):
        src = "a=1\nb=2\nc=3\n"
        result = format_text(src)
        for key in ("a", "b", "c"):
            assert key in result


# ---------------------------------------------------------------------------
# Integration: fixture-based tests
# ---------------------------------------------------------------------------


class TestFixtureIntegration:
    def test_valid_fixture_directory(self):
        """Analyze the fixtures directory — valid file should produce no errors."""
        if not FIXTURES.exists():
            pytest.skip("fixtures dir not found")
        diag = analyze_path(FIXTURES / "valid_pyatb.py")
        errors = [d for d in diag if d.severity == "error"]
        assert not errors

    def test_missing_import_fixture(self):
        if not FIXTURES.exists():
            pytest.skip("fixtures dir not found")
        diag = analyze_path(FIXTURES / "missing_import.py")
        codes = [d.code for d in diag]
        assert "PYATB101" in codes

    def test_syntax_error_fixture(self):
        if not FIXTURES.exists():
            pytest.skip("fixtures dir not found")
        diag = analyze_path(FIXTURES / "syntax_error.py")
        assert any(d.severity == "error" for d in diag)
