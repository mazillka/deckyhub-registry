---
name: deckyhub-registry
description: Maintain DeckyHub's curated registry in this repo (registry/apps.json). Use when adding, removing, renaming or editing a registry app, changing the registry schema, or fixing this repo's validate CI.
---

# Maintaining the DeckyHub registry

The curated list is `registry/apps.json` on `main`. DeckyHub ([mazillka/deckyhub-plugin](https://github.com/mazillka/deckyhub-plugin)) downloads it at startup and caches the last good copy. This repo's Pages site (`docs/`: catalog `index.html` and `editor.html`, served from `main` `/docs`) loads it live; the plugin repo's promo page renders it at deploy time.

The plugin repo's checkout sits next to this one: `../deckyhub-plugin`. Clone it with `gh repo clone mazillka/deckyhub-plugin` if it's missing. Follow its [CONTRIBUTING.md](https://github.com/mazillka/deckyhub-plugin/blob/develop/CONTRIBUTING.md#releases): work on a short kebab-case branch, never commit to `main`, one topic per PR, squash-merge.

## Adding, removing or editing an app

1. On a branch, edit `registry/apps.json`. Follow the shape of existing entries and the rules in [CONTRIBUTING.md](https://github.com/mazillka/deckyhub-plugin/blob/develop/CONTRIBUTING.md#adding-a-registry-entry):
   - `id` and `repo` unique; `repo` is a strict `owner/name`.
   - `detect` is `{"type": "decky-plugin", "names": [...]}` with the plugin's name exactly as its `plugin.json` reports it. Check the plugin's repo for that file.
   - `asset.include`/`exclude` pick exactly one release ZIP. Check the repo's latest releases (`gh release view -R owner/name --json assets`) and add `releaseTagInclude` when the repo publishes non-plugin releases too.
   - Keep schema version 1 additive (see "Schema changes" below).
   - Update the README's **Repositories** table to match, in `apps.json` order; `scripts/validate.py` (offline part too) fails until it does.
2. Validate it with the plugin's parser and schema test, from `../deckyhub-plugin` (the test skips without `DECKYHUB_REGISTRY`):

   ```bash
   DECKYHUB_REGISTRY=../deckyhub-registry/registry/apps.json python -m unittest tests.test_registry_schema
   ```

   Then check the entry against GitHub the way DeckyHub will see it (repository, one matching ZIP per channel, the ZIP's `plugin.json` name in `detect.names`, no clashing ids, repos or detect names), from this repo:

   ```bash
   GITHUB_TOKEN=$(gh auth token) python scripts/validate.py
   ```

   Fix every error. Warnings (no stable release, no SHA-256 digest) are worth a look but don't fail CI.

   Always check that every repo link is still valid, not just the entries you touched: `validate.py` checks every entry's `repo` against GitHub. Treat a renamed repo as a fix: update `repo` and every README link to the new `owner/name` (`grep -rl old/name` across the checkout) in its own PR. Treat an archived or missing repo as a question for the user: keep the entry or remove it.
3. Commit, push and open the PR; `main` only accepts squash-merged PRs whose `validate` check passed. Its CI runs both checks. Merge it.

## The weekly CI run failed

CI runs `scripts/validate.py` weekly, because a plugin's new release can break its entry (renamed ZIP, a second ZIP, a changed `plugin.json` name) with no change here. Fix the entry in a PR.

## Schema changes

The plugin repo's `tests/test_registry_schema.py` (this repo's CI runs it from the plugin's `main`) pins schema version 1 for every released DeckyHub:

- A new optional key that older versions safely ignore: add it to `OPTIONAL` in that test (plugin PR first), teach the plugin to use it, then add it to entries.
- Anything else (renaming, retyping, removing, new required meaning): bump `schemaVersion`. Older versions reject the file and keep their cached list, so plan that rollout deliberately.

## Security rules

- Registry entries are trusted project data, but only GitHub release assets of the entry's own `repo` can ever be downloaded.
- Never give an entry a `detect.names` value another entry already uses, and never `DeckyHub`; the plugin drops user-added entries that try, and the official list should never need to.
