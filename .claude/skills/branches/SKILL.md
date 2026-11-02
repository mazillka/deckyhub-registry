---
name: branches
description: The registry's branch strategy - which branch changes start from and merge into, what the bot and generated branches are, and how to clean up old branches safely. Use when starting a registry change, opening or merging a PR, touching discover/ or release-index branches, or deleting outdated branches. Shipping develop to main is the ship-registry skill.
---

# Branches

| Branch | What it is | Who writes to it |
| --- | --- | --- |
| `main` | Production; the default branch. Every DeckyHub reads `registry/apps.json` from it, Pages serves `docs/` from it, and each change to `apps.json` publishes a `registry-YYYY.MM.DD-N` release. | Release PRs from `develop` (the `ship-registry` skill) |
| `develop` | Where changes land first. DeckyHub's Pre-release registry channel reads it, and each change to `apps.json` publishes a `registry-...-develop` pre-release. | Squashed topic PRs, `discover/` PRs, and the back-merge from `main` |
| `<topic>` | One change each, short kebab-case (`add-<plugin>`, `index-graphql-403`). | You |
| `discover/YYYY-MM-DD-HHMM` | Plugins the daily discover workflow found, as a PR into `develop`. | `discover.yml` |
| `release-index`, `release-index-develop` | `releases.json` and `stats.json` that DeckyHub reads, one orphan commit each, force-pushed by `release-index.yml` from `main` and `develop`. | The workflow only: never commit to, rebase or delete these |
| `virus-scans` | `scans.json`, the ClamAV report for every plugin ZIP in both release indexes, one orphan commit force-pushed by `virus-scan.yml`. DeckyHub's Manage window reads it. | The workflow only: never commit to, rebase or delete it |

Rulesets: "Protect main" allows only **Squash and merge**; "Protect develop" allows squash, or a merge commit for the back-merge. Both block direct pushes and deletion and need the `validate` check. `.githooks/pre-commit` blocks local commits on `main` and `develop`; turn it on once per checkout with `git config core.hooksPath .githooks`.

Never push to `main` or `develop`, and never merge a PR without the user's OK.

## Starting a change

```bash
git fetch origin
git switch -c <topic> origin/develop
gh pr create --base develop
```

One change per PR, merged with **Squash and merge**; its title becomes the commit on `develop`. Registry edits follow the `deckyhub-registry` skill, and changes installed DeckyHub reads (schema, `stats.json` fields) follow the `compatibility` skill.

Getting it to users is the `ship-registry` skill: a squashed `develop` → `main` PR, then a `main` → `develop` back-merge with a merge commit.

## Cleaning up old branches

This repo doesn't delete branches when their PRs merge, so merged topic and `discover/` branches stay on GitHub until someone removes them. Squash merges also leave no merge in the history, so `git branch --merged` misses them. Judge each branch this way:

```bash
git fetch --prune origin
git branch -r
gh pr list --state all --head <branch> --json number,state,title   # MERGED, CLOSED or OPEN
git cherry origin/develop origin/<branch> | grep -c '^+'           # commits whose changes develop lacks
```

- **Safe:** its PR is merged, or it has no commits `develop` lacks. Delete with `git push origin --delete <branch>`, and `git branch -D <branch>` locally.
- **Ask first:** commits `develop` lacks and no merged PR (a closed PR, or none). Show the user what they are (`git log --oneline origin/develop..origin/<branch>`) and whether later work replaced them.
- **Keep:** `main`, `develop`, `release-index`, `release-index-develop`, `virus-scans`, anything with an open PR, and the newest `discover/` branch while its PR is open (the workflow skips plugins listed in closed `discover/` PRs by reading their bodies, not their branches, so closed ones can go).

Deleting a branch can't be undone once its commits are pruned: list what you'll delete and get the user's OK first.
