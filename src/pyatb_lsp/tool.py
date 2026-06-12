"""Agent-facing CLI for Diagnostic Engine v1 operations.

Supports: check, context, complete, hover, symbols, fix, parse-log, agent-json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .agent_operations import operation_path, with_capabilities
from .rich_diagnostics import agent_check_payload

SOFTWARE = "pyatb"


def _file_type(path: Path) -> str:
    name = path.name.upper()
    if name in {"INCAR", "POSCAR", "KPOINTS", "POTCAR", "CONTCAR"}:
        return name
    if "." in path.name:
        return path.suffix.lstrip(".").lower()
    return name.lower()


def _collect_diagnostics(path: Path) -> list[Any]:
    from .analyzer import analyze_path

    return list(analyze_path(path))


def check_path(path: Path) -> dict[str, Any]:
    uri = path.resolve().as_uri()
    diagnostics = _collect_diagnostics(path)
    return agent_check_payload(
        software=SOFTWARE,
        uri=uri,
        operation="check",
        diagnostics=diagnostics,
        path=str(path),
        file_type=_file_type(path),
    )


def _operation_payload(
    path: Path,
    operation: str,
    line: int = 0,
    character: int = 0,
) -> dict[str, Any]:
    return operation_path(
        path,
        operation,
        software=SOFTWARE,
        file_type_func=_file_type,
        collect_diagnostics=_collect_diagnostics,
        line=line,
        character=character,
    )


def _parse_log(path: Path) -> dict[str, Any]:
    """Parse a log file for runtime errors (#22)."""
    from .analyzer import parse_log_content

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = ""

    diagnostics = parse_log_content(content, str(path))
    return agent_check_payload(
        software=SOFTWARE,
        uri=path.resolve().as_uri(),
        operation="parse_log",
        diagnostics=diagnostics,
        path=str(path),
        file_type=_file_type(path),
    )


def _agent_json(path: Path) -> dict[str, Any]:
    """Build the full agent JSON payload (#11)."""
    payload = check_path(path)
    payload["capabilities"] = {
        "hover": True,
        "completion": True,
        "formatting": True,
        "code_actions": True,
        "diagnostics": True,
        "log_parser": True,
    }
    payload["rule_codes"] = {
        "PYATB-E070": "Python syntax errors",
        "PYATB-E071": "Missing required imports",
        "PYATB-E072": "Missing required symbols",
        "PYATB-E073": "Invalid JSON in configuration",
        "PYATB-E074": "Missing structure reference",
        "PYATB-W070": "Missing output path",
        "PYATB-E075": "Runtime log traceback",
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pyatb-lsp-tool")
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in (
        "check",
        "context",
        "complete",
        "hover",
        "symbols",
        "fix",
        "parse-log",
        "agent-json",
    ):
        sub = subparsers.add_parser(operation)
        sub.add_argument("path", type=Path)
        sub.add_argument("--format", choices=["json"], default="json")
        sub.add_argument(
            "--line",
            type=int,
            default=0,
            help="0-based line for position-aware operations.",
        )
        sub.add_argument(
            "--character",
            type=int,
            default=0,
            help="0-based character for position-aware operations.",
        )
        if operation == "check":
            sub.add_argument("--fail-on-blocking", action="store_true")
        if operation == "parse-log":
            sub.add_argument(
                "--log-file",
                type=Path,
                default=None,
                help="Path to log file (defaults to <path>)",
            )

    args = parser.parse_args(argv)

    if args.operation == "check":
        payload = with_capabilities(check_path(args.path), "check")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if getattr(args, "fail_on_blocking", False) and not payload["ok"] else 0

    if args.operation == "parse-log":
        log_path = getattr(args, "log_file", None) or args.path
        payload = _parse_log(log_path)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if not payload["ok"] else 0

    if args.operation == "agent-json":
        payload = _agent_json(args.path)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    payload = _operation_payload(args.path, args.operation, args.line, args.character)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
