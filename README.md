<div align="center">

<img src="docs/favicon.svg" width="72" height="72" alt="">

# DeckyHub registry

**The curated list of Steam Deck plugins that [DeckyHub](https://github.com/mazillka/deckyhub-plugin) shows on Discover.**

[![validate](https://github.com/mazillka/deckyhub-registry/actions/workflows/ci.yml/badge.svg)](https://github.com/mazillka/deckyhub-registry/actions/workflows/ci.yml)
[![apps](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmazillka%2Fdeckyhub-registry%2Frefs%2Fheads%2Fmain%2Fregistry%2Fapps.json&query=%24.apps.length&label=apps&color=1d75cc)](registry/apps.json)
[![license](https://img.shields.io/github/license/mazillka/deckyhub-registry?color=1d75cc)](LICENSE.md)

[**Browse the catalog**](https://mazillka.github.io/deckyhub-registry/) · [Registry editor](https://mazillka.github.io/deckyhub-registry/editor.html) · [Get DeckyHub](https://github.com/mazillka/deckyhub-plugin/releases/latest) · [Suggest a plugin](https://github.com/mazillka/deckyhub-registry/issues/new)

</div>

> [!CAUTION]
> **DeckyHub only fetches releases from their authors' GitHub repositories. It doesn't make, review or vouch for these plugins and isn't responsible for anything they do to your device or data. Install at your own risk.**

## How it works

DeckyHub downloads [`registry/apps.json`](registry/apps.json) from `main` every time it starts and keeps the last good copy for offline use. A merged change reaches every installed DeckyHub on its next restart, with no DeckyHub release needed.

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

## Adding a plugin

Open a pull request that adds one entry to [`registry/apps.json`](registry/apps.json), plus its row in the table above (same order). Not sure about the details? [Open an issue](https://github.com/mazillka/deckyhub-registry/issues/new) with the plugin's repository instead.

```json
{
  "id": "decksmb",
  "name": "DeckSMB",
  "description": "Manages a Samba (SMB) file-sharing server on the Steam Deck.",
  "repo": "chillibeaver/DeckSMB",
  "category": "Utilities",
  "detect": {
    "type": "decky-plugin",
    "names": [
      "DeckSMB"
    ]
  },
  "asset": {
    "include": [
      ".zip"
    ],
    "exclude": [
      "source"
    ]
  }
}
```

| Key | What it's for |
| --- | --- |
| `id` | Unique, lowercase, kebab-case. |
| `name`, `description`, `category` | What Discover shows. Reuse an existing category where one fits. |
| `repo` | The plugin's GitHub `owner/name`. DeckyHub only ever downloads this repository's release assets. |
| `detect.names` | The plugin's name exactly as its `plugin.json` reports it, so DeckyHub recognises it once installed. |
| `asset.include` / `asset.exclude` | Words that pick exactly one release ZIP. |
| `releaseTagInclude` | Optional: only releases whose tag contains this, for repos that publish other releases too. |

Every released DeckyHub reads this file, so keep changes additive. A change older versions can't read must bump `schemaVersion` (they reject it and keep their cached list) rather than reshape version 1.

### Checks

CI runs on every pull request, and weekly because a plugin's new release can break its entry:

- **Schema:** DeckyHub's own parser and v1 schema test. Locally, from a [`deckyhub-plugin`](https://github.com/mazillka/deckyhub-plugin) checkout next to this one:
  ```bash
  DECKYHUB_REGISTRY=../deckyhub-registry/registry/apps.json python -m unittest tests.test_registry_schema
  ```
- **Entries:** `scripts/validate.py` checks each entry the way DeckyHub will see it: the repository exists, each channel's newest release has exactly one ZIP matching `asset`, and that ZIP's `plugin.json` name is in `detect.names`. It also rejects shared ids, repos and detect names, `DeckyHub` as a detect name, and a README table that doesn't match `apps.json`. `--offline` skips the GitHub checks.
  ```bash
  GITHUB_TOKEN=$(gh auth token) python scripts/validate.py
  ```

## Your own registry

DeckyHub's **Repositories** → **Custom Registries** accepts `owner/repo` for any repository laid out like this one (`registry/apps.json` on the default branch), or any HTTPS `.json` URL. Fork this repository as a starting point, or build a list in the [registry editor](https://mazillka.github.io/deckyhub-registry/editor.html). An added registry can add apps but never replace one from this list.

## License

[GPL-3.0](LICENSE.md). Each listed plugin belongs to its authors and has its own license.
