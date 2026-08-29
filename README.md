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
2. Copies the agent skill to `.agents/skills/feature-map/` (or `.grok/skills/` if that tree already exists)
3. Writes `.feature-map.yaml` defaults when missing
4. Appends an `AGENTS.md` block (skip with `--no-agents`)
5. Writes `bin/feature-map` as a repo-local shim (skip with `--no-shim`)
6. Offers to launch your agent harness (claude, cursor-agent, opencode, grok,
   codex, gemini, pi) to scour the repo and author the first maps. Skip the
   prompt with `-y` and pick a harness directly with `-h <name>` (e.g.
   `feature-map init -y -h claude`).

Refresh the skill after upgrading the package:

```bash
feature-map init --upgrade-skill
```

## Commands

| Command | Purpose |
|---------|---------|
| `list` | All feature slugs |
| `show <name>` / `<name>` | Print a map (or `--section`) |
| `search <query>` | Full-text search |
| `find <path>` | Reverse lookup by path fragment |
| `graph [name]` | `related_features` graph (`mermaid`, `json`, `dot`) |
| `validate [--strict]` | Structural checks |
| `check` | Stale `entry_points` / `core_components` paths |
| `impact <file>` | Which maps reference a file |
| `stats` | Coverage summary |
| `init [-y] [-h <harness>]` | Bootstrap repo; optionally launch a harness to author maps |
| `init <name> [--force]` | Scaffold a map from the template |
| `install` | Setup status |
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
```

`apps` prefixes are used by `check` when resolving paths.

## Develop

```bash
pip install -e ".[dev]"
python -m pytest -q
```

## License

MIT
