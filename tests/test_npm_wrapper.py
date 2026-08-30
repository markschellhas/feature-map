import shutil
import subprocess
import unittest
from pathlib import Path

from feature_map._version import __version__

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "node not on PATH")
class NpmWrapperTests(unittest.TestCase):
    def test_scripts_parse(self):
        for rel in (
            "bin/feature-map.js",
            "scripts/postinstall.js",
            "scripts/python.js",
        ):
            result = subprocess.run(
                ["node", "--check", str(ROOT / rel)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_package_metadata(self):
        pkg = (ROOT / "package.json").read_text(encoding="utf-8")
        self.assertIn('"name": "feature-map-cli"', pkg)
        self.assertIn(f'"version": "{__version__}"', pkg)
        self.assertIn('"feature-map":', pkg)
