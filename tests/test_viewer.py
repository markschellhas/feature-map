import json
import threading
import unittest
from io import StringIO
from unittest import mock
from urllib.request import urlopen

from helpers import FeaturemapTestCase


class ViewerCliTests(FeaturemapTestCase):
    def test_help_mentions_no_open_and_timeout(self):
        result = self.run_cli(["viewer", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--no-open", result.stdout)
        self.assertIn("--timeout", result.stdout)

    def test_rejects_a_map_name_argument(self):
        repo = self.copy_repo()
        result = self.run_cli(["viewer", "auth"], cwd=repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("purpose:", result.stdout)

    def test_no_open_json_prints_loopback_url_and_does_not_write_repo(self):
        repo = self.copy_repo()
        before = {p.relative_to(repo) for p in repo.rglob("*") if p.is_file()}
        opened = []
        from feature_map.commands.viewer_cmd import run_viewer

        stdout = StringIO()
        with mock.patch("sys.stdout", stdout):
            payload = run_viewer(
                repo / ".features",
                repo,
                ["api", "web"],
                as_json=True,
                no_open=True,
                timeout=0.8,
                open_browser=opened.append,
            )
        self.assertIsNone(payload)
        self.assertEqual(opened, [])
        data = json.loads(stdout.getvalue())
        self.assertTrue(data["ok"])
        self.assertTrue(data["url"].startswith("http://127.0.0.1:"))
        after = {p.relative_to(repo) for p in repo.rglob("*") if p.is_file()}
        self.assertEqual(after, before)
        self.assertEqual(list(repo.rglob("*.html")), [])

    def test_cli_no_open_timeout_prints_url(self):
        repo = self.copy_repo()
        result = self.run_cli(
            ["viewer", "--no-open", "--timeout", "0.8"],
            cwd=repo,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("http://127.0.0.1:", result.stdout)
        self.assertEqual(list(repo.rglob("*.html")), [])

    def test_cli_json_shape(self):
        repo = self.copy_repo()
        result = self.run_cli(
            ["--json", "viewer", "--no-open", "--timeout", "0.8"],
            cwd=repo,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["ok"], True)
        self.assertTrue(payload["url"].startswith("http://127.0.0.1:"))

    def test_opens_browser_with_printed_url_unless_no_open(self):
        repo = self.copy_repo()
        opened = []
        from feature_map.commands.viewer_cmd import run_viewer

        stdout = StringIO()
        with mock.patch("sys.stdout", stdout):
            run_viewer(
                repo / ".features",
                repo,
                ["api", "web"],
                as_json=False,
                no_open=False,
                timeout=0.5,
                open_browser=opened.append,
            )
        url = stdout.getvalue().strip()
        self.assertTrue(url.startswith("http://127.0.0.1:"))
        self.assertEqual(opened, [url])

    def test_empty_features_dir_still_serves(self):
        repo = self.copy_repo()
        for path in (repo / ".features").glob("*.yaml"):
            path.unlink()
        from feature_map.commands.viewer_cmd import start_viewer

        session = start_viewer(repo / ".features", repo, ["api", "web"])
        thread = threading.Thread(target=session.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(session.server.shutdown)
        self.addCleanup(session.server.server_close)
        with urlopen(session.url, timeout=2) as resp:
            body = resp.read().decode("utf-8")
        self.assertIn("No feature maps", body)

    def test_missing_features_dir_is_an_error(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        result = self.run_cli(["viewer", "--no-open", "--timeout", "0.2"], cwd=repo)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
