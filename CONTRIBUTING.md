# Contributing

Use a classified branch and open a pull request against the active development
line. Every commit must use an English Conventional Commit title and include a
Developer Certificate of Origin signoff (`git commit -s`).

Before opening a pull request:

```sh
corepack pnpm install --frozen-lockfile
corepack pnpm run check
corepack pnpm run skillhub:dry-run
```

Keep `SKILL.md` and `package.json` versions identical. Do not edit generated
files under `dist/`; rebuild them. Do not publish to SkillHub from an ordinary
pull request or local verification run.
