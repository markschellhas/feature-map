import json
import unittest
from pathlib import Path

import yaml

from feature_map.confine import is_repo_relative, resolve_within
from feature_map.errors import CliError
from feature_map.loader import is_safe_slug, parse_slug, resolve_map_path
from feature_map.path_resolve import resolve_candidate_paths
from feature_map.yamlutil import MAX_YAML_DEPTH, safe_load
from helpers import FeaturemapTestCase


class SlugTests(unittest.TestCase):
    def test_accepts_plain_and_hyphenated_names(self):
        self.assertEqual(parse_slug("onboarding"), "onboarding")
        self.assertEqual(parse_slug("user-auth"), "user_auth")
        self.assertEqual(parse_slug("User Auth"), "user_auth")
        self.assertTrue(is_safe_slug("sso2"))

    def test_rejects_path_segments(self):
        for name in ("../pwned", "/tmp/pwned", "foo/bar", "..\\pwned", "foo.yaml", ""):
            with self.assertRaises(CliError):
                parse_slug(name)


class ConfineTests(unittest.TestCase):
    def test_repo_relative(self):
        self.assertTrue(is_repo_relative(".features"))
        self.assertTrue(is_repo_relative(".agents/skills"))
        self.assertFalse(is_repo_relative("/tmp/evil"))
        self.assertFalse(is_repo_relative("../outside"))
        self.assertFalse(is_repo_relative(""))
        self.assertFalse(is_repo_relative(None))

    def test_resolve_within_rejects_escape(self):
        repo = Path(__file__).resolve().parent
        with self.assertRaises(CliError):
            resolve_within(repo, repo / ".." / "outside")


class YamlBoundTests(unittest.TestCase):
    def test_rejects_aliases(self):
        with self.assertRaises(yaml.YAMLError):
            safe_load("a: &a\n  b: *a\n")

    def test_rejects_deep_nesting(self):
        nested = "a: " + ("{b: " * (MAX_YAML_DEPTH + 2)) + "1" + ("}" * (MAX_YAML_DEPTH + 2))
        with self.assertRaises(yaml.YAMLError):
            safe_load(nested)

    def test_parses_ordinary_maps(self):
        data = safe_load("feature_name: auth\npurpose: login\nentry_points:\n  - src/a.py\n")
        self.assertEqual(data["feature_name"], "auth")


class InitPathTraversalTests(FeaturemapTestCase):
    def test_init_rejects_dotdot_slug(self):
        repo = self.copy_repo()
        result = self.run_cli(["init", "../../pwned", "--json"], cwd=repo)
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertFalse((self.tmpdir / "pwned.yaml").exists())
        self.assertFalse((repo / "pwned.yaml").exists())

    def test_init_rejects_absolute_slug(self):
        repo = self.copy_repo()
        target = self.tmpdir / "abs_pwned"
        result = self.run_cli(["init", str(target), "--json"], cwd=repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(Path(str(target) + ".yaml").exists())
        self.assertFalse(target.exists())

    def test_init_still_scaffolds_hyphenated_names(self):
        repo = self.copy_repo()
        result = self.run_cli(["init", "user-auth"], cwd=repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((repo / ".features" / "user_auth.yaml").is_file())

    def test_skill_dir_rejects_escape(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        result = self.run_cli(
            ["init", "--skill-dir", "../outside-skills", "--json"], cwd=repo
        )
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertFalse((self.tmpdir / "outside-skills").exists())

    def test_config_features_dir_cannot_escape(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".feature-map.yaml").write_text(
            "features_dir: /tmp\n", encoding="utf-8"
        )
        result = self.run_cli(["init", "foo", "--json"], cwd=repo)
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("features_dir", payload["error"])

    def test_config_skill_dirs_cannot_escape(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".feature-map.yaml").write_text(
            "skill_dirs:\n  - ../../.ssh\n", encoding="utf-8"
        )
        result = self.run_cli(["init", "--json"], cwd=repo)
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])


class MapLookupTests(FeaturemapTestCase):
    def test_show_does_not_read_outside_features(self):
        repo = self.copy_repo()
        secret = self.tmpdir / "secret.yaml"
        secret.write_text(
            "feature_name: leaked\npurpose: should not be readable\nentry_points: []\n",
            encoding="utf-8",
        )
        result = self.run_cli(["show", "../../secret", "--json"], cwd=repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("leaked", result.stdout + result.stderr)
        with self.assertRaises(CliError):
            resolve_map_path(repo / ".features", "../../secret")

    def test_search_does_not_hang_on_alias_map(self):
        repo = self.copy_repo()
        (repo / ".features" / "bomb.yaml").write_text(
            "feature_name: &a\n  nested: *a\n",
            encoding="utf-8",
        )
        result = self.run_cli(["search", "subscription"], cwd=repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("billing", result.stdout)


class CheckConfineTests(unittest.TestCase):
    def test_absolute_and_dotdot_are_not_candidates(self):
        root = Path("/tmp/example-repo")
        self.assertEqual(resolve_candidate_paths("/etc/passwd", root, []), [])
        self.assertEqual(resolve_candidate_paths("../../etc/passwd", root, []), [])


if __name__ == "__main__":
    unittest.main()
