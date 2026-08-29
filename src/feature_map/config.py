from pathlib import Path

import yaml

DEFAULT_APPS = []
DEFAULT_REQUIRED_SECTIONS = ["purpose", "entry_points"]
DEFAULT_FEATURES_DIR = ".features"


def load_config(repo_root: Path) -> dict:
    config_path = repo_root / ".feature-map.yaml"
    config = {
        "features_dir": DEFAULT_FEATURES_DIR,
        "apps": list(DEFAULT_APPS),
        "required_sections": list(DEFAULT_REQUIRED_SECTIONS),
    }
    if config_path.is_file():
        with config_path.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if isinstance(loaded, dict):
            config.update(loaded)
    if not isinstance(config.get("apps"), list):
        config["apps"] = list(DEFAULT_APPS)
    return config
