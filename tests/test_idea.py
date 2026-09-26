import json
import unittest
from datetime import date
from unittest.mock import patch

from feature_map.commands.idea_cmd import run_idea, slugify_idea, unique_idea_path
from feature_map.errors import CliError
from helpers import FeaturemapTestCase


class SlugifyTests(unittest.TestCase):
    def test_uses_first_non_empty_line(self):
        self.assertEqual(slugify_idea("Add dark mode\nMore detail"), "add-dark-mode")

    def test_strips_heading_markers(self):
        self.assertEqual(slugify_idea("# Ship the viewer"), "ship-the-viewer")

    def test_fallback_when_empty_or_punctuation(self):
        self.assertEqual(slugify_idea("!!!"), "idea")
        self.assertEqual(slugify_idea(""), "idea")

    def test_rejects_path_characters(self):
        self.assertEqual(slugify_idea("../etc/passwd"), "etc-passwd")
        self.assertNotIn("/", slugify_idea("a/b/c"))
        self.assertNotIn("..", slugify_idea(".."))


class IdeaCommandTests(FeaturemapTestCase):
    def _bare_repo(self):
        repo = self.tmpdir / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        return repo

    def test_writes_markdown_under_docs_ideas(self):
        repo = self._bare_repo()
        result = self.run_cli(
            ["idea"],
            cwd=repo,
            stdin="Capture product ideas from the CLI\nMultiple lines are kept.\n",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        name = "{0}-capture-product-ideas-from-the-cli.md".format(date.today().isoformat())
        expected = repo / "docs" / "ideas" / name
        self.assertTrue(expected.is_file())
        text = expected.read_text(encoding="utf-8")
        self.assertEqual(
            text,
            "Capture product ideas from the CLI\nMultiple lines are kept.\n",
        )
        self.assertIn("docs/ideas/{0}".format(name), result.stdout)

    def test_creates_docs_ideas_when_missing(self):
        repo = self._bare_repo()
        self.assertFalse((repo / "docs").exists())
        result = self.run_cli(["idea", "a one-line idea"], cwd=repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((repo / "docs" / "ideas").is_dir())
        files = list((repo / "docs" / "ideas").glob("*.md"))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].read_text(encoding="utf-8"), "a one-line idea\n")

    def test_positional_text_skips_stdin(self):
        repo = self._bare_repo()
        result = self.run_cli(
            ["idea", "use", "the", "args"],
            cwd=repo,
            stdin="this should be ignored\n",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        files = list((repo / "docs" / "ideas").glob("*.md"))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].read_text(encoding="utf-8"), "use the args\n")

    def test_json_payload(self):
        repo = self._bare_repo()
        result = self.run_cli(["idea", "--json"], cwd=repo, stdin="Named idea\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        name = "{0}-named-idea.md".format(date.today().isoformat())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["path"], "docs/ideas/{0}".format(name))
        self.assertEqual(payload["file"], name)

    def test_empty_input_is_an_error(self):
        repo = self._bare_repo()
        result = self.run_cli(["idea", "--json"], cwd=repo, stdin="   \n")
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("No idea text", payload["error"])
        self.assertFalse((repo / "docs" / "ideas").exists())

    def test_collision_appends_counter(self):
        repo = self._bare_repo()
        ideas = repo / "docs" / "ideas"
        ideas.mkdir(parents=True)
        stem = "{0}-same-title".format(date.today().isoformat())
        (ideas / (stem + ".md")).write_text("first\n", encoding="utf-8")
        result = self.run_cli(["idea"], cwd=repo, stdin="Same title\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        second = ideas / (stem + "-2.md")
        self.assertTrue(second.is_file())
        self.assertEqual(second.read_text(encoding="utf-8"), "Same title\n")

    def test_does_not_require_features_dir(self):
        repo = self._bare_repo()
        result = self.run_cli(["idea", "no maps yet"], cwd=repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((repo / "docs" / "ideas").is_dir())

    def test_help_mentions_idea(self):
        result = self.run_cli(["idea", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("docs/ideas", result.stdout)

    def test_run_idea_direct_uses_provided_date(self):
        repo = self._bare_repo()
        payload = run_idea(
            repo,
            text="Direct call",
            as_json=True,
            today=date(2026, 1, 2),
        )
        self.assertEqual(payload["path"], "docs/ideas/2026-01-02-direct-call.md")
        written = repo / "docs" / "ideas" / "2026-01-02-direct-call.md"
        self.assertEqual(written.read_text(encoding="utf-8"), "Direct call\n")

    def test_run_idea_rejects_empty_text(self):
        repo = self._bare_repo()
        with patch("feature_map.commands.idea_cmd.read_idea_text", return_value=""):
            with self.assertRaises(CliError):
                run_idea(repo, text=None)

    def test_unique_idea_path_increments(self):
        ideas = self.tmpdir / "ideas"
        ideas.mkdir()
        (ideas / "2026-09-26-hello.md").write_text("a\n", encoding="utf-8")
        (ideas / "2026-09-26-hello-2.md").write_text("b\n", encoding="utf-8")
        path = unique_idea_path(ideas, "hello", date(2026, 9, 26))
        self.assertEqual(path.name, "2026-09-26-hello-3.md")


if __name__ == "__main__":
    unittest.main()
