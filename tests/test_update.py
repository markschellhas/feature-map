import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from feature_map.commands.update_cmd import (
    BREW_FORMULA,
    NPM_JSON_URL,
    PIP_PACKAGE,
    PYPI_JSON_URL,
    SKILL_HINT,
    InstallOrigin,
    compare_versions,
    detect_installer,
    fetch_latest,
    run_update,
)
from feature_map.errors import CliError
from helpers import FeaturemapTestCase


class VersionTests(unittest.TestCase):
    def test_compare_versions(self):
        self.assertEqual(compare_versions("1.0.0", "1.0.0"), 0)
        self.assertEqual(compare_versions("v1.0.0", "1.0.0"), 0)
        self.assertEqual(compare_versions("1.0.0", "1.0.1"), -1)
        self.assertEqual(compare_versions("1.10.0", "1.9.0"), 1)
        self.assertEqual(compare_versions("1.0", "1.0.0"), 0)


class DetectInstallerTests(FeaturemapTestCase):
    def _python(self, *parts):
        path = self.tmpdir.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        return path

    def _npm_package(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        (root / "package.json").write_text(
            json.dumps({"name": "feature-map-cli", "version": "1.0.0"}),
            encoding="utf-8",
        )
        python = root / ".venv" / "bin" / "python"
        python.parent.mkdir(parents=True, exist_ok=True)
        python.write_text("", encoding="utf-8")
        return python

    def test_detects_homebrew_cellar(self):
        python = self._python(
            "opt", "homebrew", "Cellar", "feature-map", "1.0.0", "libexec", "bin", "python"
        )
        origin = detect_installer(executable=python, dist_present=False)
        self.assertEqual(origin.kind, "brew")
        self.assertEqual(origin.command, ["brew", "upgrade", BREW_FORMULA])
        self.assertEqual(origin.package, "feature-map")

    def test_detects_homebrew_opt(self):
        python = self._python("opt", "homebrew", "opt", "feature-map", "libexec", "bin", "python")
        origin = detect_installer(executable=python, dist_present=False)
        self.assertEqual(origin.kind, "brew")

    def test_detects_npm_global(self):
        python = self._npm_package(
            self.tmpdir / "usr" / "local" / "lib" / "node_modules" / "feature-map-cli"
        )
        origin = detect_installer(executable=python, dist_present=True)
        self.assertEqual(origin.kind, "npm")
        self.assertEqual(origin.command, ["npm", "install", "-g", "feature-map-cli@latest"])
        self.assertIsNone(origin.cwd)

    def test_detects_npm_local(self):
        project = self.tmpdir / "app"
        python = self._npm_package(project / "node_modules" / "feature-map-cli")
        origin = detect_installer(executable=python, dist_present=True)
        self.assertEqual(origin.kind, "npm")
        self.assertEqual(origin.command, ["npm", "install", "feature-map-cli@latest"])
        self.assertEqual(origin.cwd, str(project.resolve()))

    def test_repo_checkout_is_not_npm(self):
        root = self.tmpdir / "feature-map"
        python = self._npm_package(root)
        origin = detect_installer(
            executable=python,
            dist_present=True,
            dist_direct_url=json.dumps({"dir_info": {"editable": True}}),
        )
        self.assertEqual(origin.kind, "source")

    def test_detects_pipx(self):
        python = self._python(
            "home", ".local", "pipx", "venvs", "feature-map-cli", "bin", "python"
        )
        origin = detect_installer(executable=python, dist_present=True)
        self.assertEqual(origin.kind, "pipx")
        self.assertEqual(origin.command, ["pipx", "upgrade", PIP_PACKAGE])

    def test_detects_uv_tool(self):
        python = self._python(
            "home", ".local", "share", "uv", "tools", "feature-map-cli", "bin", "python"
        )
        origin = detect_installer(executable=python, dist_present=True)
        self.assertEqual(origin.kind, "uv")
        self.assertEqual(origin.command, ["uv", "tool", "upgrade", PIP_PACKAGE])

    def test_falls_back_to_pip(self):
        python = self._python("venv", "bin", "python")
        origin = detect_installer(executable=python, dist_present=True, dist_direct_url=None)
        self.assertEqual(origin.kind, "pip")
        self.assertEqual(
            origin.command,
            [str(python.resolve()), "-m", "pip", "install", "--upgrade", PIP_PACKAGE],
        )

    def test_unknown_without_dist(self):
        python = self._python("venv", "bin", "python")
        origin = detect_installer(executable=python, dist_present=False)
        self.assertEqual(origin.kind, "unknown")

    def test_editable_install_is_source(self):
        python = self._python("venv", "bin", "python")
        origin = detect_installer(
            executable=python,
            dist_present=True,
            dist_direct_url=json.dumps(
                {"url": "file:///src/feature-map", "dir_info": {"editable": True}}
            ),
        )
        self.assertEqual(origin.kind, "source")


class FetchLatestTests(unittest.TestCase):
    def test_fetch_pypi(self):
        payload = {"info": {"version": "1.2.3"}}

        def fake_urlopen(url):
            self.assertEqual(url, PYPI_JSON_URL)
            return io.BytesIO(json.dumps(payload).encode("utf-8"))

        self.assertEqual(fetch_latest("pip", urlopen_fn=fake_urlopen), "1.2.3")

    def test_fetch_npm(self):
        def fake_urlopen(url):
            self.assertEqual(url, NPM_JSON_URL)
            return io.BytesIO(json.dumps({"version": "9.9.9"}).encode("utf-8"))

        self.assertEqual(fetch_latest("npm", urlopen_fn=fake_urlopen), "9.9.9")

    def test_fetch_brew(self):
        class Result:
            returncode = 0
            stdout = json.dumps({"formulae": [{"versions": {"stable": "1.4.0"}}]})
            stderr = ""

        def fake_brew(command, cwd=None):
            self.assertEqual(command[:3], ["brew", "info", "--json=v2"])
            return Result()

        self.assertEqual(fetch_latest("brew", brew_runner=fake_brew), "1.4.0")

    def test_fetch_error(self):
        def fake_urlopen(url):
            raise OSError("offline")

        with self.assertRaises(CliError):
            fetch_latest("pip", urlopen_fn=fake_urlopen)


class FakeRun:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.calls = []

    def __call__(self, command, cwd=None):
        self.calls.append((list(command), cwd))
        return self


class RunUpdateTests(unittest.TestCase):
    def test_already_latest(self):
        origin = InstallOrigin(
            kind="pip",
            command=["python", "-m", "pip", "install", "--upgrade", PIP_PACKAGE],
        )
        runner = FakeRun()
        payload = run_update(
            as_json=True,
            current_version="1.0.0",
            origin=origin,
            latest_version="1.0.0",
            runner=runner,
        )
        self.assertTrue(payload["already_latest"])
        self.assertFalse(payload["updated"])
        self.assertIn("Already on the latest version", payload["message"])
        self.assertEqual(runner.calls, [])

    def test_newer_than_registry(self):
        origin = InstallOrigin(kind="pip", command=["pip"])
        payload = run_update(
            as_json=True,
            current_version="2.0.0",
            origin=origin,
            latest_version="1.0.0",
            runner=FakeRun(),
        )
        self.assertFalse(payload["already_latest"])
        self.assertFalse(payload["updated"])
        self.assertIn("newer than", payload["message"])

    def test_upgrades_via_detected_command(self):
        origin = InstallOrigin(
            kind="npm",
            command=["npm", "install", "-g", "feature-map-cli@latest"],
        )
        runner = FakeRun()
        payload = run_update(
            as_json=True,
            current_version="1.0.0",
            origin=origin,
            latest_version="1.1.0",
            runner=runner,
        )
        self.assertTrue(payload["updated"])
        self.assertEqual(payload["latest_version"], "1.1.0")
        self.assertEqual(payload["installer"], "npm")
        self.assertEqual(runner.calls, [(origin.command, None)])
        self.assertEqual(payload["suggestion"], SKILL_HINT)

    def test_local_npm_passes_cwd(self):
        origin = InstallOrigin(
            kind="npm",
            command=["npm", "install", "feature-map-cli@latest"],
            cwd="/tmp/app",
        )
        runner = FakeRun()
        run_update(
            as_json=True,
            current_version="1.0.0",
            origin=origin,
            latest_version="1.2.0",
            runner=runner,
        )
        self.assertEqual(runner.calls, [(origin.command, "/tmp/app")])

    def test_unknown_installer(self):
        with self.assertRaises(CliError) as raised:
            run_update(as_json=True, origin=InstallOrigin(kind="unknown"))
        self.assertIn("Could not detect", raised.exception.message)

    def test_source_install(self):
        with self.assertRaises(CliError) as raised:
            run_update(
                as_json=True,
                current_version="1.0.0",
                origin=InstallOrigin(kind="source"),
            )
        self.assertIn("source/editable", raised.exception.message)

    def test_upgrade_failure(self):
        origin = InstallOrigin(kind="brew", command=["brew", "upgrade", BREW_FORMULA])
        with self.assertRaises(CliError) as raised:
            run_update(
                as_json=True,
                current_version="1.0.0",
                origin=origin,
                latest_version="1.1.0",
                runner=FakeRun(returncode=1),
            )
        self.assertIn("brew update failed", raised.exception.message)

    def test_prints_already_latest(self):
        origin = InstallOrigin(kind="pip", command=["pip"])
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            run_update(
                as_json=False,
                current_version="1.0.0",
                origin=origin,
                latest_version="1.0.0",
                runner=FakeRun(),
            )
        self.assertIn("Already on the latest version (1.0.0), installed via pip.", stdout.getvalue())


class UpdateCliTests(FeaturemapTestCase):
    def test_help_lists_update(self):
        result = self.run_cli(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("update", result.stdout)

    def test_update_help(self):
        result = self.run_cli(["update", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("package manager", result.stdout)

    def test_update_does_not_require_features(self):
        empty = self.tmpdir / "empty"
        empty.mkdir()
        from feature_map.cli import main

        with patch("os.getcwd", return_value=str(empty)):
            with patch(
                "feature_map.cli.run_update",
                return_value={
                    "ok": True,
                    "already_latest": True,
                    "message": "Already on the latest version.",
                },
            ):
                code = main(["update", "--json"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
