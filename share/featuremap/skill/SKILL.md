---
name: feature-map
version: 1.0.0
description: "Research cross-app architecture via the Feature Map CLI before feature work, debugging, PRDs, or implementation plans. Run list, show, search, find, graph, validate, and check against .features/*.yaml. On existing repos with no maps, scour the code and author maps first."
---

# Feature Map

Authoritative cross-app architecture lives in `.features/*.yaml`. **Always**
use this skill before touching a feature. Do not plan, debug, or implement
from a cold grep when a map exists — or when one should exist and does not.

Maps are **fields, not a wiki**. Prefer `list` / `search` / `show --section`
over reading a long markdown doc. That keeps token use on paths and purpose,
not narrative. See the package `GUIDE.md` ("Why this, not a wiki").

## When to invoke

- Before feature implementation, debugging, PRDs, implementation plans, or pre-mortems
- When unsure which feature map applies
- After shipping changes that affect architecture (update maps, then validate)
- When `list` is empty or `search`/`find` miss: **scour the repo and author maps** before other work (see `references/existing-repos.md`)

## Research sequence

```bash
featuremap list
featuremap search <keyword>    # when the feature name is unclear
featuremap find <path-fragment>
featuremap <feature-name>      # or: show <feature-name>
featuremap graph <feature>     # cross-cutting dependencies
```

`./bin/feature-map` is a repo-local shim for the same CLI (created by `featuremap init`).

Use `show <name> --section entry_points` (or `purpose`, `user_flow`, etc.) to limit token use on large maps.

If the list is empty, or nothing matches the area you are about to change,
**stop**. Follow `references/existing-repos.md`: inventory apps, cluster
capabilities, `featuremap init <slug>`, fill real paths, `validate` + `check`.
Then resume the research sequence.

## After implementation

1. Update relevant `.features/*.yaml`
2. Run `featuremap validate`
3. Run `featuremap check`

## Commands

See `references/commands.md` for the full CLI reference.

## Authoring

See `references/authoring.md` for required sections and conventions.
See `references/existing-repos.md` when adopting Feature Map on a codebase that already exists.
