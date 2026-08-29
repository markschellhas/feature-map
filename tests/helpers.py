import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
FEATURES = FIXTURES / ".features"
REPO = FIXTURES / "repo"


class FeaturemapTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="featuremap-"))
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)

    def copy_features(self, dest=None):
        dest = dest or (self.tmpdir / ".features")
        shutil.copytree(FEATURES, dest)
        return dest

    def copy_repo(self):
        repo = self.tmpdir / "repo"
        shutil.copytree(REPO, repo)
        shutil.copytree(FEATURES, repo / ".features")
        (repo / ".feature-map.yaml").write_text(
            "features_dir: .features\napps:\n  - api\n  - web\n",
            encoding="utf-8",
        )
        (repo / ".git").mkdir()
        return repo

    def run_cli(self, args, cwd=None, check=False):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run(
            [sys.executable, "-m", "featuremap", *args],
            cwd=str(cwd or self.tmpdir),
            env=env,
            capture_output=True,
            text=True,
            check=check,
        )
        return result


def load_json(text):
    return json.loads(text)
