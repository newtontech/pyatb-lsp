from __future__ import annotations

from pathlib import Path

from pyatb_lsp.analyzer import analyze_path, format_text


def test_valid_fixture_has_no_errors(tmp_path: Path) -> None:
    fixture = tmp_path / "run_pyatb.py"
    fixture.write_text(
        'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\nprint(hr_file, sr_file, pyatb)\n',
        encoding="utf-8",
    )

    diagnostics = analyze_path(tmp_path)

    assert not [item for item in diagnostics if item.severity == "error"]


def test_invalid_fixture_reports_diagnostic(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.py"
    fixture.write_text('import pyatb\nprint("missing files")\n', encoding="utf-8")

    diagnostics = analyze_path(tmp_path)

    assert diagnostics


def test_formatter_is_idempotent() -> None:
    first = format_text(
        'import pyatb\nhr_file = "HR.dat"\nsr_file = "SR.dat"\nprint(hr_file, sr_file, pyatb)\n'
    )
    second = format_text(first)

    assert second == first
