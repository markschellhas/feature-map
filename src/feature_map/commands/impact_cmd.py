from pathlib import Path

import yaml

from feature_map.graph import build_graph
from feature_map.loader import list_map_files
from feature_map.yamlutil import read_text_bounded


def run_impact(
    features_dir: Path,
    file_fragment: str,
    transitive: bool = False,
    as_json: bool = False,
):
    fragment_lower = file_fragment.lower()
    direct = []

    for path in list_map_files(features_dir):
        try:
            text = read_text_bounded(path)
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            continue
        if fragment_lower in text.lower():
            direct.append(path.stem)

    affected = set(direct)
    if transitive:
        graph = build_graph(features_dir)
        reverse = {}
        for source, targets in graph.items():
            for target in targets:
                reverse.setdefault(target, []).append(source)

        stack = list(direct)
        while stack:
            node = stack.pop()
            for parent in reverse.get(node, []):
                if parent not in affected:
                    affected.add(parent)
                    stack.append(parent)

    results = sorted(affected)
    payload = {
        "ok": True,
        "file": file_fragment,
        "transitive": transitive,
        "count": len(results),
        "features": results,
    }

    if as_json:
        return payload

    if not results:
        print(f"No features reference '{file_fragment}'.")
        return payload

    for feature in results:
        print(feature)
    return payload