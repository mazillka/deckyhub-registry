# DeckyHub registry

The curated list of Decky plugins that [DeckyHub](https://github.com/mazillka/deckyhub-plugin) shows. DeckyHub downloads [`registry/apps.json`](registry/apps.json) from `main` at startup, so a merged change reaches installed copies on their next restart without a DeckyHub release.

## Adding an entry

Each entry needs `id`, `name`, `repo` (`owner/repo`), `category`, a `detect` block matching the plugin's name as Decky reports it, and an `asset` include/exclude filter for picking the right release ZIP. Follow the shape of existing entries.

Every released DeckyHub reads this file, so keep changes additive. A change older versions can't read must bump `schemaVersion` (they reject it and keep their cached or bundled list) rather than reshape version 1. CI validates the file with DeckyHub's own parser and schema test; run it locally from a `deckyhub-plugin` checkout with `DECKYHUB_REGISTRY=../deckyhub-registry/registry/apps.json python -m unittest tests.test_registry_schema`.

Once merged, sync the bundled copy in `deckyhub-plugin` by running `python devtools/sync-registry.py` there, which rewrites its `registry/apps.json` and README's **Bundled repositories** table. Its CI fails until the two match, and DeckyHub versions released before this repository existed still read that copy.

## Your own registry

DeckyHub's **Repositories** → **Custom Registries** accepts `owner/repo` for any repository laid out like this one (`registry/apps.json` on the default branch), or any HTTPS `.json` URL.
