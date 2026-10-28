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

DeckyHub also reads every listed plugin's recent releases from one file, so it doesn't spend a GitHub API call per plugin (60 an hour without a token). The [release-index workflow](.github/workflows/release-index.yml) runs [`scripts/build_release_index.py`](scripts/build_release_index.py) every 30 minutes and whenever `apps.json` changes, and publishes `releases.json` on the [`release-index`](https://github.com/mazillka/deckyhub-registry/tree/release-index) branch. A new release can take up to 30 minutes to show up in DeckyHub.

The same job writes `stats.json` for the [catalog](https://mazillka.github.io/deckyhub-registry/), which shows these on each card and can sort by them:

- **Downloads:** all-time, summed over the plugin's ZIPs (the entry's `asset` filter) across every release. GitHub counts every download of a file, whether from DeckyHub, Decky, a browser or a script, so these are downloads, not installs.
- **Stars:** the repository's GitHub stars.
- **Last updated:** when the release DeckyHub shows came out; over a year ago reads **No release in a year**.
- **Runs as root:** that release's `plugin.json` has `"root"` in its `flags`, so Decky Loader runs the plugin's backend as the `root` user. It can then read and change anything on the Deck: system files, other plugins, your data. Plenty of plugins need that for real reasons (fan and power control, drivers, VPNs, system settings), so it isn't a red flag by itself, but a bug or a malicious update can do far more harm.

New plugins are found automatically too. Every day the [discover workflow](.github/workflows/discover.yml) runs [`scripts/discover.py`](scripts/discover.py) over [Decky Plugins Explorer](https://safetzahirovic.github.io/decky-plugins-explorer/)'s nightly list of every public repository with a Decky `plugin.json`. Plugins that aren't listed yet and pass the same checks as `validate.py` (and have a stable release) are opened as a pull request, at most 25 at a time. Nothing is merged without review.

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
| DeckSMB | Utilities | [bonorca/DeckSMB](https://github.com/bonorca/DeckSMB) |
| Panel de Control | Performance | [Hooandee/panel-de-control](https://github.com/Hooandee/panel-de-control) |
| DeckyShare | Utilities | [gillrajvir950-wq/deckyshare](https://github.com/gillrajvir950-wq/deckyshare) |
| ThemeDeck | Customization | [BrenticusMaximus/ThemeDeck](https://github.com/BrenticusMaximus/ThemeDeck) |
| Jedi ReFrameShade4All | Frame Generation | [sauliiin/Jedi-ReFrameShade4All](https://github.com/sauliiin/Jedi-ReFrameShade4All) |
| TitleDeck | Customization | [ValentineBSAA/TitleDeck](https://github.com/ValentineBSAA/TitleDeck) |
| Game Theme Music | Customization | [ValentineBSAA/Game-Theme-Music](https://github.com/ValentineBSAA/Game-Theme-Music) |
| ResonaDeck | Utilities | [ValentineBSAA/ResonaDeck](https://github.com/ValentineBSAA/ResonaDeck) |
| Decky Metadata | Game Libraries | [beallio/Decky-Metadata](https://github.com/beallio/Decky-Metadata) |
| Friendeck | Utilities | [panyiwei-home/Friendeck](https://github.com/panyiwei-home/Friendeck) |
| Tender | Game Libraries | [danielcopper/romm-tender](https://github.com/danielcopper/romm-tender) |
| VPN Deck | Utilities | [MrWaip/vpn-deck](https://github.com/MrWaip/vpn-deck) |
| Hydra | Game Libraries | [hydralauncher/decky-hydra-launcher](https://github.com/hydralauncher/decky-hydra-launcher) |
| Proton Pulse | Launch Options | [mdeguzis/decky-proton-pulse](https://github.com/mdeguzis/decky-proton-pulse) |
| Steamcord | Utilities | [Necrosiak/Steamcord](https://github.com/Necrosiak/Steamcord) |
| Decky Music | Utilities | [jinzhongjia/decky-music](https://github.com/jinzhongjia/decky-music) |
| Voxtype | Utilities | [mimed95/decky-voxtype](https://github.com/mimed95/decky-voxtype) |
| MQTT Status | Utilities | [jjuuzzii/decky-ha-mqtt-plugin](https://github.com/jjuuzzii/decky-ha-mqtt-plugin) |
| Game Roulette | Game Libraries | [ayrshirepixels/game-roulette](https://github.com/ayrshirepixels/game-roulette) |
| Prysm | Utilities | [hostsrc/decky-prysm](https://github.com/hostsrc/decky-prysm) |
| Ally Center | Performance | [PixelAddictUnlocked/allycenter](https://github.com/PixelAddictUnlocked/allycenter) |
| XG Mobile Manager | Utilities | [Kentronix57/Decky-Loader-XGMobile-Manager](https://github.com/Kentronix57/Decky-Loader-XGMobile-Manager) |
| Ally Vibe Control | Controllers | [piyush-tyagi-13/ally-vibe-control](https://github.com/piyush-tyagi-13/ally-vibe-control) |
| DeckyZone | Controllers | [DeckFilter/DeckyZone](https://github.com/DeckFilter/DeckyZone) |
| RumbleDeck | Controllers | [dawidmpunkt/RumbleDeck](https://github.com/dawidmpunkt/RumbleDeck) |
| Xone Driver Manager | Controllers | [SavageCore/xone-decky-plugin](https://github.com/SavageCore/xone-decky-plugin) |
| DS5 Bridge | Controllers | [kungaa/DS5-Linux-Decky](https://github.com/kungaa/DS5-Linux-Decky) |
| Steam Achievements | Customization | [AG69075/steamOS_plugin_achievements](https://github.com/AG69075/steamOS_plugin_achievements) |
| Decky UI Restored | Customization | [beallio/Decky-UI-Restored](https://github.com/beallio/Decky-UI-Restored) |
| BootNext | Utilities | [rsore/decky-bootnext](https://github.com/rsore/decky-bootnext) |
| Insignia | Utilities | [stevensnoeijen/decky-insignia](https://github.com/stevensnoeijen/decky-insignia) |
| RetroDECKY | Game Libraries | [Teppichseite/RetroDECKY](https://github.com/Teppichseite/RetroDECKY) |
| RSM-Decky | Customization | [zany130/RSM-Decky](https://github.com/zany130/RSM-Decky) |
| NordVPN | Utilities | [cwtechshiz/nordvpn-decky](https://github.com/cwtechshiz/nordvpn-decky) |
| Decky Vibrance HDR | Customization | [Rayekkk/DeckyVibranceHDR](https://github.com/Rayekkk/DeckyVibranceHDR) |
| Achievement Companion | Utilities | [parvagans/achievement-companion](https://github.com/parvagans/achievement-companion) |
| DeckTools | Game Libraries | [lopesleo/DeckTools](https://github.com/lopesleo/DeckTools) |
| Decky Controller | Controllers | [flexlug/decky-controller](https://github.com/flexlug/decky-controller) |
| Deck Shelves | Customization | [santojon/Deck-Shelves](https://github.com/santojon/Deck-Shelves) |
| Cheat Engine Launcher | Utilities | [LucifersCircle/Decky-Cheat-Engine-Launcher](https://github.com/LucifersCircle/Decky-Cheat-Engine-Launcher) |
| Quick Tab | Customization | [moi952/decky-quick-tab](https://github.com/moi952/decky-quick-tab) |
| CE Decky | Utilities | [goooroooX/CE-Decky](https://github.com/goooroooX/CE-Decky) |
| GabeCubeAura | Customization | [Alyenax/GabeCubeAura](https://github.com/Alyenax/GabeCubeAura) |
| Ambideck | Customization | [michpalm/ambideck](https://github.com/michpalm/ambideck) |
| Bluetooth Order | Utilities | [JediRhymeTrix/decky-bluetooth-order](https://github.com/JediRhymeTrix/decky-bluetooth-order) |
| Legion Go 2 Companion | Performance | [Rayekkk/LegionGo2Companion](https://github.com/Rayekkk/LegionGo2Companion) |
| Elemental DeckKeys | Utilities | [Koutasora/Elemental-DeckKeys](https://github.com/Koutasora/Elemental-DeckKeys) |
| Decky Direct Updater | Utilities | [nukeador/deckyup](https://github.com/nukeador/deckyup) |
| AlarMe | Utilities | [lemossilva/alarme-decky-plugin](https://github.com/lemossilva/alarme-decky-plugin) |
| AutoFlatpaks | Utilities | [jurassicplayer/decky-autoflatpaks](https://github.com/jurassicplayer/decky-autoflatpaks) |
| AutoSuspend | Performance | [jurassicplayer/decky-autosuspend](https://github.com/jurassicplayer/decky-autosuspend) |
| Battery Tracker | Performance | [safijari/steam-deck-battery-tracker](https://github.com/safijari/steam-deck-battery-tracker) |
| Better Keyboard | Utilities | [chenx-dust/BetterKeyboard](https://github.com/chenx-dust/BetterKeyboard) |
| Bluetooth | Utilities | [Outpox/Bluetooth](https://github.com/Outpox/Bluetooth) |
| CheatDeck | Launch Options | [SheffeyG/CheatDeck](https://github.com/SheffeyG/CheatDeck) |
| Crosshair | Customization | [xXJSONDeruloXx/crosshair-plugin](https://github.com/xXJSONDeruloXx/crosshair-plugin) |
| Deck Progress Tracker | Game Libraries | [maroun2/deck-progress-tracker](https://github.com/maroun2/deck-progress-tracker) |
| Deck Settings | Game Libraries | [DeckSettings/decky-game-settings](https://github.com/DeckSettings/decky-game-settings) |
| DeckPass | Utilities | [Teppichseite/DeckPass](https://github.com/Teppichseite/DeckPass) |
| DeckRoulette | Game Libraries | [davocarli/deck-roulette](https://github.com/davocarli/deck-roulette) |
| Decky Clash | Utilities | [chenx-dust/DeckyClash](https://github.com/chenx-dust/DeckyClash) |
| Decky DoT DNS | Utilities | [ohaiibuzzle/decky-dot-dns](https://github.com/ohaiibuzzle/decky-dot-dns) |
| Decky Localsend | Utilities | [MoYoez/Decky-LocalSend](https://github.com/MoYoez/Decky-LocalSend) |
| Decky Ludusavi | Utilities | [GedasFX/decky-ludusavi](https://github.com/GedasFX/decky-ludusavi) |
| Decky Translator | Utilities | [cat-in-a-box/Decky-Translator](https://github.com/cat-in-a-box/Decky-Translator) |
| Decky Zerotier | Utilities | [hyacz/decky-zerotier](https://github.com/hyacz/decky-zerotier) |
| Decky-Clipper | Utilities | [Managor/Decky-Clipper](https://github.com/Managor/Decky-Clipper) |
| Decky-SpoofDPI | Utilities | [ohaiibuzzle/decky-spoof-dpi](https://github.com/ohaiibuzzle/decky-spoof-dpi) |
| DeckyClocker | Utilities | [Jaccident/DeckyClocker](https://github.com/Jaccident/DeckyClocker) |
| DeckySpy | Utilities | [Seraphli/decky-spy](https://github.com/Seraphli/decky-spy) |
| Dimmer Deck | Customization | [chenx-dust/DimmerDeck](https://github.com/chenx-dust/DimmerDeck) |
| Docky | Utilities | [datbird/docky](https://github.com/datbird/docky) |
| Download All | Utilities | [bentemple/decky-download-all](https://github.com/bentemple/decky-download-all) |
| EmuDecky | Game Libraries | [EmuDeck/EmuDecky](https://github.com/EmuDeck/EmuDecky) |
| Game Sync | Utilities | [AkazaRenn/SDH-GameSync](https://github.com/AkazaRenn/SDH-GameSync) |
| Games Prefix Manager | Utilities | [Saad-Alareqi/GamesPrefixManager](https://github.com/Saad-Alareqi/GamesPrefixManager) |
| HLTB for Deck | Game Libraries | [morwy/hltb-for-deck](https://github.com/morwy/hltb-for-deck) |
| HueSync | Customization | [honjow/HueSync](https://github.com/honjow/HueSync) |
| IPv6 Enabler Plugin | Utilities | [spmzt/decky-ipv6](https://github.com/spmzt/decky-ipv6) |
| IsThereAnyDeal for Deck | Game Libraries | [JtdeGraaf/IsThereAnyDeal-DeckyPlugin](https://github.com/JtdeGraaf/IsThereAnyDeal-DeckyPlugin) |
| MagicBlack | Customization | [steam3d/MagicBlackDecky](https://github.com/steam3d/MagicBlackDecky) |
| MagicPods | Utilities | [steam3d/MagicPodsDecky](https://github.com/steam3d/MagicPodsDecky) |
| MoonDeck | Game Libraries | [FrogTheFrog/moondeck](https://github.com/FrogTheFrog/moondeck) |
| Muon | Utilities | [wtlnetwork/muon](https://github.com/wtlnetwork/muon) |
| MuraDeck | Customization | [Moonveil-Kanata/MuraDeck](https://github.com/Moonveil-Kanata/MuraDeck) |
| MuteOnSleep | Utilities | [genc-v/mute-on-sleep](https://github.com/genc-v/mute-on-sleep) |
| Output Manager | Utilities | [joeatethebeans/OutputManager](https://github.com/joeatethebeans/OutputManager) |
| Pause Games | Performance | [wynn1212/SDH-PauseGames](https://github.com/wynn1212/SDH-PauseGames) |
| PlayCount | Game Libraries | [itsOwen/playcount-decky](https://github.com/itsOwen/playcount-decky) |
| PlayTime | Game Libraries | [0u73r-h34v3n/SDH-PlayTime](https://github.com/0u73r-h34v3n/SDH-PlayTime) |
| Quick User Switcher | Utilities | [nikitaclicks/decky-multi-user](https://github.com/nikitaclicks/decky-multi-user) |
| Reroll | Utilities | [kayon/decky-reroll](https://github.com/kayon/decky-reroll) |
| ScreenSaver | Utilities | [xfangfang/DeckyInhibitScreenSaver](https://github.com/xfangfang/DeckyInhibitScreenSaver) |
| ShadowDeck | Utilities | [tikh-iv/ShadowDeck](https://github.com/tikh-iv/ShadowDeck) |
| Steam Status | Utilities | [bschelst/steamstatus-decky](https://github.com/bschelst/steamstatus-decky) |
| SuggestMe | Game Libraries | [lemossilva/suggestme-decky-plugin](https://github.com/lemossilva/suggestme-decky-plugin) |
| TabMaster | Customization | [Tormak9970/TabMaster](https://github.com/Tormak9970/TabMaster) |
| TS3 QuickAccess | Utilities | [ILadis/ts3-qs4sd](https://github.com/ILadis/ts3-qs4sd) |
| TunnelDeck | Utilities | [bkohler616/TunnelDeck](https://github.com/bkohler616/TunnelDeck) |
| VARTA | Game Libraries | [HARd/varta-decky](https://github.com/HARd/varta-decky) |
| Virtual Surround Sound | Utilities | [DeckSettings/decky-virtual-surround-sound](https://github.com/DeckSettings/decky-virtual-surround-sound) |
| Volume Mixer | Utilities | [isiah-lloyd/VolumeMixer-decky](https://github.com/isiah-lloyd/VolumeMixer-decky) |
| XR Gaming | Utilities | [wheaney/decky-XRGaming](https://github.com/wheaney/decky-XRGaming) |

## Credits

Many entries were found through [Decky Extended Plugins](https://decky-extended-plugins.beallio.com/) by [beallio](https://github.com/beallio), a community catalog that also publishes a [security audit](https://decky-extended-plugins.beallio.com/audit) of the plugins it lists. Each entry here was still checked against its own repository's releases before being added.

## Adding a plugin

Open a pull request that adds one entry to [`registry/apps.json`](registry/apps.json), plus its row in the table above (same order). Not sure about the details? [Open an issue](https://github.com/mazillka/deckyhub-registry/issues/new) with the plugin's repository instead.

```json
{
  "id": "decksmb",
  "name": "DeckSMB",
  "description": "Manages a Samba (SMB) file-sharing server on the Steam Deck.",
  "repo": "bonorca/DeckSMB",
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

DeckyHub's **Repositories** → **Custom Registries** accepts `owner/repo` for any repository laid out like this one (`registry/apps.json` on the default branch), or any HTTPS `.json` URL. Fork this repository as a starting point, or build a list in the [registry editor](https://mazillka.github.io/deckyhub-registry/editor.html) and host the file it exports. An added registry can add apps but never replace one from this list.

## Disclaimer

Not affiliated with Valve or the Decky Loader project. This list is collected from public GitHub repositories, and every plugin belongs to its own authors. Entries are checked for a working release, not reviewed for safety: DeckyHub doesn't own, endorse or take responsibility for any listed plugin. Plugins are installed at your own risk, so look at a plugin's repository before you install it.

## License

[GPL-3.0](LICENSE.md). Each listed plugin belongs to its authors and has its own license.
