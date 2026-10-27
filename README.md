# DeckyHub registry

> [!CAUTION]
> **DeckyHub only fetches releases from their authors' GitHub repositories. It doesn't make, review or vouch for these plugins and isn't responsible for anything they do to your device or data. Install at your own risk.**

The curated list of Decky plugins that [DeckyHub](https://github.com/mazillka/deckyhub-plugin) shows. DeckyHub downloads [`registry/apps.json`](registry/apps.json) from `main` at startup, so a merged change reaches installed copies on their next restart without a DeckyHub release.

## Repositories

| Tool | Category | Repository |
| --- | --- | --- |
| MAKO Decky | Frame Generation | [eugeniosegala/MAKO](https://github.com/eugeniosegala/MAKO) |
| Decky LSFG-VK | Frame Generation | [xXJSONDeruloXx/decky-lsfg-vk](https://github.com/xXJSONDeruloXx/decky-lsfg-vk) |
| Unifideck | Game Libraries | [mubaraknumann/unifideck](https://github.com/mubaraknumann/unifideck) |
| Decky Framegen | Frame Generation | [xXJSONDeruloXx/Decky-Framegen](https://github.com/xXJSONDeruloXx/Decky-Framegen) |
| Nexus Mods | Mod Managers | [RedRanger14/decky-nexus](https://github.com/RedRanger14/decky-nexus) |
| Decky Proton Launch | Launch Options | [moi952/decky-proton-launch](https://github.com/moi952/decky-proton-launch) |
| Launch Options | Launch Options | [Wurielle/decky-launch-options](https://github.com/Wurielle/decky-launch-options) |
| Non-Steam Badges | Game Libraries | [sebet/decky-nonsteam-badges](https://github.com/sebet/decky-nonsteam-badges) |
| Decky-Undervolt | Performance | [totallynotbakadestroyer/Decky-Undervolt](https://github.com/totallynotbakadestroyer/Decky-Undervolt) |
| ProtonDB Badges | Game Libraries | [bschelst/protondb-decky](https://github.com/bschelst/protondb-decky) |
| CSS Loader | Customization | [DeckThemes/SDH-CssLoader](https://github.com/DeckThemes/SDH-CssLoader) |
| Deck as Controller | Controllers | [jmedina21/deck-as-controller](https://github.com/jmedina21/deck-as-controller) |
| BGFX | Frame Generation | [andrewmd5/decky-bgfx](https://github.com/andrewmd5/decky-bgfx) |
| ThemeHub | Customization | [Kaal31/benderthemes](https://github.com/Kaal31/benderthemes) |
| Spindeck | Customization | [justinca92/spindeck](https://github.com/justinca92/spindeck) |
| Game Glance | Customization | [michpalm/game-glance](https://github.com/michpalm/game-glance) |
| Decky MultiFrameGen | Frame Generation | [MWGIH/DeckyMultiFrameGen](https://github.com/MWGIH/DeckyMultiFrameGen) |
| Finally Achievement Plugin | Customization | [otisabiburada/finally-decky-achievements](https://github.com/otisabiburada/finally-decky-achievements) |
| PS5 Dashboard | Customization | [kromossomom-debug/decky-ps5-dashboard](https://github.com/kromossomom-debug/decky-ps5-dashboard) |
| Xbox Dashboard | Customization | [kromossomom-debug/decky-xbox-dashboard](https://github.com/kromossomom-debug/decky-xbox-dashboard) |
| Loadout | Performance | [cyruzin/loadout](https://github.com/cyruzin/loadout) |
| DeckSMB | Utilities | [chillibeaver/DeckSMB](https://github.com/chillibeaver/DeckSMB) |

## Adding an entry

Each entry needs `id`, `name`, `repo` (`owner/repo`), `category`, a `detect` block matching the plugin's name as Decky reports it, and an `asset` include/exclude filter for picking the right release ZIP. Follow the shape of existing entries.

Every released DeckyHub reads this file, so keep changes additive. A change older versions can't read must bump `schemaVersion` (they reject it and keep their cached list) rather than reshape version 1. CI validates the file with DeckyHub's own parser and schema test; run it locally from a `deckyhub-plugin` checkout with `DECKYHUB_REGISTRY=../deckyhub-registry/registry/apps.json python -m unittest tests.test_registry_schema`.

`scripts/validate.py` then checks each entry against its repository the way DeckyHub will see it: the repository exists, each channel's newest release has exactly one ZIP matching `asset`, and that ZIP's `plugin.json` name is in `detect.names`. It also rejects ids, repos and detect names shared between entries, and `DeckyHub` as a detect name. CI runs it on every pull request and weekly, since a plugin's new release can break its entry. Run it with `GITHUB_TOKEN=$(gh auth token) python scripts/validate.py`; `--offline` skips the GitHub checks.

Add the entry's row to the **Repositories** table above too, in the same order as `registry/apps.json`; `scripts/validate.py` fails until the two match.

## Your own registry

DeckyHub's **Repositories** → **Custom Registries** accepts `owner/repo` for any repository laid out like this one (`registry/apps.json` on the default branch), or any HTTPS `.json` URL.
