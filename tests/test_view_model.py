import unittest

from helpers import FEATURES, REPO, FeaturemapTestCase


class ViewModelTests(FeaturemapTestCase):
    def _snapshot(self, features_dir=None, repo_root=None, apps=None):
        from feature_map.view_model import build_view_snapshot

        repo = repo_root or self.copy_repo()
        features = features_dir or (repo / ".features")
        return build_view_snapshot(features, repo, apps if apps is not None else ["api", "web"])

    def test_snapshot_lists_fixture_slugs_in_filename_order(self):
        snapshot = self._snapshot()
        self.assertEqual(snapshot["slugs"], ["auth", "billing", "notifications"])
        self.assertEqual(snapshot["selected"], "auth")
        self.assertEqual(set(snapshot["maps"]), {"auth", "billing", "notifications"})

    def test_fields_follow_prd_display_order(self):
        snapshot = self._snapshot()
        keys = [item["key"] for item in snapshot["maps"]["auth"]["fields"]]
        self.assertEqual(
            keys[:6],
            ["purpose", "user_flow", "entry_points", "apps", "related_features", "notes"],
        )
        self.assertNotIn("feature_name", keys)

    def test_extra_keys_come_after_known_fields(self):
        repo = self.copy_repo()
        extra_map = repo / ".features" / "auth.yaml"
        text = extra_map.read_text(encoding="utf-8")
        extra_map.write_text(text + "\ncore_components:\n  - src/auth/session.py\n", encoding="utf-8")
        snapshot = self._snapshot(features_dir=repo / ".features", repo_root=repo)
        keys = [item["key"] for item in snapshot["maps"]["auth"]["fields"]]
        self.assertIn("core_components", keys)
        self.assertGreater(keys.index("core_components"), keys.index("notes"))
        self.assertEqual(snapshot["maps"]["auth"]["extra"]["core_components"], ["src/auth/session.py"])

    def test_marks_stale_entry_points_without_rewriting_paths(self):
        snapshot = self._snapshot()
        billing = snapshot["maps"]["billing"]
        self.assertIn("src/missing_file.py", billing["stale_paths"])
        self.assertIn("src/missing_file.py", billing["entry_points"])
        self.assertNotIn("src/billing/plans.py", billing["stale_paths"])
        auth = snapshot["maps"]["auth"]
        self.assertEqual(auth["stale_paths"], [])
        self.assertIn("src/app.py", auth["entry_points"])

    def test_graph_reuses_existing_mermaid(self):
        snapshot = self._snapshot()
        pairs = {(edge["from"], edge["to"]) for edge in snapshot["graph"]["edges"]}
        self.assertIn(("auth", "billing"), pairs)
        self.assertIn("auth", snapshot["graph"]["nodes"])
        self.assertIn("graph LR", snapshot["graph"]["mermaid"])
        self.assertIn("auth --> billing", snapshot["graph"]["mermaid"])

    def test_related_slugs_parsed_from_related_features(self):
        snapshot = self._snapshot()
        self.assertEqual(snapshot["maps"]["auth"]["related_slugs"], ["billing"])
        self.assertTrue(
            snapshot["maps"]["auth"]["related_features"][0].startswith("billing")
        )

    def test_empty_features_dir_does_not_crash(self):
        repo = self.copy_repo()
        for path in (repo / ".features").glob("*.yaml"):
            path.unlink()
        snapshot = self._snapshot(features_dir=repo / ".features", repo_root=repo)
        self.assertEqual(snapshot["slugs"], [])
        self.assertIsNone(snapshot["selected"])
        self.assertEqual(snapshot["maps"], {})
        self.assertEqual(snapshot["graph"]["nodes"], [])

    def test_does_not_import_from_fixtures_package_root(self):
        """Sanity: helpers expose the same fixture maps the rest of the suite uses."""
        self.assertTrue((FEATURES / "auth.yaml").is_file())
        self.assertTrue((REPO / "src" / "auth" / "session.py").is_file())


if __name__ == "__main__":
    unittest.main()
