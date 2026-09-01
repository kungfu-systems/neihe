import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { unzipSync } from "fflate";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const checkDist = process.argv.includes("--dist");
const sourceRoot = checkDist ? path.join(root, "dist", "neihe") : root;
const skillPath = path.join(sourceRoot, "SKILL.md");
const maxFileCount = 200;
const maxTotalBytes = 10 * 1024 * 1024;

function parseFrontmatter(markdown) {
  const lines = markdown.split(/\r?\n/);
  assert.equal(lines[0], "---", "SKILL.md must start with YAML frontmatter");
  const end = lines.indexOf("---", 1);
  assert.ok(end > 1, "SKILL.md frontmatter must be closed with ---");
  const metadata = {};
  let listKey = "";
  for (const line of lines.slice(1, end)) {
    const list = line.match(/^\s+-\s+(.+)$/);
    if (list && listKey) {
      metadata[listKey].push(list[1].trim());
      continue;
    }
    const entry = line.match(/^([A-Za-z][A-Za-z0-9]*):\s*(.*)$/);
    assert.ok(entry, `unsupported frontmatter line: ${line}`);
    const [, key, rawValue] = entry;
    if (rawValue === "") {
      metadata[key] = [];
      listKey = key;
    } else {
      metadata[key] = rawValue.replace(/^(?:"(.*)"|'(.*)')$/, "$1$2");
      listKey = "";
    }
  }
  return metadata;
}

function digest(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

assert.ok(fs.existsSync(skillPath), `${skillPath} is missing`);
const markdown = fs.readFileSync(skillPath, "utf8");
const metadata = parseFrontmatter(markdown);
const required = ["name", "slug", "version", "displayName"];
const recommended = ["summary", "description", "tags", "license", "homepage"];
for (const key of [...required, ...recommended]) {
  assert.ok(metadata[key] && metadata[key].length !== 0, `frontmatter.${key} is required`);
}
assert.match(metadata.slug, /^[a-z0-9]+(?:-[a-z0-9]+)*$/, "slug must be kebab-case");
assert.ok(metadata.slug.length >= 2 && metadata.slug.length <= 128, "slug length must be 2-128");
assert.equal(metadata.name, metadata.slug, "name and slug must stay aligned for portable installs");
assert.match(metadata.name, /^[a-z0-9]+(?:-[a-z0-9]+)*$/, "name must be portable kebab-case");
assert.match(
  metadata.version,
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/,
  "version must be valid SemVer",
);
assert.equal(metadata.license, "Apache-2.0", "license must match the repository license");
assert.equal(metadata.homepage, "https://github.com/kungfu-systems/neihe");
assert.ok(markdown.includes("assets/AGENTS.md"), "SKILL.md must route to the bundled AGENTS.md template");
assert.ok(markdown.includes("references/module-index.md"), "SKILL.md must route through the module index");
assert.ok(fs.existsSync(path.join(sourceRoot, "assets", "AGENTS.md")), "bundled AGENTS.md template is missing");
assert.ok(fs.existsSync(path.join(sourceRoot, "references", "module-index.md")), "module index is missing");

const moduleIndex = fs.readFileSync(path.join(sourceRoot, "references", "module-index.md"), "utf8");
const modules = [
  "references/modules/seven-day-reset.md",
  "references/modules/shared-brain.md",
  "references/modules/project-agent-rules.md",
];
for (const relative of modules) {
  assert.ok(fs.existsSync(path.join(sourceRoot, relative)), `${relative} is missing`);
  assert.ok(markdown.includes(relative), `SKILL.md must directly reference ${relative}`);
  assert.ok(moduleIndex.includes(path.basename(relative)), `module index must reference ${relative}`);
}

const packageJson = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
assert.equal(metadata.version, packageJson.version, "SKILL.md and package.json versions must match");

if (checkDist) {
  const distributionFiles = ["SKILL.md", "assets/AGENTS.md", "references/module-index.md", ...modules];
  for (const relative of distributionFiles) {
    assert.equal(
      digest(path.join(root, relative)),
      digest(path.join(sourceRoot, relative)),
      `dist/${relative} differs from the source`,
    );
  }

  const archivePath = path.join(root, "dist", `neihe-skillhub-${packageJson.version}.zip`);
  assert.ok(fs.existsSync(archivePath), `${archivePath} is missing`);
  const archiveFiles = unzipSync(new Uint8Array(fs.readFileSync(archivePath)));
  const archiveNames = Object.keys(archiveFiles).sort();
  assert.ok(archiveNames.includes("SKILL.md"), "SkillHub zip must contain root SKILL.md");
  assert.equal(
    archiveNames.filter((name) => name.endsWith("/SKILL.md") || name === "SKILL.md").length,
    1,
    "SkillHub zip must contain exactly one SKILL.md",
  );
  assert.ok(archiveNames.length <= maxFileCount, `SkillHub zip exceeds ${maxFileCount} files`);
  const totalBytes = Object.values(archiveFiles).reduce((total, data) => total + data.length, 0);
  assert.ok(totalBytes <= maxTotalBytes, "SkillHub zip exceeds 10 MiB uncompressed");

  for (const name of archiveNames) {
    const distributed = path.join(sourceRoot, ...name.split("/"));
    assert.ok(fs.existsSync(distributed), `zip contains unexpected file: ${name}`);
    assert.equal(
      crypto.createHash("sha256").update(archiveFiles[name]).digest("hex"),
      digest(distributed),
      `zip/${name} differs from dist/${name}`,
    );
  }

  const expectedArchiveNames = distributionFiles.sort();
  assert.deepEqual(archiveNames, expectedArchiveNames, "zip file list differs from the expected distribution");
  console.log(
    `skillhub zip validation passed: ${archiveNames.length} files, ${totalBytes} bytes uncompressed`,
  );
}

console.log(`neihe ${metadata.version}: ${checkDist ? "distribution" : "source"} validation passed`);
