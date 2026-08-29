from pathlib import Path

from featuremap.path_extract import check_paths


def run_check(features_dir: Path, repo_root: Path, apps, as_json: bool = False):
    issues = check_paths(features_dir, repo_root, apps)
    payload = {
        "ok": True,
        "issue_count": len(issues),
        "issues": issues,
    }

    if as_json:
        return payload

    if not issues:
        print("No stale paths detected.")
        return payload

    for issue in issues:
        print(f"{issue['feature']}: missing {issue['path']}")
    return payload