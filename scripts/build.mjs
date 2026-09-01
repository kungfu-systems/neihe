import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { zipSync } from "fflate";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const output = path.join(root, "dist", "neihe");
const packageJson = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const archive = path.join(root, "dist", `neihe-skillhub-${packageJson.version}.zip`);
const archiveMtime = new Date("2000-01-01T00:00:00.000Z");

function collectFiles(directory) {
  const files = {};
  const visit = (current) => {
    const entries = fs
      .readdirSync(current, { withFileTypes: true })
      .sort((left, right) => left.name.localeCompare(right.name, "en"));
    for (const entry of entries) {
      const absolute = path.join(current, entry.name);
      if (entry.isDirectory()) {
        visit(absolute);
      } else if (entry.isFile()) {
        const relative = path.relative(directory, absolute).split(path.sep).join("/");
        files[relative] = [
          new Uint8Array(fs.readFileSync(absolute)),
          { mtime: archiveMtime },
        ];
      }
    }
  };
  visit(directory);
  return files;
}

fs.rmSync(output, { recursive: true, force: true });
fs.mkdirSync(output, { recursive: true });
fs.copyFileSync(path.join(root, "SKILL.md"), path.join(output, "SKILL.md"));
fs.cpSync(path.join(root, "assets"), path.join(output, "assets"), { recursive: true });
fs.cpSync(path.join(root, "references"), path.join(output, "references"), { recursive: true });

fs.rmSync(archive, { force: true });
fs.writeFileSync(archive, zipSync(collectFiles(output), { level: 9 }));

console.log(`built ${path.relative(root, output)}`);
console.log(`built ${path.relative(root, archive)}`);
