from pathlib import Path

from feature_map.loader import all_slugs, list_map_files
from feature_map.validate import validate_map_file


def run_validate(features_dir: Path, strict: bool = False, as_json: bool = False):
    slugs = all_slugs(features_dir)
    all_errors = []
    all_warnings = []
    map_results = []

    for path in list_map_files(features_dir):
        errors, warnings = validate_map_file(path, slugs, strict=strict)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        map_results.append(
            {
                "file": path.name,
                "slug": path.stem,
                "errors": errors,
                "warnings": warnings,
                "ok": len(errors) == 0,
            }
        )

    result = {
        "ok": len(all_errors) == 0 and (len(all_warnings) == 0 if strict else True),
        "map_count": len(map_results),
        "error_count": len(all_errors),
        "warning_count": len(all_warnings),
        "maps": map_results,
        "errors": all_errors,
        "warnings": all_warnings,
    }

    if not as_json:
        if all_errors:
            for err in all_errors:
                print(f"ERROR: {err}")
        if all_warnings:
            for warn in all_warnings:
                print(f"WARNING: {warn}")
        if not all_errors and not all_warnings:
            print(f"Validated {len(map_results)} feature maps: all passed.")
        elif not all_errors:
            print(
                f"Validated {len(map_results)} feature maps: "
                f"{len(all_warnings)} warning(s), 0 error(s)."
            )

    exit_code = 0
    if all_errors:
        exit_code = 2 if strict else 1
    elif strict and all_warnings:
        exit_code = 2

    result["exit_code"] = exit_code
    return result, exit_code