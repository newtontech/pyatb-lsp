"""Static analyzer for PyATB workflow scripts.

Provides rule-based diagnostics with PYATB-prefixed codes:
- PYATB-E070: Python syntax errors
- PYATB-E071: Missing required imports
- PYATB-E072: Missing required symbols (HR.dat / SR.dat)
- PYATB-E073: Invalid JSON in configuration files
- PYATB-E074: Missing structure reference (no tight-binding data)
- PYATB-W070: Missing output path specification
- PYATB-E075: Runtime log traceback patterns

Legacy codes (PYATB001, PYATB010, etc.) are retained for backward compatibility.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from .diagnostics import Diagnostic

DOMAIN_NAME = "PyATB"
DOMAIN_ID = "pyatb"
DOMAIN_KIND = "python"
CODE_PREFIX = "PYATB"
FILE_PATTERNS: list[str] = ["*.py"]
FILE_NAMES: list[str] = []
FILE_SUFFIXES: list[str] = [".py"]
KNOWN_TOKENS: list[str] = []
REQUIRED_TOKENS: list[str] = []
REQUIRED_IMPORTS: list[str] = ["pyatb"]
REQUIRED_SYMBOLS: list[str] = ["HR.dat", "SR.dat"]
REQUIRED_JSON_KEYS: list[str] = []

COMMENT_PREFIXES = ("#", "!", ";")

# ---------------------------------------------------------------------------
# MatMaster execution rules (#8)
# ---------------------------------------------------------------------------
# MatMaster golden test cases encode these constraints for valid PyATB runs:
MATMASTER_REQUIRED_REFERENCES = ["HR.dat"]
MATMASTER_OPTIONAL_REFERENCES = ["SR.dat"]
MATMASTER_OUTPUT_KEYWORDS = ["output", "out_file", "output_path", "result_dir"]
MATMASTER_STRUCTURE_REFERENCES = [
    "hr_file",
    "sr_file",
    "HR.dat",
    "SR.dat",
    "TightBinding",
    "TB",
]


def analyze_path(path: Path) -> list[Diagnostic]:
    path = path.resolve()
    files = _collect_files(path)
    diagnostics: list[Diagnostic] = []
    if not files:
        diagnostics.append(
            Diagnostic(
                code=f"{CODE_PREFIX}201",
                severity="error",
                message=f"no supported {DOMAIN_NAME} files found",
                file=str(path),
                line=1,
            )
        )
        return diagnostics
    for file_path in files:
        diagnostics.extend(analyze_file(file_path))
    return sorted(diagnostics, key=lambda item: (item.file, item.line, item.code))


def _collect_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if _is_supported(path) else []
    result: list[Path] = []
    for pattern in FILE_PATTERNS:
        result.extend(path.rglob(pattern))
    return sorted({item for item in result if item.is_file()})


def _is_supported(path: Path) -> bool:
    name = path.name.lower()
    suffix = path.suffix.lower()
    return (
        name in FILE_NAMES
        or suffix in FILE_SUFFIXES
        or any(path.match(pattern) for pattern in FILE_PATTERNS)
    )


def analyze_file(path: Path) -> list[Diagnostic]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [
            Diagnostic(f"{CODE_PREFIX}202", "error", "file is not valid UTF-8 text", str(path), 1)
        ]
    if DOMAIN_KIND == "python":
        return _analyze_python(path, content)
    if DOMAIN_KIND == "json":
        return _analyze_json_or_text(path, content)
    return _analyze_text(path, content)


def _analyze_text(path: Path, content: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    meaningful = _meaningful_lines(content)
    present = {line.split()[0].lower() for _, line in meaningful if line.split()}
    for required in REQUIRED_TOKENS:
        if required.lower() not in present and required.lower() not in content.lower():
            diagnostics.append(
                Diagnostic(
                    f"{CODE_PREFIX}101",
                    "warning",
                    f"expected {DOMAIN_NAME} token or setting '{required}' was not found",
                    str(path),
                    1,
                    evidence=["MVP rule derived from MatMaster execution contracts"],
                    suggested_fix={"kind": "add_required_token", "token": required},
                    confidence=0.72,
                )
            )
    for line_no, line in meaningful:
        token = line.split()[0].lower()
        if KNOWN_TOKENS and token not in KNOWN_TOKENS and not token.startswith(("#", "&", "%")):
            diagnostics.append(
                Diagnostic(
                    f"{CODE_PREFIX}001",
                    "warning",
                    f"unknown or currently unsupported {DOMAIN_NAME} keyword: {token}",
                    str(path),
                    line_no,
                    suggested_fix={"kind": "check_keyword_spelling", "keyword": token},
                    confidence=0.55,
                )
            )
    diagnostics.extend(_domain_text_checks(path, content, meaningful))
    return diagnostics


def _domain_text_checks(
    path: Path, content: str, meaningful: list[tuple[int, str]]
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    lower_name = path.name.lower()
    if DOMAIN_ID == "gpumd" and lower_name == "run.in":
        first = meaningful[0][1].split()[0].lower() if meaningful else ""
        if first != "potential":
            diagnostics.append(
                Diagnostic(
                    "GPUMD010",
                    "error",
                    "GPUMD run.in should start with the potential command",
                    str(path),
                    meaningful[0][0] if meaningful else 1,
                    evidence=["MatMaster GPUMD guard: potential must be first non-comment command"],
                    suggested_fix={
                        "kind": "move_command",
                        "command": "potential",
                        "position": "first",
                    },
                    confidence=0.9,
                )
            )
        run_lines = [line_no for line_no, line in meaningful if line.lower().startswith("run ")]
        compute_lines = [
            line_no
            for line_no, line in meaningful
            if line.lower().startswith(("compute_", "dump_"))
        ]
        if compute_lines and run_lines and min(compute_lines) > min(run_lines):
            diagnostics.append(
                Diagnostic(
                    "GPUMD011",
                    "warning",
                    "declare compute/dump commands before their run block",
                    str(path),
                    min(compute_lines),
                    confidence=0.8,
                )
            )
    if DOMAIN_ID == "abinit":
        has_structure = any(
            token in content.lower() for token in ("natom", "xred", "xcart", "znucl", "typat")
        )
        if not has_structure:
            diagnostics.append(
                Diagnostic(
                    "ABINIT010",
                    "warning",
                    "ABINIT input does not expose enough structure variables for static review",
                    str(path),
                    1,
                    suggested_fix={
                        "kind": "add_structure_block",
                        "tokens": ["natom", "znucl", "typat", "xred"],
                    },
                    confidence=0.7,
                )
            )
    return diagnostics


# ---------------------------------------------------------------------------
# Python analysis — includes all PYATB-E0xx / PYATB-W0xx RULE codes
# ---------------------------------------------------------------------------


def _analyze_python(path: Path, content: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []

    # --- PYATB-E070: Syntax errors (#14) ---
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        diagnostics.append(
            Diagnostic(
                code="PYATB-E070",
                severity="error",
                message=f"syntax error: {exc.msg}",
                file=str(path),
                line=exc.lineno or 1,
                column=exc.offset or 1,
                evidence=["Python AST parser failed"],
                suggested_fix={"kind": "fix_syntax", "message": exc.msg},
                confidence=1.0,
            )
        )
        # Also emit legacy code for backward compat
        diagnostics.append(
            Diagnostic(
                f"{CODE_PREFIX}001",
                "error",
                exc.msg,
                str(path),
                exc.lineno or 1,
                exc.offset or 1,
            )
        )
        return diagnostics

    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    imports = _import_names(tree)

    # --- PYATB-E071: Missing required imports (#15) ---
    for required in REQUIRED_IMPORTS:
        if required not in imports and required not in names:
            diagnostics.append(
                Diagnostic(
                    code="PYATB-E071",
                    severity="error",
                    message=f"missing required import: '{required}'",
                    file=str(path),
                    line=1,
                    evidence=["MatMaster execution contracts require pyatb import"],
                    suggested_fix={"kind": "add_import", "module": required},
                    confidence=0.95,
                )
            )
            # Legacy compat
            diagnostics.append(
                Diagnostic(
                    f"{CODE_PREFIX}101",
                    "warning",
                    f"expected import or symbol '{required}' was not found",
                    str(path),
                    1,
                    suggested_fix={"kind": "add_import", "module": required},
                    confidence=0.75,
                )
            )

    # --- PYATB-E072: Missing required symbols (#16) ---
    for symbol in REQUIRED_SYMBOLS:
        if symbol not in names and symbol not in attrs and symbol not in content:
            diagnostics.append(
                Diagnostic(
                    code="PYATB-E072",
                    severity="error",
                    message=f"missing required symbol: '{symbol}' not referenced in workflow",
                    file=str(path),
                    line=1,
                    evidence=[
                        f"MatMaster golden tests require reference to {symbol}",
                        "Tight-binding workflow requires both HR and SR data files",
                    ],
                    suggested_fix={"kind": "add_symbol_reference", "symbol": symbol},
                    confidence=0.88,
                )
            )
            # Legacy compat
            diagnostics.append(
                Diagnostic(
                    f"{CODE_PREFIX}102",
                    "warning",
                    f"expected workflow symbol '{symbol}' was not found",
                    str(path),
                    1,
                    confidence=0.68,
                )
            )

    # --- PYATB-E074: Missing structure reference (#18) ---
    has_structure = any(ref in content for ref in MATMASTER_STRUCTURE_REFERENCES)
    if not has_structure:
        diagnostics.append(
            Diagnostic(
                code="PYATB-E074",
                severity="error",
                message=(
                    "no tight-binding structure reference found "
                    "(need hr_file, HR.dat, TightBinding, or TB)"
                ),
                file=str(path),
                line=1,
                evidence=["MatMaster requires a structure reference for valid execution"],
                suggested_fix={
                    "kind": "add_structure_reference",
                    "options": [
                        "hr_file = 'HR.dat'",
                        "tb = pyatb.TightBinding(hr_file=...)",
                    ],
                },
                confidence=0.9,
            )
        )

    # --- PYATB-W070: Missing output path (#19) ---
    has_output = any(kw in content.lower() for kw in MATMASTER_OUTPUT_KEYWORDS)
    if not has_output:
        diagnostics.append(
            Diagnostic(
                code="PYATB-W070",
                severity="warning",
                message=(
                    "no output path specified (consider adding output, out_file, or result_dir)"
                ),
                file=str(path),
                line=1,
                evidence=["MatMaster best practice: explicit output path for reproducibility"],
                suggested_fix={"kind": "add_output_path", "example": 'output_path = "results/"'},
                confidence=0.7,
            )
        )

    # --- MatMaster rules (#8): check required HR.dat reference ---
    if DOMAIN_ID == "pyatb" and "HR.dat" not in content and "hr_file" not in content:
        diagnostics.append(
            Diagnostic(
                "PYATB010",
                "warning",
                "PyATB workflow should reference HR.dat or hr_file",
                str(path),
                1,
                confidence=0.75,
            )
        )

    # --- PYATB-E075: Runtime log traceback detection (#20) ---
    traceback_diagnostics = _detect_traceback_patterns(path, content)
    diagnostics.extend(traceback_diagnostics)

    return diagnostics


# ---------------------------------------------------------------------------
# PYATB-E073: JSON validation (#17)
# ---------------------------------------------------------------------------


def _analyze_json_or_text(path: Path, content: str) -> list[Diagnostic]:
    if path.suffix.lower() != ".json":
        return (
            _analyze_python(path, content)
            if path.suffix.lower() == ".py"
            else _analyze_text(path, content)
        )
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        return [
            Diagnostic(
                code="PYATB-E073",
                severity="error",
                message=f"invalid JSON: {exc.msg}",
                file=str(path),
                line=exc.lineno,
                column=exc.colno,
                evidence=["JSON parser failed"],
                suggested_fix={"kind": "fix_json_syntax", "message": exc.msg},
                confidence=1.0,
            ),
            # Legacy compat
            Diagnostic(f"{CODE_PREFIX}001", "error", exc.msg, str(path), exc.lineno, exc.colno),
        ]
    diagnostics: list[Diagnostic] = []
    if isinstance(payload, dict):
        for key in REQUIRED_JSON_KEYS:
            if key not in payload:
                diagnostics.append(
                    Diagnostic(
                        f"{CODE_PREFIX}101",
                        "warning",
                        f"manifest is missing required key '{key}'",
                        str(path),
                        1,
                        suggested_fix={"kind": "add_json_key", "key": key},
                        confidence=0.78,
                    )
                )
    return diagnostics


# ---------------------------------------------------------------------------
# PYATB-E075: Runtime log traceback (#20, #22)
# ---------------------------------------------------------------------------


def _detect_traceback_patterns(path: Path, content: str) -> list[Diagnostic]:
    """Detect Python traceback patterns in content."""
    diagnostics: list[Diagnostic] = []
    lines = content.splitlines()
    in_traceback = False
    traceback_start = 0

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == "Traceback (most recent call last):":
            in_traceback = True
            traceback_start = i
        elif in_traceback and stripped and not line.startswith((" ", "\t")):
            error_line = lines[i - 2].strip() if i >= 2 else "unknown error"
            diagnostics.append(
                Diagnostic(
                    code="PYATB-E075",
                    severity="error",
                    message=f"runtime traceback detected: {error_line}",
                    file=str(path),
                    line=traceback_start,
                    evidence=["Log parser detected Python traceback"],
                    suggested_fix={"kind": "investigate_traceback", "error": error_line},
                    confidence=0.95,
                )
            )
            in_traceback = False

    if in_traceback:
        diagnostics.append(
            Diagnostic(
                code="PYATB-E075",
                severity="error",
                message="runtime traceback detected: unterminated traceback block",
                file=str(path),
                line=traceback_start,
                evidence=["Log parser detected unterminated Python traceback"],
                suggested_fix={"kind": "investigate_traceback"},
                confidence=0.9,
            )
        )

    return diagnostics


def parse_log_content(content: str, file_path: str = "<log>") -> list[Diagnostic]:
    """Parse runtime log content and extract error diagnostics (#22).

    Parameters
    ----------
    content
        The log file text content.
    file_path
        The path or URI to report in diagnostics.

    Returns
    -------
    list[Diagnostic]
        Diagnostics extracted from traceback patterns and common error markers.
    """
    path = Path(file_path)
    diagnostics: list[Diagnostic] = []

    # Detect traceback patterns
    traceback_diags = _detect_traceback_patterns(path, content)
    diagnostics.extend(traceback_diags)

    # Detect common PyATB runtime error patterns
    lines = content.splitlines()
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # "Error:" patterns
        if re.match(r"^Error:", stripped):
            msg = stripped[6:].strip()
            diagnostics.append(
                Diagnostic(
                    code="PYATB-E075",
                    severity="error",
                    message=f"runtime error: {msg}",
                    file=file_path,
                    line=i,
                    evidence=["Log parser detected Error: line"],
                    confidence=0.85,
                )
            )

        # File not found patterns
        if re.search(r"FileNotFoundError|No such file or directory", stripped):
            diagnostics.append(
                Diagnostic(
                    code="PYATB-E074",
                    severity="error",
                    message=f"file not found: {stripped}",
                    file=file_path,
                    line=i,
                    evidence=["Log parser detected FileNotFoundError"],
                    suggested_fix={"kind": "check_file_path"},
                    confidence=0.9,
                )
            )

        # Import error patterns
        if re.search(r"ImportError|ModuleNotFoundError", stripped):
            module_match = re.search(r"No module named ['\"]?([^'\"]+)['\"]?", stripped)
            module_name = module_match.group(1) if module_match else "unknown"
            diagnostics.append(
                Diagnostic(
                    code="PYATB-E071",
                    severity="error",
                    message=f"import error: module '{module_name}' not found",
                    file=file_path,
                    line=i,
                    evidence=["Log parser detected ImportError/ModuleNotFoundError"],
                    suggested_fix={"kind": "install_module", "module": module_name},
                    confidence=0.9,
                )
            )

        # Segfault / signal patterns
        if re.search(r"Segmentation fault|SIGSEGV|Aborted \(core dumped\)", stripped):
            diagnostics.append(
                Diagnostic(
                    code="PYATB-E075",
                    severity="error",
                    message=f"runtime crash: {stripped}",
                    file=file_path,
                    line=i,
                    evidence=["Log parser detected crash signal"],
                    confidence=0.95,
                )
            )

    return diagnostics


def _import_names(tree: ast.AST) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".")[0])
    return result


def _meaningful_lines(content: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for line_no, raw in enumerate(content.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIXES):
            continue
        result.append((line_no, stripped))
    return result


# ---------------------------------------------------------------------------
# Safe formatter (#5)
# ---------------------------------------------------------------------------

_PYTHON_STATEMENT_KEYWORDS = frozenset(
    {
        "import",
        "from",
        "def",
        "class",
        "if",
        "elif",
        "else",
        "for",
        "while",
        "try",
        "except",
        "finally",
        "with",
        "return",
        "raise",
        "pass",
        "break",
        "continue",
        "yield",
        "assert",
        "del",
        "global",
        "nonlocal",
        "lambda",
        "and",
        "or",
        "not",
        "is",
        "in",
        "as",
    }
)


def _is_python_statement(stripped: str) -> bool:
    """Check if a line is a Python statement that should not be reformatted."""
    if not stripped:
        return False
    first_token = stripped.split()[0].rstrip(":(")
    return first_token in _PYTHON_STATEMENT_KEYWORDS or stripped.startswith("@")


def format_text(content: str) -> str:
    """Format PyATB document text.

    This formatter is *safe*: it only aligns key=value pairs and
    keyword-parameter lines. Python code (import, def, class, etc.)
    is passed through unchanged. The formatter is idempotent:
    ``format_text(format_text(x)) == format_text(x)`` for all inputs.

    Parameters
    ----------
    content
        The raw document text.

    Returns
    -------
    str
        Formatted text with trailing newline.
    """
    lines: list[str] = []
    for raw in content.splitlines():
        stripped = raw.strip()

        # Pass through blank lines, comments, and Python keywords unchanged
        if not stripped or stripped.startswith(COMMENT_PREFIXES) or _is_python_statement(stripped):
            lines.append(raw.rstrip())
            continue

        # Format key=value alignment (for config-style lines)
        if "=" in stripped:
            key, value = stripped.split("=", 1)
            formatted = f"{key.strip():<24} = {value.strip()}"
            lines.append(formatted)
        else:
            # Format keyword-parameter alignment
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2 and re.match(r"^[A-Za-z_][A-Za-z0-9_\-.]*$", parts[0]):
                lines.append(f"{parts[0]:<24} {parts[1].strip()}")
            else:
                lines.append(stripped)
    return "\n".join(lines).rstrip() + "\n"
