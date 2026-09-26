# Feature Map

Cross-app architecture research CLI. Agents and engineers keep authoritative
feature maps in `.features/*.yaml`; `feature-map` lists, searches, validates,
and graphs them.

A wiki stores architecture as prose — agents re-read a whole page to find three
files. Feature Map stores **fields** (`purpose`, `entry_points`, `apps`) and a
CLI that returns **names and sections**, so lookup is cheap and `check` can
prove paths still exist.

## Install

```bash
pip install feature-map-cli
npm install -g feature-map-cli
brew install markschellhas/tap/feature-map
```

Requires Python 3.8+ and PyYAML (the npm package installs the PyPI CLI into a
local venv). The CLI is `feature-map`. Install from PyPI or npm as
`feature-map-cli` — `pip install featuremap` is a different (biology) project,
and `feature-map` is blocked on PyPI as too similar to that name.

## Usage

```bash
cd my-repo
feature-map init
feature-map init auth          # scaffold .features/auth.yaml
feature-map list
feature-map search billing
feature-map validate
```

`feature-map init` is idempotent. It:

1. Creates `.features/`
2. Copies the agent skill to `.agents/skills/feature-map/` (or `.grok/skills/` if that tree already exists),
   and mirrors it into any other known harness directory the repo already uses
3. Adds extra copies for `--skill-dir DIR` / `skill_dirs:` targets
4. Writes `.feature-map.yaml` defaults when missing
5. Appends an `AGENTS.md` block naming the skill's path (skip with `--no-agents`)
6. Writes `bin/feature-map` as a repo-local shim (skip with `--no-shim`)
7. Offers to launch your agent harness (claude, cursor-agent, opencode, grok,
   codex, gemini, pi) to scour the repo and author the first maps. Skip the
   prompt with `-y` and pick a harness directly with `-h <name>` (e.g.
   `feature-map init -y -h claude`).

Skill directories are harness-neutral. `.agents/skills/` stays the primary
target; a known harness is *additionally* mirrored only when the repo already
uses it (its config directory exists), so `init` never seeds an agent tree
nobody asked for. Known: `.agents/skills`, `.claude/skills`, `.grok/skills`.
For anything else, name it yourself — `--skill-dir .my-agent/skills`, or
`skill_dirs:` in `.feature-map.yaml` — and it is always written.

Upgrade the CLI, then refresh the skill (every location) after a new package
version:

```bash
feature-map update
feature-map init --upgrade-skill
```

## Commands

| Command | Purpose |
|---------|---------|
| `list` | All feature slugs |
| `show <name>` / `<name>` | Print a map (or `--section`) |
| `viewer [--no-open] [--timeout SECONDS]` | Local read-only browser view of all maps (does not write HTML into the repo) |
| `search <query>` | Full-text search |
| `find <path>` | Reverse lookup by path fragment |
| `graph [name]` | `related_features` graph (`mermaid`, `json`, `dot`) |
| `validate [--strict]` | Structural checks |
| `check` | Stale `entry_points` / `core_components` paths |
| `impact <file>` | Which maps reference a file |
| `stats` | Coverage summary |
| `init [-y] [-h <harness>] [--skill-dir DIR]` | Bootstrap repo; optionally launch a harness to author maps |
| `init <name> [--force]` | Scaffold a map from the template |
| `install` | Setup status |
| `update` | Upgrade this CLI via pip, npm, brew, pipx, or uv |
| `idea [text]` | Capture a multi-line idea into `docs/ideas/` |
| `--json` / `--version` | Machine output / version |

Exit codes: `0` ok, `1` user error, `2` validation failure (`--strict`).

## Per-repo config

`.feature-map.yaml` at the git root:

```yaml
features_dir: .features
apps:
  - api
  - web
required_sections:
  - purpose
  - entry_points
min_cli_version: "1.0.0"
skill_dirs:
  - .my-agent/skills
```

`apps` prefixes are used by `check` when resolving paths. `skill_dirs` adds
skill mirror targets for harnesses the CLI does not know about.

## Develop

Published PyPI, npm, and Homebrew installs lag this tree. Work from a
checkout with an **editable install** so `feature-map` on PATH is the code
you are editing. Use a virtualenv (required on PEP 668 / Homebrew Python):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"     # same as `make install`
python -m pytest -q         # same as `make test`
feature-map --version
```

Edits under `src/feature_map/` take effect immediately. Dogfood against
another repo by keeping the venv activated and `cd`-ing there, or from
that repo: `pip install -e /path/to/feature-map`. `python -m feature_map`
is the same CLI as the console script.

Do not iterate via `npm install -g feature-map-cli` or `brew install`:
those pull the last **published** PyPI version. `feature-map update`
refuses a source/editable checkout on purpose.

To test the packaged wheel without uploading:

```bash
python -m pip install -U build
rm -rf dist && python -m build
pip install dist/feature_map_cli-*.whl
```

Uninstall with `pip uninstall -y feature-map-cli`, then return to
`pip install -e ".[dev]"`. Full notes: [GUIDE.md](GUIDE.md) (Local
development).

## License

MIT
