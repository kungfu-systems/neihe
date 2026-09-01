import path from "node:path";
import fs from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const packageJson = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const skill = path.join(root, "dist", `neihe-skillhub-${packageJson.version}.zip`);
const result = spawnSync(
  "skillhub",
  ["publish", skill, "--host", "https://api.skillhub.cn", "--dry-run", "--json"],
  { cwd: root, encoding: "utf8" },
);
if (result.error?.code === "ENOENT") {
  console.error("skillhub CLI is not installed; install or update it before running the official dry-run.");
  process.exit(1);
}
if (result.stdout) process.stdout.write(result.stdout);
if (result.stderr) process.stderr.write(result.stderr);
process.exit(result.status ?? 1);
