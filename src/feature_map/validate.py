import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

import yaml

from feature_map.loader import extract_related_slug, normalize_slug
from feature_map.paths import schema_path

REQUIRED_KEYS = ["feature_name", "purpose", "entry_points"]
RECOMMENDED_KEYS = ["apps", "user_flow", "related_features"]

_SCHEMA_CACHE = None


def load_schema() -> dict:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = json.loads(schema_path().read_text(encoding="utf-8"))
    return _SCHEMA_CACHE


def _matches_schema_type(value, types: List[str]) -> bool:
    if "string" in types and isinstance(value, str):
        return True
    if "array" in types and isinstance(value, list):
        return True
    if "object" in types and isinstance(value, dict):
        return True
    if "null" in types and value is None:
        return True
    return False


def validate_against_schema(data: dict) -> List[str]:
    schema = load_schema()
    errors: List[str] = []

    for key in schema.get("required", []):
        if key not in data or data[key] in (None, "", []):
            errors.append(f"missing required key '{key}' (schema)")

    properties = schema.get("properties", {})
    for key, spec in properties.items():
        if key not in data:
            continue
        value = data[key]
        expected = spec.get("type")
        if not expected:
            continue
        if isinstance(expected, str):
            expected = [expected]
        if not _matches_schema_type(value, expected):
            errors.append(f"'{key}' has invalid type per schema")
            continue
        if key == "entry_points" and isinstance(value, list):
            min_items = spec.get("minItems", 0)
            if len(value) < min_items:
                errors.append(f"'entry_points' must have at least {min_items} item(s) (schema)")
        if isinstance(value, str) and spec.get("minLength"):
            if len(value) < spec["minLength"]:
                errors.append(f"'{key}' is too short per schema")

    return errors


def _extract_field_from_text(text: str, key: str) -> Optional[str]:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip('"').strip("'")


def validate_map_file(
    path: Path,
    all_slugs: set,
    strict: bool = False,
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    text = path.read_text(encoding="utf-8")
    data = None

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        parse_error = str(exc)
        if strict:
            errors.append(f"{path.name}: YAML parse error: {parse_error}")
        else:
            warnings.append(
                f"{path.name}: YAML parse error (skipped structural checks): {parse_error}"
            )

    stem = path.stem
    if data is not None:
        if not isinstance(data, dict):
            errors.append(f"{path.name}: root must be a mapping")
            return errors, warnings

        schema_errors = validate_against_schema(data)
        for msg in schema_errors:
            full = f"{path.name}: {msg}"
            if strict:
                errors.append(full)
            else:
                warnings.append(full)

        feature_name = data.get("feature_name")
        if feature_name:
            normalized = normalize_slug(str(feature_name))
            if normalized != normalize_slug(stem):
                warnings.append(
                    f"{path.name}: feature_name '{feature_name}' "
                    f"does not match filename stem '{stem}'"
                )

        for key in RECOMMENDED_KEYS:
            if key not in data or data[key] in (None, "", []):
                warnings.append(f"{path.name}: missing recommended key '{key}'")

        related = data.get("related_features") or []
        if isinstance(related, list):
            for entry in related:
                slug = extract_related_slug(entry)
                if slug and slug not in all_slugs:
                    warnings.append(
                        f"{path.name}: related_features entry '{entry}' "
                        f"does not resolve to an existing map (slug: {slug})"
                    )
    else:
        schema = load_schema()
        for key in schema.get("required", REQUIRED_KEYS):
            if not _extract_field_from_text(text, key):
                msg = f"{path.name}: missing required key '{key}' (text scan)"
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)
        feature_name = _extract_field_from_text(text, "feature_name")
        if feature_name and normalize_slug(feature_name) != normalize_slug(stem):
            warnings.append(
                f"{path.name}: feature_name '{feature_name}' "
                f"does not match filename stem '{stem}' (text scan)"
            )

    return errors, warnings