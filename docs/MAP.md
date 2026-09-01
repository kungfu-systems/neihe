# Project map

- `SKILL.md` — learner-facing Agent Skill contract and SkillHub metadata.
- `references/module-index.md` — progressive-disclosure routing table.
- `references/modules/` — learner-facing course modules loaded only when needed.
- `assets/AGENTS.md` — first reusable course template.
- `.buildchain/buildchain.toml` — version-state and lifecycle authority.
- `.buildchain/*contract-lock.json` — accepted stable and Alpha Buildchain contracts.
- `.github/workflows/build.yml` — thin Buildchain v4 consumer.
- `scripts/check.mjs` — metadata, SemVer, resource, and distribution checks.
- `scripts/build.mjs` — exact SkillHub distribution assembly.
- `scripts/skillhub-dry-run.mjs` — official SkillHub CLI local preflight.
- `dist/neihe/` — generated, untracked SkillHub publication directory.
- `dist/neihe-skillhub-<version>.zip` — generated, upload-ready SkillHub archive.
