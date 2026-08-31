from pathlib import Path
from typing import Dict, List

import yaml

from feature_map.loader import list_map_files
from feature_map.yamlutil import read_text_bounded, safe_load


def _flatten(value, prefix="") -> List[str]:
    lines = []
    if isinstance(value, dict):
        for key, item in value.items():
            lines.extend(_flatten(item, f"{prefix}{key}."))
    elif isinstance(value, list):
        for item in value:
            lines.extend(_flatten(item, prefix))
    elif value is not None:
        lines.append(f"{prefix}{value}")
    return lines


def build_text_index(features_dir: Path) -> Dict[str, str]:
    index = {}
    for path in list_map_files(features_dir):
        try:
            text = read_text_bounded(path)
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            continue
        index[path.stem] = text
        try:
            data = safe_load(text) or {}
            if isinstance(data, dict):
                index[path.stem] = "\n".join(_flatten(data))
        except yaml.YAMLError:
            pass
    return index


def search_maps(features_dir: Path, query: str) -> List[dict]:
    query_lower = query.lower()
    results = []
    for slug, text in build_text_index(features_dir).items():
        if query_lower not in text.lower():
            continue
        snippets = []
        for line in text.splitlines():
            if query_lower in line.lower():
                snippets.append(line.strip())
                if len(snippets) >= 3:
                    break
        results.append({"feature": slug, "snippets": snippets})
    return results