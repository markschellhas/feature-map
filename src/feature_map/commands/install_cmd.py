import os
import shutil
from pathlib import Path

from feature_map.bootstrap import SKILL_DIRS, SKILL_NAME
from feature_map.paths import guide_path
from feature_map.paths import skill_dir as bundled_skill_dir


def _deployed_skills(repo_root: Path):
    """Every known skill location in this repo, deployed or not."""
    found = []
    for harness, relative in SKILL_DIRS.items():
        path = repo_root / relative / SKILL_NAME
        found.append((harness, path, (path / "SKILL.md").is_file()))
    return found


def _detect_deployed_skill(repo_root: Path) -> Path:
    for _, path, ok in _deployed_skills(repo_root):
        if ok:
            return path
    return repo_root / SKILL_DIRS["agents"] / SKILL_NAME


def run_install(repo_root: Path, as_json: bool = False):
    shim = repo_root / "bin" / "feature-map"
    features_dir = repo_root / ".features"
    config_file = repo_root / ".feature-map.yaml"
    skill_path = _detect_deployed_skill(repo_root)
    on_path = shutil.which("feature-map")

    shim_ok = shim.is_file() and os.access(shim, os.X_OK)
    skill_ok = (skill_path / "SKILL.md").is_file()
    bundled_ok = (bundled_skill_dir() / "SKILL.md").is_file()
    features_ok = features_dir.is_dir()
    config_ok = config_file.is_file()
    guide = guide_path()

    payload = {
        "ok": bundled_ok and (shim_ok or bool(on_path)),
        "cli_on_path": {"command": "feature-map", "path": on_path, "exists": bool(on_path)},
        "shim": {"path": str(shim), "exists": shim.is_file(), "executable": shim_ok},
        "skill": {"path": str(skill_path), "exists": skill_ok},
        "skill_locations": [
            {"harness": harness, "path": str(path), "exists": ok}
            for harness, path, ok in _deployed_skills(repo_root)
        ],
        "bundled_skill": {"path": str(bundled_skill_dir()), "exists": bundled_ok},
        "guide": {"path": str(guide), "exists": guide.is_file()},
        "features_dir": {"path": str(features_dir), "exists": features_ok},
        "config": {"path": str(config_file), "exists": config_ok},
    }

    if as_json:
        return payload

    print("Feature Map install status:")
    print(f"  feature-map on PATH: {'ok' if on_path else 'missing'} ({on_path or 'not found'})")
    print(f"  shim: {'ok' if shim_ok else 'missing or not executable'} ({shim})")
    print(f"  skill: {'ok' if skill_ok else 'missing'} ({skill_path})")
    for harness, path, ok in _deployed_skills(repo_root):
        if ok and path != skill_path:
            print(f"  skill ({harness}): ok ({path})")
    print(f"  bundled skill: {'ok' if bundled_ok else 'missing'} ({bundled_skill_dir()})")
    print(f"  guide: {'ok' if guide.is_file() else 'missing'} ({guide})")
    print(f"  .features/: {'ok' if features_ok else 'missing'} ({features_dir})")
    print(f"  .feature-map.yaml: {'ok' if config_ok else 'missing'} ({config_file})")
    if not features_ok:
        print('Suggestion: run "feature-map init" to bootstrap this repository.')
    return payload
