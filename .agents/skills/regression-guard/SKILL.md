---
name: regression-guard
description: Check a registry change reaches every consumer and breaks nothing installed before calling it done - apps.json and the README table, stats.json and the plugin, site and extension that read it, the schemas, and a test that fails without the fix. Use before finishing or opening a PR for any apps.json edit, scripts change, new stats field or workflow change, and when fixing a bug.
---

# Regression guard

DeckyHub in people's hands, the website and the browser extension all read what this repo publishes. A change is done when every reader still works.

## 1. List every reader of what you changed

- **`registry/apps.json` and the README's Repositories table** move together, in the same order (`scripts/validate.py` fails until they match). A new entry needs the plugin's `plugin.json` name in `detect.names`, one matching ZIP per channel, and a valid `repo`; check it against GitHub, not only the offline tests.
- **`stats.json` and `releases.json` change additively.** Never rename, retype or drop a field. A new field is optional and written only when there is something to say; add it to the written-fields list in `tests/test_docs.py` and to the schemas (`tests/test_schemas.py`), describe it at the top of `scripts/build_release_index.py`, and ship the readers first or together: the plugin's `PluginStats` type and its `OPTIONAL` schema test, deckyhub.com (`plugin_pages.py`) and the extension (`badge-parity`).
- **Badges mirror across surfaces** (informative, equal changes): a new fact in `stats.json` becomes a badge in the plugin, on the site and in the extension, worded the same and never stronger.
- **Workflows** rely on branches, labels and permissions that must already exist on `main`; check before you rely on one. `develop` → `main` is a deliberate release (`ship-registry`).
- **Discovery and submission PRs** are third-party input: read the entry (`review-plugin-submission`), don't trust the description.

## 2. A bug gets a test that fails without the fix

Add it under `tests/`, see it fail on the old code, then pass. A test that was never red proves nothing.

## 3. Run what CI runs

```bash
python -m unittest discover -s tests          # jsonschema must be installed, or test_schemas can't import
GITHUB_TOKEN=$(gh auth token) python scripts/validate.py   # live check; takes minutes, run it in the background
```

A GraphQL change (`releases_query`) is only proven against GitHub: run it for one known repo that has the thing and one that hasn't, and print the result.

## 4. Say what you did not check

End with what was skipped (the live validate run, a reader not updated) and any risk.
