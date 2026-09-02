# Project map

- `SKILL.md` — learner-facing Agent Skill contract and SkillHub metadata.
- `references/module-index.md` — progressive-disclosure routing table.
- `references/modules/` — learner-facing course modules loaded only when needed.
- `assets/AGENTS.md` — first reusable course template.
- `assets/shared-brain/` — minimal shared-brain files created without overwriting user content.
- `.buildchain/buildchain.toml` — version-state and lifecycle authority.
- `.buildchain/*contract-lock.json` — accepted stable and Alpha Buildchain contracts.
- `.github/workflows/build.yml` — thin Buildchain v4 consumer.
- `scripts/check.mjs` — metadata, SemVer, resource, and distribution checks.
- `scripts/build.mjs` — exact SkillHub distribution assembly.
- `scripts/skillhub-dry-run.mjs` — official SkillHub CLI local preflight.
- `scripts/shared_brain.py` — learner-facing locator, initializer, doctor, and experience-candidate runtime.
- `tests/test_shared_brain.py` — black-box safety and idempotency tests for the Python runtime.
- `dist/neihe/` — generated, untracked SkillHub publication directory.
- `dist/neihe-skillhub-<version>.zip` — generated, upload-ready SkillHub archive.
