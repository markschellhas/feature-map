from pathlib import Path

import yaml

from feature_map.loader import load_map, load_map_text, resolve_map_path


def run_show(features_dir: Path, name: str, section=None, as_json: bool = False):
    path = resolve_map_path(features_dir, name)
    if as_json:
        data = load_map(path)
        if section:
            if section not in data:
                from feature_map.errors import CliError

                raise CliError(
                    f'Section "{section}" not found in {path.stem}.',
                    suggestion=f"Available keys: {', '.join(sorted(data.keys()))}",
                )
            return {"ok": True, "feature": path.stem, "section": section, "data": data[section]}
        return {"ok": True, "feature": path.stem, "data": data}

    if section:
        data = load_map(path)
        if section not in data:
            from feature_map.errors import CliError

            raise CliError(
                f'Section "{section}" not found in {path.stem}.',
                suggestion=f"Available keys: {', '.join(sorted(data.keys()))}",
            )
        return yaml.dump({section: data[section]}, sort_keys=False)

    return load_map_text(path)