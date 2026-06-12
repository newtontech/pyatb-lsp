"""Tests for the LSP server module.

Covers capabilities:
- Diagnostics (#13)
- Hover (#7)
- Completion
- Formatting (#5)
- Code Actions (#21)
- Agent JSON (#11)
"""

from __future__ import annotations

from pathlib import Path

from pyatb_lsp.server import (
    PyATBServer,
    complete_keywords,
    create_server,
    diagnose_document,
    format_document,
    get_agent_json,
    get_code_actions,
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


# ---------------------------------------------------------------------------
# Diagnostics (#13)
# ---------------------------------------------------------------------------


class TestDiagnoseDocument:
    def test_valid_document_no_errors(self):
        content = 'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\noutput = "out"\n'
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
        warnings = [d for d in diags if d.severity == 2]
        assert len(warnings) >= 1

    def test_empty_content(self):
        diags = diagnose_document("file:///test.py", "")
        assert isinstance(diags, list)

    def test_diagnostic_has_pyatb_source(self):
        content = "def broken(\n"
        diags = diagnose_document("file:///test.py", content)
        for d in diags:
            assert d.source == "pyatb-lsp"

    def test_diagnostic_has_code(self):
        content = "def broken(\n"
        diags = diagnose_document("file:///test.py", content)
        for d in diags:
            assert d.code is not None

    def test_new_rule_codes_in_diagnostics(self):
        """Verify that new PYATB-E0xx codes appear in diagnostics."""
        content = "print('no import')\n"
        diags = diagnose_document("file:///test.py", content)
        codes = [str(d.code) for d in diags]
        assert any("E071" in c for c in codes)

    def test_e074_in_diagnostics(self):
        """PYATB-E074 for missing structure reference."""
        content = "import pyatb\nresult = 42\n"
        diags = diagnose_document("file:///test.py", content)
        codes = [str(d.code) for d in diags]
        assert any("E074" in c for c in codes)

    def test_w070_in_diagnostics(self):
        """PYATB-W070 for missing output path."""
        content = 'import pyatb\nhr_file = "HR.dat"\n'
        diags = diagnose_document("file:///test.py", content)
        codes = [str(d.code) for d in diags]
        assert any("W070" in c for c in codes)


# ---------------------------------------------------------------------------
# Formatting (#5)
# ---------------------------------------------------------------------------


class TestFormatDocument:
    def test_formats_key_value(self):
        content = "key=value\n"
        result = format_document(content)
        assert "key" in result
        assert "=" in result

    def test_idempotent(self):
        content = 'import pyatb\nhr_file = "HR.dat"\n'
        assert format_document(format_document(content)) == format_document(content)

    def test_safe_python_pass_through(self):
        """Python code should not be reformatted."""
        content = "import pyatb\n"
        result = format_document(content)
        assert result == content

    def test_safe_def_pass_through(self):
        content = "def foo():\n    pass\n"
        result = format_document(content)
        assert result == content

    def test_safe_class_pass_through(self):
        content = "class TB:\n    pass\n"
        result = format_document(content)
        assert result == content

    def test_idempotent_config_style(self):
        src = "key                      = value\n"
        result = format_document(src)
        assert format_document(result) == result


# ---------------------------------------------------------------------------
# Completion
# ---------------------------------------------------------------------------


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

    def test_completion_output_keywords(self):
        """New MatMaster output keywords should be in completions."""
        items = complete_keywords("out")
        labels = [item.label for item in items]
        assert "output" in labels or "out_file" in labels or "output_path" in labels

    def test_completion_result_dir(self):
        items = complete_keywords("result")
        labels = [item.label for item in items]
        assert "result_dir" in labels

    def test_completion_case_insensitive(self):
        items = complete_keywords("TB")
        labels = [item.label for item in items]
        assert "TB" in labels


# ---------------------------------------------------------------------------
# Hover (#7)
# ---------------------------------------------------------------------------


class TestHoverInfo:
    def test_hover_for_import(self):
        info = hover_info("import pyatb", 0, 7)
        assert info is not None
        assert "pyatb" in info.lower() or "PyATB" in info

    def test_hover_for_unknown(self):
        info = hover_info("unknown_token", 0, 3)
        assert info is None or isinstance(info, str)

    def test_hover_for_tightbinding(self):
        """Extended hover for TightBinding (#7)."""
        info = hover_info("tb = TightBinding()", 0, 5)
        assert info is not None
        assert "TightBinding" in info

    def test_hover_for_hr_file(self):
        """Extended hover for hr_file (#7)."""
        info = hover_info('hr_file = "HR.dat"', 0, 3)
        assert info is not None
        assert "hr_file" in info

    def test_hover_for_kmsh(self):
        """Extended hover for kmesh (#7)."""
        info = hover_info("kmesh = [4,4,4]", 0, 3)
        assert info is not None
        assert "kmesh" in info.lower() or "k-point" in info.lower()

    def test_hover_for_conductivity(self):
        info = hover_info("conductivity = calc()", 0, 3)
        assert info is not None
        assert "conductivity" in info.lower() or "transport" in info.lower()

    def test_hover_for_dos(self):
        info = hover_info("dos = calc()", 0, 3)
        assert info is not None
        assert "dos" in info.lower() or "density of states" in info.lower()

    def test_hover_for_band(self):
        info = hover_info("band = calc()", 0, 3)
        assert info is not None
        assert "band" in info.lower() or "structure" in info.lower()

    def test_hover_out_of_range_line(self):
        info = hover_info("x = 1\n", 5, 0)
        assert info is None

    def test_hover_out_of_range_column(self):
        info = hover_info("x = 1\n", 0, 100)
        assert info is None

    def test_hover_empty_position(self):
        info = hover_info("x = 1\n", 0, 0)
        # At column 0 we might get hover for 'x' which is not in catalog
        assert info is None or isinstance(info, str)


# ---------------------------------------------------------------------------
# Code Actions (#21)
# ---------------------------------------------------------------------------


class TestCodeActions:
    def test_code_action_for_missing_import(self):
        from lsprotocol.types import Diagnostic as LspDiag
        from lsprotocol.types import Position, Range

        content = "print('hello')\n"
        diag = LspDiag(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=1),
            ),
            message="[PYATB-E071] missing import",
            severity=1,
            code="PYATB-E071",
        )
        actions = get_code_actions("file:///test.py", content, [diag])
        assert len(actions) >= 1
        titles = [a.title for a in actions]
        assert any("import pyatb" in t for t in titles)

    def test_code_action_for_missing_structure(self):
        from lsprotocol.types import Diagnostic as LspDiag
        from lsprotocol.types import Position, Range

        content = "import pyatb\nresult = 42\n"
        diag = LspDiag(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=1),
            ),
            message="[PYATB-E074] missing structure",
            severity=1,
            code="PYATB-E074",
        )
        actions = get_code_actions("file:///test.py", content, [diag])
        assert len(actions) >= 1

    def test_code_action_for_missing_output(self):
        from lsprotocol.types import Diagnostic as LspDiag
        from lsprotocol.types import Position, Range

        content = 'import pyatb\nhr_file = "HR.dat"\n'
        diag = LspDiag(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=1),
            ),
            message="[PYATB-W070] missing output",
            severity=2,
            code="PYATB-W070",
        )
        actions = get_code_actions("file:///test.py", content, [diag])
        assert len(actions) >= 1
        titles = [a.title for a in actions]
        assert any("output" in t.lower() for t in titles)

    def test_code_action_for_syntax_error(self):
        from lsprotocol.types import Diagnostic as LspDiag
        from lsprotocol.types import Position, Range

        content = "def broken(\n"
        diag = LspDiag(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=1),
            ),
            message="[PYATB-E070] syntax error",
            severity=1,
            code="PYATB-E070",
        )
        actions = get_code_actions("file:///test.py", content, [diag])
        assert len(actions) >= 1

    def test_no_code_actions_for_clean_file(self):
        actions = get_code_actions("file:///test.py", "import pyatb\n", [])
        assert len(actions) == 0

    def test_code_action_add_import_has_edit(self):
        from lsprotocol.types import Diagnostic as LspDiag
        from lsprotocol.types import Position, Range

        content = "print('hello')\n"
        diag = LspDiag(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=1),
            ),
            message="[PYATB-E071] missing import",
            severity=1,
            code="PYATB-E071",
        )
        actions = get_code_actions("file:///test.py", content, [diag])
        # Find the add import action
        add_import = [a for a in actions if "import pyatb" in a.title]
        assert len(add_import) >= 1
        assert add_import[0].edit is not None


# ---------------------------------------------------------------------------
# Agent JSON (#11)
# ---------------------------------------------------------------------------


class TestAgentJSON:
    def test_agent_json_returns_dict(self):
        content = 'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\noutput = "out"\n'
        payload = get_agent_json("file:///test.py", content)
        assert isinstance(payload, dict)

    def test_agent_json_has_capabilities(self):
        content = 'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\noutput = "out"\n'
        payload = get_agent_json("file:///test.py", content)
        assert "capabilities" in payload
        caps = payload["capabilities"]
        assert caps["hover"] is True
        assert caps["completion"] is True
        assert caps["formatting"] is True
        assert caps["code_actions"] is True
        assert caps["diagnostics"] is True
        assert caps["log_parser"] is True

    def test_agent_json_has_rule_codes(self):
        content = 'import pyatb\nhr_file = "HR.dat"\n'
        payload = get_agent_json("file:///test.py", content)
        assert "rule_codes" in payload
        rules = payload["rule_codes"]
        assert "PYATB-E070" in rules
        assert "PYATB-E071" in rules
        assert "PYATB-E072" in rules
        assert "PYATB-E073" in rules
        assert "PYATB-E074" in rules
        assert "PYATB-W070" in rules
        assert "PYATB-E075" in rules

    def test_agent_json_has_diagnostics(self):
        content = 'import pyatb\nhr_file = "HR.dat"\n'
        payload = get_agent_json("file:///test.py", content)
        assert "diagnostics" in payload

    def test_agent_json_has_software(self):
        content = 'import pyatb\nhr_file = "HR.dat"\n'
        payload = get_agent_json("file:///test.py", content)
        assert payload["software"] == "pyatb"

    def test_agent_json_has_diagnostic_engine(self):
        content = 'import pyatb\nhr_file = "HR.dat"\n'
        payload = get_agent_json("file:///test.py", content)
        assert payload["diagnostic_engine"] == "1.0"
