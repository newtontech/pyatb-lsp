"""Comprehensive tests for the analyzer module.

Covers all RULE diagnostics:
- PYATB-E070: Python syntax errors (#14)
- PYATB-E071: Missing required imports (#15)
- PYATB-E072: Missing required symbols (#16)
- PYATB-E073: Invalid JSON (#17)
- PYATB-E074: Missing structure reference (#18)
- PYATB-W070: Missing output path (#19)
- PYATB-E075: Runtime log traceback (#20)
- MatMaster execution rules (#8)
- Formatter idempotence (#5)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pyatb_lsp.analyzer import (
    _collect_files,
    _detect_traceback_patterns,
    _is_python_statement,
    _is_supported,
    _meaningful_lines,
    analyze_file,
    analyze_path,
    format_text,
    parse_log_content,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"

# A minimal valid PyATB script that passes all new rules
_FULL_VALID = 'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\noutput = "out"\n'


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# analyze_path — directory-level
# ---------------------------------------------------------------------------


class TestAnalyzePathDirectory:
    def test_valid_fixture_dir_no_errors(self, tmp_path: Path):
        _write(tmp_path, "run.py", _FULL_VALID)
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
        _write(tmp_path, "good.py", _FULL_VALID)
        _write(tmp_path, "bad.py", 'print("no import")\n')
        diag = analyze_path(tmp_path)
        files = {d.file for d in diag}
        assert any("bad.py" in f for f in files)

    def test_single_file_mode(self, tmp_path: Path):
        p = _write(tmp_path, "single.py", _FULL_VALID)
        diag = analyze_path(p)
        assert isinstance(diag, list)

    def test_results_are_sorted(self, tmp_path: Path):
        _write(tmp_path, "a.py", _FULL_VALID)
        _write(tmp_path, "b.py", _FULL_VALID)
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
        assert diag[0].code == "PYATB-E070"

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
        assert "PYATB-E071" in codes

    def test_missing_hr_dat_symbol(self, tmp_path: Path):
        p = _write(tmp_path, "no_hr.py", "import pyatb\nprint(pyatb)\n")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E072" in codes

    def test_valid_script_no_errors(self, tmp_path: Path):
        p = _write(tmp_path, "ok.py", _FULL_VALID)
        diag = analyze_file(p)
        errors = [d for d in diag if d.severity == "error"]
        assert not errors

    def test_pyatb_specific_check_missing_hr_reference(self, tmp_path: Path):
        p = _write(tmp_path, "no_ref.py", "import pyatb\nresult = pyatb.compute()\n")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB010" in codes

    def test_pyatb_with_hr_file_in_content_no_pyatb010(self, tmp_path: Path):
        p = _write(tmp_path, "has_hr.py", 'import pyatb\npath = "HR.dat"\nprint(path)\n')
        diag = analyze_file(p)
        pyatb010 = [d for d in diag if d.code == "PYATB010"]
        assert not pyatb010

    def test_pyatb_with_hr_file_keyword_no_pyatb010(self, tmp_path: Path):
        p = _write(tmp_path, "has_hr_kw.py", 'import pyatb\ntb = pyatb.TB(hr_file="HR.dat")\n')
        diag = analyze_file(p)
        pyatb010 = [d for d in diag if d.code == "PYATB010"]
        assert not pyatb010

    def test_from_import_pyatb(self, tmp_path: Path):
        content = 'from pyatb import TightBinding\nhr_file = "HR.dat"\n'
        p = _write(tmp_path, "from_import.py", content)
        diag = analyze_file(p)
        e071 = [d for d in diag if d.code == "PYATB-E071"]
        assert not e071

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
        assert "PYATB-E071" in codes

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
        # valid_pyatb.py has HR.dat, SR.dat, TightBinding but no output keyword
        # so it may have W070 warning, but no errors
        errors = [d for d in diag if d.severity == "error"]
        assert not errors


# ---------------------------------------------------------------------------
# PYATB-E070: Syntax error rule (#14)
# ---------------------------------------------------------------------------


class TestRuleE070SyntaxError:
    """PYATB-E070: Python syntax errors."""

    def test_syntax_error_emits_e070(self, tmp_path: Path):
        p = _write(tmp_path, "bad.py", "def broken(\n")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E070" in codes

    def test_e070_has_high_confidence(self, tmp_path: Path):
        p = _write(tmp_path, "bad.py", "x =\n")
        diag = analyze_file(p)
        e070 = [d for d in diag if d.code == "PYATB-E070"]
        assert len(e070) == 1
        assert e070[0].confidence == 1.0

    def test_e070_includes_evidence(self, tmp_path: Path):
        p = _write(tmp_path, "bad.py", "def (\n")
        diag = analyze_file(p)
        e070 = [d for d in diag if d.code == "PYATB-E070"]
        assert len(e070) == 1
        assert len(e070[0].evidence) > 0

    def test_e070_has_suggested_fix(self, tmp_path: Path):
        p = _write(tmp_path, "bad.py", "def (\n")
        diag = analyze_file(p)
        e070 = [d for d in diag if d.code == "PYATB-E070"]
        assert len(e070) == 1
        assert e070[0].suggested_fix is not None
        assert e070[0].suggested_fix["kind"] == "fix_syntax"

    def test_e070_also_emits_legacy_code(self, tmp_path: Path):
        p = _write(tmp_path, "bad.py", "def (\n")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E070" in codes
        assert "PYATB001" in codes

    def test_valid_syntax_no_e070(self, tmp_path: Path):
        p = _write(tmp_path, "good.py", _FULL_VALID)
        diag = analyze_file(p)
        e070 = [d for d in diag if d.code == "PYATB-E070"]
        assert not e070

    def test_e070_reports_correct_line(self, tmp_path: Path):
        p = _write(tmp_path, "bad.py", "x = 1\ndef (\n")
        diag = analyze_file(p)
        e070 = [d for d in diag if d.code == "PYATB-E070"]
        assert len(e070) == 1
        assert e070[0].line == 2

    def test_fixture_syntax_error_has_e070(self):
        p = FIXTURES / "syntax_error.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E070" in codes


# ---------------------------------------------------------------------------
# PYATB-E071: Missing required import (#15)
# ---------------------------------------------------------------------------


class TestRuleE071MissingImport:
    """PYATB-E071: Missing required imports."""

    def test_missing_pyatb_import_emits_e071(self, tmp_path: Path):
        p = _write(tmp_path, "no_import.py", 'hr_file = "HR.dat"\nprint(hr_file)\n')
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E071" in codes

    def test_e071_is_error_severity(self, tmp_path: Path):
        p = _write(tmp_path, "no_import.py", "print('hello')\n")
        diag = analyze_file(p)
        e071 = [d for d in diag if d.code == "PYATB-E071"]
        assert len(e071) >= 1
        assert e071[0].severity == "error"

    def test_e071_has_add_import_fix(self, tmp_path: Path):
        p = _write(tmp_path, "no_import.py", "print('hello')\n")
        diag = analyze_file(p)
        e071 = [d for d in diag if d.code == "PYATB-E071"]
        assert len(e071) >= 1
        assert e071[0].suggested_fix is not None
        assert e071[0].suggested_fix["kind"] == "add_import"
        assert e071[0].suggested_fix["module"] == "pyatb"

    def test_with_pyatb_import_no_e071(self, tmp_path: Path):
        p = _write(tmp_path, "ok.py", _FULL_VALID)
        diag = analyze_file(p)
        e071 = [d for d in diag if d.code == "PYATB-E071"]
        assert not e071

    def test_from_import_satisfies_e071(self, tmp_path: Path):
        p = _write(
            tmp_path,
            "ok.py",
            'from pyatb import TightBinding\nhr_file = "HR.dat"\n',
        )
        diag = analyze_file(p)
        e071 = [d for d in diag if d.code == "PYATB-E071"]
        assert not e071

    def test_e071_also_emits_legacy_code(self, tmp_path: Path):
        p = _write(tmp_path, "no_import.py", "print('hello')\n")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E071" in codes
        assert "PYATB101" in codes

    def test_fixture_missing_import_has_e071(self):
        p = FIXTURES / "missing_import.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E071" in codes


# ---------------------------------------------------------------------------
# PYATB-E072: Missing required symbols (#16)
# ---------------------------------------------------------------------------


class TestRuleE072MissingSymbols:
    """PYATB-E072: Missing required symbols (HR.dat / SR.dat)."""

    def test_missing_hr_dat_emits_e072(self, tmp_path: Path):
        p = _write(tmp_path, "no_hr.py", "import pyatb\nprint(pyatb)\n")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E072" in codes

    def test_missing_sr_dat_emits_e072(self, tmp_path: Path):
        p = _write(tmp_path, "no_sr.py", 'import pyatb\nhr_file = "HR.dat"\n')
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E072" in codes

    def test_e072_is_error_severity(self, tmp_path: Path):
        p = _write(tmp_path, "no_hr.py", "import pyatb\nprint(pyatb)\n")
        diag = analyze_file(p)
        e072 = [d for d in diag if d.code == "PYATB-E072"]
        assert any(d.severity == "error" for d in e072)

    def test_e072_has_add_symbol_fix(self, tmp_path: Path):
        p = _write(tmp_path, "no_hr.py", "import pyatb\nprint(pyatb)\n")
        diag = analyze_file(p)
        e072 = [d for d in diag if d.code == "PYATB-E072"]
        for d in e072:
            assert d.suggested_fix is not None
            assert d.suggested_fix["kind"] == "add_symbol_reference"

    def test_with_all_symbols_no_e072(self, tmp_path: Path):
        p = _write(tmp_path, "ok.py", _FULL_VALID)
        diag = analyze_file(p)
        e072 = [d for d in diag if d.code == "PYATB-E072"]
        assert not e072

    def test_e072_also_emits_legacy_code(self, tmp_path: Path):
        p = _write(tmp_path, "no_hr.py", "import pyatb\nprint(pyatb)\n")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E072" in codes
        assert "PYATB102" in codes

    def test_e072_reports_evidence(self, tmp_path: Path):
        p = _write(tmp_path, "no_hr.py", "import pyatb\nprint(pyatb)\n")
        diag = analyze_file(p)
        e072 = [d for d in diag if d.code == "PYATB-E072"]
        assert all(len(d.evidence) > 0 for d in e072)

    def test_fixture_missing_symbols_has_e072(self):
        p = FIXTURES / "missing_symbols.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E072" in codes


# ---------------------------------------------------------------------------
# PYATB-E074: Missing structure reference (#18)
# ---------------------------------------------------------------------------


class TestRuleE074MissingStructure:
    """PYATB-E074: Missing structure reference."""

    def test_no_structure_emits_e074(self, tmp_path: Path):
        p = _write(tmp_path, "no_struct.py", "import pyatb\nresult = 42\n")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E074" in codes

    def test_e074_is_error(self, tmp_path: Path):
        p = _write(tmp_path, "no_struct.py", "import pyatb\nresult = 42\n")
        diag = analyze_file(p)
        e074 = [d for d in diag if d.code == "PYATB-E074"]
        assert len(e074) == 1
        assert e074[0].severity == "error"

    def test_with_hr_file_no_e074(self, tmp_path: Path):
        p = _write(tmp_path, "ok.py", 'import pyatb\nhr_file = "HR.dat"\n')
        diag = analyze_file(p)
        e074 = [d for d in diag if d.code == "PYATB-E074"]
        assert not e074

    def test_with_tightbinding_no_e074(self, tmp_path: Path):
        p = _write(tmp_path, "ok.py", "import pyatb\ntb = pyatb.TightBinding()\n")
        diag = analyze_file(p)
        e074 = [d for d in diag if d.code == "PYATB-E074"]
        assert not e074

    def test_with_tb_alias_no_e074(self, tmp_path: Path):
        p = _write(tmp_path, "ok.py", "import pyatb\ntb = pyatb.TB()\n")
        diag = analyze_file(p)
        e074 = [d for d in diag if d.code == "PYATB-E074"]
        assert not e074

    def test_e074_has_structure_fix_options(self, tmp_path: Path):
        p = _write(tmp_path, "no_struct.py", "import pyatb\nresult = 42\n")
        diag = analyze_file(p)
        e074 = [d for d in diag if d.code == "PYATB-E074"]
        assert e074[0].suggested_fix["kind"] == "add_structure_reference"
        assert len(e074[0].suggested_fix["options"]) >= 2

    def test_fixture_no_structure_has_e074(self):
        p = FIXTURES / "no_structure.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-E074" in codes


# ---------------------------------------------------------------------------
# PYATB-W070: Missing output path (#19)
# ---------------------------------------------------------------------------


class TestRuleW070MissingOutput:
    """PYATB-W070: Missing output path (warning)."""

    def test_no_output_emits_w070(self, tmp_path: Path):
        p = _write(
            tmp_path,
            "no_out.py",
            'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\n',
        )
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-W070" in codes

    def test_w070_is_warning(self, tmp_path: Path):
        p = _write(
            tmp_path,
            "no_out.py",
            'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\n',
        )
        diag = analyze_file(p)
        w070 = [d for d in diag if d.code == "PYATB-W070"]
        assert len(w070) == 1
        assert w070[0].severity == "warning"

    def test_with_output_no_w070(self, tmp_path: Path):
        p = _write(
            tmp_path,
            "ok.py",
            'import pyatb\nhr_file = "HR.dat"\noutput = "results/"\n',
        )
        diag = analyze_file(p)
        w070 = [d for d in diag if d.code == "PYATB-W070"]
        assert not w070

    def test_with_output_path_no_w070(self, tmp_path: Path):
        p = _write(
            tmp_path,
            "ok.py",
            'import pyatb\nhr_file = "HR.dat"\noutput_path = "results/"\n',
        )
        diag = analyze_file(p)
        w070 = [d for d in diag if d.code == "PYATB-W070"]
        assert not w070

    def test_with_result_dir_no_w070(self, tmp_path: Path):
        p = _write(
            tmp_path,
            "ok.py",
            'import pyatb\nhr_file = "HR.dat"\nresult_dir = "/tmp/out"\n',
        )
        diag = analyze_file(p)
        w070 = [d for d in diag if d.code == "PYATB-W070"]
        assert not w070

    def test_w070_has_suggested_fix(self, tmp_path: Path):
        p = _write(
            tmp_path,
            "no_out.py",
            'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\n',
        )
        diag = analyze_file(p)
        w070 = [d for d in diag if d.code == "PYATB-W070"]
        assert w070[0].suggested_fix["kind"] == "add_output_path"

    def test_fixture_missing_output_has_w070(self):
        p = FIXTURES / "missing_output.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        codes = [d.code for d in diag]
        assert "PYATB-W070" in codes

    def test_fixture_has_output_no_w070(self):
        p = FIXTURES / "has_output.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        w070 = [d for d in diag if d.code == "PYATB-W070"]
        assert not w070


# ---------------------------------------------------------------------------
# PYATB-E075: Runtime log traceback (#20)
# ---------------------------------------------------------------------------


class TestRuleE075Traceback:
    """PYATB-E075: Runtime log traceback detection."""

    def test_traceback_emits_e075_via_parse_log(self):
        content = "Traceback (most recent call last):\n  File 'x'\nError: bad\n"
        diags = parse_log_content(content)
        e075 = [d for d in diags if d.code == "PYATB-E075"]
        assert len(e075) >= 1

    def test_e075_is_error_severity(self):
        content = "Traceback (most recent call last):\n  File 'x'\nError: bad\n"
        diags = parse_log_content(content)
        e075 = [d for d in diags if d.code == "PYATB-E075"]
        assert all(d.severity == "error" for d in e075)

    def test_no_traceback_no_e075(self, tmp_path: Path):
        p = _write(tmp_path, "ok.py", _FULL_VALID)
        diag = analyze_file(p)
        e075 = [d for d in diag if d.code == "PYATB-E075"]
        assert not e075

    def test_traceback_reports_start_line(self):
        content = "x = 1\nTraceback (most recent call last):\n  File 'x'\nError: bad\n"
        diags = parse_log_content(content)
        e075 = [d for d in diags if d.code == "PYATB-E075"]
        assert len(e075) >= 1
        assert e075[0].line == 2

    def test_unterminated_traceback(self):
        content = "Traceback (most recent call last):\n  File 'x'\n  more\n"
        diags = parse_log_content(content)
        e075 = [d for d in diags if d.code == "PYATB-E075"]
        assert len(e075) == 1
        assert "unterminated" in e075[0].message


class TestRuleE073InvalidJSON:
    """PYATB-E073: Invalid JSON in configuration files."""

    def test_invalid_json_emits_e073(self, tmp_path: Path):
        p = tmp_path / "bad.json"
        p.write_text("{invalid json}", encoding="utf-8")
        from pyatb_lsp.analyzer import _analyze_json_or_text

        diag = _analyze_json_or_text(p, "{invalid json}")
        codes = [d.code for d in diag]
        assert "PYATB-E073" in codes

    def test_e073_is_error(self, tmp_path: Path):
        p = tmp_path / "bad.json"
        p.write_text("{invalid}", encoding="utf-8")
        from pyatb_lsp.analyzer import _analyze_json_or_text

        diag = _analyze_json_or_text(p, "{invalid}")
        e073 = [d for d in diag if d.code == "PYATB-E073"]
        assert len(e073) == 1
        assert e073[0].severity == "error"

    def test_valid_json_no_e073(self, tmp_path: Path):
        p = tmp_path / "good.json"
        p.write_text('{"hr_file": "HR.dat"}', encoding="utf-8")
        from pyatb_lsp.analyzer import _analyze_json_or_text

        diag = _analyze_json_or_text(p, '{"hr_file": "HR.dat"}')
        e073 = [d for d in diag if d.code == "PYATB-E073"]
        assert not e073

    def test_e073_reports_line(self, tmp_path: Path):
        p = tmp_path / "bad.json"
        content = '{\n  "key": "val",\n  bad_key\n}'
        from pyatb_lsp.analyzer import _analyze_json_or_text

        diag = _analyze_json_or_text(p, content)
        e073 = [d for d in diag if d.code == "PYATB-E073"]
        assert len(e073) == 1
        assert e073[0].line >= 1

    def test_e073_has_fix_suggestion(self, tmp_path: Path):
        p = tmp_path / "bad.json"
        from pyatb_lsp.analyzer import _analyze_json_or_text

        diag = _analyze_json_or_text(p, "{invalid}")
        e073 = [d for d in diag if d.code == "PYATB-E073"]
        assert e073[0].suggested_fix is not None
        assert e073[0].suggested_fix["kind"] == "fix_json_syntax"


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
# format_text — idempotence and safety (#5)
# ---------------------------------------------------------------------------


class TestFormatText:
    def test_idempotent_simple(self):
        src = 'import pyatb\nhr_file = "HR.dat"\n'
        assert format_text(format_text(src)) == format_text(src)

    def test_idempotent_config_style(self):
        src = "key                      = value\n"
        assert format_text(format_text(src)) == format_text(src)

    def test_idempotent_python_code(self):
        src = "import pyatb\nfrom pyatb import TightBinding\n"
        assert format_text(format_text(src)) == format_text(src)

    def test_idempotent_mixed(self):
        src = 'import pyatb\nkey=value\nhr_file = "HR.dat"\n'
        first = format_text(src)
        second = format_text(first)
        assert second == first

    def test_safe_formatter_preserves_python(self):
        src = "import pyatb\n"
        result = format_text(src)
        assert "import pyatb" in result

    def test_safe_formatter_preserves_def(self):
        src = "def foo():\n    pass\n"
        result = format_text(src)
        assert result == src

    def test_safe_formatter_preserves_class(self):
        src = "class MyTB:\n    pass\n"
        result = format_text(src)
        assert result == src

    def test_safe_formatter_preserves_if(self):
        src = "if True:\n    pass\n"
        result = format_text(src)
        assert result == src

    def test_safe_formatter_preserves_for(self):
        src = "for i in range(10):\n    pass\n"
        result = format_text(src)
        assert result == src

    def test_safe_formatter_preserves_return(self):
        src = "def f():\n    return 42\n"
        result = format_text(src)
        assert "return 42" in result

    def test_key_value_alignment(self):
        src = "key=value\n"
        result = format_text(src)
        assert "key" in result
        assert "=" in result
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
        src = "some random text without structure\n"
        result = format_text(src)
        assert "some" in result
        assert "random text without structure" in result

    def test_multiple_key_values(self):
        src = "a=1\nb=2\nc=3\n"
        result = format_text(src)
        for key in ("a", "b", "c"):
            assert key in result

    def test_idempotent_complex_document(self):
        src = (
            '"""Docstring."""\n'
            "import pyatb\n"
            "\n"
            "# Config\n"
            'hr_file = "HR.dat"\n'
            'sr_file = "SR.dat"\n'
            "\n"
            "tb = pyatb.TightBinding(hr_file=hr_file, sr_file=sr_file)\n"
            "tb.run()\n"
        )
        first = format_text(src)
        second = format_text(first)
        assert second == first


# ---------------------------------------------------------------------------
# _is_python_statement helper
# ---------------------------------------------------------------------------


class TestIsPythonStatement:
    def test_import(self):
        assert _is_python_statement("import pyatb") is True

    def test_from(self):
        assert _is_python_statement("from pyatb import TB") is True

    def test_def(self):
        assert _is_python_statement("def foo():") is True

    def test_class(self):
        assert _is_python_statement("class MyTB:") is True

    def test_if(self):
        assert _is_python_statement("if x > 0:") is True

    def test_for(self):
        assert _is_python_statement("for i in range(10):") is True

    def test_return(self):
        assert _is_python_statement("return 42") is True

    def test_assignment(self):
        assert _is_python_statement("x = 1") is False

    def test_function_call(self):
        assert _is_python_statement("tb.run()") is False

    def test_empty(self):
        assert _is_python_statement("") is False

    def test_decorator(self):
        assert _is_python_statement("@property") is True


# ---------------------------------------------------------------------------
# parse_log_content — runtime log parser (#22)
# ---------------------------------------------------------------------------


class TestParseLogContent:
    """Runtime log parser tests (#22)."""

    def test_parse_traceback(self):
        content = (
            "Traceback (most recent call last):\n  File 'run.py', line 10\nRuntimeError: bad\n"
        )
        diags = parse_log_content(content)
        e075 = [d for d in diags if d.code == "PYATB-E075"]
        assert len(e075) >= 1

    def test_parse_error_line(self):
        content = "Error: could not parse file\n"
        diags = parse_log_content(content)
        e075 = [d for d in diags if d.code == "PYATB-E075"]
        assert len(e075) >= 1
        assert "could not parse" in e075[0].message

    def test_parse_file_not_found(self):
        content = "FileNotFoundError: No such file or directory: 'HR.dat'\n"
        diags = parse_log_content(content)
        e074 = [d for d in diags if d.code == "PYATB-E074"]
        assert len(e074) >= 1

    def test_parse_import_error(self):
        content = "ModuleNotFoundError: No module named 'pyatb'\n"
        diags = parse_log_content(content)
        e071 = [d for d in diags if d.code == "PYATB-E071"]
        assert len(e071) >= 1
        assert "pyatb" in e071[0].message

    def test_parse_segfault(self):
        content = "Segmentation fault (core dumped)\n"
        diags = parse_log_content(content)
        e075 = [d for d in diags if d.code == "PYATB-E075"]
        assert len(e075) >= 1
        assert "crash" in e075[0].message

    def test_clean_log_no_diagnostics(self):
        content = "Starting calculation...\nDone.\n"
        diags = parse_log_content(content)
        assert len(diags) == 0

    def test_multiple_errors(self):
        content = "Traceback (most recent call last):\n  File 'x'\nError: first\nError: second\n"
        diags = parse_log_content(content)
        assert len(diags) >= 2

    def test_fixture_runtime_traceback(self):
        p = FIXTURES / "runtime_traceback.log"
        if not p.exists():
            pytest.skip("fixture not available")
        content = p.read_text(encoding="utf-8")
        diags = parse_log_content(content, str(p))
        assert len(diags) >= 1
        e075 = [d for d in diags if d.code == "PYATB-E075"]
        assert len(e075) >= 1

    def test_fixture_runtime_errors(self):
        p = FIXTURES / "runtime_errors.log"
        if not p.exists():
            pytest.skip("fixture not available")
        content = p.read_text(encoding="utf-8")
        diags = parse_log_content(content, str(p))
        assert len(diags) >= 3


# ---------------------------------------------------------------------------
# _detect_traceback_patterns
# ---------------------------------------------------------------------------


class TestDetectTracebackPatterns:
    def test_no_traceback(self, tmp_path: Path):
        content = "print('hello')\nx = 1\n"
        diags = _detect_traceback_patterns(tmp_path / "test.py", content)
        assert len(diags) == 0

    def test_single_traceback(self, tmp_path: Path):
        content = "x = 1\nTraceback (most recent call last):\n  File 'x'\nValueError: bad\n"
        diags = _detect_traceback_patterns(tmp_path / "test.py", content)
        assert len(diags) == 1
        assert diags[0].code == "PYATB-E075"
        assert diags[0].line == 2

    def test_multiple_tracebacks(self, tmp_path: Path):
        content = (
            "Traceback (most recent call last):\n"
            "  File 'a'\n"
            "Error: first\n"
            "Traceback (most recent call last):\n"
            "  File 'b'\n"
            "Error: second\n"
        )
        diags = _detect_traceback_patterns(tmp_path / "test.py", content)
        assert len(diags) == 2


# ---------------------------------------------------------------------------
# Integration: fixture-based tests
# ---------------------------------------------------------------------------


class TestFixtureIntegration:
    def test_valid_fixture_directory(self):
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
        assert "PYATB-E071" in codes

    def test_syntax_error_fixture(self):
        if not FIXTURES.exists():
            pytest.skip("fixtures dir not found")
        diag = analyze_path(FIXTURES / "syntax_error.py")
        assert any(d.severity == "error" for d in diag)

    def test_complete_valid_fixture(self):
        p = FIXTURES / "complete_valid.py"
        if not p.exists():
            pytest.skip("fixture not available")
        diag = analyze_file(p)
        errors = [d for d in diag if d.severity == "error"]
        assert not errors
        w070 = [d for d in diag if d.code == "PYATB-W070"]
        assert not w070
