# Feature Map — development, packaging, and adoption

This is the operator's guide for `feature-map`: how it was built, how to
publish it so anyone can install it, and how a developer (or an agent)
adopts it in another repository — including existing codebases that do
not yet have maps.

---

## Why this, not a wiki

A Karpathy-style (or any LLM-written) wiki works: agents dump what they
learned into markdown and the next session can read it. The failure mode
is **shape**. Language models write prose. A wiki page on "signup" becomes
a narrative — history, asides, duplicated README, a little architecture —
and the next agent has to **ingest the whole page** to find the three
files that matter. That is slow in wall time and expensive in tokens.

Feature Map stores the same knowledge as **fields**, not essays:

| Need | Wiki | Feature Map |
|------|------|-------------|
| What is this? | Buried in a paragraph | `purpose` |
| Where do I start? | Maybe a link, maybe not | `entry_points` (real paths) |
| Which apps? | Prose | `apps` |
| How does a user move? | A story | `user_flow` |
| What else is coupled? | "See also" if you are lucky | `related_features` → `graph` |
| Is this stale? | You re-read it | `check` (paths on disk), `validate` |

**How an agent finds a feature (cheap path):**

```bash
feature-map list                          # names only
feature-map search billing                # slugs + short snippets
feature-map show billing --section entry_points
```

`list` is a few dozen tokens. `search` returns hits, not chapters.
`--section` loads **one key** from one YAML file. The agent opens the
code at those paths instead of reading a 2k-word wiki page and then
still grepping.

That is why it is more efficient:

1. **Addressable.** The CLI is an index (`list`, `search`, `find`,
   `impact`). A wiki is a pile of documents you `cat`.
2. **Bounded reads.** Structured keys + `--section` cap context. A wiki
   has no equivalent of "give me only the files."
3. **Checkable.** `validate` and `check` catch missing fields and dead
   paths. A wiki cannot tell you the controller it mentions was renamed.
4. **Stable voice.** YAML fields do not grow a new introduction every
   time an agent "updates the docs."

**Value to the developer** (human, not just the agent):

- You get a **directory of the product** — one slug per capability —
  without maintaining a second documentation site.
- Reviews stay honest: if `entry_points` does not list the file you
  changed, the map is wrong and you fix it in the same PR.
- Onboarding is `feature-map list` then `show`, not "read the wiki and"
  hope the architecture section is current."
- You still write PRDs and plans for *what to build*. The map only
  answers *where it lives and what it touches*. That split keeps both
  artifacts small.

A wiki can still hold narrative (vision, history, runbooks). Feature Map
is the **index the agent is required to hit first** so it does not spend
the budget re-discovering the tree.

---

## 1. How we developed this

### Why it exists

Taptics is a multi-app monorepo (`rails/`, `mobile_app/`, `worldcuppuzzles-web/`,
and others). Agents and engineers kept guessing which files belonged to which
product feature. The answer we wanted was a **per-repo, human-authored
architecture index** — YAML maps in `.features/` — plus a small CLI so agents
can `list` / `search` / `show` / `validate` instead of grepping the tree
blindly.

Maps are research infrastructure, not product features. They do not replace
PRDs or implementation plans. They tell you *where the code lives and how
the pieces connect* before you touch anything.

### Two-phase delivery

The work is specified in playbook-app `docs/PRDs/prd-feature-map-cli.md`.

| Phase | Where | Goal |
|-------|--------|------|
| **1** | Inside playbook-app | Dogfood a complete CLI and agent skill against real maps |
| **2** | This `feature-map` package | Extract that CLI so other repos can install it |

Phase 1 shipped first under `.agents/skills/feature-map/` with a repo-root
`./bin/feature-map` shim. Commands, schema, discovery (walk up from `cwd` to
the git root), JSON output, and a bash harness were proven against the
monorepo's maps.

Phase 2 is this directory. The Python package was moved, not rewritten:

- Import package `feature_map`; public CLI / Homebrew name `feature-map`;
  PyPI project `feature-map-cli`
- Assets (schema, template, agent skill) live in `share/feature_map/` and
  ship inside the wheel
- Tests use `tests/fixtures/` only — no dependency on Taptics maps
- Defaults are generic (`apps: []`); Rails-style path fallbacks apply only
  when `rails` is listed in `.feature-map.yaml`

### Design rules that made extraction cheap

1. **No imports from the host repo.** The CLI only reads `.features/`,
   `.feature-map.yaml`, and the filesystem.
2. **Package-relative assets.** Schema and templates resolve via
   `feature_map.paths.assets_root()`, not hardcoded monorepo paths.
3. **Thin entrypoint.** `python -m feature_map` and the `feature-map` console
   script both call `feature_map.cli:main`.
4. **Two meanings of `init`.** `feature-map init` bootstraps a consumer repo.
   `feature-map init <name>` scaffolds one map. Both are required for
   distribution: the first installs the workflow, the second authors data.

### What a feature map is

A map is a YAML file `.features/<slug>.yaml` with at least:

- `feature_name` — matches the filename stem
- `purpose` — what it does and why
- `entry_points` — real file paths (and routes if useful)

Recommended: `apps`, `user_flow`, `related_features`, `notes`. Cross-app
features get one map, not one map per app. `related_features` is how
`graph` and `impact --transitive` work.

### What we did *not* build

- No web UI or database of maps
- No auto-generator that invents maps from the AST (maps stay authored;
  agents may draft them after reading the code — see §3)
- No coupling to Rails, Flutter, or Taptics runtime

---

## 2. How to package it so anybody can use it

The product that other people install is **this directory**, not playbook-app.
Map *data* never ships in the package. Each consumer repo keeps its own
`.features/*.yaml`.

### 2.1 Split out of playbook-app (first publish)

This tree started as `playbook-app/featuremap/`. Cloud Agent tokens cannot
create GitHub repositories. Create `markschellhas/feature-map` (public, MIT)
in the GitHub UI, then:

```bash
cd /path/to/playbook-app
git subtree split --prefix=featuremap -b featuremap-split
git push git@github.com:markschellhas/feature-map.git featuremap-split:main
```

After that, develop and tag in the standalone repo. See `EXTRACT.md`.

### 2.2 pip (primary for Linux / CI)

From the `feature-map` repo root:

```bash
python3 -m pip install build twine
python3 -m build                # sdist + wheel in dist/
python3 -m twine check dist/*
python3 -m twine upload dist/   # once PyPI project "feature-map-cli" exists
# Preferred: Trusted Publishing. Full steps: PUBLISH.md
```

`pyproject.toml` already declares:

- distribution name `feature-map-cli`; import package `feature_map` under `src/feature_map`
- console script `feature-map = feature_map.cli:main`
- runtime dep `pyyaml>=6.0`
- wheel force-include of `share/feature_map` → `feature_map/share`

Until PyPI is live, anyone can install from git:

```bash
pip install "git+https://github.com/markschellhas/feature-map.git"
# or a local checkout:
pip install -e /path/to/feature-map
```

### 2.3 Homebrew (primary for macOS)

`Formula/feature-map.rb` is a draft. After the GitHub repo exists
(full steps: `PUBLISH.md`):

1. Tag a release: `git tag v1.0.0 && git push origin v1.0.0`
2. Fill `url` + `sha256` on the formula (or keep `head` for `--HEAD`)
3. Add the formula to a tap (`homebrew-taptics` or a personal tap)

```bash
brew tap markschellhas/tap
brew install feature-map
# or during bring-up:
brew install --HEAD markschellhas/tap/feature-map
```

The formula should leave `feature-map` on PATH and, when possible, install
`share/feature_map/{schema,templates,skill}` for `init`.

### 2.4 Versioning

- Semver on the CLI (`feature-map --version`, today `1.0.0`)
- Skill frontmatter `version:` should match the CLI version
- Record changes in `CHANGELOG.md`
- Consumer repos may pin `min_cli_version` in `.feature-map.yaml`

### 2.5 What a release contains vs what it does not

| Ships in the package | Stays in each consumer repo |
|----------------------|-----------------------------|
| `feature-map` binary | `.features/*.yaml` (the maps) |
| Schema + map template | `.feature-map.yaml` |
| Agent skill (`SKILL.md` + references) | `AGENTS.md` snippet (written by `init`) |
| Homebrew formula / CI for the tool | `bin/feature-map` shim (written by `init`) |

### 2.6 Verify a package before you publish

```bash
cd feature-map
pip install -e ".[dev]"
python -m pytest -q
feature-map --version
feature-map --help
```

CI (`.github/workflows/ci.yml`) runs the same tests on 3.8 and 3.12.

---

## 3. Install and use it in another repository

This section is for a developer adopting Feature Map in **their** repo,
greenfield or existing. It is also the contract agents must follow once
`feature-map init` has run.

### 3.1 Install the CLI

Pick one:

```bash
# once published
brew install markschellhas/tap/feature-map
pip install feature-map-cli
npm install -g feature-map-cli

# until then
pip install "git+https://github.com/markschellhas/feature-map.git"
pip install -e /path/to/playbook-app/featuremap
```

Confirm:

```bash
feature-map --version
```

### 3.2 Bootstrap the repo

From the consumer repo root (must be a git checkout, or `init` still works
if you are already at the intended root):

```bash
feature-map init
```

This is idempotent. It:

1. Creates `.features/`
2. Copies the agent skill to `.agents/skills/feature-map/`
   (or `.grok/skills/feature-map/` if that tree already exists)
3. Writes `.feature-map.yaml` if missing
4. Appends (or refreshes) an `AGENTS.md` block that **requires** agents
   to use Feature Map before feature work
5. Writes `bin/feature-map` — a shim that execs `feature-map` on PATH

Useful flags: `--no-agents`, `--no-shim`, `--upgrade-skill`, `--force`.
Also: `-y/--yes` skips the "start authoring maps?" prompt and
`-h/--harness <name>` picks the agent harness non-interactively
(`claude|cursor-agent|opencode|grok|codex|gemini|pi`). On an empty repo
`init` then offers to launch your harness to scour the code and author the
first maps; answer `n` or pick `skip` to do it yourself.

Then declare this repo's apps so `check` can resolve paths:

```yaml
# .feature-map.yaml
features_dir: .features
apps:
  - api
  - web
  - mobile
required_sections:
  - purpose
  - entry_points
min_cli_version: "1.0.0"
```

### 3.3 Instruction for agents — always use the feature map

`feature-map init` writes this mandate into `AGENTS.md`. Keep it. Do not
weaken it. Downstream skills (plans, PRDs, debugging) should say:

> **REQUIRED SUB-SKILL:** Use `feature-map` before proceeding.

**Agents must:**

1. **Before any feature work, debug, PRD, or plan** — run
   `feature-map list` (or `./bin/feature-map list`).
2. If the feature name is unclear — `feature-map search <keyword>` and
   `feature-map find <path-fragment>`.
3. Read the map — `feature-map <slug>` or
   `feature-map show <slug> --section entry_points` to save tokens.
4. For cross-cutting work — `feature-map graph <slug>`.
5. After shipping architecture changes — update the relevant
   `.features/*.yaml`, then `feature-map validate` and `feature-map check`.

**Agents must not** implement, plan, or "just grep the repo" when a map
exists for that area. The map is authoritative; the tree is how you
verify the map.

If `list` is empty, or search/find miss the area you are about to touch,
**stop and author maps first** (§3.4). Do not invent architecture in a
PRD or plan without writing the map.

Day-to-day commands:

```bash
feature-map list
feature-map search billing
feature-map find src/invoices
feature-map billing
feature-map show billing --section entry_points
feature-map graph billing --format mermaid
feature-map validate
feature-map check
feature-map impact src/invoices/create.py
```

`./bin/feature-map` is the same CLI if the global binary is not on PATH
in a given environment.

### 3.4 Existing repos — scour the code, then write maps

`init` does **not** generate maps from source. On a repo that already has
code, an agent (or a developer) must **read the tree and author maps**.
This is expected and should be the first Feature Map task in that repo.

Do not emit one map per file. Cluster by *user-visible capability* or
*deployed subsystem*.

#### Step A — inventory the repo

```bash
# top-level apps / packages
ls
# language / package manifests
# Gemfile, package.json, pyproject.toml, go.mod, pubspec.yaml, apps/, packages/
```

Write the `apps:` list in `.feature-map.yaml` from that inventory
(`api`, `web`, `ios`, `worker`, …). Prefer directory names that `check`
can prefix onto paths.

#### Step B — find seams (where features show up)

Scour, in order, whatever exists:

| Signal | Typical paths |
|--------|----------------|
| HTTP routes | `config/routes.rb`, `**/routes.*`, OpenAPI, `app/controllers` |
| App shells | `src/App.svelte`, `lib/main.dart`, `cmd/*/main.go`, `app/page.tsx` |
| Domain models | `app/models`, `src/domain`, `internal/` |
| Background jobs | `app/jobs`, `workers/`, queues |
| CLIs | `bin/`, `cmd/`, `cli/` |
| Docs / PRDs | `docs/`, `README*`, existing architecture notes |
| Tests | test names often name the feature better than folders |

Use the CLI as you go:

```bash
feature-map find <controller_or_package>
feature-map search <domain word>
```

On a first pass those will miss (no maps yet). That is the signal to
**draft** maps, not to skip them.

#### Step C — cluster into features

A feature is a slice a human would name in a standup ("signup",
"billing", "push notifications"), usually spanning several files and
sometimes several apps.

Cluster when they share:

- the same user journey
- the same primary models / tables
- the same entry controllers or screens
- a documented product name

Split when journeys, owners, or deployables diverge. Cross-app flows
(one API + one mobile screen + one worker) are **one** map with multiple
`apps` and `entry_points`, not three maps.

#### Step D — author each map

```bash
feature-map init signup          # scaffold .features/signup.yaml
```

Then replace placeholders by reading the real code. Required:

```yaml
feature_name: signup
purpose: "How a new account is created and reaches the first authenticated screen."
entry_points:
  - api/src/signup/handler.go
  - web/src/routes/signup/+page.svelte
apps:
  - api
  - web
user_flow:
  primary: "Email submit → API creates user → redirect to /app"
related_features:
  - billing (plan attached after first login)
notes: >
  Status: mapped from existing code on 2026-08-27. Confirm webhook path
  before changing Stripe.
```

Rules while scouring:

- Prefer **paths that exist on disk**. `feature-map check` will flag
  missing ones; invented paths train agents to look in the wrong place.
- Routes (`GET /signup`) may appear in `entry_points` as extra context,
  but put the implementing file next to them.
- `related_features` entries must start with a real slug once that map
  exists (`billing (note)`, not a sentence).
- Record uncertainty in `notes` instead of guessing.

Work in batches: scaffold 5–10 obvious features, `validate`, then fill
gaps `check` and `stats` report.

```bash
feature-map validate
feature-map check --json
feature-map stats --json
```

`validate` without `--strict` treats missing recommended sections as
warnings (exit 0). Use `--strict` in CI once the first pass is honest.

#### Step E — when to stop the first pass

Stop when:

- Every app in `.feature-map.yaml` appears on at least one map
- The main user journeys (signup, core loop, billing/admin if any) have maps
- `feature-map search <product noun>` hits something for the nouns in the README
- `check` only reports paths you *intend* to add, not typos

You do not need 100% file coverage. You need **named doors** into the
system so the next agent does not start from zero.

#### Step F — keep maps alive

After that first scour:

- New feature → `feature-map init <slug>` in the same PR as the code
- Moved/renamed files → update `entry_points`, run `check`
- Cross-feature work → update `related_features` and re-read `graph`

### 3.5 Greenfield repos

If there is almost no code yet, still `feature-map init`, then add a map
when the first vertical slice lands. Empty `.features/` plus the
`AGENTS.md` mandate is enough: the next agent is required to author the
map with the feature, not after the fact.

### 3.6 CI in the consumer repo

```yaml
# example GitHub Actions step
- run: pip install feature-map-cli
- run: feature-map validate
# optional, once maps are trusted:
# - run: feature-map validate --strict
```

Trigger on changes to `.features/**` and, if you want a backstop, on
every PR.

### 3.7 Upgrade

```bash
feature-map update
# or, by hand:
# pip install -U feature-map-cli
# npm install -g feature-map-cli@latest
# brew upgrade markschellhas/tap/feature-map
feature-map init --upgrade-skill
```

`feature-map update` detects whether this copy came from pip, npm, Homebrew,
pipx, or uv and upgrades through that channel. If you are already on the
latest version it says so and exits 0. A source/editable checkout cannot
be upgraded this way — install a released package instead.

`--upgrade-skill` overwrites the deployed `SKILL.md` and references from
the installed package version. Re-run `feature-map init` to refresh the
`AGENTS.md` marked block.

---

## Related files in this package

| File | Role |
|------|------|
| `README.md` | Short install + command list |
| `PUBLISH.md` | Submit to PyPI and Homebrew |
| `EXTRACT.md` | Split this directory into its own GitHub repo |
| `CHANGELOG.md` | Released CLI versions |
| `share/feature_map/skill/SKILL.md` | Agent skill copied by `init` |
| `share/feature_map/skill/references/existing-repos.md` | Scour-the-code playbook for agents |
| `share/feature_map/skill/references/authoring.md` | Map shape and conventions |
| `share/feature_map/skill/references/commands.md` | Full CLI reference |
