#!/usr/bin/env node
"use strict";

const fs = require("fs");
const { missingPythonMessage, run, venvCli } = require("../scripts/python");

const cli = venvCli();
if (!fs.existsSync(cli)) {
  console.error("feature-map is not installed in this npm package.");
  console.error("Re-run: npm install -g feature-map-cli");
  console.error(missingPythonMessage());
  process.exit(1);
}

const result = run(cli, process.argv.slice(2), { stdio: "inherit" });
if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status === null ? 1 : result.status);
