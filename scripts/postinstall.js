"use strict";

const fs = require("fs");
const {
  findPython,
  missingPythonMessage,
  packageVersion,
  run,
  venvCli,
  venvDir,
  venvPython,
} = require("./python");

function fail(message, result) {
  if (message) {
    console.error(message);
  }
  if (result && result.stderr) {
    process.stderr.write(result.stderr);
  }
  process.exit(1);
}

const python = findPython();
if (!python) {
  fail(missingPythonMessage());
}

const version = packageVersion();
const py = venvPython();
if (fs.existsSync(py)) {
  const check = run(py, ["-c", "import feature_map; print(feature_map.__version__)"]);
  if (check.status === 0 && check.stdout.trim() === version && fs.existsSync(venvCli())) {
    process.exit(0);
  }
}

const venv = run(python.command, [...python.prefix, "-m", "venv", venvDir], {
  stdio: "inherit",
});
if (venv.status !== 0) {
  fail("Could not create a Python virtualenv for feature-map-cli.");
}

if (!fs.existsSync(py)) {
  fail("Python venv is missing its interpreter. Try reinstalling Python 3.8+.");
}

const ensurepip = run(py, ["-m", "ensurepip", "--upgrade"], { stdio: "inherit" });
if (ensurepip.status !== 0) {
  fail("Could not bootstrap pip in the feature-map-cli virtualenv.");
}

const install = run(
  py,
  ["-m", "pip", "install", "--disable-pip-version-check", `feature-map-cli==${version}`],
  { stdio: "inherit" },
);
if (install.status !== 0) {
  fail(`Could not pip install feature-map-cli==${version}.`);
}

if (!fs.existsSync(venvCli())) {
  fail("pip install succeeded but the feature-map executable is missing.");
}
