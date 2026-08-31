from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml

from feature_map.errors import CliError
from feature_map.yamlutil import read_text_bounded, read_yaml_file

# Init writes `{slug}.yaml` under `.features/`. Restrict to a single path
# segment so `feature-map init ../tmp/pwned` cannot write outside the repo.
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,62}$")


def normalize_slug(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def is_safe_slug(slug: str) -> bool:
    return bool(slug and SLUG_RE.fullmatch(slug))


def parse_slug(name: str) -> str:
    slug = normalize_slug(name)
    if not is_safe_slug(slug):
        raise CliError(
            f'Invalid feature name "{name}".',
            suggestion="Use a short slug like auth or user_settings (letters, numbers, underscores).",
        )
    return slug


def list_map_files(features_dir: Path):
    """Return `*.yaml` files that resolve inside *features_dir* (no symlink escape)."""
    try:
        base = features_dir.resolve()
    except (OSError, RuntimeError):
        return []
    files = []
    for path in sorted(features_dir.glob("*.yaml")):
        try:
            resolved = path.resolve()
            resolved.relative_to(base)
        except (ValueError, OSError, RuntimeError):
            continue
        if resolved.is_file():
            files.append(path)
    return files


def resolve_map_path(features_dir: Path, name: str) -> Path:
    """Look up a map by slug. Never joins *name* onto the filesystem."""
    slug = normalize_slug(name)
    for path in list_map_files(features_dir):
        if path.stem == slug or path.stem == name or path.name == name:
            return path
    raise CliError(
        f'Feature "{name}" not found.',
        suggestion='Run "feature-map list" to see available features.',
    )


def load_map(path: Path) -> dict:
    try:
        data = read_yaml_file(path)
    except (OSError, UnicodeDecodeError) as exc:
        raise CliError(f"Failed to read {path.name}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise CliError(f"Failed to parse {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise CliError(f"Feature map {path.name} must be a YAML mapping.")
    return data


def load_map_text(path: Path) -> str:
    try:
        return read_text_bounded(path)
    except (OSError, UnicodeDecodeError) as exc:
        raise CliError(f"Failed to read {path.name}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise CliError(str(exc)) from exc


def extract_related_slug(entry) -> Optional[str]:
    if not isinstance(entry, str):
        return None
    match = re.match(r'^["\']?([a-zA-Z0-9_-]+)', entry.strip())
    if not match:
        return None
    return normalize_slug(match.group(1))


def all_slugs(features_dir: Path) -> set[str]:
    return {path.stem for path in list_map_files(features_dir)}