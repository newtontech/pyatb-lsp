"""PyATB Language Server Protocol implementation.

Exposes PyATB workflow analysis as LSP features:
diagnostics, formatting, completion, hover, and code actions.

Capabilities:
- Diagnostics (#13): Full diagnostic push on open/change
- Hover (#7): Keyword catalog hover + Python builtin hover
- Completion: PyATB keyword completion
- Formatting (#5): Safe idempotent formatter
- Code Actions (#21): Quick-fix actions for diagnostics

LLM Wiki: wiki/synthesis/openqc-agent-context.md
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from lsprotocol.types import (
    TEXT_DOCUMENT_CODE_ACTION,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_FORMATTING,
    TEXT_DOCUMENT_HOVER,
    CodeAction,
    CodeActionKind,
    CodeActionParams,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentFormattingParams,
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
    TextDocumentSyncKind,
    TextEdit,
    WorkspaceEdit,
)
from pygls.server import LanguageServer

from pyatb_lsp.analyzer import analyze_file, format_text

logger = logging.getLogger(__name__)

SERVER_NAME = "pyatb-lsp"
SERVER_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# Built-in keyword catalog for PyATB / materials-science workflow scripts
# ---------------------------------------------------------------------------

KEYWORD_CATALOG: dict[str, str] = {
    "import": "Python import statement",
    "pyatb": "PyATB tight-binding library for materials simulation",
    "hr_file": "Path to the Hamiltonian real-space (HR) file — e.g. 'HR.dat'",
    "sr_file": "Path to the overlap real-space (SR) file — e.g. 'SR.dat'",
    "HR.dat": "Default Hamiltonian real-space data file (tight-binding)",
    "SR.dat": "Default overlap real-space data file (tight-binding)",
    "TightBinding": "PyATB TightBinding class — construct with hr_file and sr_file",
    "tb": "Conventional variable name for a TightBinding instance",
    "TB": "Alias for TightBinding (shorthand)",
    "hr": "Hamiltonian real-space matrix",
    "sr": "Overlap real-space matrix",
    "hs": "Hamiltonian + overlap combined object",
    "kmesh": "Monkhorst-Pack k-point mesh specification",
    "kpath": "High-symmetry k-point path for band structure",
    "kpoints": "List or array of k-point coordinates",
    "band": "Band structure calculation",
    "dos": "Density of states calculation",
    "conductivity": "Optical / DC conductivity calculation",
    "spin": "Spin-polarised calculation flag or data",
    "SOC": "Spin-orbit coupling flag or strength",
    "soc": "Spin-orbit coupling flag or strength",
    "fermi": "Fermi level / Fermi energy",
    "EF": "Fermi energy",
    "efermi": "Fermi energy attribute",
    "run": "Execute the calculation",
    "kernel": "Run the main solver kernel",
    "converged": "Check whether the solver converged",
    "compute": "Generic compute call on a result object",
    "result": "Result container for computed quantities",
    "plot": "Plot or visualise the result",
    "eigvals": "Eigenvalues from the calculation",
    "eigvecs": "Eigenvectors from the calculation",
    "weight": "Weights associated with eigenvalues / k-points",
    # Additional MatMaster keywords (#8)
    "output": "Output directory or file path for calculation results",
    "out_file": "Output file path for writing results",
    "output_path": "Explicit output directory path",
    "result_dir": "Directory for storing calculation results",
}

# Hover documentation extensions for PyATB-specific symbols (#7)
HOVER_DOCS: dict[str, str] = {
    "TightBinding": (
        "**TightBinding**  \n"
        "PyATB core class for tight-binding calculations.  \n\n"
        "```python\n"
        "import pyatb\n"
        "tb = pyatb.TightBinding(hr_file='HR.dat', sr_file='SR.dat')\n"
        "```\n\n"
        "Requires `hr_file` (Hamiltonian) and optionally `sr_file` (overlap)."
    ),
    "hr_file": (
        "**hr_file**  \n"
        "Path to the Hamiltonian real-space file (HR.dat).  \n\n"
        "Required for all tight-binding calculations in PyATB."
    ),
    "sr_file": (
        "**sr_file**  \n"
        "Path to the overlap real-space file (SR.dat).  \n\n"
        "Optional but recommended for accurate tight-binding calculations."
    ),
    "kmesh": (
        "**kmesh**  \n"
        "Monkhorst-Pack k-point mesh specification.  \n\n"
        "Controls the Brillouin zone sampling density."
    ),
    "conductivity": (
        "**conductivity**  \n"
        "Optical or DC conductivity calculation module.  \n\n"
        "Computes transport properties from the electronic structure."
    ),
    "dos": (
        "**dos**  \n"
        "Density of states calculation module.  \n\n"
        "Computes the electronic density of states."
    ),
    "band": (
        "**band**  \n"
        "Band structure calculation module.  \n\n"
        "Computes energy eigenvalues along k-point paths."
    ),
}


def _ls_diagnostic_from_analyzer(diag: object, uri: str) -> Diagnostic:
    """Convert an analyzer Diagnostic (pyatb_lsp.diagnostics) to an LSP Diagnostic.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    from pyatb_lsp.diagnostics import Diagnostic as AnalyzerDiag

    if not isinstance(diag, AnalyzerDiag):
        return Diagnostic(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=0),
            ),
            message=str(diag),
            severity=DiagnosticSeverity.Error,
        )

    severity_map = {
        "error": DiagnosticSeverity.Error,
        "warning": DiagnosticSeverity.Warning,
        "info": DiagnosticSeverity.Information,
        "hint": DiagnosticSeverity.Hint,
        "information": DiagnosticSeverity.Information,
    }
    line = max(diag.line - 1, 0)
    col = max(diag.column - 1, 0)
    return Diagnostic(
        range=Range(
            start=Position(line=line, character=col),
            end=Position(line=line, character=col + 1),
        ),
        message=f"[{diag.code}] {diag.message}",
        severity=severity_map.get(diag.severity, DiagnosticSeverity.Information),
        code=diag.code,
        source=SERVER_NAME,
    )


# ---------------------------------------------------------------------------
# Standalone functions (testable without a server instance)
# ---------------------------------------------------------------------------


def diagnose_document(uri: str, content: str) -> list[Diagnostic]:
    """Analyse the content of a Python/PyATB document and return LSP diagnostics.

        Parameters
        ----------
        uri
            The document URI (used for file path extraction).
        content
            The full text content of the document.

        Returns
        -------
        list[Diagnostic]
            Zero or more LSP Diagnostic objects.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    import tempfile

    from pyatb_lsp.diagnostics import Diagnostic as AnalyzerDiag

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
    tmp.write(content)
    path = Path(tmp.name)
    tmp.close()

    try:
        analyzer_diags = analyze_file(path)
    finally:
        path.unlink(missing_ok=True)

    all_diags = list(analyzer_diags)

    if not content.strip():
        all_diags.append(
            AnalyzerDiag(
                code="PYATB003",
                severity="information",
                message="file is empty or contains only whitespace",
                file=uri,
                line=1,
            )
        )

    return [_ls_diagnostic_from_analyzer(d, uri) for d in all_diags]


def format_document(content: str) -> str:
    """Format PyATB document text using the analyzer's safe formatter.

        Parameters
        ----------
        content
            The raw document text.

        Returns
        -------
        str
            Formatted text (idempotent).

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    return format_text(content)


def complete_keywords(prefix: str) -> list[CompletionItem]:
    """Return completion items whose label starts with *prefix*.

        Parameters
        ----------
        prefix
            The user's current word prefix (case-insensitive).

        Returns
        -------
        list[CompletionItem]
            Completion items matching the prefix.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    lower = prefix.lower()
    items: list[CompletionItem] = []
    for keyword in KEYWORD_CATALOG:
        if keyword.lower().startswith(lower):
            kind = CompletionItemKind.Keyword
            if keyword in ("pyatb", "TightBinding", "TB"):
                kind = CompletionItemKind.Class
            elif keyword in (
                "hr_file",
                "sr_file",
                "output",
                "out_file",
                "output_path",
                "result_dir",
            ):
                kind = CompletionItemKind.Variable
            elif keyword in ("HR.dat", "SR.dat"):
                kind = CompletionItemKind.File
            items.append(
                CompletionItem(
                    label=keyword,
                    kind=kind,
                    detail=KEYWORD_CATALOG.get(keyword, ""),
                    documentation=KEYWORD_CATALOG.get(keyword, ""),
                )
            )
    return items


def hover_info(content: str, line: int, column: int) -> str | None:
    """Return hover documentation for the word at *line*, *column* in *content*.

        Parameters
        ----------
        content
            The full document text.
        line
            Zero-based line index.
        column
            Zero-based column index.

        Returns
        -------
        str or None
            Markdown hover text, or ``None`` if nothing relevant was found.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    lines = content.splitlines()
    if line >= len(lines):
        return None
    line_text = lines[line]
    if column >= len(line_text):
        return None

    # Extract the word at the cursor position
    start = column
    while start > 0 and (line_text[start - 1].isalnum() or line_text[start - 1] == "_"):
        start -= 1
    end = column
    while end < len(line_text) and (line_text[end].isalnum() or line_text[end] == "_"):
        end += 1
    if start == end:
        return None

    word = line_text[start:end]

    # Check extended hover docs first (#7)
    if word in HOVER_DOCS:
        return HOVER_DOCS[word]

    # Look up in the keyword catalog
    if word in KEYWORD_CATALOG:
        return f"**{word}**  \n{KEYWORD_CATALOG[word]}"

    # Provide limited hover for Python builtins / common patterns
    if word == "import":
        return "**import**  \nPython import statement."
    if word == "from":
        return "**from**  \nPython ``from ... import`` construct."

    return None


def get_code_actions(uri: str, content: str, diagnostics: list[Diagnostic]) -> list[CodeAction]:
    """Generate code actions for the given diagnostics (#21).

        Parameters
        ----------
        uri
            Document URI.
        content
            Full document text.
        diagnostics
            LSP diagnostics for which to generate actions.

        Returns
        -------
        list[CodeAction]
            Available quick-fix actions.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    actions: list[CodeAction] = []
    lines = content.splitlines()

    for diag in diagnostics:
        code = str(diag.code) if diag.code else ""

        # PYATB-E071: Add missing import
        if "E071" in code or code == "PYATB101":
            actions.append(
                CodeAction(
                    title="Add 'import pyatb'",
                    kind=CodeActionKind.QuickFix,
                    diagnostics=[diag],
                    edit=WorkspaceEdit(
                        changes={
                            uri: [
                                TextEdit(
                                    range=Range(
                                        start=Position(line=0, character=0),
                                        end=Position(line=0, character=0),
                                    ),
                                    new_text="import pyatb\n",
                                )
                            ]
                        }
                    ),
                )
            )

        # PYATB-E072 / PYATB-E074: Add missing symbol/structure reference
        if "E072" in code or "E074" in code or code == "PYATB102":
            # Determine which symbol is missing
            msg = diag.message or ""
            if "HR.dat" in msg or "hr_file" in msg or "structure" in msg:
                new_text = 'hr_file = "HR.dat"\n'
                title = 'Add hr_file = "HR.dat"'
            else:
                new_text = 'sr_file = "SR.dat"\n'
                title = 'Add sr_file = "SR.dat"'

            # Find insertion point (after imports or at top)
            insert_line = 0
            for i, ln in enumerate(lines):
                stripped = ln.strip()
                if stripped.startswith(("import ", "from ")):
                    insert_line = i + 1
                elif stripped.startswith("#") or not stripped:
                    continue
                else:
                    break

            actions.append(
                CodeAction(
                    title=title,
                    kind=CodeActionKind.QuickFix,
                    diagnostics=[diag],
                    edit=WorkspaceEdit(
                        changes={
                            uri: [
                                TextEdit(
                                    range=Range(
                                        start=Position(line=insert_line, character=0),
                                        end=Position(line=insert_line, character=0),
                                    ),
                                    new_text=new_text,
                                )
                            ]
                        }
                    ),
                )
            )

        # PYATB-W070: Add output path
        if "W070" in code:
            actions.append(
                CodeAction(
                    title='Add output_path = "results/"',
                    kind=CodeActionKind.QuickFix,
                    diagnostics=[diag],
                    edit=WorkspaceEdit(
                        changes={
                            uri: [
                                TextEdit(
                                    range=Range(
                                        start=Position(line=len(lines), character=0),
                                        end=Position(line=len(lines), character=0),
                                    ),
                                    new_text='\noutput_path = "results/"\n',
                                )
                            ]
                        }
                    ),
                )
            )

        # PYATB-E070: Fix syntax (generic guidance)
        if "E070" in code or code == "PYATB001":
            actions.append(
                CodeAction(
                    title="Show syntax error details",
                    kind=CodeActionKind.QuickFix,
                    diagnostics=[diag],
                )
            )

    return actions


def get_agent_json(uri: str, content: str) -> dict[str, Any]:
    """Build the agent-facing JSON payload for diagnostics (#11).

        Parameters
        ----------
        uri
            The document URI.
        content
            The full document text.

        Returns
        -------
        dict
            Agent JSON payload with diagnostics, metadata, and hover context.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    # Re-analyze to get analyzer diagnostics for rich serialization
    import tempfile

    from pyatb_lsp.rich_diagnostics import agent_check_payload

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
    tmp.write(content)
    path = Path(tmp.name)
    tmp.close()

    try:
        analyzer_diags = analyze_file(path)
    finally:
        path.unlink(missing_ok=True)

    payload = agent_check_payload(
        software="pyatb",
        uri=uri,
        operation="check",
        diagnostics=analyzer_diags,
        path=uri,
        file_type="py",
    )

    # Add capability metadata (#11)
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


def create_server() -> PyATBServer:
    """Create and return a :class:`PyATBServer` instance.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    return PyATBServer()


# ---------------------------------------------------------------------------
# Server implementation
# ---------------------------------------------------------------------------


class PyATBServer(LanguageServer):
    """Language Server for PyATB workflow scripts.

        Provides diagnostics, formatting, completion, hover, and code actions
        for Python scripts that use the ``pyatb`` tight-binding library.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    def __init__(self) -> None:
        super().__init__(
            SERVER_NAME,
            SERVER_VERSION,
            text_document_sync_kind=TextDocumentSyncKind.Full,
        )

        self.feature(TEXT_DOCUMENT_DID_OPEN)(PyATBServer.did_open)
        self.feature(TEXT_DOCUMENT_DID_CHANGE)(PyATBServer.did_change)
        self.feature(TEXT_DOCUMENT_COMPLETION)(PyATBServer.completion)
        self.feature(TEXT_DOCUMENT_HOVER)(PyATBServer.hover)
        self.feature(TEXT_DOCUMENT_FORMATTING)(PyATBServer.formatting)
        self.feature(TEXT_DOCUMENT_CODE_ACTION)(PyATBServer.code_action)

    # ---- diagnostics (pushed on open / change / save) ----

    def _do_diagnose(self, uri: str, content: str) -> None:
        """Compute and publish diagnostics for a document.

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        diagnostics = diagnose_document(uri, content)
        self.publish_diagnostics(uri, diagnostics)

    def did_open(self, params: DidOpenTextDocumentParams) -> None:
        """Called when a document is opened in the editor.

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        self._do_diagnose(params.text_document.uri, params.text_document.text)

    def did_change(self, params: DidChangeTextDocumentParams) -> None:
        """Called when a document's content changes.

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        if params.content_changes:
            content = params.content_changes[-1].text
        else:
            content = ""
        self._do_diagnose(params.text_document.uri, content)

    def completion(self, params: CompletionParams) -> CompletionList:
        """Provide completion items based on the current line prefix.

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        prefix = ""
        try:
            document = self.workspace.get_text_document(params.text_document.uri)
            line_text = document.lines[params.position.line]
            text_before = line_text[: params.position.character]
            col = len(text_before)
            while col > 0 and (text_before[col - 1].isalnum() or text_before[col - 1] == "_"):
                col -= 1
            prefix = text_before[col:]
        except Exception:
            prefix = ""

        items = complete_keywords(prefix)
        return CompletionList(is_incomplete=False, items=items)

    def hover(self, params: HoverParams) -> Hover | None:
        """Return hover documentation for a symbol in the document.

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        try:
            document = self.workspace.get_text_document(params.text_document.uri)
            line = params.position.line
            col = params.position.character
            content = document.source

            info = hover_info(content, line, col)
            if info is None:
                return None
            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=info,
                )
            )
        except Exception:
            return None

    def formatting(self, params: DocumentFormattingParams) -> list[dict[str, object]]:
        """Format the document using the PyATB safe formatter.

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        try:
            document = self.workspace.get_text_document(params.text_document.uri)
            content = document.source
        except Exception:
            return []

        formatted = format_document(content)

        lines = content.splitlines(keepends=True)
        last_line = len(lines) - 1
        last_char = len(lines[-1]) if lines else 0

        return [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": last_line, "character": last_char},
                },
                "newText": formatted,
            }
        ]

    def code_action(self, params: CodeActionParams) -> list[CodeAction]:
        """Provide code actions for PyATB diagnostics (#21).

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        try:
            document = self.workspace.get_text_document(params.text_document.uri)
            content = document.source
            uri = params.text_document.uri
        except Exception:
            return []

        return get_code_actions(uri, content, params.context.diagnostics)
