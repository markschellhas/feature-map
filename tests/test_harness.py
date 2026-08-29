import os
import stat
import unittest
from pathlib import Path

from feature_map import harness as harness_mod
from feature_map.errors import CliError

from helpers import FeaturemapTestCase

FAKE_HARNESS_SCRIPT = """#!/bin/sh
printf '%s\\n' "$@" >> "$LOGFILE"
"""


class HarnessTests(FeaturemapTestCase):
    def fake_bins(self, names):
        bindir = self.tmpdir / "fake-bin"
        bindir.mkdir(parents=True, exist_ok=True)
        for name in names:
            path = bindir / name
            path.write_text(FAKE_HARNESS_SCRIPT, encoding="utf-8")
            path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return bindir

    def make_repo(self):
        repo = self.tmpdir / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        return repo

    def path_env(self, names, logfile):
        bindir = self.fake_bins(names)
        return {"PATH": str(bindir), "LOGFILE": str(logfile)}

    # --- unit-level -------------------------------------------------

    def test_detect_harnesses_filters_and_orders(self):
        bindir = self.fake_bins(["pi", "claude"])
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = str(bindir)
        try:
            self.assertEqual(harness_mod.detect_harnesses(), ["claude", "pi"])
        finally:
            os.environ["PATH"] = original_path

    def test_build_prompt_embeds_skill_path(self):
        prompt = harness_mod.build_prompt("/repo/.agents/skills/feature-map")
        self.assertIn("/repo/.agents/skills/feature-map", prompt)
        self.assertIn(".features/", prompt)

    def test_unknown_harness_raises_cli_error(self):
        with self.assertRaises(CliError) as ctx:
            harness_mod.offer_authoring(Path("/repo"), "/skill", yes=True, harness="nope")
        self.assertIn("Unknown harness", str(ctx.exception))

    def test_offer_authoring_noops_without_flags(self):
        # Non-interactive, no -y: silently skip.
        self.assertFalse(harness_mod.offer_authoring(Path("/repo"), "/skill"))

    # --- end-to-end through the CLI ----------------------------------

    def test_init_yes_and_harness_launches_agent(self):
        repo = self.make_repo()
        logfile = self.tmpdir / "harness.log"
        result = self.run_cli(
            ["init", "-y", "-h", "claude"],
            cwd=repo,
            env=self.path_env(["claude"], logfile),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Launching "claude"', result.stdout)
        self.assertTrue(logfile.is_file())
        self.assertIn(".features/", logfile.read_text(encoding="utf-8"))

    def test_init_yes_uses_single_detected_harness(self):
        repo = self.make_repo()
        logfile = self.tmpdir / "harness.log"
        result = self.run_cli(
            ["init", "-y"],
            cwd=repo,
            env=self.path_env(["pi"], logfile),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(logfile.is_file())

    def test_init_yes_with_ambiguous_harnesses_asks_for_flag(self):
        repo = self.make_repo()
        logfile = self.tmpdir / "harness.log"
        result = self.run_cli(
            ["init", "-y"],
            cwd=repo,
            env=self.path_env(["claude", "pi"], logfile),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cannot pick a harness", result.stderr)
        self.assertFalse(logfile.exists())

    def test_init_unknown_harness_flag_errors(self):
        repo = self.make_repo()
        result = self.run_cli(["init", "-y", "-h", "nope"], cwd=repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown harness", result.stderr)

    def test_init_plain_never_prompts(self):
        repo = self.make_repo()
        result = self.run_cli(["init"], cwd=repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Initialized Feature Map", result.stdout)


if __name__ == "__main__":
    unittest.main()
