from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml

from feature_map.errors import CliError


def normalize_slug(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def list_map_files(features_dir: Path):
    return sorted(features_dir.glob("*.yaml"))


def resolve_map_path(features_dir: Path, name: str) -> Path:
    slug = normalize_slug(name)
    exact = features_dir / f"{slug}.yaml"
    if exact.exists():
        return exact
    fallback = features_dir / f"{name}.yaml"
    if fallback.exists():
        return fallback
    for path in features_dir.glob("*.yaml"):
        if path.stem == slug or path.stem == name:
            return path
    raise CliError(
        f'Feature "{name}" not found.',
        suggestion='Run "feature-map list" to see available features.',
    )


def load_map(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise CliError(f"Failed to parse {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise CliError(f"Feature map {path.name} must be a YAML mapping.")
    return data


def load_map_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_related_slug(entry) -> Optional[str]:
    if not isinstance(entry, str):
        return None
    match = re.match(r'^["\']?([a-zA-Z0-9_-]+)', entry.strip())
    if not match:
        return None
    return normalize_slug(match.group(1))


def all_slugs(features_dir: Path) -> set[str]:
    return {path.stem for path in list_map_files(features_dir)}