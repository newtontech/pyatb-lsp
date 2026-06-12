"""Agent-facing CLI for Diagnostic Engine v1 operations.

Supports: check, context, complete, hover, symbols, fix, parse-log, agent-json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .rich_diagnostics import agent_check_payload

SOFTWARE = "pyatb"


def _capabilities_payload() -> dict[str, Any]:
    for parent in Path(__file__).resolve().parents:
        manifest_path = parent / "lsp-capabilities.json"
        if manifest_path.exists():
            return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "schema": "OpenQCLspCapabilities",
        "version": 1,
        "software": SOFTWARE,
        "capabilities": [
            "diagnostics",
            "rich-diagnostics",
            "completion",
            "hover",
            "symbols",
            "fix-preview",
            "llm-wiki",
            "openqc-context",
        ],
        "agentCli": {
            "operations": ["capabilities", "check", "context", "complete", "hover", "symbols", "fix"],
            "jsonFormat": True,
            "failOnBlocking": True,
        },
    }


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


def _empty_operation(path: Path, operation: str) -> dict[str, Any]:
    payload = agent_check_payload(
        software=SOFTWARE,
        uri=path.resolve().as_uri(),
        operation=operation,
        diagnostics=[],
        path=str(path),
        file_type=_file_type(path),
    )
    payload["summary"]["note"] = (
        f"{operation} is reserved by the Diagnostic Engine v1 CLI contract"
    )
    return payload


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
    capabilities = subparsers.add_parser("capabilities")
    capabilities.add_argument("--format", choices=["json"], default="json")
    for operation in (
        "check", "context", "complete", "hover", "symbols", "fix",
        "parse-log", "agent-json",
    ):
        sub = subparsers.add_parser(operation)
        sub.add_argument("path", type=Path)
        sub.add_argument("--format", choices=["json"], default="json")
        if operation == "check":
            sub.add_argument("--fail-on-blocking", action="store_true")
        if operation == "parse-log":
            sub.add_argument(
                "--log-file", type=Path, default=None,
                help="Path to log file (defaults to <path>)",
            )

    args = parser.parse_args(argv)

    if args.operation == "capabilities":
        print(json.dumps(_capabilities_payload(), indent=2, sort_keys=True))
        return 0

    if args.operation == "check":
        payload = check_path(args.path)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return (
            1
            if getattr(args, "fail_on_blocking", False) and not payload["ok"]
            else 0
        )

    if args.operation == "parse-log":
        log_path = getattr(args, "log_file", None) or args.path
        payload = _parse_log(log_path)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if not payload["ok"] else 0

    if args.operation == "agent-json":
        payload = _agent_json(args.path)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(json.dumps(_empty_operation(args.path, args.operation), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
