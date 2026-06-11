"""PyATB Language Server Protocol implementation.

Exposes PyATB workflow analysis as LSP features:
diagnostics, formatting, completion, and hover documentation.
"""

from __future__ import annotations

import logging
from pathlib import Path

from lsprotocol.types import (
    TEXT_DOCUMENT_CODE_ACTION,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_FORMATTING,
    TEXT_DOCUMENT_HOVER,
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
    PublishDiagnosticsParams,
    Range,
    TextDocumentSyncKind,
)
from pygls.lsp.server import LanguageServer

from pyatb_lsp.analyzer import analyze_file, format_text

logger = logging.getLogger(__name__)

SERVER_NAME = "pyatb-lsp"
SERVER_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# Built-in keyword catalog for PyATB / materials-science workflow scripts
# ---------------------------------------------------------------------------
# These are keywords the LSP uses for completion and hover. The list covers
# common PyATB API members, typical variable names, and file references seen
# in MatMaster golden test cases.

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
}


def _ls_diagnostic_from_analyzer(diag: object, uri: str) -> Diagnostic:
    """Convert an analyzer Diagnostic (pyatb_lsp.diagnostics) to an LSP Diagnostic."""
    from pyatb_lsp.diagnostics import Diagnostic as AnalyzerDiag

    if not isinstance(diag, AnalyzerDiag):
        return Diagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=0)),
            message=str(diag),
            severity=DiagnosticSeverity.Error,
        )

    severity_map = {
        "error": DiagnosticSeverity.Error,
        "warning": DiagnosticSeverity.Warning,
        "info": DiagnosticSeverity.Information,
        "hint": DiagnosticSeverity.Hint,
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
    """
    # Write content to a temp file for analysis (analyze_file reads from disk).
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

    # Some analyzer diagnostics come from domain-wide checks that should also
    # apply here (e.g. missing HR.dat reference).
    all_diags = list(analyzer_diags)

    # Add custom checks for zero-length content
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
    """Format PyATB document text using the analyzer's formatter.

    Parameters
    ----------
    content
        The raw document text.

    Returns
    -------
    str
        Formatted text.
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
    """
    lower = prefix.lower()
    items: list[CompletionItem] = []
    for keyword in KEYWORD_CATALOG:
        if keyword.lower().startswith(lower):
            # Determine completion kind
            kind = CompletionItemKind.Keyword
            if keyword in ("pyatb", "TightBinding", "TB"):
                kind = CompletionItemKind.Class
            elif keyword in ("hr_file", "sr_file"):
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

    # Look up in the keyword catalog
    if word in KEYWORD_CATALOG:
        return f"**{word}**  \n{KEYWORD_CATALOG[word]}"

    # Provide limited hover for Python builtins / common patterns
    if word == "import":
        return "**import**  \nPython import statement."
    if word == "from":
        return "**from**  \nPython ``from ... import`` construct."

    return None


def create_server() -> PyATBServer:
    """Create and return a :class:`PyATBServer` instance.

    The server is pre-configured with the registered LSP features
    but is **not** started. Call ``start_io()`` or ``start_tcp()``
    to begin listening.
    """
    return PyATBServer()


# ---------------------------------------------------------------------------
# Server implementation
# ---------------------------------------------------------------------------


class PyATBServer(LanguageServer):  # type: ignore[misc]
    """Language Server for PyATB workflow scripts.

    Provides diagnostics, formatting, completion, hover, and code actions
    for Python scripts that use the ``pyatb`` tight-binding library.
    """

    def __init__(self) -> None:
        super().__init__(
            SERVER_NAME,
            SERVER_VERSION,
            text_document_sync_kind=TextDocumentSyncKind.Full,
        )

        # Register LSP features via the instance decorator.
        # Access unbound functions through the class dict to avoid
        # .__func__ access on bound methods, which mypy rejects.
        self.feature(TEXT_DOCUMENT_DID_OPEN)(PyATBServer.did_open)
        self.feature(TEXT_DOCUMENT_DID_CHANGE)(PyATBServer.did_change)
        self.feature(TEXT_DOCUMENT_COMPLETION)(PyATBServer.completion)
        self.feature(TEXT_DOCUMENT_HOVER)(PyATBServer.hover)
        self.feature(TEXT_DOCUMENT_FORMATTING)(PyATBServer.formatting)
        self.feature(TEXT_DOCUMENT_CODE_ACTION)(PyATBServer.code_action)

    # ---- diagnostics (pushed on open / change / save) ----

    def _do_diagnose(self, uri: str, content: str) -> None:
        """Compute and publish diagnostics for a document."""
        diagnostics = diagnose_document(uri, content)
        params = PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
        self.text_document_publish_diagnostics(params)

    def did_open(self, params: DidOpenTextDocumentParams) -> None:
        """Called when a document is opened in the editor."""
        self._do_diagnose(params.text_document.uri, params.text_document.text)

    def did_change(self, params: DidChangeTextDocumentParams) -> None:
        """Called when a document's content changes."""
        if params.content_changes:
            content = params.content_changes[-1].text
        else:
            content = ""
        self._do_diagnose(params.text_document.uri, content)

    def completion(self, params: CompletionParams) -> CompletionList:
        """Provide completion items based on the current line prefix."""
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
        """Return hover documentation for a symbol in the document."""
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
        """Format the document using the PyATB formatter."""
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

    def code_action(self, params: CodeActionParams) -> list[object]:
        """Provide code actions for PyATB diagnostics.

        Currently a placeholder; returns an empty list.
        """
        return []
