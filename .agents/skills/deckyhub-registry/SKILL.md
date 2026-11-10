---
name: deckyhub-registry
description: Maintain DeckyHub's plugin registry in this repo (registry/apps.json). Use when adding, removing, renaming or editing a registry app, changing the registry schema, or fixing this repo's validate CI.
---

# Maintaining the DeckyHub registry

DeckyHub's plugin list is `registry/apps.json` on `main`. DeckyHub ([mazillka/deckyhub-plugin](https://github.com/mazillka/deckyhub-plugin)) downloads it at startup and caches the last good copy. This repo's Pages site (`docs/`: catalog `index.html` and `editor.html`, served from `main` `/docs`) loads it live; the plugin repo's promo page renders it at deploy time.

The plugin repo's checkout sits next to this one: `../deckyhub-plugin`. Clone it with `gh repo clone mazillka/deckyhub-plugin` if it's missing. Follow its [CONTRIBUTING.md](https://github.com/mazillka/deckyhub-plugin/blob/develop/CONTRIBUTING.md#releases): work on a short kebab-case branch from `develop`, never commit to `main` or `develop`, one topic per PR against `develop`, squash-merge. A `develop` → `main` PR ships to users (see the README's Branches section).

DeckyHub is in production: anything it reads (`apps.json`, the release index, `stats.json`, their branches and URLs) only changes additively. Follow the `compatibility` skill before changing any of it.

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
3. Commit, push and open the PR against `develop`; it only accepts squash-merged PRs whose `validate` check passed. Its CI runs both checks. Merge it, check the notes of the `-develop` pre-release that merge publishes (step 5 of the `ship-registry` skill), then ship with a `develop` → `main` PR.

## Discovery PRs

`.github/workflows/discover.yml` runs `scripts/discover.py` every three hours at 41 minutes past the hour (UTC), from `develop`. It reads three public sources: Decky Plugins Explorer, Decky Extended Plugins and our own GitHub repository search. When approved Reddit Data API access is configured, it also reads recent post links/text and up to 20 top-level comments and their replies on each of 20 posts from r/deckyloader using `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` GitHub Actions secrets. Without both secrets Reddit is skipped cleanly; source failures never stop the others. Reddit candidates must have a root `plugin.json`, like GitHub search results. It checks each unlisted repo for a release ZIP whose `plugin.json` name is free, skips the ones `scripts/quality.py` says look unfinished, adds the rest, and opens a `discover/<date>` PR against `develop`, dispatching CI on it. Bots cannot approve their own PRs: review each entry's name, category and description, and never merge without the user's OK. Never print or check in Reddit credentials. Try it locally with `GITHUB_TOKEN=$(gh auth token) python scripts/discover.py --dry-run --limit 5`.

## Release index and stats

`.github/workflows/release-index.yml` runs `scripts/build_release_index.py` every hour (and on pushes that change `apps.json` or the script). It force-pushes two files to the orphan `release-index` branch: `releases.json` (each repo's 5 newest installable releases plus the newest stable one if it's older, `kept_releases()`, which DeckyHub reads instead of calling the GitHub API per repo) and `stats.json` (downloads, stars, last release date, runs-as-root and audit `warnings`/`prereleaseWarnings` per repo, shown on Discover and the catalog page). The same workflow publishes `develop`'s index on `release-index-develop` for DeckyHub's opt-in Registry: Pre-release setting; when `develop`'s `apps.json` and `scripts/` match `main`'s, it copies `main`'s index instead of building it again, to save the shared token's API budget. A repo missing from them just falls back to the API in DeckyHub, so a failed run is worth fixing but breaks nothing. Never push to `release-index` by hand.

DeckyHub in people's hands reads both files, so changes to them stay additive: never rename or drop a field. `tests/test_docs.py` checks this against the plugin's default branch in CI (`DECKYHUB_PLUGIN`; locally it skips unless `../deckyhub-plugin` sits beside the checkout or the variable points at one). Audit warnings, and the issue the workflow opens when they grow, are in the `audit-warnings` skill.

## Unfinished plugins already listed

`GITHUB_TOKEN=$(gh auth token) python scripts/quality.py` lists registry entries that look unfinished, with the reason. It only reports: ask the user before removing any, since people may have them installed.

## CI

`ci.yml` runs on pushes to `main` and `develop`, on every PR and weekly: the plugin's schema test, `python -m unittest discover -s tests` (which includes `node --check` on every `<script>` in `docs/*.html`, so a typo can't leave the catalog stuck on "Loading…", and the stats contract above) and `scripts/validate.py`. Shipping `develop` to `main` is in the `ship-registry` skill.

## The weekly CI run failed

CI runs `scripts/validate.py` weekly, because a plugin's new release can break its entry (renamed ZIP, a second ZIP, a changed `plugin.json` name) with no change here. Fix the entry in a PR.

## Schema changes

The plugin repo's `tests/test_registry_schema.py` (this repo's CI runs it from the plugin's `main`) pins schema version 1 for every released DeckyHub:

- A new optional key that older versions safely ignore: add it to `OPTIONAL` in that test (plugin PR first), teach the plugin to use it, then add it to entries.
- Anything else (renaming, retyping, removing, new required meaning): bump `schemaVersion`. Older versions reject the file and keep their cached list, so plan that rollout deliberately.

## Security rules

- Registry entries are trusted project data, but only GitHub release assets of the entry's own `repo` can ever be downloaded.
- Never give an entry a `detect.names` value another entry already uses, and never `DeckyHub`; the plugin drops user-added entries that try, and the official list should never need to.
