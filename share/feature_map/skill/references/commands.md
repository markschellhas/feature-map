# Feature Map CLI Reference

Invocation: `feature-map` (on PATH) or `./bin/feature-map` (repo-local shim).

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
feature-map list
feature-map auth
feature-map show auth --section entry_points
feature-map search billing
feature-map find src/app.py
feature-map graph auth --format mermaid
feature-map validate
feature-map check --json
feature-map impact src/app.py
feature-map stats --json
feature-map init
feature-map init billing --force
```

## Exit codes

- `0` — success
- `1` — user error (e.g. feature not found)
- `2` — validation failure (`validate --strict`)
