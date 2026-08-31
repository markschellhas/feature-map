from pathlib import Path

import yaml

from feature_map.loader import list_map_files
from feature_map.yamlutil import read_text_bounded


def run_find(features_dir: Path, fragment: str, as_json: bool = False):
    results = []
    fragment_lower = fragment.lower()

    for path in list_map_files(features_dir):
        matches = []
        try:
            text = read_text_bounded(path)
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if fragment_lower in line.lower():
                matches.append({"line": line_no, "text": line.strip()})
        if matches:
            results.append({"feature": path.stem, "matches": matches})

    payload = {
        "ok": True,
        "fragment": fragment,
        "count": len(results),
        "results": results,
    }

    if as_json:
        return payload

    if not results:
        print(f"No features reference '{fragment}'.")
        return payload

    for item in results:
        print(item["feature"])
        for match in item["matches"][:5]:
            print(f"  L{match['line']}: {match['text']}")
    return payload