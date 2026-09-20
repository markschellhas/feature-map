# PRD: Feature Map Viewer

**Status:** Draft
**Owner:** feature-map maintainers

Local-only viewer: render maps in the installed browser. Do not write HTML into
the consumer repo or treat generated pages as a second source of truth.

Source issue: https://github.com/markschellhas/feature-map/issues/1

---

## Overview

Humans need to read `.features/*.yaml` as a product directory: purpose, doors,
flow, and neighbors. Today they get raw YAML from `feature-map show` and a
Mermaid string from `feature-map graph`. That is enough for agents. It is a
poor reading surface for a person trying to understand the feature.

This work adds `feature-map viewer`. The CLI loads the same maps it already
owns, renders them in memory, and opens the user's installed browser. A sidebar
lists every map. The main pane shows one map. Related-feature slugs switch the
pane.

The page is a throwaway rendering. It is not a document. It is not written into
the consumer repo, not written under `.features/`, not written into `docs/`, and
not kept as a second copy of the maps. YAML on disk stays the only source of
truth.

This is the human counterpart to `show`. Agents keep using stdout and `--json`.
GUIDE.md currently lists "no web UI" as an explicit non-build; this PRD
replaces that decision for a local, ephemeral, read-only view only.

The CLI does not take a map slug. Opening a specific map is in-page (sidebar /
related-feature clicks), not `feature-map viewer <name>`.

## Goals / Non-Goals

**Goals:**

1. A human can run `feature-map viewer` in a repo with `.features/` and see
   every map listed in a sidebar in their default browser.
2. Clicking a sidebar row or a related-feature slug shows that map without
   leaving the page.
3. The main pane presents map fields in schema order: `purpose`, `user_flow`,
   `entry_points`, `apps`, `related_features`, `notes`, then any extra keys.
4. `related_features` graph from the existing `graph` data is visible on the
   page (Mermaid is already produced by the CLI).
5. `entry_points` flagged missing by the existing `check` logic are marked on
   the page. Paths are not rewritten.
6. Rendered HTML is never written into the consumer repo or treated as
   canonical. The command may hold HTML in memory or in a process-scoped temp
   file that is not part of the repo.
7. `feature-map show` and `feature-map <name>` stay stdout YAML. Agents and
   scripts are unchanged.
8. Headless or no-display environments can run `feature-map viewer --no-open`
   and get a local URL (and `--json` URL payload) without spawning a browser.

**Non-Goals:**

- A CLI argument to open one map (`feature-map viewer <name>` /
  `feature-map view <name>`). Selection is in-page only.
- Editing maps in the browser, saving YAML, or round-tripping HTML back to
  `.features/`.
- A packaged desktop app, protocol handler, Typora/Electron/Tauri shell, or
  `feature-map://` deep links.
- A hosted site, static export, wiki, or generated Markdown tree of maps.
- Writing HTML, CSS, or generated pages into `.features/`, `docs/`, `share/`,
  or any consumer-repo path as a stored artifact.
- New runtime dependencies beyond the Python standard library and the existing
  PyYAML dependency.
- Changing the feature-map schema or map authoring rules.
- Auto-generating maps from source.
- Opening `entry_points` in an editor (may be a later increment; not v1).
- Live multi-user collaboration, auth, or binding the local server off
  loopback.

## Current Implementation

No current implementation — greenfield feature for the viewing surface.

What already exists and must be reused:

- Package `feature_map` in `markschellhas/feature-map`. Public CLI
  `feature-map`. Discovery walks from cwd to the git root (`discover.py`) and
  reads `.feature-map.yaml` (`config.py`).
- Command table in `src/feature_map/cli.py`: `list`, `show`, `search`, `find`,
  `graph`, `validate`, `check`, `impact`, `stats`, `init`, `install`, `update`.
  `COMMANDS` and `preprocess_argv` treat a bare slug as `show`.
- `show` (`commands/show_cmd.py`) prints the YAML file text, or one
  `--section`, or JSON. That remains the agent path.
- `list` returns slugs. `search` / `find` / `impact` are the index. `graph`
  (`commands/graph_cmd.py`, `graph.py`) already emits Mermaid, DOT, and JSON
  from `related_features`.
- `check` (`commands/check_cmd.py`) reports stale `entry_points` /
  `core_components` paths using `apps` prefixes from config.
- Loader and path helpers: `loader.py`, `paths.py`, `path_resolve.py`,
  `confine.py`. Output helpers: `output.py`. Errors: `errors.py` (`CliError`
  exit 1, validate `--strict` exit 2).
- Launch-another-app precedent is `harness.py` after `init` (spawn `opencode`
  and similar). That is a process spawn, not a desktop protocol. This viewer
  should open the default browser the same way: CLI does the work, then hands
  off.
- GUIDE.md "What we did *not* build" currently says no web UI. README command
  table has no `viewer`.
- Install surfaces that will need a one-line command mention after ship:
  `README.md`, `share/feature_map/skill/references/commands.md`,
  `CHANGELOG.md`. Skill copy is refreshed in consumer repos via
  `feature-map init --upgrade-skill`.

There is no `.features/view.yaml` in this package. Maps live only in consumer
repos. This package's own tests use
`tests/fixtures/.features/{auth,billing,notifications}.yaml`.

## Proposed Implementation

Single package: `feature-map` (`feature_map` on PyPI as `feature-map-cli`). No
second app.

**User-facing**

- New subcommand `viewer` with no map argument: `feature-map viewer`.
- Flags: `--no-open` (do not spawn a browser), existing global `--json` (emit
  `{ ok, url }` instead of opening quietly).
- Browser UI: sidebar of map titles only; main pane for the selected map;
  related slugs and graph nodes navigate in-page. Related-feature graphs and
  Mermaid render as diagrams on a canvas, not as source.
- Empty `.features/`: open the shell page with an empty list and a short "no
  maps" message, not a crash.

**Contracts this work defines**

- CLI contract (defined in `cli.py` + new `commands/viewer_cmd.py`): command
  name `viewer`, no `name` argument, `--no-open`, `--json` shape
  `{ "ok": true, "url": "..." }`.
- View model contract (defined in a new module next to the command, consumed
  only by the renderer): a JSON-serializable snapshot built from existing
  `load_map`, `graph_data`, and `check` results. Fields: slugs, selected slug,
  per-map data, stale paths. No new on-disk schema.
- Render contract: HTML is produced from that snapshot plus a packaged
  template under `share/feature_map/` (shipped in the wheel like the schema
  and skill). The template is part of the *tool*, not part of the consumer
  repo. Running `viewer` must not copy that template into the consumer tree.

**What does not change**

- Map schema (`share/feature_map/schema/feature-map.schema.json`).
- `show` alias for a bare name.
- `init` harness launch.
- Consumer-repo layout (`.features/`, `.feature-map.yaml`).

**Docs that change after behavior exists**

- `README.md` command table.
- `share/feature_map/skill/references/commands.md`.
- `CHANGELOG.md`.
- GUIDE.md "What we did not build" line: local ephemeral view is allowed;
  stored HTML / wiki export is still forbidden.

## Technical Details

All files are in the `feature-map` package.

**Command wiring**

- `src/feature_map/cli.py` — add `viewer` to `COMMANDS`, parser, and
  `dispatch`. Do not add `viewer` to `OPTIONAL_FEATURES_COMMANDS` (need a
  features dir). Do not treat `viewer` as a show alias.
- `src/feature_map/commands/viewer_cmd.py` — new. Resolve maps with the same
  `resolve_context` as `show`. Build the view snapshot. Start a loopback-only
  server that serves the rendered page from memory. Optionally call the stdlib
  browser opener. Return the URL string or the JSON payload.

**Reuse, do not re-parse**

- `loader.py` / `resolve_map_path` for each map.
- `graph.py` `graph_data` + existing Mermaid formatter for the on-page graph.
- `check` internals for stale path marks (same resolution rules as `apps`
  prefixes).
- `errors.py` / `output.py` for failures and `--json`.

**Renderer**

- Packaged template(s) under `share/feature_map/view/` (or equivalent),
  resolved via `feature_map.paths.assets_root()` like schema and skill.
- Render in process: fill the template from the snapshot. Do not write the
  result into the repo root, `.features/`, or `docs/`.
- If the platform browser opener requires a `file://` path, use a
  process-scoped temp file outside the repo and do not document that path as
  an artifact. Prefer `http://127.0.0.1:<port>/` so nothing is written at all.
- Bind `127.0.0.1` only. Do not serve the repository filesystem. Do not follow
  paths out of the rendered snapshot.

**Process lifetime**

- With a browser open: keep the loopback server alive until interrupt, or
  until a short idle timeout documented in `--help`. Print the URL so the
  human can refresh.
- With `--no-open` / `--json`: print the URL (or JSON) and either keep the
  server for the same lifetime or refuse if no server can be held — pick one
  behavior and test it. Headless CI must not hang waiting on a display.

**Packaging / tests**

- `pyproject.toml` — no new third-party deps.
- Tests under `tests/` using `tests/fixtures/.features`. Cover: command
  registration, snapshot contains fixture slugs, `--no-open` prints a loopback
  URL, no file created under the fixture repo root.
- After ship: README, commands.md, CHANGELOG, GUIDE exception for ephemeral
  view.

**Skill / consumer repos**

- `viewer` is a human command. The agent skill should mention it as optional
  for humans and keep requiring `show` / `--section` for agents. Do not make
  agents open a browser.

## Effort Estimates

- CLI command + dispatch + flags + JSON/error contract: **S**
- View snapshot from loader / graph / check: **S**
- In-memory loopback renderer + packaged template + sidebar/detail/graph: **M**
- Tests (fixtures, no-write invariant, headless `--no-open`): **S**
- Docs (README, commands.md, CHANGELOG, GUIDE exception): **S**

## Open Questions

Resolved in `docs/plans/2026-09-20-view.md`:

- **Server lifetime:** block the terminal until Ctrl-C. `--timeout SECONDS`
  (default `0` = until interrupt) is documented in `--help` so CI and tests
  do not hang.
- **Watch:** one-shot render for v1. Restart the command to pick up YAML
  edits.
- **Editor links:** out of v1.
- **Port:** ephemeral (`bind(..., 0)`). Always print the URL.
- **First selected map:** first slug from `list_map_files` (sorted by
  filename). Empty dir selects nothing and shows a "no maps" message.

## Related Docs

- This draft: `docs/prds/prd-view.md`
- Plan: `docs/plans/2026-09-20-view.md`
- Tool guide: `GUIDE.md`
- CLI help text source: `README.md`,
  `share/feature_map/skill/references/commands.md`
- Map shape: `share/feature_map/skill/references/example-map.md`,
  `share/feature_map/schema/feature-map.schema.json`
- Existing read path: `src/feature_map/cli.py`,
  `src/feature_map/commands/show_cmd.py`,
  `src/feature_map/commands/graph_cmd.py`,
  `src/feature_map/commands/check_cmd.py`,
  `src/feature_map/loader.py`, `src/feature_map/graph.py`
- Launch-other-app precedent: `src/feature_map/harness.py`
- Consumer maps live at `.features/<name>.yaml` in each adopting repo (not in
  this package)
