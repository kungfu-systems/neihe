# Neihe

Neihe is the course skill for **Neihe Evolution**. It gives learners one short
entry point—`/neihe`—for HermesAgent guidance, project-level Agent rules, and
course templates.

The learner-facing content is Chinese. Repository governance and engineering
documentation are English.

## Current release

The repository starts at `0.1.0-alpha.0`. This first functional release provides
one learner-facing `/neihe` entry point, an on-demand module index, the first
three course modules, the Buildchain lifecycle, a SkillHub dry-run, and a
versioned SkillHub ZIP. The broader course resource library is not yet claimed
complete.

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

The results are:

- `dist/neihe/` — the exact unpacked SkillHub package;
- `dist/neihe-skillhub-<version>.zip` — the upload-ready archive whose root
  contains exactly one `SKILL.md`.

Repository-only files are intentionally excluded. The build also enforces the
current SkillHub package ceiling of 200 files and 10 MiB uncompressed content.

With SkillHub CLI 2026.8.5 or newer installed, run the official local preflight:

```sh
corepack pnpm run skillhub:dry-run
```

This command validates the generated ZIP but does not publish it.

## Publication boundary

SkillHub publication is a separate side effect. After review and authorization:

```sh
skillhub login --key "$SKILLHUB_KEY" --host "https://api.skillhub.cn"
skillhub publish dist/neihe-skillhub-0.1.0-alpha.0.zip --host "https://api.skillhub.cn"
```

Never commit or print the API key. A successful local build or dry-run is not a
published SkillHub release.

## Version authority

`main` is the repository's single content and release mainline, following the
same lightweight model as the Kungfu site repositories. Normal changes arrive
through reviewed feature pull requests; Buildchain builds and validates every
pull request and every push to `main`.

Buildchain keeps SemVer synchronized between `package.json` and `SKILL.md`.
SkillHub versions are immutable publication identities, so each published
version must use a new SemVer and an exact Git tag such as
`v0.1.0-alpha.0`. This repository does not use separate
`dev/alpha/release` branches.
