import re
from pathlib import Path
from typing import Iterable, List, Optional

import yaml

from featuremap.path_normalize import normalize_path_candidate
from featuremap.path_resolve import resolve_candidate_paths

__all__ = [
    "normalize_path_candidate",
    "resolve_candidate_paths",
    "extract_paths_from_map",
    "collect_corpus_strings",
    "check_paths",
]


def _extract_from_value(value) -> List[str]:
    paths: List[str] = []
    if isinstance(value, str):
        candidate = normalize_path_candidate(value)
        if candidate:
            paths.append(candidate)
    elif isinstance(value, list):
        for item in value:
            paths.extend(_extract_from_value(item))
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                key_path = normalize_path_candidate(key)
                if key_path:
                    paths.append(key_path)
            paths.extend(_extract_from_value(item))
    return paths


def extract_paths_from_map(data: dict) -> List[str]:
    paths: List[str] = []
    seen = set()

    def add(path: Optional[str]):
        if path and path not in seen:
            seen.add(path)
            paths.append(path)

    for section in ("entry_points", "core_components"):
        section_data = data.get(section)
        if section_data is None:
            continue
        if section == "core_components" and isinstance(section_data, dict):
            for val in section_data.values():
                for path in _extract_from_value(val):
                    add(path)
        else:
            for path in _extract_from_value(section_data):
                add(path)

    return paths


def _text_scan_section_strings(text: str, section: str) -> List[str]:
    """Extract list-ish string lines from a section when YAML parse fails."""
    strings: List[str] = []
    match = re.search(rf"^{re.escape(section)}:\s*\n", text, re.MULTILINE)
    if not match:
        return strings
    start = match.end()
    rest = text[start:]
    end_match = re.search(r"^\w[\w_]*:\s", rest, re.MULTILINE)
    block = rest[: end_match.start()] if end_match else rest
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            strings.append(stripped[2:].strip().strip('"').strip("'"))
    return strings


def collect_corpus_strings(features_dir: Path) -> List[tuple]:
    """Return (feature_slug, raw_string) pairs from entry_points + core_components."""
    corpus: List[tuple] = []
    for map_path in sorted(features_dir.glob("*.yaml")):
        text = map_path.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(text) or {}
            if isinstance(data, dict):
                for section in ("entry_points", "core_components"):
                    section_data = data.get(section)
                    if section_data is None:
                        continue
                    for raw in _flatten_strings(section_data):
                        corpus.append((map_path.stem, raw))
                continue
        except yaml.YAMLError:
            pass
        for section in ("entry_points", "core_components"):
            for raw in _text_scan_section_strings(text, section):
                corpus.append((map_path.stem, raw))
    return corpus


def _flatten_strings(value) -> List[str]:
    out: List[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, list):
        for item in value:
            out.extend(_flatten_strings(item))
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                out.append(key)
            out.extend(_flatten_strings(item))
    return out


def check_paths(features_dir: Path, repo_root: Path, apps: List[str]) -> List[dict]:
    issues = []
    for map_path in sorted(features_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(map_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        for clean_path in extract_paths_from_map(data):
            exists = any(
                candidate.exists()
                for candidate in resolve_candidate_paths(clean_path, repo_root, apps)
            )
            if not exists:
                issues.append(
                    {
                        "feature": map_path.stem,
                        "path": clean_path,
                        "status": "missing",
                    }
                )
    return issues