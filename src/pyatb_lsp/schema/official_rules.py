"""Offline PyATB rule/provenance index derived from official documentation."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_RULE_INDEX = Path(__file__).with_name("pyatb_rules.json")


@lru_cache(maxsize=1)
def load_rule_index() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(_RULE_INDEX.read_text(encoding="utf-8"))
    return data


def pipeline_steps() -> list[str]:
    return list(load_rule_index().get("pipeline", []))


def source_provenance() -> list[dict[str, Any]]:
    return list(load_rule_index().get("sourceProvenance", []))


def diagnostic_rules() -> dict[str, dict[str, Any]]:
    return dict(load_rule_index().get("diagnosticRules", {}))


def provenance_for_code(code: str) -> dict[str, Any] | None:
    rule = diagnostic_rules().get(code)
    if not rule:
        return None
    source_id = rule.get("source_id")
    if not source_id:
        return None
    for item in source_provenance():
        if item.get("id") == source_id:
            return {
                "source_id": source_id,
                "wiki_ref": rule.get("wiki_ref"),
                "manual_ref": item.get("url") or item.get("upstream_url"),
                "label": item.get("label"),
                "kind": item.get("kind"),
            }
    return {"source_id": source_id, "wiki_ref": rule.get("wiki_ref")}
