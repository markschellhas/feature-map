import json
import unittest

from feature_map._version import __version__
from helpers import FeaturemapTestCase


class CliTests(FeaturemapTestCase):
    def test_version(self):
        result = self.run_cli(["--version"])
        self.assertEqual(result.returncode, 0)
        self.assertIn(__version__, result.stdout)

    def test_help_lists_commands(self):
        result = self.run_cli(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("feature-map", result.stdout)
        self.assertIn("cross-app feature index for agents", result.stdout)
        self.assertIn("by @MarkSchellhas", result.stdout)
        self.assertNotIn("usage: featuremap ", result.stdout)
        for name in ("list", "show", "search", "find", "graph", "validate", "init", "update"):
            self.assertIn(name, result.stdout)

    def test_list_and_show(self):
        repo = self.copy_repo()
        listed = self.run_cli(["list"], cwd=repo)
        self.assertEqual(listed.returncode, 0)
        self.assertIn("auth", listed.stdout)

        shown = self.run_cli(["auth"], cwd=repo)
        self.assertEqual(shown.returncode, 0)
        self.assertIn("purpose:", shown.stdout)

        section = self.run_cli(["show", "auth", "--section", "entry_points"], cwd=repo)
        self.assertEqual(section.returncode, 0)
        self.assertIn("src/auth/session.py", section.stdout)

    def test_list_json(self):
        repo = self.copy_repo()
        result = self.run_cli(["list", "--json"], cwd=repo)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        slugs = {item["slug"] for item in payload["features"]}
        self.assertEqual(slugs, {"auth", "billing", "notifications"})

    def test_unknown_feature_json_error(self):
        repo = self.copy_repo()
        result = self.run_cli(["nonexistent", "--json"], cwd=repo)
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("error", payload)
        self.assertIn("feature-map list", payload.get("suggestion", ""))

    def test_search_and_find(self):
        repo = self.copy_repo()
        search = self.run_cli(["search", "subscription"], cwd=repo)
        self.assertEqual(search.returncode, 0)
        self.assertIn("billing", search.stdout)

        found = self.run_cli(["find", "session.py"], cwd=repo)
        self.assertEqual(found.returncode, 0)
        self.assertIn("auth", found.stdout)

    def test_graph_json(self):
        repo = self.copy_repo()
        result = self.run_cli(["graph", "auth", "--format", "json"], cwd=repo)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("edges", payload)
        pairs = {(edge["from"], edge["to"]) for edge in payload["edges"]}
        self.assertIn(("auth", "billing"), pairs)

    def test_validate_and_stats(self):
        repo = self.copy_repo()
        validate = self.run_cli(["validate", "--json"], cwd=repo)
        self.assertEqual(validate.returncode, 0)
        payload = json.loads(validate.stdout)
        self.assertEqual(payload["error_count"], 0)
        self.assertGreaterEqual(payload["warning_count"], 1)

        stats = self.run_cli(["stats", "--json"], cwd=repo)
        self.assertEqual(stats.returncode, 0)
        stats_payload = json.loads(stats.stdout)
        self.assertEqual(stats_payload["map_count"], 3)
        self.assertGreaterEqual(stats_payload["broken_related_features"], 1)

    def test_check_reports_missing_without_failing(self):
        repo = self.copy_repo()
        result = self.run_cli(["check", "--json"], cwd=repo)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        missing = {issue["path"] for issue in payload["issues"]}
        self.assertIn("src/missing_file.py", missing)
        self.assertNotIn("src/app.py", missing)

    def test_impact(self):
        repo = self.copy_repo()
        result = self.run_cli(["impact", "src/app.py"], cwd=repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn("auth", result.stdout)

    def test_init_scaffolds_map(self):
        repo = self.copy_repo()
        result = self.run_cli(["init", "onboarding", "--force"], cwd=repo)
        self.assertEqual(result.returncode, 0)
        created = repo / ".features" / "onboarding.yaml"
        self.assertTrue(created.is_file())
        text = created.read_text(encoding="utf-8")
        self.assertIn("feature_name: onboarding", text)
        self.assertIn("One sentence:", text)
        self.assertNotIn("why it matters", text)
        self.assertNotIn("Authoring tips:", text)
        self.assertNotRegex(text, r"^notes:", msg="scaffold should omit notes unless there is a caveat")

    def test_discovery_from_subdirectory(self):
        repo = self.copy_repo()
        nested = repo / "src" / "auth"
        result = self.run_cli(["list"], cwd=nested)
        self.assertEqual(result.returncode, 0)
        self.assertIn("auth", result.stdout)


if __name__ == "__main__":
    unittest.main()
