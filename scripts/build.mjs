import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const output = path.join(root, "dist", "neihe");
fs.rmSync(output, { recursive: true, force: true });
fs.mkdirSync(output, { recursive: true });
fs.copyFileSync(path.join(root, "SKILL.md"), path.join(output, "SKILL.md"));
fs.cpSync(path.join(root, "assets"), path.join(output, "assets"), { recursive: true });
console.log(`built ${path.relative(root, output)}`);
