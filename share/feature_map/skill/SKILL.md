---
name: feature-map
version: 1.1.0
description: "Research cross-app architecture via the Feature Map CLI before feature work, debugging, PRDs, or implementation plans. Run list, show, search, find, graph, validate, and check against .features/*.yaml. On existing repos with no maps, scour the code and author maps first."
---

# Feature Map

Authoritative cross-app architecture lives in `.features/*.yaml`. **Always**
use this skill before touching a feature. Do not plan, debug, or implement
from a cold grep when a map exists — or when one should exist and does not.

Maps are **fields, not a wiki**. Prefer `list` / `search` / `show --section`
over reading a long markdown doc. That keeps token use on paths and purpose,
not narrative. When writing or updating a map, same rule: cover every door
and coupling; do not write narrative (`references/authoring.md`, Density).
`references/example-map.md` is a full map with the reasoning for every line.
Full narrative: the packaged `GUIDE.md` (path: `feature-map install --json` → `.guide.path`), "Why this, not a wiki".

## When to invoke

- Before feature implementation, debugging, PRDs, implementation plans, or pre-mortems
- When unsure which feature map applies
- After shipping changes that affect architecture (update maps, then validate)
- When `list` is empty or `search`/`find` miss: **scour the repo and author maps** before other work (see `references/existing-repos.md`)

## Research sequence

```bash
feature-map list
feature-map search <keyword>    # when the feature name is unclear
feature-map find <path-fragment>
feature-map <feature-name>      # or: show <feature-name>
feature-map graph <feature>     # cross-cutting dependencies
```

`./bin/feature-map` is a repo-local shim for the same CLI (created by `feature-map init`).

Use `show <name> --section entry_points` (or `purpose`, `user_flow`, etc.) to limit token use on large maps.

If the list is empty, or nothing matches the area you are about to change,
**stop**. Follow `references/existing-repos.md`: inventory apps, cluster
capabilities, `feature-map init <slug>`, fill real paths, `validate` + `check`.
Then resume the research sequence.

## After implementation

1. Patch the fields that changed. Do not grow the map with prose.
2. Run `feature-map validate`
3. Run `feature-map check`

## Commands

See `references/commands.md` for the full CLI reference.

## Authoring

See `references/authoring.md` for shape, density, and conventions.
See `references/example-map.md` for a complete map, annotated line by line.
See `references/existing-repos.md` when adopting Feature Map on a codebase that already exists.
