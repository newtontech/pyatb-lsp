"""Tests for pyatb-lsp-tool CLI."""

from __future__ import annotations

import json
from pathlib import Path

from pyatb_lsp.tool import main as tool_main


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


class TestToolCheck:
    def test_check_valid_file(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "ok.py", 'import pyatb\nhr_file = "HR.dat"\n')
        rc = tool_main(["check", str(p)])
        assert rc == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert data["software"] == "pyatb"

    def test_check_invalid_file(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "bad.py", "syntax error (\n")
        rc = tool_main(["check", str(p), "--fail-on-blocking"])
        assert rc == 1

    def test_check_has_diagnostics(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "bad.py", "print('no import')\n")
        tool_main(["check", str(p)])
        data = json.loads(capsys.readouterr().out)
        assert data["summary"]["count"] >= 1


class TestToolParseLog:
    """Tests for parse-log operation (#22)."""

    def test_parse_log_clean(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "clean.log", "Starting...\nDone.\n")
        rc = tool_main(["parse-log", str(p)])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["summary"]["count"] == 0

    def test_parse_log_with_errors(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "error.log", "Error: something bad\n")
        rc = tool_main(["parse-log", str(p)])
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        assert data["summary"]["count"] >= 1

    def test_parse_log_with_traceback(self, tmp_path: Path, capsys):
        content = (
            "Traceback (most recent call last):\n"
            "  File 'x'\n"
            "RuntimeError: fail\n"
        )
        p = _write(tmp_path, "traceback.log", content)
        rc = tool_main(["parse-log", str(p)])
        assert rc == 1


class TestToolAgentJSON:
    """Tests for agent-json operation (#11)."""

    def test_agent_json_has_capabilities(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "ok.py", 'import pyatb\nhr_file = "HR.dat"\n')
        rc = tool_main(["agent-json", str(p)])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert "capabilities" in data
        assert data["capabilities"]["hover"] is True

    def test_agent_json_has_rule_codes(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "ok.py", 'import pyatb\nhr_file = "HR.dat"\n')
        tool_main(["agent-json", str(p)])
        data = json.loads(capsys.readouterr().out)
        assert "rule_codes" in data
        assert "PYATB-E070" in data["rule_codes"]


class TestToolAgentOperations:
    def test_context_operation(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "ok.py", "x = 1\n")
        rc = tool_main(["context", str(p)])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["operation"] == "context"
        assert data["capabilities"]["operation"] == "context"

    def test_hover_operation(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "ok.py", "x = 1\n")
        rc = tool_main(["hover", str(p)])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["operation"] == "hover"
        assert data["capabilities"]["operation"] == "hover"
