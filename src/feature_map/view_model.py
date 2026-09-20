"""JSON-serializable viewer snapshot. Not an on-disk schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from feature_map.errors import CliError
from feature_map.graph import format_mermaid, graph_data
from feature_map.loader import extract_related_slug, list_map_files, load_map
from feature_map.path_extract import check_paths

DISPLAY_KEYS = (
    "purpose",
    "user_flow",
    "entry_points",
    "apps",
    "related_features",
    "notes",
)
HEADING_KEYS = frozenset({"feature_name"})


def _stale_by_feature(issues: List[dict]) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {}
    for issue in issues:
        if issue.get("status") != "missing":
            continue
        feature = issue.get("feature")
        path = issue.get("path")
        if not feature or not path:
            continue
        grouped.setdefault(feature, []).append(path)
    return grouped


def _ordered_fields(data: dict) -> List[dict]:
    fields = []
    seen = set()
    for key in DISPLAY_KEYS:
        if key in data:
            fields.append({"key": key, "value": data[key]})
            seen.add(key)
    for key, value in data.items():
        if key in seen or key in HEADING_KEYS:
            continue
        fields.append({"key": key, "value": value})
    return fields


def _related_slugs(related) -> List[str]:
    slugs = []
    if not isinstance(related, list):
        return slugs
    for entry in related:
        target = extract_related_slug(entry)
        if target:
            slugs.append(target)
    return slugs


def _map_payload(slug: str, data: dict, stale_paths: List[str]) -> dict:
    extra = {
        key: value
        for key, value in data.items()
        if key not in DISPLAY_KEYS and key not in HEADING_KEYS
    }
    related = data.get("related_features") if isinstance(data.get("related_features"), list) else []
    entry_points = data.get("entry_points") if isinstance(data.get("entry_points"), list) else []
    return {
        "slug": slug,
        "feature_name": data.get("feature_name") or slug,
        "purpose": data.get("purpose") or "",
        "user_flow": data.get("user_flow"),
        "entry_points": entry_points,
        "apps": data.get("apps"),
        "related_features": related,
        "related_slugs": _related_slugs(related),
        "notes": data.get("notes"),
        "extra": extra,
        "fields": _ordered_fields(data),
        "stale_paths": list(stale_paths),
    }


def _load_or_stub(path: Path) -> dict:
    try:
        return load_map(path)
    except (CliError, OSError, UnicodeDecodeError):
        return {}


def build_view_snapshot(
    features_dir: Path,
    repo_root: Path,
    apps: Optional[List[str]] = None,
) -> dict:
    files = list_map_files(features_dir)
    slugs = [path.stem for path in files]
    issues = check_paths(features_dir, repo_root, apps or [])
    stale = _stale_by_feature(issues)
    maps: Dict[str, Any] = {}
    for path in files:
        data = _load_or_stub(path)
        maps[path.stem] = _map_payload(path.stem, data, stale.get(path.stem, []))
    graph = graph_data(features_dir)
    return {
        "slugs": slugs,
        "selected": slugs[0] if slugs else None,
        "maps": maps,
        "graph": {
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "mermaid": format_mermaid(graph),
        },
    }
