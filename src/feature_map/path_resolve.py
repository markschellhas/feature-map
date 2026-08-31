from pathlib import Path
from typing import Iterable, List

PATH_EXTENSIONS = (".rb", ".js", ".erb", ".svelte", ".ts", ".tsx", ".py", ".go", ".yaml", ".yml")


def resolve_candidate_paths(path_str: str, repo_root: Path, apps: Iterable[str]) -> List[Path]:
    """Expand a pre-normalized path to filesystem candidates. Does not re-normalize."""
    path_str = path_str.strip()
    apps = [app for app in apps if isinstance(app, str) and app]
    candidates: List[Path] = []
    seen = set()
    try:
        root_resolved = repo_root.resolve()
    except (OSError, RuntimeError):
        root_resolved = repo_root

    def add(candidate: Path):
        try:
            resolved = candidate.resolve()
            resolved.relative_to(root_resolved)
        except (ValueError, OSError, RuntimeError):
            return
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            candidates.append(candidate)

    add(repo_root / path_str)
    for app in apps:
        add(repo_root / app / path_str)
        prefix = f"{app}/"
        if path_str.startswith(prefix):
            add(repo_root / path_str)
            add(repo_root / path_str[len(prefix) :])

    # Rails-style fallbacks when the consumer repo lists a rails app.
    if "rails" in apps:
        if path_str.startswith("app/"):
            add(repo_root / "rails" / path_str)
        if "/" not in path_str and path_str.endswith(PATH_EXTENSIONS):
            add(repo_root / "rails" / "app" / "javascript" / "controllers" / path_str)
            add(repo_root / "rails" / "app" / "controllers" / path_str)

    return candidates
