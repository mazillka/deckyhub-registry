---
name: ship-registry
description: Ship what's on the registry's develop branch to main, where every DeckyHub install reads it, merge main back into develop, and write the registry releases' notes. Use when asked to write registry release notes, or when asked to release, ship, publish or promote registry changes, open the develop → main PR, or fix a develop/main conflict.
---

# Shipping the registry

`main` is production: every DeckyHub fetches `registry/apps.json` from it at startup (`REMOTE_REGISTRY_URL` in deckyhub-plugin's `main.py`), the Pages catalog serves `docs/` from it, and the release-index workflow builds `releases.json` and `stats.json` from it every hour. `develop` is where changes land first. Both branches are protected by rulesets ("Protect main": squash only; "Protect develop": squash, or a merge commit for the back-merge), and both need the `validate` check.

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

- The release-index workflow runs on pushes to `main` that touch `apps.json` or `build_release_index.py`, otherwise within the hour: `gh run list --workflow release-index.yml --limit 3`.
- A change to `apps.json` also publishes a new registry release, which DeckyHub reads first: `gh run list --workflow registry-release.yml --limit 3` and `gh release view -R mazillka/deckyhub-registry`.
- `curl -s https://raw.githubusercontent.com/mazillka/deckyhub-registry/release-index/stats.json | head -c 300` shows the new `generatedAt`.
- The catalog at https://mazillka.github.io/deckyhub-registry/ loads (Pages can take a few minutes).

## 5. Write the release notes

Every registry release, `develop` pre-releases too, gets notes a Steam Deck user can read. `registry-release.yml` only writes "registry/apps.json from main at <sha>", so once its run finishes, replace that with `gh release edit <tag> --notes-file <file>`. This covers the release this ship made on `main`, and the `-develop` pre-release made when a PR that changes `apps.json` (a `discover/` PR too) merges into `develop`.

Compare with the previous release of the same channel (tags ending `-develop` are `develop`'s; the others are `main`'s; the first release of a channel has nothing to compare):

```bash
git fetch origin --tags
gh release list --limit 20 --json tagName --jq '.[].tagName'
python - <previous tag> <new tag> <<'PY'
import json, subprocess, sys
load = lambda ref: {a["id"]: a for a in json.loads(subprocess.check_output(["git", "show", f"{ref}:registry/apps.json"]))["apps"]}
old, new = load(sys.argv[1]), load(sys.argv[2])
for i in new.keys() - old.keys(): print(f"+ {new[i]['name']} ({new[i]['repo']}, {new[i]['category']}): {new[i]['description']}")
for i in old.keys() - new.keys(): print(f"- {old[i]['name']} ({old[i]['repo']})")
for i in old.keys() & new.keys():
    changed = [k for k in old[i].keys() | new[i].keys() if old[i].get(k) != new[i].get(k)]
    if changed: print(f"~ {new[i]['name']}: {', '.join(sorted(changed))}")
PY
```

Write it from that list, not from commit titles:

- **Added**: each new plugin as `**Name**: what it does` (its description), grouped by category when there are more than a few.
- **Removed**: each plugin and why, in a few words: archived, its releases stopped working, replaced by a fork (name it).
- **Changed**: what a user notices, such as a new name, category or description, or a fixed install (an `asset` or `releaseTagInclude` fix: "installs the right ZIP again"). Leave out `detect` and other changes nobody sees.
- Plain language, no commit hashes, PR numbers or field names. Leave out empty groups. If nothing a user sees changed, one line says so ("No plugin changes: registry maintenance only.").
- End with how many plugins the list has now (`apps` length).
