---
name: ship-registry
description: Ship what's on the registry's develop branch to main, where every DeckyHub install reads it, then merge main back into develop. Use when asked to release, ship, publish or promote registry changes, open the develop → main PR, or fix a develop/main conflict.
---

# Shipping the registry

`main` is production: every DeckyHub fetches `registry/apps.json` from it at startup (`REMOTE_REGISTRY_URL` in deckyhub-plugin's `main.py`), the Pages catalog serves `docs/` from it, and the release-index workflow builds `releases.json` and `stats.json` from it every 30 minutes. `develop` is where changes land first. Both branches are protected by rulesets ("Protect main": squash only; "Protect develop": squash, or a merge commit for the back-merge), and both need the `validate` check.

Never push to either branch, and never merge a PR here without the user's OK.

## 1. Check develop is ready

```bash
git fetch origin
git log --oneline origin/main..origin/develop
gh pr list --base develop --state open
```

Something waiting on `develop` with nothing open against it means it's ready. Run the checks on `origin/develop` before asking:

```bash
git switch --detach origin/develop
python -m unittest discover -s tests
GITHUB_TOKEN=$(gh auth token) python scripts/validate.py
```

Look for anything that would break installed DeckyHub: a removed or renamed field in `apps.json`'s schema or in `stats.json` (the schema rules are in the `deckyhub-registry` skill), and workflow changes that rely on a branch, label or permission that doesn't exist yet.

## 2. Open the release PR

```bash
gh pr create --base main --head develop --title "release: registry $(date -u +%Y-%m-%d)" --body "<the commits from step 1, one line each>"
```

Wait for CI. Once the user approves, merge it with **Squash and merge**: `main` allows nothing else.

## 3. Merge main back into develop

The squash makes a commit `develop` doesn't have, so the next release PR conflicts unless `develop` gets it:

```bash
gh pr create --base develop --head main --title "chore: merge main back into develop ($(date -u +%Y-%m-%d))" --body "Back-merge after the release, so the next develop → main PR doesn't conflict."
```

Merge this one with **Create a merge commit**, the one PR that isn't squashed.

## 4. Check it reached people

- The release-index workflow runs on pushes to `main` that touch `apps.json` or `build_release_index.py`, otherwise within 30 minutes: `gh run list --workflow release-index.yml --limit 3`.
- `curl -s https://raw.githubusercontent.com/mazillka/deckyhub-registry/release-index/stats.json | head -c 300` shows the new `generatedAt`.
- The catalog at https://mazillka.github.io/deckyhub-registry/ loads (Pages can take a few minutes).
