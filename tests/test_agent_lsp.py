"""Tests for the AgentLSP wrapper (#11, #22)."""

from __future__ import annotations

from pathlib import Path

from pyatb_lsp.agent_lsp import AgentLSP


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


class TestAgentLSPCheck:
    def test_check_from_text(self):
        agent = AgentLSP.from_text('import pyatb\nhr_file = "HR.dat"\n')
        payload = agent.check()
        assert payload["software"] == "pyatb"
        assert "diagnostics" in payload

    def test_check_from_path(self, tmp_path: Path):
        p = _write(tmp_path, "test.py", 'import pyatb\nhr_file = "HR.dat"\n')
        agent = AgentLSP.from_path(p)
        payload = agent.check()
        assert payload["software"] == "pyatb"

    def test_check_has_summary(self):
        agent = AgentLSP.from_text('import pyatb\nhr_file = "HR.dat"\n')
        payload = agent.check()
        assert "summary" in payload
        assert "count" in payload["summary"]


class TestAgentLSPAgentJSON:
    """Tests for agent_json() capability (#11)."""

    def test_agent_json_has_capabilities(self):
        agent = AgentLSP.from_text('import pyatb\nhr_file = "HR.dat"\n')
        payload = agent.agent_json()
        assert "capabilities" in payload
        assert payload["capabilities"]["hover"] is True
        assert payload["capabilities"]["completion"] is True
        assert payload["capabilities"]["formatting"] is True
        assert payload["capabilities"]["code_actions"] is True
        assert payload["capabilities"]["diagnostics"] is True
        assert payload["capabilities"]["log_parser"] is True

    def test_agent_json_has_rule_codes(self):
        agent = AgentLSP.from_text('import pyatb\nhr_file = "HR.dat"\n')
        payload = agent.agent_json()
        assert "rule_codes" in payload
        codes = payload["rule_codes"]
        assert "PYATB-E070" in codes
        assert "PYATB-E071" in codes
        assert "PYATB-E072" in codes
        assert "PYATB-E073" in codes
        assert "PYATB-E074" in codes
        assert "PYATB-W070" in codes
        assert "PYATB-E075" in codes

    def test_agent_json_has_software(self):
        agent = AgentLSP.from_text("x = 1\n")
        payload = agent.agent_json()
        assert payload["software"] == "pyatb"


class TestAgentLSPLogParser:
    """Tests for parse_log() capability (#22)."""

    def test_parse_log_clean(self):
        agent = AgentLSP()
        payload = agent.parse_log("Starting...\nDone.\n")
        assert payload["log_parsed"] is True
        assert payload["log_diagnostics_count"] == 0

    def test_parse_log_with_traceback(self):
        agent = AgentLSP()
        content = "Traceback (most recent call last):\n  File 'run.py'\nError: bad\n"
        payload = agent.parse_log(content)
        assert payload["log_parsed"] is True
        assert payload["log_diagnostics_count"] >= 1

    def test_parse_log_with_error(self):
        agent = AgentLSP()
        payload = agent.parse_log("Error: something failed\n")
        assert payload["log_diagnostics_count"] >= 1

    def test_parse_log_with_import_error(self):
        agent = AgentLSP()
        payload = agent.parse_log("ModuleNotFoundError: No module named 'pyatb'\n")
        assert payload["log_diagnostics_count"] >= 1

    def test_parse_log_with_file_not_found(self):
        agent = AgentLSP()
        payload = agent.parse_log("FileNotFoundError: No such file: 'HR.dat'\n")
        assert payload["log_diagnostics_count"] >= 1

    def test_parse_log_has_diagnostics(self):
        agent = AgentLSP()
        payload = agent.parse_log("Error: test\n")
        assert "diagnostics" in payload
        assert len(payload["diagnostics"]) >= 1


class TestAgentLSPContext:
    def test_context_returns_position(self):
        agent = AgentLSP()
        payload = agent.context(line=5, character=10)
        assert payload["position"]["line"] == 5
        assert payload["position"]["character"] == 10

    def test_hover_returns_position(self):
        agent = AgentLSP()
        payload = agent.hover(line=3, character=5)
        assert payload["position"]["line"] == 3

    def test_complete_returns_position(self):
        agent = AgentLSP()
        payload = agent.complete(line=1, character=4)
        assert payload["position"]["line"] == 1

    def test_symbols_returns_items(self):
        agent = AgentLSP()
        payload = agent.symbols()
        assert "items" in payload
