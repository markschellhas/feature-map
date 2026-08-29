"""Locate bundled schema, templates, and agent skill assets."""

from pathlib import Path


def package_dir() -> Path:
    return Path(__file__).resolve().parent


def source_share_dir() -> Path:
    """Repo-root share/featuremap when running from a source checkout."""
    return package_dir().parent.parent / "share" / "featuremap"


def assets_root() -> Path:
    bundled = package_dir() / "share"
    if (bundled / "schema").is_dir() or (bundled / "templates").is_dir():
        return bundled
    share = source_share_dir()
    if share.is_dir():
        return share
    return bundled


def schema_path() -> Path:
    return assets_root() / "schema" / "feature-map.schema.json"


def template_path() -> Path:
    return assets_root() / "templates" / "feature.yaml.tpl"


def skill_dir() -> Path:
    return assets_root() / "skill"
