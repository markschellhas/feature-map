"""Post-init flow: offer to launch an agent harness that authors the maps."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from feature_map.errors import CliError
from feature_map.prompt import confirm, select

HARNESSES = ["claude", "cursor-agent", "opencode", "grok", "codex", "gemini", "pi"]

PROMPT_TEMPLATE = (
    "Feature Map has been initialized in this repository. Read the skill at "
    "{skill} and follow its references/existing-repos.md playbook (with "
    "references/example-map.md as the shape to copy): scour the "
    "repository, cluster user-visible capabilities, and author feature maps in "
    ".features/ — scaffold each with './bin/feature-map init <slug>', fill real "
    "paths from the code, then run './bin/feature-map validate' and "
    "'./bin/feature-map check'."
)


def detect_harnesses():
    """Known harness binaries present on PATH, in HARNESSES order."""
    return [name for name in HARNESSES if shutil.which(name)]


def build_prompt(skill_path):
    return PROMPT_TEMPLATE.format(skill=skill_path)


def launch_harness(harness, prompt, repo_root):
    """Run the chosen harness in the repo root. Returns its exit status."""
    try:
        return subprocess.call([harness, prompt], cwd=str(repo_root))
    except FileNotFoundError:
        raise CliError(
            f'Harness not found on PATH: "{harness}".',
            suggestion="Install it or pick another: " + ", ".join(HARNESSES),
        )


def offer_authoring(repo_root: Path, skill_path, *, yes=False, harness=None):
    """After bootstrap, offer to scour the repo and author maps via a harness.

    Non-interactive runs (pipes, CI, --json) stay quiet unless flags force the
    choice. Returns True when a harness was launched.
    """
    interactive = sys.stdin.isatty() and sys.stdout.isatty()

    if harness is not None and harness not in HARNESSES:
        raise CliError(
            f'Unknown harness "{harness}".',
            suggestion="Choose from: " + ", ".join(HARNESSES),
        )

    if not interactive and not yes:
        return False

    if interactive and not yes:
        if not confirm("Start creating feature maps for this project now?"):
            print("Skipping. Start later with: feature-map init -y [-h <harness>]")
            return False

    chosen = harness or _pick_harness(interactive)

    if not chosen:
        print("Skipping harness launch.")
        return False

    prompt = build_prompt(skill_path)
    print(f'Launching "{chosen}" to author the feature maps…')
    exit_code = launch_harness(chosen, prompt, repo_root)
    if exit_code:
        print(f'"{chosen}" exited with status {exit_code}.')
    return True


def _pick_harness(interactive):
    """Resolve which harness to use when none was passed explicitly."""
    detected = detect_harnesses()
    if interactive:
        if len(detected) == 1:
            print(f"Using detected harness: {detected[0]}")
            return detected[0]
        choices = detected if detected else HARNESSES
        label = "Which agent harness should author the maps?"
        if not detected:
            label += " (none detected on PATH; pick one to try anyway)"
        chosen = select(label, list(choices) + ["skip"])
        return None if chosen in (None, "skip") else chosen
    if len(detected) == 1:
        return detected[0]
    raise CliError(
        "Cannot pick a harness without a terminal.",
        suggestion="Pass -h/--harness: " + ", ".join(HARNESSES),
    )
