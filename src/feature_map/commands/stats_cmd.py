import re
from collections import Counter
from pathlib import Path
from typing import Optional

import yaml

from feature_map.loader import all_slugs, extract_related_slug, list_map_files
from feature_map.validate import RECOMMENDED_KEYS, REQUIRED_KEYS
from feature_map.yamlutil import read_yaml_file


def normalize_app_name(app) -> Optional[str]:
    if not isinstance(app, str):
        return None
    app = app.strip()
    if not app or app.startswith("("):
        return None
    match = re.match(r'^["\']?([a-zA-Z0-9_-]+)', app)
    if match:
        return match.group(1)
    return None


def run_stats(features_dir: Path, as_json: bool = False):
    slugs = all_slugs(features_dir)
    apps_counter = Counter()
    missing_sections = 0
    broken_links = 0
    parse_failures = 0

    for path in list_map_files(features_dir):
        try:
            data = read_yaml_file(path) or {}
        except (yaml.YAMLError, OSError, UnicodeDecodeError):
            parse_failures += 1
            missing_sections += len(REQUIRED_KEYS) + len(RECOMMENDED_KEYS)
            continue

        if not isinstance(data, dict):
            continue

        for key in REQUIRED_KEYS + RECOMMENDED_KEYS:
            if key not in data or data[key] in (None, "", []):
                missing_sections += 1

        apps = data.get("apps")
        if isinstance(apps, list):
            for app in apps:
                name = normalize_app_name(app)
                if name:
                    apps_counter[name] += 1
        elif isinstance(apps, dict):
            for app in apps:
                name = normalize_app_name(app)
                if name:
                    apps_counter[name] += 1

        related = data.get("related_features") or []
        if isinstance(related, list):
            for entry in related:
                slug = extract_related_slug(entry)
                if slug and slug not in slugs:
                    broken_links += 1

    payload = {
        "ok": True,
        "map_count": len(list(list_map_files(features_dir))),
        "parse_failures": parse_failures,
        "missing_sections": missing_sections,
        "broken_related_features": broken_links,
        "maps_per_app": dict(sorted(apps_counter.items())),
    }

    if as_json:
        return payload

    print(f"Maps: {payload['map_count']}")
    print(f"Parse failures: {payload['parse_failures']}")
    print(f"Missing sections: {payload['missing_sections']}")
    print(f"Broken related_features: {payload['broken_related_features']}")
    if apps_counter:
        print("Maps per app:")
        for app, count in sorted(apps_counter.items()):
            print(f"  {app}: {count}")
    return payload