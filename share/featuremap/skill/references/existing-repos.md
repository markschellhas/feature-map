# Bootstrapping maps on an existing repository

`featuremap init` creates the workflow. It does **not** invent maps from
source. On a repo that already has code, you must **scour the tree and
author** `.features/*.yaml` before doing feature work.

## When this applies

- `featuremap list` is empty
- `search` / `find` miss the area you are about to change
- `.feature-map.yaml` `apps` is `[]` but the repo has multiple packages

Do not skip this and "just grep". Author maps first, then implement.

## Playbook

1. **Inventory apps** — top-level directories and manifests (`Gemfile`,
   `package.json`, `pyproject.toml`, `go.mod`, `pubspec.yaml`, `apps/`,
   `packages/`). Write them under `apps:` in `.feature-map.yaml`.
2. **Find seams** — routes, app shells, domain models, jobs, CLIs, docs,
   and test names. These are where features show up.
3. **Cluster** — one map per user-visible capability or subsystem, not
   per file. Cross-app journeys are one map with several `apps` and
   `entry_points`.
4. **Scaffold + fill** — `featuremap init <slug>`, then replace
   placeholders with real paths and a short `purpose` you verified in
   code.
5. **Verify** — `featuremap validate` and `featuremap check`. Prefer
   paths that exist on disk. Record uncertainty in `notes`.
6. **Stop the first pass** when every listed app appears on at least one
   map and the README's product nouns `search` successfully.

Full narrative: the package `GUIDE.md` §3.4 (existing repos).

## Anti-patterns

- One map per source file
- Invented `entry_points` that `check` would mark missing
- `related_features` that do not start with a real slug
- Planning or coding a feature that has no map "because the repo is old"
