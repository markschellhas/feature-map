"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const packageRoot = path.join(__dirname, "..");
const venvDir = path.join(packageRoot, ".venv");
const isWin = process.platform === "win32";

function venvPython() {
  return isWin
    ? path.join(venvDir, "Scripts", "python.exe")
    : path.join(venvDir, "bin", "python");
}

function venvCli() {
  return isWin
    ? path.join(venvDir, "Scripts", "feature-map.exe")
    : path.join(venvDir, "bin", "feature-map");
}

function run(command, args, opts) {
  return spawnSync(command, args, {
    encoding: "utf8",
    ...opts,
  });
}

function findPython() {
  const candidates = isWin
    ? [
        { command: "py", prefix: ["-3"] },
        { command: "python", prefix: [] },
      ]
    : [
        { command: "python3", prefix: [] },
        { command: "python", prefix: [] },
      ];

  for (const { command, prefix } of candidates) {
    const probe = run(
      command,
      [...prefix, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)"],
    );
    if (probe.status === 0) {
      return { command, prefix };
    }
  }
  return null;
}

function missingPythonMessage() {
  return [
    "feature-map-cli needs Python 3.8+ on PATH to install the CLI.",
    "Install Python, then re-run: npm install -g feature-map-cli",
    "Or skip npm:  pip install feature-map-cli   /   brew install markschellhas/tap/feature-map",
  ].join("\n");
}

function packageVersion() {
  return JSON.parse(fs.readFileSync(path.join(packageRoot, "package.json"), "utf8")).version;
}

module.exports = {
  findPython,
  missingPythonMessage,
  packageRoot,
  packageVersion,
  run,
  venvCli,
  venvDir,
  venvPython,
};
