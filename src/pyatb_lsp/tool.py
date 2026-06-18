"""Agent-facing CLI for Diagnostic Engine v1 operations.

Supports: check, preflight, manifest, context, complete, hover, symbols, fix,
parse-log, agent-json.

LLM Wiki: wiki/synthesis/openqc-agent-context.md
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, cast

from .agent_operations import operation_path, with_capabilities
from .rich_diagnostics import agent_check_payload
from .skill_export import export_skill, skill_spec_text

SOFTWARE = "pyatb"
INTENT_DIR = ".pyatb-lsp"


def _capabilities_payload() -> dict[str, Any]:
    for parent in Path(__file__).resolve().parents:
        manifest_path = parent / "lsp-capabilities.json"
        if manifest_path.exists():
            return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))
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
            "preflight",
        ],
        "agentCli": {
            "operations": [
                "capabilities",
                "check",
                "preflight",
                "manifest",
                "context",
                "complete",
                "hover",
                "symbols",
                "fix",
            ],
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


def _load_intent(path: Path) -> dict[str, Any] | None:
    """Load the optional preflight intent contract for a case directory.

        The intent contract is the only place preflight policy overrides live
        (e.g. ``software_version``, ``runtime_image``, ``kpath_warning_density``).
        It is a workspace-local artifact, never a MatMaster/Bohrium runtime concept.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    case_dir = path if path.is_dir() else path.parent
    intent_path = case_dir / INTENT_DIR / "intent.json"
    if not intent_path.exists():
        return None
    try:
        data = json.loads(intent_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _looks_like_workspace(case_dir: Path) -> bool:
    """True when a directory is a real generated-input workspace.

        Preflight needs at least one Python workflow script that drives the pyatb
        library to build a meaningful cross-artifact graph; a directory with no
        ``.py`` file falls back to the legacy single-file lint path.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    if not case_dir.is_dir():
        return False
    py_files = list(case_dir.glob("*.py"))
    if not py_files:
        return False
    return any(_script_imports_pyatb(candidate) for candidate in py_files)


def _script_imports_pyatb(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "pyatb":
                    return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] == "pyatb":
                return True
    return False


def _collect_preflight(
    path: Path, intent: dict[str, Any] | None
) -> tuple[list[Any], list[dict[str, Any]], dict[str, Any]]:
    """Return (preflight_diagnostics, artifact_graph, version_assumption).

        Imported lazily so callers that never touch preflight (e.g. single-file
        LSP hover) pay no import cost.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    from .preflight import preflight_diagnostics, resolve_version_assumption

    case_dir = path if path.is_dir() else path.parent
    diagnostics, graph = preflight_diagnostics(case_dir, intent=intent)
    version_assumption = resolve_version_assumption(intent)
    return diagnostics, graph.to_json(), version_assumption


def check_path(path: Path) -> dict[str, Any]:
    uri = path.resolve().as_uri()
    intent = _load_intent(path)
    diagnostics = _collect_diagnostics(path)
    # Universal preflight diagnostics augment the legacy analyzer output, but
    # only for a real generated-input workspace (a directory). A bare single
    # file path keeps the legacy single-file behavior so existing consumers
    # that lint one workflow at a time are unaffected.
    case_dir = path if path.is_dir() else (path.parent if path.suffix.lower() == ".py" else None)
    artifacts: list[dict[str, Any]] = []
    version_assumption: dict[str, Any] | None = None
    if case_dir is not None and _looks_like_workspace(case_dir):
        preflight, artifacts, version_assumption = _collect_preflight(path, intent)
        diagnostics.extend(_dedupe_preflight(diagnostics, preflight))
    return agent_check_payload(
        software=SOFTWARE,
        uri=uri,
        operation="check",
        diagnostics=diagnostics,
        path=str(path),
        file_type=_file_type(path),
        intent=intent,
        version_assumption=version_assumption,
        artifacts=artifacts,
    )


# Codes already emitted by the legacy analyzer that overlap with the universal
# preflight surface. We keep the legacy emission (it carries the existing test
# contract) and drop the duplicate preflight variant to avoid noisy double
# reports. The preflight shape is still proven by every other fixture.
_OVERLAP_CODES_BY_LEGACY = {
    "PYATB-E074": {"PYATB602"},  # legacy missing structure reference
    "PYATB-E073": {"PYATB604"},  # legacy invalid JSON in configuration
    "PYATB010": {"PYATB602"},  # legacy HR.dat/hr_file guard
}


def _dedupe_preflight(legacy: list[Any], preflight: list[Any]) -> list[Any]:
    """Drop preflight diagnostics whose finding the legacy analyzer already emitted.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    emitted_legacy = {
        getattr(item, "code", None) or (item.get("code") if isinstance(item, dict) else None)
        for item in legacy
    }
    suppressed_preflight: set[str] = set()
    for legacy_code, preflight_codes in _OVERLAP_CODES_BY_LEGACY.items():
        if legacy_code in emitted_legacy:
            suppressed_preflight |= preflight_codes
    return [
        item
        for item in preflight
        if (item.get("code") if isinstance(item, dict) else None) not in suppressed_preflight
    ]


def preflight_path(path: Path) -> dict[str, Any]:
    """Return a preflight-only payload (universal checks, no legacy analyzer).

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    from .preflight import preflight_diagnostics, resolve_version_assumption

    intent = _load_intent(path)
    case_dir = path if path.is_dir() else path.parent
    diagnostics, graph = preflight_diagnostics(case_dir, intent=intent)
    version_assumption = resolve_version_assumption(intent)
    payload = agent_check_payload(
        software=SOFTWARE,
        uri=case_dir.resolve().as_uri(),
        operation="preflight",
        diagnostics=diagnostics,
        path=str(case_dir),
        file_type="case-dir",
        intent=intent,
        version_assumption=version_assumption,
        artifacts=graph.to_json(),
    )
    return with_capabilities(payload, "preflight")


def manifest_path(path: Path | None = None) -> dict[str, Any]:
    """Return the fleet preflight manifest.

        When ``path`` is given, fixture expectations declared in
        ``.pyatb-lsp/fixtures.json`` are merged in so the parent probe can confirm
        a case directory exercises the documented codes.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    from .preflight import fleet_manifest

    fixtures: list[dict[str, Any]] = []
    if path is not None:
        case_dir = path if path.is_dir() else path.parent
        fixtures_path = case_dir / INTENT_DIR / "fixtures.json"
        if fixtures_path.exists():
            try:
                data = json.loads(fixtures_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = None
            if isinstance(data, list):
                fixtures = [item for item in data if isinstance(item, dict)]
            elif isinstance(data, dict) and isinstance(data.get("fixtures"), list):
                fixtures = [item for item in data["fixtures"] if isinstance(item, dict)]
    return fleet_manifest(fixtures=fixtures)


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
    """Parse a log file for runtime errors (#22).

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
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


def _fix_path(path: Path) -> dict[str, Any]:
    """Generate fix previews for diagnostics on the given path (#40).

        Returns a DiagnosticEnvelope/v1 payload with ``fix_preview`` entries
        attached to each diagnostic that has a suggested_fix.  Safe-to-apply
        fixes are flagged so agents can auto-apply them.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    from .fix_preview import generate_fix_preview
    from .rich_diagnostics import serialize_diagnostics

    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        content = ""

    diagnostics = _collect_diagnostics(path)

    # Use the rich diagnostics serializer for envelope v1 compliance.
    serialized = serialize_diagnostics(
        diagnostics, software=SOFTWARE, path=str(path), file_type=_file_type(path)
    )

    # Attach fix previews to each serialized diagnostic.
    for item in serialized:
        suggested_fix = item.get("fix_hints", [None])[0] if item.get("fix_hints") else None
        fix_preview = generate_fix_preview(path, content, item["code"], suggested_fix)
        if fix_preview is not None:
            item["fix_preview"] = fix_preview

    blocking_count = sum(1 for item in serialized if item["blocking"])
    return {
        "uri": path.resolve().as_uri(),
        "operation": "fix",
        "ok": blocking_count == 0,
        "version": "1.0",
        "software": SOFTWARE,
        "diagnostic_engine": "1.0",
        "diagnostic_envelope": "v1",
        "path": str(path),
        "file_type": _file_type(path),
        "diagnostics": serialized,
        "summary": {
            "count": len(serialized),
            "blocking": blocking_count,
            "errors": sum(1 for item in serialized if item["severity"] == "error"),
            "warnings": sum(1 for item in serialized if item["severity"] == "warning"),
        },
    }


def _agent_json(path: Path) -> dict[str, Any]:
    """Build the full agent JSON payload (#11).

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
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
    skill_spec = subparsers.add_parser("skill-spec")
    skill_spec.add_argument("--format", choices=["json", "yaml"], default="json")
    skill_export = subparsers.add_parser("skill-export")
    skill_export.add_argument("--output", type=Path, required=True)
    capabilities = subparsers.add_parser("capabilities")
    capabilities.add_argument("--format", choices=["json"], default="json")
    for operation in (
        "check",
        "preflight",
        "manifest",
        "context",
        "complete",
        "hover",
        "symbols",
        "fix",
        "parse-log",
        "agent-json",
    ):
        sub = subparsers.add_parser(operation)
        if operation == "manifest":
            sub.add_argument(
                "path",
                type=Path,
                nargs="?",
                help="Optional case directory to merge fixture expectations from.",
            )
        else:
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
        if operation == "preflight":
            sub.add_argument("--fail-on-blocking", action="store_true")
        if operation == "parse-log":
            sub.add_argument(
                "--log-file",
                type=Path,
                default=None,
                help="Path to log file (defaults to <path>)",
            )

    args = parser.parse_args(argv)

    if args.operation == "skill-spec":
        print(skill_spec_text(args.format))
        return 0
    if args.operation == "skill-export":
        print(json.dumps(export_skill(args.output), indent=2, sort_keys=True))
        return 0

    if args.operation == "capabilities":
        print(json.dumps(_capabilities_payload(), indent=2, sort_keys=True))
        return 0

    if args.operation == "check":
        payload = with_capabilities(check_path(args.path), "check")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if getattr(args, "fail_on_blocking", False) and not payload["ok"] else 0

    if args.operation == "preflight":
        payload = preflight_path(args.path)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if getattr(args, "fail_on_blocking", False) and not payload["ok"] else 0

    if args.operation == "manifest":
        payload = manifest_path(getattr(args, "path", None))
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.operation == "parse-log":
        log_path = getattr(args, "log_file", None) or args.path
        payload = _parse_log(log_path)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if not payload["ok"] else 0

    if args.operation == "agent-json":
        payload = _agent_json(args.path)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.operation == "fix":
        payload = with_capabilities(_fix_path(args.path), "fix")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if not payload["ok"] else 0

    payload = _operation_payload(args.path, args.operation, args.line, args.character)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
