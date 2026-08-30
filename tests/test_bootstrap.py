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
        self.assertIn("<!-- feature-map:start -->", agents)
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
        self.assertEqual(text.count("<!-- feature-map:start -->"), 1)
        self.assertNotIn("<!-- featuremap:start -->", text)

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
        self.assertEqual(agents.count("<!-- feature-map:start -->"), 1)

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

    def test_shim_invokes_feature_map(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        self.run_cli(["init"], cwd=repo)
        shim = (repo / "bin" / "feature-map").read_text(encoding="utf-8")
        self.assertIn("pip install feature-map-cli", shim)
        self.assertIn("npm install -g feature-map-cli", shim)
        self.assertIn("command -v feature-map", shim)
        self.assertNotIn("pip install featuremap", shim)

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

    def test_mirrors_skill_into_existing_harness_dirs(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".claude").mkdir()

        result = self.run_cli(["init", "--json"], cwd=repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)

        # Primary target is unchanged; the harness in use is mirrored alongside.
        self.assertTrue((repo / ".agents" / "skills" / "feature-map" / "SKILL.md").is_file())
        self.assertTrue((repo / ".claude" / "skills" / "feature-map" / "SKILL.md").is_file())
        self.assertIn(
            str(repo.resolve() / ".claude" / "skills" / "feature-map"),
            payload["skill_mirrors"],
        )

    def test_does_not_seed_unused_harness_dirs(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()

        result = self.run_cli(["init", "--json"], cwd=repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual(payload["skill_mirrors"], [])
        self.assertFalse((repo / ".claude").exists())
        self.assertFalse((repo / ".grok").exists())

    def test_skill_dir_flag_mirrors_unknown_harness(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()

        result = self.run_cli(
            ["init", "--skill-dir", ".my-agent/skills", "--json"], cwd=repo
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((repo / ".my-agent" / "skills" / "feature-map" / "SKILL.md").is_file())

    def test_config_skill_dirs_are_mirrored(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        self.run_cli(["init"], cwd=repo)
        config = repo / ".feature-map.yaml"
        config.write_text(
            config.read_text(encoding="utf-8") + "skill_dirs:\n  - .other/skills\n",
            encoding="utf-8",
        )

        result = self.run_cli(["init"], cwd=repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((repo / ".other" / "skills" / "feature-map" / "SKILL.md").is_file())

    def test_grok_primary_is_not_duplicated_as_a_mirror(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".grok" / "skills").mkdir(parents=True)

        result = self.run_cli(["init", "--json"], cwd=repo)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["skill"], str(repo.resolve() / ".grok" / "skills" / "feature-map")
        )
        self.assertEqual(payload["skill_mirrors"], [])

    def test_agents_block_names_the_skill_path(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".claude").mkdir()
        self.run_cli(["init"], cwd=repo)

        agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(".agents/skills/feature-map/SKILL.md", agents)
        self.assertIn(".claude/skills/feature-map/SKILL.md", agents)
        self.assertIn("references/example-map.md", agents)

    def test_skill_ships_worked_example(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        self.run_cli(["init"], cwd=repo)

        example = repo / ".agents" / "skills" / "feature-map" / "references" / "example-map.md"
        self.assertTrue(example.is_file())
        self.assertIn("feature_name: signup", example.read_text(encoding="utf-8"))

    def test_install_reports_guide_and_locations(self):
        repo = self.tmpdir / "empty"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".claude").mkdir()
        self.run_cli(["init"], cwd=repo)

        payload = json.loads(self.run_cli(["install", "--json"], cwd=repo).stdout)
        self.assertTrue(payload["guide"]["exists"])
        deployed = {
            entry["harness"] for entry in payload["skill_locations"] if entry["exists"]
        }
        self.assertEqual(deployed, {"agents", "claude"})


if __name__ == "__main__":
    unittest.main()
