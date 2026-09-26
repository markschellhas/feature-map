"""Capture a free-form idea as markdown under docs/ideas/."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

from feature_map.confine import resolve_within
from feature_map.errors import CliError

IDEAS_REL = Path("docs") / "ideas"
SLUG_MAX = 50
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slugify_idea(text: str) -> str:
    """Build a filename slug from the first non-empty line of *text*."""
    first = ""
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            first = stripped
            break
    slug = _NON_SLUG.sub("-", first.lower()).strip("-")
    slug = slug[:SLUG_MAX].rstrip("-")
    return slug or "idea"


def unique_idea_path(ideas_dir: Path, slug: str, today: date) -> Path:
    base = "{0}-{1}".format(today.isoformat(), slug)
    candidate = ideas_dir / (base + ".md")
    n = 2
    while candidate.exists():
        candidate = ideas_dir / "{0}-{1}.md".format(base, n)
        n += 1
    return candidate


def read_idea_text():
    """Read a multi-line idea from stdin.

    Piped input is read to EOF. On a TTY, a prompt is printed and input ends
    on an empty line or EOF (Ctrl-D / Ctrl-Z).
    """
    if not sys.stdin.isatty():
        return sys.stdin.read()
    sys.stderr.write("Enter your idea. Finish with an empty line or Ctrl-D.\n")
    sys.stderr.flush()
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def run_idea(repo_root: Path, text=None, as_json=False, today=None):
    body = "" if text is None else str(text).strip()
    if not body:
        body = read_idea_text().strip()
    if not body:
        raise CliError(
            "No idea text provided.",
            suggestion="Type the idea, then finish with an empty line or Ctrl-D.",
        )

    today = today or date.today()
    ideas_dir = resolve_within(repo_root, repo_root / IDEAS_REL)
    if ideas_dir.exists() and not ideas_dir.is_dir():
        raise CliError(
            "Cannot write ideas: {0} exists and is not a directory.".format(IDEAS_REL),
        )
    try:
        ideas_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CliError("Could not create {0}: {1}".format(IDEAS_REL, exc)) from exc

    target = unique_idea_path(ideas_dir, slugify_idea(body), today)
    target = resolve_within(repo_root, target)
    content = body if body.endswith("\n") else body + "\n"
    try:
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise CliError("Could not write {0}: {1}".format(target.name, exc)) from exc

    rel = target.relative_to(repo_root.resolve()).as_posix()
    payload = {"ok": True, "path": rel, "file": target.name}

    if as_json:
        return payload

    print("Saved {0}".format(rel))
    return payload
