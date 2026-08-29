# Feature Map CLI Reference

Invocation: `featuremap` (on PATH) or `./bin/feature-map` (repo-local shim).

Global flags: `--json`, `--version`

## Commands

| Command | Description |
|---------|-------------|
| `list [--json]` | All feature slugs; JSON includes mtime and app count |
| `show <name> [--section <key>] [--json]` | Full map or one top-level section |
| `<name>` | Alias for `show <name>` |
| `search <query> [--json]` | Full-text search across all maps |
| `find <path-fragment> [--json]` | Reverse lookup by path string |
| `graph [name] [--format mermaid\|json\|dot]` | `related_features` graph |
| `validate [--strict] [--json]` | Structural validation |
| `check [--json]` | Staleness check for entry-point paths |
| `impact <file> [--transitive] [--json]` | Features referencing a file |
| `stats [--json]` | Coverage statistics |
| `init` | Bootstrap `.features/`, agent skill, config, AGENTS.md, shim |
| `init <name> [--force]` | Scaffold `.features/<name>.yaml` |
| `init --upgrade-skill` | Refresh the agent skill from the installed package |
| `install [--json]` | Verify install and repo setup |

## Examples

```bash
featuremap list
featuremap auth
featuremap show auth --section entry_points
featuremap search billing
featuremap find src/app.py
featuremap graph auth --format mermaid
featuremap validate
featuremap check --json
featuremap impact src/app.py
featuremap stats --json
featuremap init
featuremap init billing --force
```

## Exit codes

- `0` — success
- `1` — user error (e.g. feature not found)
- `2` — validation failure (`validate --strict`)
