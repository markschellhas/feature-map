from __future__ import annotations

import json

from feature_map.errors import CliError
from feature_map.paths import view_template_path

PLACEHOLDER = "__VIEW_SNAPSHOT_JSON__"


def snapshot_json(snapshot: dict) -> str:
    payload = json.dumps(snapshot, default=str, ensure_ascii=True)
    return payload.replace("<", "\\u003c").replace(">", "\\u003e")


def render_view_html(snapshot: dict) -> str:
    path = view_template_path()
    if not path.is_file():
        raise CliError(
            "Viewer template not found in the feature-map package.",
            suggestion="Reinstall feature-map-cli so share/feature_map/view ships in the wheel.",
        )
    template = path.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise CliError("Viewer template is missing the snapshot placeholder.")
    return template.replace(PLACEHOLDER, snapshot_json(snapshot))
