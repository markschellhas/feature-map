from datetime import datetime
from pathlib import Path

from featuremap.loader import list_map_files


def run_list(features_dir: Path, as_json: bool = False):
    files = list_map_files(features_dir)
    slugs = [path.stem for path in files]

    if as_json:
        items = []
        for path in files:
            mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            apps_count = 0
            try:
                import yaml as yaml_lib

                data = yaml_lib.safe_load(path.read_text(encoding="utf-8")) or {}
                apps = data.get("apps")
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