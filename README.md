# DeckyHub registry

The curated list of Decky plugins that [DeckyHub](https://github.com/mazillka/deckyhub-plugin) shows. DeckyHub downloads [`registry/apps.json`](registry/apps.json) from `main` at startup, so a merged change reaches installed copies on their next restart without a DeckyHub release.

## Adding an entry

Each entry needs `id`, `name`, `repo` (`owner/repo`), `category`, a `detect` block matching the plugin's name as Decky reports it, and an `asset` include/exclude filter for picking the right release ZIP. Follow the shape of existing entries.

Every released DeckyHub reads this file, so keep changes additive. A change older versions can't read must bump `schemaVersion` (they reject it and keep their cached or bundled list) rather than reshape version 1. CI validates the file with DeckyHub's own parser and schema test.

`scripts/validate.py` then checks each entry against its repository the way DeckyHub will see it: the repository exists, each channel's newest release has exactly one ZIP matching `asset`, and that ZIP's `plugin.json` name is in `detect.names`. It also rejects ids, repos and detect names shared between entries, and `DeckyHub` as a detect name. CI runs it on every pull request and weekly, since a plugin's new release can break its entry. Run it with `GITHUB_TOKEN=$(gh auth token) python scripts/validate.py`; `--offline` skips the GitHub checks.

Once merged, sync the bundled copy in `deckyhub-plugin` (`registry/apps.json` and README's **Bundled repositories** table); its CI fails until the two match, and DeckyHub versions released before this repository existed still read that copy.

## Your own registry

DeckyHub's Manage & Add → **Custom Registries** accepts `owner/repo` for any repository laid out like this one (`registry/apps.json` on the default branch), or any HTTPS `.json` URL.
