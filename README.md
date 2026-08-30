# Neihe

Neihe is the course skill for **Neihe Evolution**. It gives learners one short
entry point—`/neihe`—for HermesAgent guidance, project-level Agent rules, and
course templates.

The learner-facing content is Chinese. Repository governance and engineering
documentation are English.

## Current release

The repository starts at `0.1.0-alpha.0`. This is an initialization release:
the metadata, Buildchain lifecycle, SkillHub dry-run, and first `AGENTS.md`
template are present, but the broader course resource library is not yet
claimed complete.

## Local verification

Requirements: Node.js 22.14 or later, Corepack, and pnpm 11.20.0.

```sh
corepack pnpm install --frozen-lockfile
corepack pnpm run check
corepack pnpm run doctor
```

Build the exact SkillHub directory:

```sh
corepack pnpm run build
```

The result is `dist/neihe/`. Repository-only files are intentionally excluded.

With SkillHub CLI 2026.8.5 or newer installed, run the official local preflight:

```sh
corepack pnpm run skillhub:dry-run
```

This command validates and packages the skill but does not publish it.

## Publication boundary

SkillHub publication is a separate side effect. After review and authorization:

```sh
skillhub login --key "$SKILLHUB_KEY" --host "https://api.skillhub.cn"
skillhub publish dist/neihe --host "https://api.skillhub.cn"
```

Never commit or print the API key. A successful local build or dry-run is not a
published SkillHub release.

## Version authority

Buildchain manages SemVer in both `package.json` and `SKILL.md`. The active
development line is `dev/v0/v0.1`; future Alpha and stable promotion targets
are `alpha/v0/v0.1` and `release/v0/v0.1`.
