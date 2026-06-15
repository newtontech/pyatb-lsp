"""Universal generated-input preflight capabilities.

This module implements the four fleet-wide preflight capabilities called out in
``newtontech/pyatb-lsp#32`` against a *generic artifact-role model*, so the
checks generalize to any backend in the scientific LSP fleet instead of being
wired to MatMaster submission policy:

* ``version-aware-keywords``  - explicit runtime/version assumption metadata
  and pyatb-API keyword compatibility validation derived from the builtin
  schema, never guessed.
* ``cross-artifact-graph``   - resolves a PyATB case directory as a graph of
  artifacts with stable roles (primary-input, config, tb-hamiltonian,
  tb-overlap, tb-model, orbital). For PyATB the primary input is the Python
  workflow script that drives the ``pyatb`` library; the cross-file artifacts
  are the DFT-derived tight-binding data it consumes (``HR.dat``/``SR.dat``/
  ``tb_model*``), a JSON config file referenced from the script, and any
  numerical-orbital files. The same role set generalizes to the rest of the
  fleet because it never bakes in MatMaster/Bohrium runtime concepts.
* ``code-actions``           - normalizes repair hints/actions on every
  diagnostic and exposes a blocking gate the agent CLI can run as
  ``check --fail-on-blocking``.
* ``fleet-regression-fixtures`` - ``fleet_manifest`` returns a machine-readable
  description of the preflight surface (codes, capabilities, fixture
  expectations) so the parent ``bohrium_skills`` probe/report workflow can
  consume regression evidence without re-deriving it.

The diagnostics emitted here are plain dictionaries (not the legacy
``Diagnostic`` dataclass) so they can carry the richer ``DiagnosticEnvelope/v1``
fields (``source_provenance``, ``domain_tags``, ``facts``, ``artifact_roles``,
``version_assumption``, ``actions``) directly.

LLM Wiki: wiki/synthesis/openqc-agent-context.md
"""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --- Artifact-role model ---------------------------------------------------

# Generic roles. These are intentionally software-agnostic: every fleet backend
# can map its native files onto this same small role set, which is what lets the
# parent router consume cross-file checks without learning MatMaster specifics.
# For PyATB the primary-input role is the Python workflow script; the remaining
# roles are the DFT-derived data artifacts it references plus a config file.
ROLE_PRIMARY_INPUT = "primary-input"
ROLE_CONFIG = "config"
ROLE_TB_HAMILTONIAN = "tb-hamiltonian"
ROLE_TB_OVERLAP = "tb-overlap"
ROLE_TB_MODEL = "tb-model"
ROLE_ORBITAL = "orbital"

ALL_ROLES = (
    ROLE_PRIMARY_INPUT,
    ROLE_CONFIG,
    ROLE_TB_HAMILTONIAN,
    ROLE_TB_OVERLAP,
    ROLE_TB_MODEL,
    ROLE_ORBITAL,
)

# Conservative workflow thresholds used by the warning-level k-mesh check. The
# actual cutoff is overridable via the preflight intent contract; this is only
# the default fleet baseline, not a MatMaster policy.
DEFAULT_KPATH_DENSITY_WARNING = 0.01  # points per 1/A below this is suspicious

# Codes reserved for the universal preflight surface. They use the ``PYATB6xx``
# band so they sort after existing rule codes and stay identifiable as
# cross-fleet preflight findings.
CODE_MISSING_ARTIFACT = "PYATB601"
CODE_TB_HAMILTONIAN_MISSING = "PYATB602"
CODE_UNRESOLVED_ARTIFACT = "PYATB603"
CODE_CONFIG_PARSE = "PYATB604"
CODE_UNKNOWN_PYATB_KEYWORD = "PYATB605"
CODE_KPATH_TOO_COARSE = "PYATB606"
CODE_VERSION_ASSUMPTION = "PYATB607"
CODE_KEYWORD_VERSION_MISMATCH = "PYATB608"

# Recognized pyatb API surface (version-aware-keywords evidence). Keywords are
# the kwarg names accepted by the public ``pyatb`` classes/functions a generated
# input is expected to drive. This is the builtin schema the preflight validates
# against when the exact runtime version is unknown; it is intentionally a small
# conservative set so we do not over-report on valid modern inputs.
KNOWN_PYATB_KWARGS = frozenset(
    {
        # ABFuncParams / basis
        "hr_file",
        "sr_file",
        "r0",
        "lr",
        "dr",
        "rmax",
        "nr",
        # properties band structure
        "kpath",
        "kpoints",
        "nkpt",
        "kline_type",
        "kpath_filename",
        "fermi_energy",
        "fermi_energy_list",
        "emin",
        "emax",
        "delta_e",
        "Ecut",
        "omega",
        "eta",
        # boltzmann transport
        "temperature",
        "tmax",
        "dt",
        "mu_min",
        "mu_max",
        "mu_step",
        "boltz_kmesh",
        # optical / wboltz
        "eta_list",
        "omega_list",
        "domega",
        "omega_set",
        "wboltz_kmesh",
        # general
        "output",
        "out_file",
        "output_path",
        "result_dir",
        "calculation",
        "tf_type",
    }
)

# KWARGS that are mutually exclusive-or-required for the named pyatb entry
# points. Used by the version-aware-keywords check to surface incompatibilities.
CALCULATION_REQUIRES_KWARGS = {
    # boltzmann transport needs a chemical-potential window + kmesh
    "boltz_traj": {"mu_min", "mu_max", "mu_step", "boltz_kmesh"},
    "wboltz_traj": {"mu_min", "mu_max", "mu_step", "wboltz_kmesh"},
}

# Map common pyatb calculation names to the entry-point key above so the
# keyword-availability check can reason about which kwargs are required.
CALCULATION_TO_ENTRYPOINT = {
    "boltz_traj": "boltz_traj",
    "boltzmann": "boltz_traj",
    "boltzmann_transport": "boltz_traj",
    "wboltz_traj": "wboltz_traj",
    "wannier_boltzmann": "wboltz_traj",
    "wboltzmann": "wboltz_traj",
}


@dataclass(frozen=True)
class ArtifactNode:
    """A node in the cross-artifact graph.

        ``role`` is one of the fleet-generic roles above; ``path`` is the resolved
        filesystem path (may be a non-existent reference, which is itself a
        finding); ``source`` records where the reference originated so consumers
        can trace provenance.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    role: str
    path: Path
    exists: bool
    source: str
    referenced_from: tuple[str, int] | None = None
    detail: dict[str, Any] | None = None


@dataclass
class ArtifactGraph:
    """Generic cross-artifact graph built from a parsed case directory.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    case_dir: Path
    nodes: list[ArtifactNode] = field(default_factory=list)

    def by_role(self, role: str) -> list[ArtifactNode]:
        return [node for node in self.nodes if node.role == role]

    def to_json(self) -> list[dict[str, Any]]:
        """Serialize the graph for the parent probe/report workflow.

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """

        def _node_json(node: ArtifactNode) -> dict[str, Any]:
            payload: dict[str, Any] = {
                "role": node.role,
                "path": str(node.path),
                "exists": node.exists,
                "source": node.source,
            }
            if node.referenced_from is not None:
                payload["referenced_from"] = {
                    "path": node.referenced_from[0],
                    "line": node.referenced_from[1],
                }
            if node.detail:
                payload["detail"] = node.detail
            return payload

        return sorted(
            (_node_json(node) for node in self.nodes),
            key=lambda item: (item["role"], item["path"]),
        )


@dataclass(frozen=True)
class ParsedWorkflow:
    """Light view of a parsed PyATB workflow script.

        Captures only what the preflight needs: the primary input path, the set of
        ``pyatb`` keyword arguments found in the AST, their source line numbers,
        file-path string literals that reference cross-file artifacts, and any
        JSON config references (``json.load(open(...))`` patterns). This is kept
        intentionally narrower than the legacy analyzer's full diagnostic walk.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    path: Path
    has_pyatb_import: bool
    kwargs: dict[str, tuple[Any, int]]
    file_literals: list[tuple[str, int]]
    config_refs: list[tuple[str, int]]
    syntax_error: tuple[str, int, int] | None = None


def parse_workflow(path: Path) -> ParsedWorkflow:
    """Parse a PyATB workflow script into the narrow preflight view.

        The parser is defensive: any decode/AST failure is captured as a
        ``syntax_error`` rather than raised, so the preflight graph can still
        surface a missing-artifact finding for a malformed-but-present script.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ParsedWorkflow(
            path=path,
            has_pyatb_import=False,
            kwargs={},
            file_literals=[],
            config_refs=[],
            syntax_error=("file is not valid UTF-8 text", 1, 1),
        )
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        return ParsedWorkflow(
            path=path,
            has_pyatb_import=False,
            kwargs={},
            file_literals=[],
            config_refs=[],
            syntax_error=(exc.msg or "syntax error", exc.lineno or 1, exc.offset or 1),
        )

    has_pyatb_import = _imports_pyatb(tree)
    kwargs = _collect_kwargs(tree)
    file_literals = _collect_file_literals(tree)
    config_refs = _collect_config_refs(tree)
    return ParsedWorkflow(
        path=path,
        has_pyatb_import=has_pyatb_import,
        kwargs=kwargs,
        file_literals=file_literals,
        config_refs=config_refs,
    )


def _imports_pyatb(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "pyatb":
                    return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] == "pyatb":
                return True
    return False


def _collect_kwargs(tree: ast.AST) -> dict[str, tuple[Any, int]]:
    """Collect keyword-argument names seen on any call/class instantiation.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    out: dict[str, tuple[Any, int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg:
                    value = _literal_value(kw.value)
                    out.setdefault(kw.arg, (value, kw.lineno))
    return out


def _literal_value(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None


def _collect_file_literals(tree: ast.AST) -> list[tuple[str, int]]:
    """Collect string literals that look like data-file references.

        A literal is a candidate when its basename carries a known data extension
        (``.dat``, ``.HR``, ``.SR``, ``.orb``, ``tb_model`` prefix) or matches a
        recognized tight-binding filename. Pure module paths (containing ``/`` and
        a ``.py`` suffix) are excluded so import-like strings are not mistaken for
        data artifacts.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    data_suffixes = (".dat", ".hr", ".sr", ".orb", ".txt", ".xml")
    tb_prefixes = ("tb_model", "HR", "SR")
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        text = node.value.strip()
        if not text:
            continue
        name = Path(text).name
        lower = name.lower()
        if name.lower().endswith(".py") and "/" in text:
            continue
        is_suffix = any(lower.endswith(suf) for suf in data_suffixes)
        is_prefix = any(name.startswith(pre) for pre in tb_prefixes)
        if is_suffix or is_prefix:
            out.append((text, node.lineno))
    # Preserve discovery order while dropping duplicates.
    seen: set[str] = set()
    unique: list[tuple[str, int]] = []
    for text, line in out:
        if text in seen:
            continue
        seen.add(text)
        unique.append((text, line))
    return unique


def _collect_config_refs(tree: ast.AST) -> list[tuple[str, int]]:
    """Collect JSON config file references.

        PyATB generated inputs reach a JSON config in a few common shapes:
        ``open("foo.json")``, ``Path("foo.json")``, ``json.load(open("foo.json"))``,
        and ``pyatb.load_config("foo.json")``. Rather than special-case each, we
        treat any string-literal call argument ending in ``.json`` as a config
        reference and surface it so the cross-artifact graph can record a config
        role node. Module-path imports (``foo/bar.py``) are excluded above.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    out: list[tuple[str, int]] = []
    seen: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for arg in node.args:
            value = _literal_value(arg)
            if not isinstance(value, str):
                continue
            if not value.lower().endswith(".json"):
                continue
            if value in seen:
                continue
            seen.add(value)
            out.append((value, node.lineno))
    return out


def build_artifact_graph(case_dir: Path, workflow: ParsedWorkflow) -> ArtifactGraph:
    """Build the cross-artifact graph from a parsed PyATB case directory.

        The model is generic: it records roles + resolved paths + provenance. The
        same shape generalizes to other fleet backends because it never bakes in
        MatMaster/Bohrium runtime concepts (no input_dir, no image, no session).

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    case_dir = case_dir.resolve()
    graph = ArtifactGraph(case_dir=case_dir)

    graph.nodes.append(
        ArtifactNode(
            role=ROLE_PRIMARY_INPUT,
            path=workflow.path,
            exists=workflow.path.exists(),
            source="case-root",
            detail={"has_pyatb_import": workflow.has_pyatb_import},
        )
    )

    for config_ref, line in workflow.config_refs:
        resolved = _resolve_path(case_dir, config_ref)
        graph.nodes.append(
            ArtifactNode(
                role=ROLE_CONFIG,
                path=resolved,
                exists=resolved.exists(),
                source=f"workflow:json-ref:{config_ref}",
                referenced_from=(str(workflow.path), line),
            )
        )

    for filename, line in workflow.file_literals:
        role = _classify_data_role(filename)
        resolved = _resolve_path(case_dir, filename)
        graph.nodes.append(
            ArtifactNode(
                role=role,
                path=resolved,
                exists=resolved.exists(),
                source=f"workflow:data-literal:{filename}",
                referenced_from=(str(workflow.path), line),
                detail={"declared_name": filename},
            )
        )

    # If the script never references HR.dat / sr_file explicitly but imports
    # pyatb, record an absent hamiltonian node so the missing-artifact finding
    # has a graph node to attach to. This mirrors how the legacy analyzer
    # treats an absent HR reference.
    if not graph.by_role(ROLE_TB_HAMILTONIAN) and workflow.has_pyatb_import:
        default_hr = case_dir / "HR.dat"
        graph.nodes.append(
            ArtifactNode(
                role=ROLE_TB_HAMILTONIAN,
                path=default_hr,
                exists=default_hr.exists(),
                source="workflow:implicit-default",
                referenced_from=(str(workflow.path), 1),
                detail={"declared_name": "HR.dat", "implicit": True},
            )
        )

    return graph


def _classify_data_role(filename: str) -> str:
    """Map a referenced data filename to a fleet-generic artifact role.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    name = Path(filename).name
    lower = name.lower()
    if lower.startswith("tb_model") or "tb_model" in lower:
        return ROLE_TB_MODEL
    if name.upper().startswith("HR") or lower == "hr.dat" or "hamiltonian" in lower:
        return ROLE_TB_HAMILTONIAN
    if name.upper().startswith("SR") or lower == "sr.dat" or "overlap" in lower:
        return ROLE_TB_OVERLAP
    if lower.endswith(".orb") or "orbital" in lower:
        return ROLE_ORBITAL
    # Default TB data files (.dat) without a clearer signal are treated as
    # hamiltonian-role references because that is the required cross-file
    # artifact PyATB cannot run without.
    return ROLE_TB_HAMILTONIAN


def _resolve_path(case_dir: Path, declared: str) -> Path:
    candidate = Path(declared)
    if candidate.is_absolute():
        return candidate
    return case_dir / candidate


# --- Preflight diagnostics -------------------------------------------------


def preflight_diagnostics(
    case_dir: Path,
    *,
    workflow_path: Path | None = None,
    intent: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], ArtifactGraph]:
    """Run universal generated-input preflight checks.

        Returns a tuple of (diagnostics, artifact_graph). Diagnostics are envelope
        dicts carrying the full ``DiagnosticEnvelope/v1`` field set so the agent
        CLI can emit them directly without re-shaping.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    case_dir = case_dir.resolve()
    workflow_path = workflow_path or _locate_workflow(case_dir)
    version_assumption = resolve_version_assumption(intent)
    diagnostics: list[dict[str, Any]] = []

    if workflow_path is None:
        # No primary-input script in the workspace: a single blocking finding
        # so the parent probe has a stable handle. The graph stays empty.
        diagnostics.append(
            _diag(
                code=CODE_MISSING_ARTIFACT,
                severity="error",
                message=("no PyATB workflow script (primary-input role) found in case directory"),
                path=case_dir,
                line=1,
                category="cross-file reference",
                confidence=0.95,
                blocking=True,
                source_provenance={
                    "role": ROLE_PRIMARY_INPUT,
                    "reason": "no .py workflow with a pyatb import in case dir",
                },
                fix_hints=[
                    "Add a Python workflow script that imports pyatb",
                ],
                actions=[
                    {
                        "kind": "create_artifact",
                        "role": ROLE_PRIMARY_INPUT,
                        "target": str(case_dir / "workflow.py"),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"case_dir": str(case_dir)},
                artifact_roles=[ROLE_PRIMARY_INPUT],
                domain_tags=["cross-file", "blocking"],
                version_assumption=version_assumption,
            )
        )
        return diagnostics, ArtifactGraph(case_dir=case_dir)

    workflow = parse_workflow(workflow_path)
    graph = build_artifact_graph(case_dir, workflow)

    diagnostics.extend(_missing_artifact_diagnostics(graph, workflow))
    diagnostics.extend(_tb_hamiltonian_diagnostics(graph, workflow))
    diagnostics.extend(_unresolved_artifact_diagnostics(graph))
    diagnostics.extend(_config_parse_diagnostics(graph, workflow))
    diagnostics.extend(_unknown_pyatb_keyword_diagnostics(workflow, version_assumption))
    diagnostics.extend(_calculation_keyword_diagnostics(workflow, version_assumption))
    diagnostics.extend(_kpath_coarse_diagnostics(workflow, intent, version_assumption))
    diagnostics.extend(_version_assumption_diagnostic(version_assumption, intent))

    return (
        sorted(
            diagnostics,
            key=lambda item: (
                item.get("range", {}).get("start", {}).get("line", 0),
                item.get("range", {}).get("start", {}).get("character", 0),
                item["code"],
            ),
        ),
        graph,
    )


def _locate_workflow(case_dir: Path) -> Path | None:
    """Pick the primary-input workflow script for a case directory.

        Prefers ``workflow.py`` then any single ``.py`` file that imports pyatb;
        falls back to the first ``.py`` file when none imports pyatb so the
        missing-import finding still has a node to attach to. Returns ``None`` when
        the directory has no Python file at all.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    py_files = sorted(case_dir.glob("*.py"))
    if not py_files:
        return None
    for candidate in py_files:
        if candidate.name == "workflow.py":
            return candidate
    for candidate in py_files:
        parsed = parse_workflow(candidate)
        if parsed.has_pyatb_import:
            return candidate
    return py_files[0]


def _diag(
    *,
    code: str,
    severity: str,
    message: str,
    path: Path,
    line: int = 1,
    column: int = 1,
    category: str,
    confidence: float,
    blocking: bool,
    source_provenance: dict[str, Any],
    fix_hints: list[str],
    actions: list[dict[str, Any]] | None = None,
    facts: dict[str, Any] | None = None,
    artifact_roles: list[str] | None = None,
    domain_tags: list[str] | None = None,
    version_assumption: dict[str, Any] | None = None,
    manual_ref: str | None = None,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a single normalized preflight diagnostic.

        Carries every field the issue acceptance criteria require (``code``,
        ``severity``, ``path``/``range``, ``blocking``, ``category``,
        ``source_provenance``, ``fix_hints``/``actions``) plus the richer envelope
        fields (``facts``, ``artifact_roles``, ``domain_tags``,
        ``version_assumption``) used by the parent fleet probe.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    line0 = max(line - 1, 0)
    col0 = max(column - 1, 0)
    payload: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
        "file": str(path),
        "line": line,
        "column": column,
        "category": category,
        "confidence": confidence,
        "source": "pyatb-preflight",
        "range": {
            "start": {"line": line0, "character": col0},
            "end": {"line": line0, "character": col0 + 1},
        },
        "blocking": blocking,
        "fix_hints": fix_hints,
        "source_provenance": source_provenance,
    }
    if actions:
        payload["actions"] = actions
    if facts:
        payload["facts"] = facts
    if artifact_roles:
        payload["artifact_roles"] = artifact_roles
    if domain_tags:
        payload["domain_tags"] = domain_tags
    if version_assumption:
        payload["version_assumption"] = version_assumption
    if manual_ref:
        payload["manual_ref"] = manual_ref
    if intent:
        payload["intent"] = intent
    return payload


def _missing_artifact_diagnostics(
    graph: ArtifactGraph, workflow: ParsedWorkflow
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    # The config role is only blocking-missing when the script actually
    # referenced a JSON config (otherwise it is simply unused).
    for node in graph.by_role(ROLE_CONFIG):
        if not node.exists:
            ref = node.referenced_from or (str(workflow.path), 1)
            out.append(
                _diag(
                    code=CODE_MISSING_ARTIFACT,
                    severity="error",
                    message=(
                        f"{ROLE_CONFIG} artifact referenced from workflow is "
                        f"missing: {node.path.name}"
                    ),
                    path=node.path,
                    line=ref[1],
                    category="cross-file reference",
                    confidence=0.95,
                    blocking=True,
                    source_provenance={
                        "role": ROLE_CONFIG,
                        "referenced_from": {"path": ref[0], "line": ref[1]},
                        "declared_in": node.source,
                    },
                    fix_hints=[
                        f"Create {node.path.name} in the case directory",
                        "Or correct the JSON reference in the workflow",
                    ],
                    actions=[
                        {
                            "kind": "create_artifact",
                            "role": ROLE_CONFIG,
                            "target": str(node.path),
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={"missing_path": str(node.path)},
                    artifact_roles=[ROLE_CONFIG],
                    domain_tags=["cross-file", "blocking"],
                )
            )
    return out


def _tb_hamiltonian_diagnostics(
    graph: ArtifactGraph, workflow: ParsedWorkflow
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    hr_nodes = graph.by_role(ROLE_TB_HAMILTONIAN)
    # When the workflow does not import pyatb we cannot assert a hamiltonian
    # requirement (the legacy analyzer already reports the missing import).
    if not workflow.has_pyatb_import:
        return out
    missing = [node for node in hr_nodes if not node.exists]
    if missing:
        node = missing[0]
        ref = node.referenced_from or (str(workflow.path), 1)
        out.append(
            _diag(
                code=CODE_TB_HAMILTONIAN_MISSING,
                severity="error",
                message=(
                    "PyATB workflow requires a tight-binding Hamiltonian data "
                    f"file but {node.path.name} was not found"
                ),
                path=node.path,
                line=ref[1],
                category="cross-file reference",
                confidence=0.95,
                blocking=True,
                source_provenance={
                    "role": ROLE_TB_HAMILTONIAN,
                    "referenced_from": {"path": ref[0], "line": ref[1]},
                    "declared_in": node.source,
                    "implicit_default": bool((node.detail or {}).get("implicit")),
                },
                fix_hints=[
                    f"Provide {node.path.name} (tight-binding Hamiltonian) in the case dir",
                    "Or set hr_file=<path> in the workflow to point at the data",
                ],
                actions=[
                    {
                        "kind": "resolve_artifact",
                        "role": ROLE_TB_HAMILTONIAN,
                        "target": str(node.path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={
                    "missing_path": str(node.path),
                    "declared_name": (node.detail or {}).get("declared_name"),
                },
                artifact_roles=[ROLE_TB_HAMILTONIAN, ROLE_PRIMARY_INPUT],
                domain_tags=["cross-file", "blocking"],
            )
        )
    return out


def _unresolved_artifact_diagnostics(graph: ArtifactGraph) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    # TB overlap, tb_model, orbital are non-blocking when missing (they are
    # optional depending on the calculation) but still worth surfacing so the
    # parent probe knows the assumption.
    for role in (ROLE_TB_OVERLAP, ROLE_TB_MODEL, ROLE_ORBITAL):
        for node in graph.by_role(role):
            if node.exists:
                continue
            ref = node.referenced_from or (str(graph.case_dir), 1)
            out.append(
                _diag(
                    code=CODE_UNRESOLVED_ARTIFACT,
                    severity="warning",
                    message=(
                        f"{role} artifact referenced from workflow cannot be "
                        f"resolved: {node.path.name}"
                    ),
                    path=node.path,
                    line=ref[1],
                    category="cross-file reference",
                    confidence=0.8,
                    blocking=False,
                    source_provenance={
                        "role": role,
                        "declared_in": node.source,
                        "declared_name": (node.detail or {}).get("declared_name"),
                    },
                    fix_hints=[
                        f"Place {node.path.name} in the declared location",
                        "Or correct the path referenced in the workflow",
                    ],
                    actions=[
                        {
                            "kind": "resolve_artifact",
                            "role": role,
                            "target": str(node.path),
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={"unresolved_path": str(node.path)},
                    artifact_roles=[role],
                    domain_tags=["cross-file", "workspace-resolve"],
                )
            )
    return out


def _config_parse_diagnostics(
    graph: ArtifactGraph, workflow: ParsedWorkflow
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in graph.by_role(ROLE_CONFIG):
        if not node.exists:
            continue
        try:
            text = node.path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            ref = node.referenced_from or (str(workflow.path), 1)
            out.append(
                _diag(
                    code=CODE_CONFIG_PARSE,
                    severity="error",
                    message=f"config file {node.path.name} is not valid JSON: {exc.msg}",
                    path=node.path,
                    line=exc.lineno,
                    column=exc.colno,
                    category="syntax",
                    confidence=1.0,
                    blocking=True,
                    source_provenance={
                        "role": ROLE_CONFIG,
                        "referenced_from": {"path": ref[0], "line": ref[1]},
                        "parser": "json.loads",
                    },
                    fix_hints=[
                        f"Fix the JSON syntax in {node.path.name}",
                    ],
                    actions=[
                        {
                            "kind": "fix_json_syntax",
                            "target": str(node.path),
                            "message": exc.msg,
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={"message": exc.msg, "json_line": exc.lineno},
                    artifact_roles=[ROLE_CONFIG],
                    domain_tags=["syntax", "blocking"],
                )
            )
            continue
        if not isinstance(payload, dict):
            ref = node.referenced_from or (str(workflow.path), 1)
            out.append(
                _diag(
                    code=CODE_CONFIG_PARSE,
                    severity="error",
                    message=(
                        f"config file {node.path.name} must be a JSON object at the top level"
                    ),
                    path=node.path,
                    line=1,
                    category="schema",
                    confidence=0.95,
                    blocking=True,
                    source_provenance={
                        "role": ROLE_CONFIG,
                        "referenced_from": {"path": ref[0], "line": ref[1]},
                        "top_level_type": type(payload).__name__,
                    },
                    fix_hints=[
                        f"Wrap the {node.path.name} payload in a JSON object",
                    ],
                    actions=[
                        {
                            "kind": "wrap_json_object",
                            "target": str(node.path),
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={"top_level_type": type(payload).__name__},
                    artifact_roles=[ROLE_CONFIG],
                    domain_tags=["schema", "blocking"],
                )
            )
    return out


def _unknown_pyatb_keyword_diagnostics(
    workflow: ParsedWorkflow, version_assumption: dict[str, Any]
) -> list[dict[str, Any]]:
    """Flag keyword arguments that are not part of the builtin pyatb schema.

        This is the version-aware-keywords evidence: a kwarg outside the known set
        is either a typo or an API only present in a newer/older pyatb version,
        and we surface the exact schema we validated against so the parent probe
        can branch on the assumption.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    out: list[dict[str, Any]] = []
    if not workflow.has_pyatb_import:
        return out
    for keyword, (value, line) in workflow.kwargs.items():
        if keyword in KNOWN_PYATB_KWARGS:
            continue
        out.append(
            _diag(
                code=CODE_UNKNOWN_PYATB_KEYWORD,
                severity="warning",
                message=(f"workflow kwarg '{keyword}' is not in the builtin pyatb keyword schema"),
                path=workflow.path,
                line=line,
                category="schema",
                confidence=0.72,
                blocking=False,
                source_provenance={
                    "role": ROLE_PRIMARY_INPUT,
                    "keyword": keyword,
                    "schema_source": version_assumption["schema_source"],
                },
                fix_hints=[
                    f"Check the spelling of '{keyword}' against the pyatb API",
                    "Or declare software_version in the intent contract",
                ],
                actions=[
                    {
                        "kind": "review_keyword",
                        "keyword": keyword,
                        "target": str(workflow.path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"keyword": keyword, "value": value},
                artifact_roles=[ROLE_PRIMARY_INPUT],
                domain_tags=["schema", "version-aware"],
                version_assumption=version_assumption,
            )
        )
    return out


def _calculation_keyword_diagnostics(
    workflow: ParsedWorkflow, version_assumption: dict[str, Any]
) -> list[dict[str, Any]]:
    """Flag required-but-absent kwargs for a declared pyatb calculation type.

        When ``calculation`` is set to a transport entry point, the corresponding
        chemical-potential window + kmesh kwargs must be present. This is a real
        version/capability compatibility finding the parent probe can act on, and
        it is blocking because a missing kmesh would silently produce wrong
        results.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    out: list[dict[str, Any]] = []
    calc_entry = workflow.kwargs.get("calculation")
    if calc_entry is None:
        return out
    calc_value, calc_line = calc_entry
    if not isinstance(calc_value, str):
        return out
    entry_key = CALCULATION_TO_ENTRYPOINT.get(calc_value.strip().lower())
    if entry_key is None:
        return out
    required = CALCULATION_REQUIRES_KWARGS[entry_key]
    present = set(workflow.kwargs)
    missing = sorted(required - present)
    if not missing:
        return out
    out.append(
        _diag(
            code=CODE_KEYWORD_VERSION_MISMATCH,
            severity="error",
            message=(
                f"calculation='{calc_value}' requires kwargs that are missing: {', '.join(missing)}"
            ),
            path=workflow.path,
            line=calc_line,
            category="schema",
            confidence=0.92,
            blocking=True,
            source_provenance={
                "role": ROLE_PRIMARY_INPUT,
                "calculation": calc_value,
                "entry_point": entry_key,
                "schema_source": version_assumption["schema_source"],
            },
            fix_hints=[
                f"Add the required kwargs for calculation='{calc_value}': {', '.join(missing)}",
                "Or change calculation to a value that does not require them",
            ],
            actions=[
                {
                    "kind": "set_keyword",
                    "keyword": missing[0],
                    "target": str(workflow.path),
                    "safe_to_auto_apply": False,
                }
            ],
            facts={
                "calculation": calc_value,
                "entry_point": entry_key,
                "missing_kwargs": missing,
                "required_kwargs": sorted(required),
            },
            artifact_roles=[ROLE_PRIMARY_INPUT],
            domain_tags=["schema", "version-aware", "blocking"],
            version_assumption=version_assumption,
        )
    )
    return out


def _kpath_coarse_diagnostics(
    workflow: ParsedWorkflow,
    intent: dict[str, Any] | None,
    version_assumption: dict[str, Any],
) -> list[dict[str, Any]]:
    """Warn on suspiciously coarse k-path / kmesh declarations.

        PyATB transport/optical calculations depend on a dense k-sampling; a
        ``boltz_kmesh`` / ``wboltz_kmesh`` of 1 (Gamma-only) or an ``nkpt`` of 1
        is almost always a user mistake. This is a runtime-risk warning rather
        than a hard block.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    out: list[dict[str, Any]] = []
    if not workflow.has_pyatb_import:
        return out
    mesh_keywords = ("boltz_kmesh", "wboltz_kmesh", "nkpt")
    for keyword in mesh_keywords:
        entry = workflow.kwargs.get(keyword)
        if entry is None:
            continue
        value, line = entry
        grid = _coerce_mesh(value)
        if grid is None:
            continue
        if any(component <= 1 for component in grid):
            out.append(
                _diag(
                    code=CODE_KPATH_TOO_COARSE,
                    severity="warning",
                    message=(
                        f"{keyword}={list(grid)} contains a 1-point axis; "
                        "under-sampling risks silently inaccurate transport/optical results"
                    ),
                    path=workflow.path,
                    line=line,
                    category="preflight/runtime-risk",
                    confidence=0.78,
                    blocking=False,
                    source_provenance={
                        "role": ROLE_PRIMARY_INPUT,
                        "keyword": keyword,
                        "threshold_source": (
                            "intent" if "kpath_warning_density" in (intent or {}) else "default"
                        ),
                    },
                    fix_hints=[
                        f"Increase the sparse {keyword} axis",
                        "Or confirm the system is genuinely Gamma-only on purpose",
                    ],
                    actions=[
                        {
                            "kind": "review_keyword",
                            "keyword": keyword,
                            "target": str(workflow.path),
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={"keyword": keyword, "grid": list(grid)},
                    artifact_roles=[ROLE_PRIMARY_INPUT],
                    domain_tags=["preflight", "runtime-risk"],
                    version_assumption=version_assumption,
                )
            )
    return out


def _coerce_mesh(value: Any) -> tuple[int, ...] | None:
    """Coerce a kwarg value into an integer mesh tuple, if possible.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return (value,)
    if isinstance(value, float) and value.is_integer():
        return (int(value),)
    if isinstance(value, (list, tuple)):
        try:
            coerced = [int(component) for component in value]
        except (TypeError, ValueError):
            return None
        return tuple(coerced)
    if isinstance(value, str):
        # Accept "1 1 1" / "1x1x1" style declarations generated by templates.
        cleaned = re.sub(r"[x,\s]+", " ", value.strip())
        parts = cleaned.split()
        if not parts:
            return None
        try:
            return tuple(int(part) for part in parts)
        except ValueError:
            return None
    return None


# --- version-aware-keywords ------------------------------------------------


def resolve_version_assumption(intent: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve the explicit runtime/version assumption for this preflight run.

        When the exact runtime/image version is unknown we record that fact
        explicitly rather than guessing, per the issue's version-assumptions
        acceptance criterion. The intent contract can override ``software_version``
        (e.g. ``pyatb >=1.3.3``); otherwise we fall back to the schema version the
        builtin keyword set was authored against.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    intent = intent or {}
    software_version = intent.get("software_version")
    runtime_image = intent.get("runtime_image")
    assumption: dict[str, Any] = {
        "software": "pyatb",
        "software_version": software_version or "unknown",
        "runtime_image": runtime_image or "unknown",
        "schema_source": intent.get("schema_source", "pyatb-lsp builtin"),
        # The fallback is intentional and explicit so consumers never have to
        # guess whether ``unknown`` means "not checked" or "could not determine".
        "exact_runtime_known": bool(software_version or runtime_image),
    }
    if software_version or runtime_image:
        assumption["declared_by"] = "intent"
    else:
        assumption["declared_by"] = "fallback"
    return assumption


def _version_assumption_diagnostic(
    version_assumption: dict[str, Any], intent: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Emit an explicit information diagnostic when the runtime version is unknown.

        This makes the version assumption machine-readable in the diagnostic stream
        itself (not just metadata) so the parent probe can surface it without
        parsing the envelope top-level.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    if version_assumption["exact_runtime_known"]:
        return []
    return [
        _diag(
            code=CODE_VERSION_ASSUMPTION,
            severity="information",
            message=(
                "Exact pyatb runtime/image version is unknown; preflight "
                "validated against the builtin keyword schema"
            ),
            path=Path(version_assumption.get("schema_source", "pyatb-lsp builtin")),
            line=1,
            category="preflight/runtime-risk",
            confidence=1.0,
            blocking=False,
            source_provenance={
                "role": ROLE_PRIMARY_INPUT,
                "reason": "software_version and runtime_image not declared in intent",
            },
            fix_hints=[
                "Declare software_version/runtime_image in the intent contract",
            ],
            actions=[],
            facts={
                "software_version": version_assumption["software_version"],
                "runtime_image": version_assumption["runtime_image"],
                "schema_source": version_assumption["schema_source"],
            },
            artifact_roles=[ROLE_PRIMARY_INPUT],
            domain_tags=["version-aware", "assumption"],
            version_assumption=version_assumption,
            intent=dict(intent) if intent else None,
        )
    ]


# --- fleet-regression-fixtures --------------------------------------------


def fleet_manifest(
    *,
    fixtures: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a machine-readable preflight manifest for the parent fleet.

        The parent ``bohrium_skills`` probe/report workflow consumes this to know
        which preflight codes exist, which capabilities are implemented, and which
        fixtures exercise them. Keeping it as data (not README prose) means the
        fleet regression evidence stays in sync with the implementation.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    codes = {
        CODE_MISSING_ARTIFACT: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "primary-input or referenced config artifact missing",
        },
        CODE_TB_HAMILTONIAN_MISSING: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "pyatb workflow without a resolvable HR/tb hamiltonian artifact",
        },
        CODE_UNRESOLVED_ARTIFACT: {
            "severity": "warning",
            "category": "cross-file reference",
            "blocking": False,
            "capability": "cross-artifact-graph",
            "summary": "referenced tb-overlap/tb-model/orbital file cannot be resolved",
        },
        CODE_CONFIG_PARSE: {
            "severity": "error",
            "category": "syntax",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "referenced JSON config is not a valid JSON object",
        },
        CODE_UNKNOWN_PYATB_KEYWORD: {
            "severity": "warning",
            "category": "schema",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "workflow kwarg outside the builtin pyatb keyword schema",
        },
        CODE_KEYWORD_VERSION_MISMATCH: {
            "severity": "error",
            "category": "schema",
            "blocking": True,
            "capability": "version-aware-keywords",
            "summary": "calculation declares an entry point without its required kwargs",
        },
        CODE_KPATH_TOO_COARSE: {
            "severity": "warning",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "k-mesh/kpath declaration has a 1-point axis",
        },
        CODE_VERSION_ASSUMPTION: {
            "severity": "information",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "exact runtime version unknown; fallback schema used",
        },
    }
    capabilities = {
        "version-aware-keywords": {
            "status": "available",
            "evidence_codes": [
                CODE_UNKNOWN_PYATB_KEYWORD,
                CODE_KEYWORD_VERSION_MISMATCH,
                CODE_KPATH_TOO_COARSE,
                CODE_VERSION_ASSUMPTION,
            ],
        },
        "cross-artifact-graph": {
            "status": "available",
            "roles": list(ALL_ROLES),
            "evidence_codes": [
                CODE_MISSING_ARTIFACT,
                CODE_TB_HAMILTONIAN_MISSING,
                CODE_UNRESOLVED_ARTIFACT,
                CODE_CONFIG_PARSE,
            ],
        },
        "code-actions": {
            "status": "available",
            "blocking_gate": "pyatb-lsp-tool check --fail-on-blocking",
            "evidence_codes": list(codes.keys()),
        },
        "fleet-regression-fixtures": {
            "status": "available",
            "fixtures": list(fixtures) if fixtures else [],
        },
    }
    return {
        "software": "pyatb",
        "preflight_envelope": "DiagnosticEnvelope/v1",
        "artifact_roles": list(ALL_ROLES),
        "capabilities": capabilities,
        "codes": codes,
    }
