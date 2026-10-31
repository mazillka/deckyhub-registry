---
name: compatibility
description: Keep every installed DeckyHub working when the registry changes. Use before changing anything DeckyHub reads (apps.json, its schema, the release index, stats.json, branch or file names, URLs, workflows that publish them), before shipping develop to main, and whenever a change could affect existing users.
---

# Backward compatibility

DeckyHub is in production. Installed copies, including old releases nobody has updated, fetch this repo's files on their own schedule and can't be changed. A change that breaks them breaks DeckyHub for those users until they update, which many never do. So every change here is checked against **every released DeckyHub**, not only the newest.

## What installed DeckyHub reads

| File | Where | Reader in deckyhub-plugin | Rules |
| --- | --- | --- | --- |
| `registry/apps.json` | `main`, `refs/heads/main/registry/apps.json` | `REMOTE_REGISTRY_URL` in `main.py` | `schemaVersion` 1; every key in `tests/test_registry_schema.py` keeps its name, type and meaning; at most 512 KB, or DeckyHub up to 3.0.0 refuses it and keeps its cached list (newer releases accept 4 MB, `MAX_REMOTE_REGISTRY_BYTES`) |
| `registry/apps.json` | `develop` | `PRERELEASE_REGISTRY_URL`, the opt-in Registry: Pre-release setting | same rules: testers run the same releases |
| `releases.json` | `release-index` branch (`release-index-develop` for pre-release) | `fetchReleaseIndex()` in `src/releases.ts` | `generatedAt`, `releases` keyed by lowercase `owner/name`, REST-shaped releases (`slim()` in `build_release_index.py`), only installable ones (`kept_releases()`: the 5 newest plus the newest stable), so never drop the newest stable or the newest pre-release a channel would pick; over 7 days old, it's ignored |
| `stats.json` | same branches | `fetchPluginStats()`, `PluginStats` in `src/types.ts` | `generatedAt`, `plugins` keyed by lowercase `owner/name`; fields and warning IDs only ever added |

The branch names, file paths and raw.githubusercontent.com URLs are part of this too: never rename or move them. Old DeckyHub releases from before the registry moved here still read the plugin repo's `registry/apps.json`, which no longer exists. That's the kind of break this skill exists to prevent.

## Rules

1. **Additive only.** Add fields, keys, warning IDs and files; never rename, retype, repurpose or drop one that a released DeckyHub reads. To replace something, publish the new one beside the old one, release DeckyHub reading the new one, and drop the old one only once no supported release reads it (ask the user which releases still matter).
2. **Unknown is ignored, missing is handled.** DeckyHub ignores keys it doesn't know and treats a missing optional field as absent. Rely on that only for new optional data, never for something an older release needs.
3. **New behavior is opt-in.** The default stays what users have today (the Registry channel defaults to Stable and falls back to it). Never point existing users at `develop` or test data.
4. **Publishing must not break.** A workflow step that only reports (audit alerts, issues) never blocks writing the index (`continue-on-error`). A run that would publish something thin or broken stops instead, so DeckyHub keeps the last good file (`build_release_index.py` refuses when under half the repos answer).
5. **`main` is production.** Everything lands on `develop` first and reaches `main` only through the `ship-registry` flow.

## Before merging or shipping

- `python -m unittest discover -s tests` with `DECKYHUB_PLUGIN` pointing at a checkout of deckyhub-plugin's `main` (what users run). `tests/test_docs.py` fails if `stats.json` drops a field `PluginStats` reads or a warning ID `AUDIT_WARNINGS` knows, or if `apps.json` gets near 512 KB.
- From `../deckyhub-plugin`: `DECKYHUB_REGISTRY=../deckyhub-registry/registry/apps.json python -m unittest tests.test_registry_schema` (CI runs it from the plugin's `main`).
- For a change to the data's shape, also check the oldest DeckyHub release the user still supports: read its `main.py`/`src/releases.ts` at that tag (`git -C ../deckyhub-plugin show vX.Y.Z:src/releases.ts`), or install it on a Deck (`deck-test` skill in deckyhub-plugin) and point it at the new data.
- Say in the PR what an older DeckyHub sees after the change. "Nothing different" is the usual answer; anything else needs the user's OK first.

## A schema change that can't be additive

Bump `schemaVersion` only with the user's agreement and a plan: older releases reject the new file and keep their cached list forever, so they stop getting new plugins. Usually it's better to keep publishing a v1 file beside the new one.
