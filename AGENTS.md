# DeckyHub registry agent guide

Read [README.md](README.md) for the registry format, validation, branching and publishing workflows. Keep registry changes compatible with released DeckyHub versions and validate the affected entries as described there.

Repository skills live only in `.agents/skills/`; `.claude/skills` is a symlink to it for Claude Code (on Windows, run `git config core.symlinks true` before checking out). Edit them there; apply a skill when it is relevant to the task. For multi-file changes use `plan-then-implement`: plan with the strongest model, implement with a cheaper one.

## Branches and releases

The `branches` skill has the shared branch strategy; this repo adds:

- `main` is production: every DeckyHub reads `registry/apps.json` from it, Pages serves `docs/` from it, and each change to `apps.json` publishes a `registry-YYYY.MM.DD-N` release. `develop` feeds DeckyHub's Pre-release registry channel and publishes `registry-...-develop` pre-releases. Both are automatic: nothing here gets a version bump.
- Rulesets "Protect main" (squash only) and "Protect develop" (squash, or a merge commit for the back-merge) require the `validate` check.
- GitHub doesn't delete branches here when their PRs merge, so merged topic and `discover/` branches stay until someone removes them.
- `discover/YYYY-MM-DD-HHMM`: PRs into `develop` with plugins `discover.yml` found. When cleaning up, keep the newest while its PR is open; closed ones can go (the workflow reads closed PRs' bodies, not their branches).
- `ship-plugins/YYYY-MM-DD-HHMM`: `develop`'s plugin list alone as a PR into `main`, from `ship-plugins.yml` or by hand.
- Workflow-owned, never commit to, rebase or delete: `release-index` and `release-index-develop` (`releases.json` and `stats.json`, force-pushed by `release-index.yml`), and `virus-scans` (scan reports, force-pushed by `virus-scan.yml`).
- Shipping `develop` to `main` (everything, or only the plugin list) is the `ship-registry` skill. Registry edits follow the `deckyhub-registry` skill; changes installed DeckyHub reads (schema, `stats.json` fields) follow the `compatibility` skill.
