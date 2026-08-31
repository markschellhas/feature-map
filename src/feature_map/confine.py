"""Keep filesystem operations inside a repository root."""

from __future__ import annotations

from pathlib import Path

from feature_map.errors import CliError


def is_repo_relative(value: str) -> bool:
    """True when value is a non-empty relative path with no `..` parts."""
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    path = Path(text)
    return not path.is_absolute() and ".." not in path.parts


def resolve_within(root: Path, candidate: Path) -> Path:
    """Resolve *candidate* and require it stays inside *root*.

    Follows symlinks, so a dest that looks in-repo but points outside is
    rejected. Works for paths that do not exist yet (`Path.resolve` is not
    strict).
    """
    try:
        root_resolved = root.resolve()
        resolved = candidate.resolve()
    except (OSError, RuntimeError) as exc:
        raise CliError("Could not resolve path: {0}".format(candidate)) from exc
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        raise CliError(
            "Path is outside the repository: {0}".format(candidate),
            suggestion="Use a path inside the repository.",
        )
    return resolved
