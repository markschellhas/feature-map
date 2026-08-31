from pathlib import Path

import yaml

from feature_map.confine import is_repo_relative
from feature_map.errors import CliError
from feature_map.yamlutil import read_yaml_file

DEFAULT_APPS = []
DEFAULT_REQUIRED_SECTIONS = ["purpose", "entry_points"]
DEFAULT_FEATURES_DIR = ".features"
DEFAULT_SKILL_DIRS = []


def _require_repo_relative(value, field: str) -> str:
    if not is_repo_relative(value):
        raise CliError(
            ".feature-map.yaml {0} must be a relative path inside the repo.".format(field),
            suggestion='Use a repo-relative path like ".features" or ".agents/skills".',
        )
    return value.strip()


def load_config(repo_root: Path) -> dict:
    config_path = repo_root / ".feature-map.yaml"
    config = {
        "features_dir": DEFAULT_FEATURES_DIR,
        "apps": list(DEFAULT_APPS),
        "required_sections": list(DEFAULT_REQUIRED_SECTIONS),
        "skill_dirs": list(DEFAULT_SKILL_DIRS),
    }
    if config_path.is_file():
        try:
            loaded = read_yaml_file(config_path) or {}
        except yaml.YAMLError as exc:
            raise CliError(
                "Failed to parse .feature-map.yaml: {0}".format(exc),
                suggestion="Fix the YAML or delete the file and run feature-map init.",
            ) from exc
        except (OSError, UnicodeDecodeError) as exc:
            raise CliError("Failed to read .feature-map.yaml: {0}".format(exc)) from exc
        if isinstance(loaded, dict):
            config.update(loaded)
    if not isinstance(config.get("apps"), list):
        config["apps"] = list(DEFAULT_APPS)
    features_dir = config.get("features_dir", DEFAULT_FEATURES_DIR)
    if features_dir is None or features_dir == "":
        features_dir = DEFAULT_FEATURES_DIR
    config["features_dir"] = _require_repo_relative(features_dir, "features_dir")
    raw_skill_dirs = config.get("skill_dirs")
    if not isinstance(raw_skill_dirs, list):
        config["skill_dirs"] = list(DEFAULT_SKILL_DIRS)
    else:
        config["skill_dirs"] = [
            _require_repo_relative(entry, "skill_dirs") for entry in raw_skill_dirs
        ]
    return config
