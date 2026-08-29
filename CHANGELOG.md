# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Homebrew formula draft in `Formula/feature-map.rb`
- pip-installable entrypoint via `pyproject.toml`

### Changed

- Public CLI and Homebrew name is `feature-map` (`brew install feature-map`).
  The PyPI project is `feature-map-cli` (`pip install feature-map-cli`) because
  PyPI treats `feature-map` as too similar to the existing biology package
  `featuremap`. The Python import is `feature_map`.
- Repo-local `bin/feature-map` shim execs `feature-map` without recursing if
  `bin/` is on PATH.
- `init` writes `<!-- feature-map:start -->` in `AGENTS.md` and migrates the
  older `<!-- featuremap:start -->` block.

[Unreleased]: https://github.com/markschellhas/feature-map/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/markschellhas/feature-map/releases/tag/v1.0.0
