# Authoring Feature Maps

Feature maps live in `.features/<slug>.yaml` at the repo root.

## Required sections

- `feature_name` — must match the filename stem (normalized)
- `purpose` — one sentence: what it does. Skip motivation unless it changes where you look.
- `entry_points` — primary doors only (routes, screens, jobs, CLIs); real paths
- `apps` — app names as a list, not descriptions (recommended; warning if missing)

## Recommended sections

- `user_flow` — one line per distinct path: `Actor → step → result`. Add `alt`/`error` only if code diverges.
- `related_features` — `slug (coupling)`; parenthetical is a phrase

## Optional

- `notes` — caveats and unknowns only; omit the key if none. Never history, README, or process tips. `validate` does not warn when this key is absent.

## Density

Index, not essay. Completeness is doors, apps, and couplings. Delete a sentence if it would not change which file the next agent opens. Do not drop a real door, app, or related slug to stay short. Do not add narrative keys (`overview`, `history`, `architecture`, `background`). `core_components` is the only extra path group `check` understands.

## Conventions

- Use underscores in filenames: `user_signup.yaml`
- `related_features` entries should start with a resolvable slug
- Run `feature-map validate` and `feature-map check` after edits
- Scaffold new maps: `feature-map init <name>`
- Bootstrap a new repo: `feature-map init`
- Existing repo with no maps: scour the code first (`existing-repos.md`); do not skip maps because the codebase predates Feature Map
- Patch fields in place when the architecture changes; do not append prose

## Schema

JSON Schema ships with the package at `share/featuremap/schema/feature-map.schema.json`.
