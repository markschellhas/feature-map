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

AGENTS_BLOCK = f"""{AGENTS_MARKER}
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
**scour the existing code and author maps first** (skill:
`feature-map` → `references/existing-repos.md`). Cluster by user-visible
capability, not by file. Prefer `entry_points` that exist on disk, then
run `feature-map validate` and `feature-map check`.
{AGENTS_END}
"""

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
"""


def detect_skill_parent(repo_root: Path) -> Path:
    agents = repo_root / ".agents" / "skills"
    grok = repo_root / ".grok" / "skills"
    if grok.exists() and not agents.exists():
        return grok
    return agents


def copy_skill(dest_parent: Path, force: bool = False) -> Path:
    source = bundled_skill_dir()
    dest = dest_parent / "feature-map"
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


def append_agents_snippet(repo_root: Path) -> Path:
    target = repo_root / "AGENTS.md"
    block = AGENTS_BLOCK.strip() + "\n"
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
) -> dict:
    features_dir = ensure_features_dir(repo_root)
    skill_parent = detect_skill_parent(repo_root)
    skill_path = copy_skill(skill_parent, force=upgrade_skill or force)
    config_path = write_config(repo_root, force=False)
    shim_path = write_shim(repo_root, force=force) if shim else None
    agents_path = append_agents_snippet(repo_root) if agents else None

    return {
        "ok": True,
        "repo_root": str(repo_root),
        "features_dir": str(features_dir),
        "skill": str(skill_path),
        "config": str(config_path),
        "shim": str(shim_path) if shim_path else None,
        "agents": str(agents_path) if agents_path else None,
        "upgraded_skill": bool(upgrade_skill or force),
    }
