# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-08-27

### Added

- `featuremap` CLI
- Full command surface: `list`, `show`, `search`, `find`, `graph`, `validate`,
  `check`, `impact`, `stats`, `init`, `install`, `--json`, `--version`
- `featuremap init` bootstraps any repo: `.features/`, agent skill, `.feature-map.yaml`,
  `AGENTS.md` snippet, and `bin/feature-map` shim
- `featuremap init <name>` scaffolds a new map from the bundled template
- `featuremap init --upgrade-skill` refreshes the agent skill from the installed package
- Fixture-based test suite
- Homebrew formula draft in `Formula/featuremap.rb`
- pip-installable entrypoint via `pyproject.toml`

[1.0.0]: https://github.com/markschellhas/featuremap/releases/tag/v1.0.0
