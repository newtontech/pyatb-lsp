"""Tests for CLI entry points."""

from __future__ import annotations

from pathlib import Path

import pytest

from pyatb_lsp.cli import fmt_main, lint_main, log_main, lsp_main
from pyatb_lsp.cli import test_main as pyatb_test_main


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


class TestLintMain:
    def test_clean_file_returns_zero(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "ok.py", 'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\noutput = "out"\n')
        rc = lint_main([str(p)])
        assert rc == 0

    def test_error_file_returns_one(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "bad.py", "syntax error here (\n")
        rc = lint_main([str(p)])
        assert rc == 1

    def test_json_output(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "bad.py", "import os\nprint(os)\n")
        lint_main([str(p), "--json"])
        import json

        output = capsys.readouterr().out
        data = json.loads(output)
        assert isinstance(data, list)

    def test_text_output_format(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "bad.py", "import os\nprint(os)\n")
        lint_main([str(p)])
        output = capsys.readouterr().out
        assert ".py:" in output

    def test_lint_shows_new_rule_codes(self, tmp_path: Path, capsys):
        """New PYATB-E0xx codes should appear in lint output."""
        p = _write(tmp_path, "bad.py", "print('no import')\n")
        lint_main([str(p)])
        output = capsys.readouterr().out
        # Should have at least one E071 or E074 code
        assert "E071" in output or "E074" in output


class TestFmtMain:
    def test_format_to_stdout(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "in.py", "key=value\n")
        fmt_main([str(p)])
        output = capsys.readouterr().out
        assert "key" in output

    def test_format_write_in_place(self, tmp_path: Path):
        p = _write(tmp_path, "in.py", "key=value\n")
        fmt_main(["-w", str(p)])
        content = p.read_text()
        assert "key" in content

    def test_format_multiple_files(self, tmp_path: Path, capsys):
        p1 = _write(tmp_path, "a.py", "a=1\n")
        p2 = _write(tmp_path, "b.py", "b=2\n")
        fmt_main([str(p1), str(p2)])
        output = capsys.readouterr().out
        assert "a" in output

    def test_format_preserves_python(self, tmp_path: Path, capsys):
        """Formatting should not modify Python import statements."""
        p = _write(tmp_path, "in.py", "import pyatb\n")
        fmt_main([str(p)])
        output = capsys.readouterr().out
        assert output == "import pyatb\n"

    def test_format_idempotent_via_cli(self, tmp_path: Path):
        """Write then write again should be stable."""
        p = _write(tmp_path, "in.py", "key=value\n")
        fmt_main(["-w", str(p)])
        first = p.read_text()
        fmt_main(["-w", str(p)])
        second = p.read_text()
        assert first == second


class TestTestMain:
    def test_static_subcommand(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "ok.py", 'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\noutput = "out"\n')
        rc = pyatb_test_main(["static", str(p)])
        assert rc == 0

    def test_static_with_json(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "bad.py", "import os\nprint(os)\n")
        pyatb_test_main(["static", str(p), "--json"])
        import json

        output = capsys.readouterr().out
        data = json.loads(output)
        assert isinstance(data, list)


class TestLspMain:
    def test_stdio_mode(self, monkeypatch, capsys):
        class FakeServer:
            started = False

            def start_io(self) -> None:
                self.started = True

        fake = FakeServer()
        monkeypatch.setattr("pyatb_lsp.cli.create_server", lambda: fake)

        rc = lsp_main(["--stdio"])

        assert rc == 0
        assert fake.started

    def test_missing_stdio_flag(self):
        with pytest.raises(SystemExit):
            lsp_main([])


class TestLogMain:
    """Tests for pyatb-log CLI (#22)."""

    def test_clean_log_returns_zero(self, tmp_path: Path, capsys):
        p = _write(tmp_path, "clean.log", "Starting...\nDone.\n")
        rc = log_main([str(p)])
        assert rc == 0

    def test_error_log_returns_one(self, tmp_path: Path, capsys):
        p = _write(
            tmp_path, "error.log",
            "Traceback (most recent call last):\n  File 'x'\nError: bad\n",
        )
        rc = log_main([str(p)])
        assert rc == 1

    def test_json_output(self, tmp_path: Path, capsys):
        p = _write(
            tmp_path, "error.log",
            "Error: something went wrong\n",
        )
        log_main([str(p), "--json"])
        import json

        output = capsys.readouterr().out
        data = json.loads(output)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_text_output_format(self, tmp_path: Path, capsys):
        p = _write(
            tmp_path, "error.log",
            "Error: bad\n",
        )
        log_main([str(p)])
        output = capsys.readouterr().out
        assert "PYATB-E075" in output

    def test_missing_file_returns_two(self, tmp_path: Path, capsys):
        rc = log_main([str(tmp_path / "nonexistent.log")])
        assert rc == 2
