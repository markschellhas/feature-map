from datetime import datetime
from pathlib import Path

from feature_map.loader import list_map_files
from feature_map.yamlutil import read_yaml_file


def run_list(features_dir: Path, as_json: bool = False):
    files = list_map_files(features_dir)
    slugs = [path.stem for path in files]

    if as_json:
        items = []
        for path in files:
            mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            apps_count = 0
            try:
                data = read_yaml_file(path) or {}
                apps = data.get("apps") if isinstance(data, dict) else None
                if isinstance(apps, list):
                    apps_count = len(apps)
                elif isinstance(apps, dict):
                    apps_count = len(apps)
            except Exception:
                pass
            items.append(
                {
                    "slug": path.stem,
                    "file": path.name,
                    "mtime": mtime,
                    "apps_count": apps_count,
                }
            )
        return {"ok": True, "count": len(items), "features": items}

    return {"features": slugs}