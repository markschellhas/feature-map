import json
import unittest

from helpers import FeaturemapTestCase


class BootstrapTests(FeaturemapTestCase):
    def test_init_bootstraps_empty_repo(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()

        result = self.run_cli(["init", "--json"], cwd=repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])

        self.assertTrue((repo / ".features").is_dir())
        self.assertTrue((repo / ".feature-map.yaml").is_file())
        self.assertTrue((repo / ".agents" / "skills" / "feature-map" / "SKILL.md").is_file())
        self.assertTrue((repo / "bin" / "feature-map").is_file())
        agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("<!-- featuremap:start -->", agents)
        self.assertIn("feature-map list", agents)
        self.assertIn("ALWAYS", agents)
        self.assertIn("scour the existing code", agents)
        self.assertTrue(
            (repo / ".agents" / "skills" / "feature-map" / "references" / "existing-repos.md").is_file()
        )

    def test_init_refreshes_agents_block(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        self.run_cli(["init"], cwd=repo)
        agents_path = repo / "AGENTS.md"
        stale = (
            "# Agent instructions\n\n"
            "<!-- featuremap:start -->\nOLD BLOCK\n<!-- featuremap:end -->\n"
        )
        agents_path.write_text(stale, encoding="utf-8")
        result = self.run_cli(["init"], cwd=repo)
        self.assertEqual(result.returncode, 0)
        text = agents_path.read_text(encoding="utf-8")
        self.assertNotIn("OLD BLOCK", text)
        self.assertIn("ALWAYS", text)
        self.assertEqual(text.count("<!-- featuremap:start -->"), 1)

    def test_init_is_idempotent(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        first = self.run_cli(["init"], cwd=repo)
        self.assertEqual(first.returncode, 0)
        second = self.run_cli(["init", "--json"], cwd=repo)
        self.assertEqual(second.returncode, 0)
        payload = json.loads(second.stdout)
        self.assertTrue(payload["ok"])
        agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(agents.count("<!-- featuremap:start -->"), 1)

    def test_init_upgrade_skill(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        self.run_cli(["init"], cwd=repo)
        skill = repo / ".agents" / "skills" / "feature-map" / "SKILL.md"
        skill.write_text("stale\n", encoding="utf-8")
        result = self.run_cli(["init", "--upgrade-skill"], cwd=repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Feature Map", skill.read_text(encoding="utf-8"))

    def test_init_no_agents_no_shim(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        result = self.run_cli(["init", "--no-agents", "--no-shim"], cwd=repo)
        self.assertEqual(result.returncode, 0)
        self.assertFalse((repo / "AGENTS.md").exists())
        self.assertFalse((repo / "bin" / "feature-map").exists())
        self.assertTrue((repo / ".features").is_dir())

    def test_prefers_grok_skills_when_present(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".grok" / "skills").mkdir(parents=True)
        result = self.run_cli(["init"], cwd=repo)
        self.assertEqual(result.returncode, 0)
        self.assertTrue((repo / ".grok" / "skills" / "feature-map" / "SKILL.md").is_file())
        self.assertFalse((repo / ".agents" / "skills" / "feature-map" / "SKILL.md").exists())

    def test_install_status_json(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        self.run_cli(["init"], cwd=repo)
        result = self.run_cli(["install", "--json"], cwd=repo)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["features_dir"]["exists"])
        self.assertTrue(payload["skill"]["exists"])
        self.assertTrue(payload["config"]["exists"])


if __name__ == "__main__":
    unittest.main()
