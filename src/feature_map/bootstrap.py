"""Phase 2 repo bootstrap: deploy skill, config, AGENTS.md, and optional shim."""

from __future__ import annotations

import shutil
from pathlib import Path

from feature_map.paths import skill_dir as bundled_skill_dir

AGENTS_MARKER = "<!-- feature-map:start -->"
AGENTS_END = "<!-- feature-map:end -->"
LEGACY_AGENTS_MARKERS = (
    ("<!-- featuremap:start -->", "<!-- featuremap:end -->"),
)

SKILL_NAME = "feature-map"

# Repo-relative skill directories, keyed by the harness that reads them. This
# table is a lookup, not a ranking: the primary deploy target is still chosen by
# detect_skill_parent(). Every other entry is mirrored only when that harness is
# already in use in this repo (its config directory exists), so no single agent
# is privileged. Add a harness by adding a row; add an unlisted one per-repo via
# `skill_dirs` in .feature-map.yaml or `--skill-dir`.
SKILL_DIRS = {
    "agents": ".agents/skills",
    "claude": ".claude/skills",
    "grok": ".grok/skills",
}

SHIM_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ -x "$ROOT/.venv/bin/feature-map" ]; then
  exec "$ROOT/.venv/bin/feature-map" "$@"
fi

# Global install, but not this shim (bin/ may be on PATH).
if command -v feature-map >/dev/null 2>&1; then
  CAND="$(command -v feature-map)"
  CAND_ABS="$(cd "$(dirname "$CAND")" && pwd)/$(basename "$CAND")"
  if [ "$CAND_ABS" != "$SELF" ]; then
    exec "$CAND" "$@"
  fi
fi

if python3 -c "import feature_map" >/dev/null 2>&1; then
  exec python3 -m feature_map "$@"
fi

echo "feature-map is not installed. Try: pip install feature-map-cli  (or: npm install -g feature-map-cli)" >&2
exit 1
"""

DEFAULT_CONFIG = """# Feature Map CLI configuration
features_dir: .features
apps: []
required_sections:
  - purpose
  - entry_points
min_cli_version: "1.0.0"
# Extra directories to mirror the agent skill into, for harnesses this CLI does
# not know about. Repo-relative; each gets a <dir>/feature-map/ copy on init.
# skill_dirs:
#   - .my-agent/skills
"""


def _display_path(repo_root: Path, path: Path) -> str:
    """Repo-relative when possible, so AGENTS.md stays portable."""
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def agents_block(repo_root: Path = None, skill_paths=()) -> str:
    """The AGENTS.md block, naming the deployed skill by path when known."""
    lines = []
    for path in skill_paths:
        path = Path(path)
        rel = _display_path(repo_root, path) if repo_root else path.as_posix()
        lines.append(f"`{rel}/SKILL.md`")

    if lines:
        location = "Skill: " + ", ".join(lines) + "\n"
    else:
        location = f"Skill: `.agents/skills/{SKILL_NAME}/SKILL.md`\n"

    return f"""{AGENTS_MARKER}
## Feature Map

**ALWAYS** use Feature Map before feature work, debugging, PRDs, or plans.
Do not implement from a cold grep when a map exists.

```bash
./bin/feature-map list
./bin/feature-map search <keyword>
./bin/feature-map find <path-fragment>
./bin/feature-map <feature-name>
```

Maps in `.features/*.yaml` are the authoritative cross-app architecture source.
Keep them dense: fields, not essays.

If `list` is empty or search/find miss the area you are about to change,
**scour the existing code and author maps first**. Cluster by user-visible
capability, not by file. Prefer `entry_points` that exist on disk, then
run `feature-map validate` and `feature-map check`.

{location}Read it before authoring: `references/existing-repos.md` (playbook),
`references/authoring.md` (fields), `references/example-map.md` (worked example).
{AGENTS_END}
"""


# Backward-compatible constant for callers that imported the static block.
AGENTS_BLOCK = agents_block()


def detect_skill_parent(repo_root: Path) -> Path:
    agents = repo_root / SKILL_DIRS["agents"]
    grok = repo_root / SKILL_DIRS["grok"]
    if grok.exists() and not agents.exists():
        return grok
    return agents


def detect_mirror_parents(repo_root: Path, primary: Path, extra_dirs=()) -> list:
    """Skill directories to mirror into, besides the primary one.

    A known harness is mirrored only when it is already used in this repo (its
    config directory exists) — that keeps init from seeding agent directories
    nobody asked for. Directories named explicitly (config `skill_dirs` or
    --skill-dir) are always written.
    """
    seen = {primary.resolve()}
    targets = []

    def add(path: Path):
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        targets.append(path)

    for relative in SKILL_DIRS.values():
        parent = repo_root / relative
        # `.claude`, `.grok`, `.agents` — evidence the harness is used here.
        if parent.parent.is_dir():
            add(parent)

    for relative in extra_dirs or ():
        add(repo_root / str(relative))

    return targets


def copy_skill(dest_parent: Path, force: bool = False) -> Path:
    source = bundled_skill_dir()
    dest = dest_parent / SKILL_NAME
    dest.mkdir(parents=True, exist_ok=True)

    if not source.is_dir():
        raise FileNotFoundError(f"Bundled skill not found at {source}")

    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        target = dest / relative
        if target.exists() and not force:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    return dest


def write_config(repo_root: Path, force: bool = False) -> Path:
    target = repo_root / ".feature-map.yaml"
    if target.exists() and not force:
        return target
    target.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return target


def write_shim(repo_root: Path, force: bool = False) -> Path:
    bin_dir = repo_root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / "feature-map"
    if target.exists() and not force:
        return target
    target.write_text(SHIM_SCRIPT, encoding="utf-8")
    target.chmod(target.stat().st_mode | 0o111)
    return target


def _replace_marked_block(text: str, block: str):
    pairs = ((AGENTS_MARKER, AGENTS_END),) + LEGACY_AGENTS_MARKERS
    for start_tok, end_tok in pairs:
        if start_tok in text and end_tok in text:
            start = text.index(start_tok)
            end = text.index(end_tok) + len(end_tok)
            new_text = text[:start] + block.rstrip() + text[end:]
            if not new_text.endswith("\n"):
                new_text += "\n"
            return new_text
        if start_tok in text:
            return text
    return None


def append_agents_snippet(repo_root: Path, skill_paths=()) -> Path:
    target = repo_root / "AGENTS.md"
    block = agents_block(repo_root, skill_paths).strip() + "\n"
    if target.exists():
        text = target.read_text(encoding="utf-8")
        replaced = _replace_marked_block(text, block)
        if replaced is not None:
            if replaced != text:
                target.write_text(replaced, encoding="utf-8")
            return target
        if not text.endswith("\n"):
            text += "\n"
        target.write_text(text + "\n" + block, encoding="utf-8")
    else:
        target.write_text("# Agent instructions\n\n" + block, encoding="utf-8")
    return target


def ensure_features_dir(repo_root: Path, features_dir_name: str = ".features") -> Path:
    features_dir = repo_root / features_dir_name
    features_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = features_dir / ".gitkeep"
    if not any(features_dir.glob("*.yaml")) and not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
    return features_dir


def bootstrap_repo(
    repo_root: Path,
    *,
    upgrade_skill: bool = False,
    agents: bool = True,
    shim: bool = True,
    force: bool = False,
    skill_dirs=(),
) -> dict:
    features_dir = ensure_features_dir(repo_root)
    skill_parent = detect_skill_parent(repo_root)
    refresh = upgrade_skill or force
    skill_path = copy_skill(skill_parent, force=refresh)

    mirrors = [
        copy_skill(parent, force=refresh)
        for parent in detect_mirror_parents(repo_root, skill_parent, skill_dirs)
    ]

    config_path = write_config(repo_root, force=False)
    shim_path = write_shim(repo_root, force=force) if shim else None
    agents_path = (
        append_agents_snippet(repo_root, [skill_path] + mirrors) if agents else None
    )

    return {
        "ok": True,
        "repo_root": str(repo_root),
        "features_dir": str(features_dir),
        "skill": str(skill_path),
        "skill_mirrors": [str(path) for path in mirrors],
        "config": str(config_path),
        "shim": str(shim_path) if shim_path else None,
        "agents": str(agents_path) if agents_path else None,
        "upgraded_skill": bool(refresh),
    }
