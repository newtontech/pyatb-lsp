"""Fix preview/patch operations for PyATB scripts.

This module provides deterministic repair previews for common PyATB
diagnostic issues. Each fix operation returns a structured patch
that can be applied to the file.

Fix operations:
- add_import: Add missing import statement
- add_symbol_reference: Add missing symbol reference (HR.dat, SR.dat)
- add_structure_reference: Add missing structure reference
- add_output_path: Add missing output path
- fix_syntax: Placeholder for syntax error fixes
- fix_json_syntax: Placeholder for JSON syntax fixes
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_fix_preview(
    path: Path,
    content: str,
    diagnostic_code: str,
    suggested_fix: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Generate a fix preview for a diagnostic.

    Parameters
    ----------
    path
        The file path.
    content
        The file content.
    diagnostic_code
        The diagnostic code to fix.
    suggested_fix
        The suggested fix from the diagnostic.

    Returns
    -------
    dict or None
        A fix preview with edit operations, or None if no fix is available.
    """
    if suggested_fix is None:
        return None

    kind = suggested_fix.get("kind", "")

    if kind == "add_import":
        return _fix_add_import(path, content, suggested_fix)
    elif kind == "add_symbol_reference":
        return _fix_add_symbol_reference(path, content, suggested_fix)
    elif kind == "add_structure_reference":
        return _fix_add_structure_reference(path, content, suggested_fix)
    elif kind == "add_output_path":
        return _fix_add_output_path(path, content, suggested_fix)
    elif kind == "fix_syntax":
        return _fix_syntax(path, content, suggested_fix)
    elif kind == "fix_json_syntax":
        return _fix_json_syntax(path, content, suggested_fix)
    elif kind == "add_required_token":
        return _fix_add_required_token(path, content, suggested_fix)
    elif kind == "add_structure_block":
        return _fix_add_structure_block(path, content, suggested_fix)
    elif kind == "check_keyword_spelling":
        return None  # Cannot auto-fix spelling
    elif kind == "check_file_path":
        return None  # Cannot auto-fix file paths
    elif kind == "investigate_traceback":
        return None  # Cannot auto-fix tracebacks
    elif kind == "install_module":
        return None  # Cannot auto-fix missing modules
    elif kind == "move_command":
        return _fix_move_command(path, content, suggested_fix)
    elif kind == "add_json_key":
        return _fix_add_json_key(path, content, suggested_fix)

    return None


def _fix_add_import(
    path: Path, content: str, suggested_fix: dict[str, Any]
) -> dict[str, Any] | None:
    """Fix missing import by adding import statement."""
    module = suggested_fix.get("module", "pyatb")
    lines = content.splitlines()

    # Find the right place to insert the import
    # After existing imports or at the beginning
    insert_line = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            insert_line = i + 1
        elif (
            stripped
            and not stripped.startswith("#")
            and not stripped.startswith('"""')
            and not stripped.startswith("'''")
        ):
            break

    new_line = f"import {module}"
    return {
        "title": f"Add missing import: {module}",
        "kind": "quickfix",
        "diagnostic_code": "PYATB-E071",
        "confidence": 0.95,
        "safe_to_auto_apply": True,
        "edit": {
            "changes": [
                {
                    "range": {
                        "start": {"line": insert_line, "character": 0},
                        "end": {"line": insert_line, "character": 0},
                    },
                    "newText": f"{new_line}\n",
                }
            ]
        },
    }


def _fix_add_symbol_reference(
    path: Path, content: str, suggested_fix: dict[str, Any]
) -> dict[str, Any] | None:
    """Fix missing symbol reference by adding variable assignment."""
    symbol = suggested_fix.get("symbol", "HR.dat")
    lines = content.splitlines()

    # Find the right place to insert (after imports or at the beginning)
    insert_line = 0
    in_imports = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            insert_line = i + 1
            in_imports = True
        elif in_imports and not stripped:
            insert_line = i + 1
        elif in_imports and (
            stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''")
        ):
            continue
        elif in_imports and stripped:
            in_imports = False

    # Create variable name from symbol
    var_name = symbol.lower().replace(".", "_").replace("-", "_")
    if var_name == "hr_dat":
        var_name = "hr_file"
    elif var_name == "sr_dat":
        var_name = "sr_file"

    new_line = f'{var_name} = "{symbol}"'
    return {
        "title": f"Add missing symbol reference: {symbol}",
        "kind": "quickfix",
        "diagnostic_code": "PYATB-E072",
        "confidence": 0.88,
        "safe_to_auto_apply": False,
        "edit": {
            "changes": [
                {
                    "range": {
                        "start": {"line": insert_line, "character": 0},
                        "end": {"line": insert_line, "character": 0},
                    },
                    "newText": f"{new_line}\n",
                }
            ]
        },
    }


def _fix_add_structure_reference(
    path: Path, content: str, suggested_fix: dict[str, Any]
) -> dict[str, Any] | None:
    """Fix missing structure reference by adding TightBinding usage."""
    options = suggested_fix.get("options", ["hr_file = 'HR.dat'"])
    lines = content.splitlines()

    # Find the right place to insert (after imports)
    insert_line = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            insert_line = i + 1
        elif (
            stripped
            and not stripped.startswith("#")
            and not stripped.startswith('"""')
            and not stripped.startswith("'''")
        ):
            break

    new_line = options[0] if options else "hr_file = 'HR.dat'"
    new_line = options[0] if options else "hr_file = 'HR.dat'"
    return {
        "title": "Add missing structure reference",
        "kind": "quickfix",
        "diagnostic_code": "PYATB-E074",
        "confidence": 0.9,
        "safe_to_auto_apply": False,
        "edit": {
            "changes": [
                {
                    "range": {
                        "start": {"line": insert_line, "character": 0},
                        "end": {"line": insert_line, "character": 0},
                    },
                    "newText": f"{new_line}\n",
                }
            ]
        },
    }


def _fix_add_output_path(
    path: Path, content: str, suggested_fix: dict[str, Any]
) -> dict[str, Any] | None:
    """Fix missing output path by adding output_path variable."""
    example = suggested_fix.get("example", 'output_path = "results/"')
    lines = content.splitlines()

    # Find the right place to insert (after other variable assignments)
    insert_line = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            insert_line = i + 1
        elif stripped.startswith("import ") or stripped.startswith("from "):
            insert_line = i + 1

    return {
        "title": "Add missing output path",
        "kind": "quickfix",
        "diagnostic_code": "PYATB-W070",
        "confidence": 0.7,
        "safe_to_auto_apply": True,
        "edit": {
            "changes": [
                {
                    "range": {
                        "start": {"line": insert_line, "character": 0},
                        "end": {"line": insert_line, "character": 0},
                    },
                    "newText": f"{example}\n",
                }
            ]
        },
    }


def _fix_syntax(path: Path, content: str, suggested_fix: dict[str, Any]) -> dict[str, Any] | None:
    """Placeholder for syntax error fixes."""
    return {
        "title": "Fix syntax error (manual review required)",
        "kind": "quickfix",
        "diagnostic_code": "PYATB-E070",
        "confidence": 0.5,
        "safe_to_auto_apply": False,
        "edit": None,
        "reason": "Syntax errors require manual review to preserve intent",
    }


def _fix_json_syntax(
    path: Path, content: str, suggested_fix: dict[str, Any]
) -> dict[str, Any] | None:
    """Placeholder for JSON syntax fixes."""
    return {
        "title": "Fix JSON syntax error (manual review required)",
        "kind": "quickfix",
        "diagnostic_code": "PYATB-E073",
        "confidence": 0.5,
        "safe_to_auto_apply": False,
        "edit": None,
        "reason": "JSON syntax errors require manual review to preserve intent",
    }


def _fix_add_required_token(
    path: Path, content: str, suggested_fix: dict[str, Any]
) -> dict[str, Any] | None:
    """Fix missing required token by adding it."""
    token = suggested_fix.get("token", "")
    if not token:
        return None

    lines = content.splitlines()

    # Find the right place to insert
    insert_line = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            insert_line = i + 1

    return {
        "title": f"Add missing token: {token}",
        "kind": "quickfix",
        "diagnostic_code": "PYATB101",
        "confidence": 0.72,
        "safe_to_auto_apply": False,
        "edit": {
            "changes": [
                {
                    "range": {
                        "start": {"line": insert_line, "character": 0},
                        "end": {"line": insert_line, "character": 0},
                    },
                    "newText": f"{token}\n",
                }
            ]
        },
    }


def _fix_add_structure_block(
    path: Path, content: str, suggested_fix: dict[str, Any]
) -> dict[str, Any] | None:
    """Fix missing structure block by adding required tokens."""
    tokens = suggested_fix.get("tokens", [])
    if not tokens:
        return None

    lines = content.splitlines()

    # Find the right place to insert
    insert_line = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            insert_line = i + 1

    new_lines = [f"{token} = ..." for token in tokens]
    return {
        "title": "Add missing structure block",
        "kind": "quickfix",
        "diagnostic_code": "ABINIT010",
        "confidence": 0.7,
        "safe_to_auto_apply": False,
        "edit": {
            "changes": [
                {
                    "range": {
                        "start": {"line": insert_line, "character": 0},
                        "end": {"line": insert_line, "character": 0},
                    },
                    "newText": "\n".join(new_lines) + "\n",
                }
            ]
        },
    }


def _fix_move_command(
    path: Path, content: str, suggested_fix: dict[str, Any]
) -> dict[str, Any] | None:
    """Fix command ordering by moving command to first position."""
    command = suggested_fix.get("command", "")
    if not command:
        return None

    lines = content.splitlines()
    command_line = None
    command_index = None

    # Find the command line
    for i, line in enumerate(lines):
        if line.strip().startswith(command):
            command_line = line
            command_index = i
            break

    if command_line is None or command_index == 0:
        return None

    # Create edit to move command to first position
    return {
        "title": f"Move {command} to first position",
        "kind": "quickfix",
        "diagnostic_code": "GPUMD010",
        "confidence": 0.9,
        "safe_to_auto_apply": False,
        "edit": {
            "changes": [
                {
                    "range": {
                        "start": {"line": command_index, "character": 0},
                        "end": {"line": command_index, "character": len(command_line) + 1},
                    },
                    "newText": "",
                },
                {
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 0},
                    },
                    "newText": f"{command_line}\n",
                },
            ]
        },
    }


def _fix_add_json_key(
    path: Path, content: str, suggested_fix: dict[str, Any]
) -> dict[str, Any] | None:
    """Fix missing JSON key by adding it."""
    key = suggested_fix.get("key", "")
    if not key:
        return None

    # Find the last key-value pair in the JSON
    lines = content.splitlines()
    insert_line = len(lines) - 1

    for i, line in enumerate(lines):
        if line.strip().startswith("}"):
            insert_line = i
            break

    return {
        "title": f"Add missing JSON key: {key}",
        "kind": "quickfix",
        "diagnostic_code": "PYATB101",
        "confidence": 0.78,
        "safe_to_auto_apply": False,
        "edit": {
            "changes": [
                {
                    "range": {
                        "start": {"line": insert_line, "character": 0},
                        "end": {"line": insert_line, "character": 0},
                    },
                    "newText": f'    "{key}": "value",\n',
                }
            ]
        },
    }
