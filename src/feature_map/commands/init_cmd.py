from pathlib import Path

from feature_map.bootstrap import bootstrap_repo, ensure_features_dir
from feature_map.errors import CliError
from feature_map.harness import offer_authoring
from feature_map.loader import normalize_slug
from feature_map.paths import template_path


def run_init_map(features_dir: Path, name: str, force: bool = False, as_json: bool = False):
    slug = normalize_slug(name)
    if not slug:
        raise CliError(f'Invalid feature name "{name}".')

    features_dir.mkdir(parents=True, exist_ok=True)
    target = features_dir / f"{slug}.yaml"
    if target.exists() and not force:
        raise CliError(
            f"Feature map already exists: {target.name}",
            suggestion="Use --force to overwrite.",
        )

    tpl = template_path()
    if not tpl.is_file():
        raise CliError("Template not found in the feature-map package.")

    content = tpl.read_text(encoding="utf-8")
    content = content.replace("{{feature_name}}", slug)
    content = content.replace("{{FEATURE_TITLE}}", name.replace("_", " ").title())

    target.write_text(content, encoding="utf-8")
    payload = {"ok": True, "feature": slug, "path": str(target)}

    if as_json:
        return payload

    print(f"Created {target}")
    return payload


def run_bootstrap(
    repo_root: Path,
    *,
    upgrade_skill: bool = False,
    agents: bool = True,
    shim: bool = True,
    force: bool = False,
    as_json: bool = False,
    yes: bool = False,
    harness: str = None,
    skill_dirs=(),
):
    payload = bootstrap_repo(
        repo_root,
        upgrade_skill=upgrade_skill,
        agents=agents,
        shim=shim,
        force=force,
        skill_dirs=skill_dirs,
    )
    if as_json:
        return payload

    print("Initialized Feature Map in this repository:")
    print(f"  .features/: {payload['features_dir']}")
    print(f"  skill: {payload['skill']}")
    for mirror in payload.get("skill_mirrors") or []:
        print(f"  skill (mirror): {mirror}")
    print(f"  config: {payload['config']}")
    if payload.get("shim"):
        print(f"  shim: {payload['shim']}")
    if payload.get("agents"):
        print(f"  AGENTS.md: {payload['agents']}")

    offer_authoring(repo_root, payload["skill"], yes=yes, harness=harness)
    return payload


# Backward-compatible alias used by older call sites / tests
def run_init(features_dir: Path, name: str, force: bool = False, as_json: bool = False):
    return run_init_map(features_dir, name, force=force, as_json=as_json)
