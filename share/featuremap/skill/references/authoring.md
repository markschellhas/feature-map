# Authoring Feature Maps

Feature maps live in `.features/<slug>.yaml` at the repo root.

## Required sections

- `feature_name` — must match the filename stem (normalized)
- `purpose` — what the feature does and why
- `entry_points` — files, routes, or surfaces (prefer real paths)
- `apps` — which apps participate (recommended; warning if missing)

## Recommended sections

- `user_flow` — key journeys
- `related_features` — links to other maps (use `slug (note)` format)
- `notes` — caveats, status, open questions

## Conventions

- Use underscores in filenames: `user_signup.yaml`
- `related_features` entries should start with a resolvable slug
- Run `featuremap validate` and `featuremap check` after edits
- Scaffold new maps: `featuremap init <name>`
- Bootstrap a new repo: `featuremap init`
- Existing repo with no maps: scour the code first (`existing-repos.md`); do not skip maps because the codebase predates Feature Map

## Schema

JSON Schema ships with the package at `share/featuremap/schema/feature-map.schema.json`.
