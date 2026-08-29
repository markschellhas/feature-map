import unittest
from pathlib import Path

from feature_map.path_normalize import normalize_path_candidate, passes_normalized_invariants
from feature_map.path_resolve import resolve_candidate_paths


class NormalizeTests(unittest.TestCase):
    def test_strips_line_range_and_comment(self):
        self.assertEqual(
            normalize_path_candidate("src/app.py:10-20 — entry"),
            "src/app.py",
        )

    def test_rejects_http_routes(self):
        self.assertIsNone(normalize_path_candidate("GET /api/session"))

    def test_accepts_python_and_go(self):
        self.assertEqual(normalize_path_candidate("src/auth/session.py"), "src/auth/session.py")
        self.assertEqual(normalize_path_candidate("internal/handler.go"), "internal/handler.go")

    def test_invariants(self):
        self.assertTrue(passes_normalized_invariants("src/app.py"))
        self.assertFalse(passes_normalized_invariants("src/app.py:12"))


class ResolveTests(unittest.TestCase):
    def test_resolves_against_repo_root_and_apps(self):
        root = Path("/tmp/example")
        candidates = resolve_candidate_paths("src/app.py", root, ["api", "web"])
        as_str = [str(path) for path in candidates]
        self.assertIn(str(root / "src" / "app.py"), as_str)
        self.assertIn(str(root / "api" / "src" / "app.py"), as_str)


if __name__ == "__main__":
    unittest.main()
