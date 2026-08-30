# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `feature-map update` upgrades the installed CLI (or reports that it is
  already latest). Detects pip, npm, Homebrew, pipx, and uv from the
  running executable and uses that package manager.
- After bootstrapping, `feature-map init` offers to launch your agent harness
  (`claude`, `cursor-agent`, `opencode`, `grok`, `codex`, `gemini`, `pi`) to
  scour the repo and author the first maps, with an arrow-key picker when
  multiple harnesses are on PATH. Shortcut with `-y/--yes` and
  `-h/--harness <name>`; prompts are skipped for `--json` and non-TTY runs.
- npm package `feature-map-cli` (`npm install -g feature-map-cli`) wraps the
  PyPI CLI in a local virtualenv. Still requires Python 3.8+.

## [1.0.0] — 2026-08-29

### Added

- `feature-map` CLI
- Full command surface: `list`, `show`, `search`, `find`, `graph`, `validate`,
  `check`, `impact`, `stats`, `init`, `install`, `--json`, `--version`
- `feature-map init` bootstraps any repo: `.features/`, agent skill, `.feature-map.yaml`,
  `AGENTS.md` snippet, and `bin/feature-map` shim
- `feature-map init <name>` scaffolds a new map from the bundled template
- `feature-map init --upgrade-skill` refreshes the agent skill from the installed package
- Fixture-based test suite
- Homebrew formula in `Formula/feature-map.rb` (tap: `markschellhas/tap`)
- pip-installable entrypoint via `pyproject.toml` (`feature-map-cli`)

### Changed

- Public CLI and Homebrew name is `feature-map` (`brew install markschellhas/tap/feature-map`).
  The PyPI project is `feature-map-cli` (`pip install feature-map-cli`) because
  PyPI treats `feature-map` as too similar to the existing biology package
  `featuremap`. The Python import is `feature_map`.
- Repo-local `bin/feature-map` shim execs `feature-map` without recursing if
  `bin/` is on PATH.
- `init` writes `<!-- feature-map:start -->` in `AGENTS.md` and migrates the
  older `<!-- featuremap:start -->` block.

[Unreleased]: https://github.com/markschellhas/feature-map/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/markschellhas/feature-map/releases/tag/v1.0.0
