#!/usr/bin/env python3
"""Refresh PyATB raw assets, wiki provenance, and source manifest snapshots.

Runtime code reads the checked-in rule index under
``src/pyatb_lsp/schema/pyatb_rules.json``. Network access is optional; the
offline mode validates the checked-in manifest without fetching upstream docs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RULE_INDEX = ROOT / "src" / "pyatb_lsp" / "schema" / "pyatb_rules.json"
CAPABILITIES = ROOT / "lsp-capabilities.json"
RAW_ASSETS = ROOT / "raw" / "assets"
WIKI_ROOT = ROOT / "wiki"


def load_rule_index() -> dict[str, Any]:
    return json.loads(RULE_INDEX.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def index_local_assets(fetched_at: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not RAW_ASSETS.exists():
        return entries
    for path in sorted(RAW_ASSETS.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        entries.append(
            {
                "id": rel.replace("/", "-").replace(".", "-"),
                "path": rel,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "retrieved_at": fetched_at,
                "kind": "local_mirror",
            }
        )
    return entries


def index_wiki_pages(fetched_at: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not WIKI_ROOT.exists():
        return entries
    for path in sorted(WIKI_ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        entries.append(
            {
                "id": rel.replace("/", "-").replace(".", "-"),
                "path": rel,
                "sha256": sha256_file(path),
                "retrieved_at": fetched_at,
                "kind": "wiki_page",
            }
        )
    return entries


def fetch_url(url: str, timeout: int) -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": "pyatb-lsp-provenance/0.1"})
    with urlopen(req, timeout=timeout) as response:
        body = response.read()
        return {
            "url": url,
            "final_url": response.geturl(),
            "status": response.status,
            "content_type": response.headers.get("content-type", ""),
            "sha256": hashlib.sha256(body).hexdigest(),
            "size_bytes": len(body),
        }


def write_capabilities_provenance(fetched_at: str) -> None:
    rules = load_rule_index()
    capabilities = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
    capabilities["sourceProvenance"] = rules.get("sourceProvenance", [])
    capabilities["pipeline"] = rules.get("pipeline", [])
    capabilities["ruleIndex"] = str(RULE_INDEX.relative_to(ROOT))
    capabilities["provenanceUpdatedAt"] = fetched_at
    CAPABILITIES.write_text(
        json.dumps(capabilities, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def validate_offline() -> None:
    rules = load_rule_index()
    provenance_path = RAW_ASSETS / "source-provenance.json"
    if not provenance_path.exists():
        raise SystemExit("missing raw/assets/source-provenance.json")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    source_ids = {item["id"] for item in rules.get("sourceProvenance", [])}
    manifest_ids = {item["id"] for item in provenance.get("sources", []) if item.get("id")}
    if not source_ids <= manifest_ids:
        missing = sorted(source_ids - manifest_ids)
        raise SystemExit(f"provenance manifest missing source ids: {missing}")
    for rule in rules.get("diagnosticRules", {}).values():
        source_id = rule.get("source_id")
        if source_id and source_id not in source_ids:
            raise SystemExit(f"diagnostic rule references unknown source_id: {source_id}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--offline", action="store_true", help="Validate checked-in artifacts only.")
    parser.add_argument(
        "--fetch-official",
        action="store_true",
        help="Fetch official doc landing page checksums (optional network).",
    )
    args = parser.parse_args(argv)

    if args.offline:
        validate_offline()
        return 0

    RAW_ASSETS.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rules = load_rule_index()
    local_assets = index_local_assets(fetched_at)
    wiki_pages = index_wiki_pages(fetched_at)

    fetched_remote: list[dict[str, Any]] = []
    if args.fetch_official:
        for source in rules.get("sourceProvenance", []):
            url = source.get("url") or source.get("upstream_url")
            if not url:
                continue
            try:
                payload = fetch_url(url, args.timeout)
            except OSError as exc:
                payload = {"url": url, "error": str(exc)}
            fetched_remote.append({"id": source["id"], **payload})

    snapshot = {
        "schema": "PyatbOfficialDocsSnapshot/v1",
        "fetched_at": fetched_at,
        "pipeline": rules.get("pipeline", []),
        "local_assets": local_assets,
        "wiki_pages": wiki_pages,
        "remote_snapshots": fetched_remote,
    }
    (RAW_ASSETS / "pyatb-official-docs.json").write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    provenance_sources: list[dict[str, Any]] = []
    for source in rules.get("sourceProvenance", []):
        entry = dict(source)
        entry["retrieved_at"] = fetched_at
        local_path = source.get("path")
        if local_path:
            path = ROOT / local_path
            if path.exists():
                entry["sha256"] = sha256_file(path)
                entry["size_bytes"] = path.stat().st_size
        remote = next((item for item in fetched_remote if item.get("id") == source.get("id")), None)
        if remote and remote.get("sha256"):
            entry["remote_sha256"] = remote["sha256"]
            entry["final_url"] = remote.get("final_url", remote.get("url"))
        provenance_sources.append(entry)

    provenance = {
        "schema": "SourceProvenance/v1",
        "fetched_at": fetched_at,
        "rule_index": str(RULE_INDEX.relative_to(ROOT)),
        "sources": provenance_sources,
        "local_asset_count": len(local_assets),
        "wiki_page_count": len(wiki_pages),
    }
    (RAW_ASSETS / "source-provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_capabilities_provenance(fetched_at)
    print(
        json.dumps(
            {
                "ok": True,
                "local_assets": len(local_assets),
                "wiki_pages": len(wiki_pages),
                "remote_snapshots": len(fetched_remote),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
