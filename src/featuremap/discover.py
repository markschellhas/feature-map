import subprocess
from pathlib import Path

from featuremap.errors import FeaturesNotFoundError


def _is_git_root(path: Path) -> bool:
    return (path / ".git").exists()


def find_repo_root(start: Path) -> Path:
    start = start.resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            cwd=start,
        )
        toplevel = result.stdout.strip()
        if toplevel:
            return Path(toplevel)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    current = start
    while current != current.parent:
        if _is_git_root(current):
            return current
        current = current.parent
    return start


def find_features_dir(start: Path) -> Path:
    start = start.resolve()
    repo_root = find_repo_root(start)

    if _is_git_root(repo_root):
        root_candidate = repo_root / ".features"
        if root_candidate.is_dir():
            return root_candidate

    current = start
    while True:
        candidate = current / ".features"
        if candidate.is_dir():
            return candidate
        if _is_git_root(current):
            break
        if current.parent == current:
            break
        current = current.parent

    root_candidate = repo_root / ".features"
    if root_candidate.is_dir():
        return root_candidate

    raise FeaturesNotFoundError()
