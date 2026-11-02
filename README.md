<div align="center">

<img src="docs/favicon.svg" width="72" height="72" alt="">

# DeckyHub registry

**The list of Steam Deck plugins that [DeckyHub](https://github.com/mazillka/deckyhub-plugin) shows on Discover.**

[![validate](https://github.com/mazillka/deckyhub-registry/actions/workflows/ci.yml/badge.svg)](https://github.com/mazillka/deckyhub-registry/actions/workflows/ci.yml)
[![apps](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmazillka%2Fdeckyhub-registry%2Frefs%2Fheads%2Fmain%2Fregistry%2Fapps.json&query=%24.apps.length&label=apps&color=1d75cc)](registry/apps.json)
[![license](https://img.shields.io/github/license/mazillka/deckyhub-registry?color=1d75cc)](LICENSE.md)

[**Browse the catalog**](https://mazillka.github.io/deckyhub-registry/) · [Registry editor](https://mazillka.github.io/deckyhub-registry/editor.html) · [Get DeckyHub](https://github.com/mazillka/deckyhub-plugin/releases/latest) · [Suggest a plugin](https://github.com/mazillka/deckyhub-registry/issues/new)

</div>

> [!CAUTION]
> **DeckyHub only fetches releases from their authors' GitHub repositories. It doesn't make, review or vouch for these plugins and isn't responsible for anything they do to your device or data. Install at your own risk.**

## How it works

DeckyHub downloads [`registry/apps.json`](registry/apps.json) every time it starts and keeps the last good copy for offline use. A change shipped to `main` reaches every installed DeckyHub on its next restart, with no DeckyHub release needed. Each change to the file is also published as a [release](https://github.com/mazillka/deckyhub-registry/releases) with notes on what changed ([registry-release workflow](.github/workflows/registry-release.yml)): DeckyHub 3.1.0 and newer read `apps.json` from the newest one first and fall back to `main`'s file, which older releases read directly.

Testers can see changes before they ship: the opt-in **Registry Channel: Pre-release**, in DeckyHub's own **Manage** window (Quick Access → DeckyHub → **Manage**), reads `develop` instead (the newest registry release, pre-releases included, else `develop`'s file), both its `registry/apps.json` and a release index the same workflow publishes on the `release-index-develop` branch (copied from `main`'s when the two branches match). It falls back to `main`'s files when `develop`'s can't be read. **Stable** is the default.

DeckyHub also reads every listed plugin's recent releases from one file (its 5 newest installable releases, plus the newest stable one if that's older), so it doesn't spend a GitHub API call per plugin (60 an hour without a token). The [release-index workflow](.github/workflows/release-index.yml) runs [`scripts/build_release_index.py`](scripts/build_release_index.py) every hour and whenever `apps.json` changes, and publishes `releases.json` on the [`release-index`](https://github.com/mazillka/deckyhub-registry/tree/release-index) branch. A new release can take up to an hour to show up in DeckyHub.

The same job writes `stats.json` for the [catalog](https://mazillka.github.io/deckyhub-registry/), which shows these on each card and can sort by them:

- **Downloads:** all-time, summed over the plugin's ZIPs (the entry's `asset` filter) across every release. GitHub counts every download of a file, whether from DeckyHub, Decky, a browser or a script, so these are downloads, not installs.
- **Stars:** the repository's GitHub stars.
- **Last updated:** when the release DeckyHub shows came out; over a year ago reads **No release in a year**.
- **Fork:** the repository is a fork; the catalog says of what. Discovery lists a fork only while it's the active one: its original is archived, gone, or hasn't released since.
- **Runs as root:** that release's `plugin.json` has `"root"` in its `flags`, so Decky Loader runs the plugin's backend as the `root` user. It can then read and change anything on the Deck: system files, other plugins, your data. Plenty of plugins need that for real reasons (fan and power control, drivers, VPNs, system settings), so it isn't a red flag by itself, but a bug or a malicious update can do far more harm.
- **Audit warnings:** what [Decky Extended Plugins' automated audit](https://decky-extended-plugins.beallio.com/audit) found in that release (matched by the ZIP's sha256, else by tag), or in a newer pre-release, that's worth a warning: **Blocked by audit** (malware or a broken archive), **Reads private data** (Steam login data, SSH keys, environment secrets), **Changes system startup** (shell profiles, `LD_PRELOAD`, kernel modules, udev rules), **Code not in its repo** (scripts or programs in the ZIP that aren't in its source), **Hidden code** (encoded or packed code), **Skips HTTPS checks**, **Runs downloaded scripts** (`curl … | sh`) and **Known vulnerabilities** (bundled libraries with published CVEs). Routine findings like `sudo`, `mount` or `systemctl` aren't shown: many plugins need them on SteamOS, and **Runs as root** already covers that. The mapping is `WARNINGS` in `build_release_index.py`. A warning isn't proof of harm and no warning isn't proof of safety. When a listed plugin gains a warning, the workflow opens an issue to look at it. If the audit site is down, the stats go out without warnings.

Every plugin ZIP DeckyHub can install is also scanned for viruses with [ClamAV](https://www.clamav.net/), DeckyHub's own releases included. The [virus-scan workflow](.github/workflows/virus-scan.yml) runs [`scripts/virus_scan.py`](scripts/virus_scan.py) every 3 hours over both branches' `releases.json`: it downloads each ZIP it has no report for (every plugin's newest release first, a few GB per run), scans it with that day's signatures, and publishes one report per ZIP as `scans.json` on the [`virus-scans`](https://github.com/mazillka/deckyhub-registry/tree/virus-scans) branch: its sha256, the result (**clean**, **infected** with what ClamAV matched, **incomplete** when the ZIP went past ClamAV's size limits, or **error** with why: the download failed, or ClamAV couldn't read the file or couldn't run), the ClamAV and signature versions, and when. A failed scan never stops the workflow: the ZIP gets an error report and is tried again on the next run, while one that already had a good report keeps it. A ZIP replaced under the same name is scanned again, and reports older than a month are redone with newer signatures. Every listed plugin ends up with a report; each run's log says how many are still waiting. DeckyHub's **Manage** window shows the report for the release you're about to install, or says it hasn't been scanned yet. A report is information, not a block: whether to install is up to you. ClamAV knows Linux malware less well than Windows malware: a clean report isn't proof of safety.

New plugins are found automatically too. Every day the [discover workflow](.github/workflows/discover.yml) runs [`scripts/discover.py`](scripts/discover.py) over two community catalogs, [Decky Plugins Explorer](https://safetzahirovic.github.io/decky-plugins-explorer/)'s nightly list of every public repository with a Decky `plugin.json` and [Decky Extended Plugins](https://decky-extended-plugins.beallio.com/) (the Decky store plus community plugins), and our own GitHub search: repositories tagged or named like Decky plugins (`topic:decky-plugin`, `decky in:name` and a few more) with a `plugin.json` at their root. The search keeps discovery working if both catalogs go away. Plugins that aren't listed yet, pass the same checks as `validate.py` (and have a stable release) and don't look unfinished ([`scripts/quality.py`](scripts/quality.py): a first release under 14 days old, no stars and under 10 downloads, a `0.0.x` version or no description; those are tried again later) are opened as a pull request against `develop`, at most 50 at a time. Nothing is merged without review.

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
| SimpleDeckyTDP | Performance | [aarron-lee/SimpleDeckyTDP](https://github.com/aarron-lee/SimpleDeckyTDP) |
| Bazzite Buddy | Utilities | [ublue-os/decky-bazzite-buddy](https://github.com/ublue-os/decky-bazzite-buddy) |
| PowerControl | Performance | [mengmeet/PowerControl](https://github.com/mengmeet/PowerControl) |
| EmuDeck Retro Library | Game Libraries | [EmuDeck/decky-rom-library](https://github.com/EmuDeck/decky-rom-library) |
| Apps Manager | Utilities | [moi952/decky-apps-manager](https://github.com/moi952/decky-apps-manager) |
| Hiddify VPN | Utilities | [b-ostrov/hiddify-steam-deck-vpn](https://github.com/b-ostrov/hiddify-steam-deck-vpn) |
| To Moon | Utilities | [YukiCoco/ToMoon](https://github.com/YukiCoco/ToMoon) |
| Colores | Customization | [Hooandee/decky-colores](https://github.com/Hooandee/decky-colores) |
| BC-250 FSR4 Launch Options | Performance | [rpf16rj/bc250-steamos-real-toolkit](https://github.com/rpf16rj/bc250-steamos-real-toolkit) |
| Desk of Madness | Utilities | [Marshy-Madness/desk-of-madness](https://github.com/Marshy-Madness/desk-of-madness) |
| OpenSave | Utilities | [Liquid-co/OpenSave](https://github.com/Liquid-co/OpenSave) |
| Xray Decky | Utilities | [VadimOnix/xray-decky](https://github.com/VadimOnix/xray-decky) |
| Legion Go 2 Brightness fix CachyOS | Utilities | [jorgemmsilva/decky-plugin-fix-lego2-brightness-cachyos](https://github.com/jorgemmsilva/decky-plugin-fix-lego2-brightness-cachyos) |
| SteamOS CEC Toolkit | Utilities | [Twsts/steamos-cec-toolkit](https://github.com/Twsts/steamos-cec-toolkit) |
| Sentinel | Game Libraries | [RemakeCode/sentinel](https://github.com/RemakeCode/sentinel) |
| AudioForge | Utilities | [neoseek/AudioForge](https://github.com/neoseek/AudioForge) |
| DeckyEmu | Controllers | [elpendor/deckyemu](https://github.com/elpendor/deckyemu) |
| EnhancedGV | Game Libraries | [Featherwolf/EnhancedGV](https://github.com/Featherwolf/EnhancedGV) |
| GameVault | Game Libraries | [Starkka15/GameVault](https://github.com/Starkka15/GameVault) |
| CheevoDeck | Game Libraries | [FAILINATOR5000/decky-cheevodeck](https://github.com/FAILINATOR5000/decky-cheevodeck) |
| Rabbit Digger Pro | Utilities | [spacemeowx2/rabbit-digger-pro](https://github.com/spacemeowx2/rabbit-digger-pro) |
| Playhub Metadata | Game Libraries | [LoZazaMastro/Playhub-Metadata](https://github.com/LoZazaMastro/Playhub-Metadata) |
| SteamOS LACT Toolkit | Performance | [Twsts/steamos-lact-toolkit](https://github.com/Twsts/steamos-lact-toolkit) |
| Decktation | Utilities | [silverfoxy/decktation](https://github.com/silverfoxy/decktation) |
| Decky OptiScaler | Frame Generation | [danielcamilo1/decky-optiscaler](https://github.com/danielcamilo1/decky-optiscaler) |
| WiFi Optimizer | Utilities | [ArcadaLabs-Jason/WifiOptimizer](https://github.com/ArcadaLabs-Jason/WifiOptimizer) |
| decky-optiscaler | Frame Generation | [xXJSONDeruloXx/decky-optiscaler](https://github.com/xXJSONDeruloXx/decky-optiscaler) |
| LetMeReShade | Utilities | [Cliffback/LetMeReShade](https://github.com/Cliffback/LetMeReShade) |
| DeckyNatpierce | Utilities | [honjow/decky-natpierce](https://github.com/honjow/decky-natpierce) |
| PowerDeck | Performance | [fewtarius/PowerDeck](https://github.com/fewtarius/PowerDeck) |
| Achievement Customizer | Game Libraries | [Hector2242/decky-plugin](https://github.com/Hector2242/decky-plugin) |
| BC250 Toolkit | Launch Options | [Necrosiak/bc250-toolkit-decky](https://github.com/Necrosiak/bc250-toolkit-decky) |
| OneXPlayer Apex Tools | Performance | [srsholmes/onexplayer-apex-bazzite-fixes](https://github.com/srsholmes/onexplayer-apex-bazzite-fixes) |
| cec-mote | Utilities | [xXJSONDeruloXx/cec-mote](https://github.com/xXJSONDeruloXx/cec-mote) |
| Deskflow Decky | Utilities | [bschelst/deskflow-decky](https://github.com/bschelst/deskflow-decky) |
| Apple Music | Utilities | [BrielleG116/decky-apple-music](https://github.com/BrielleG116/decky-apple-music) |
| Playhub Artworks | Game Libraries | [LoZazaMastro/Playhub-Artworks](https://github.com/LoZazaMastro/Playhub-Artworks) |
| SkullKey | Game Libraries | [Necrosiak/SkullKey](https://github.com/Necrosiak/SkullKey) |
| EmuSync | Utilities | [emu-sync/EmuSync-DeckyPlugin](https://github.com/emu-sync/EmuSync-DeckyPlugin) |
| Github Plugin Updater | Utilities | [Steamdeckchecker/Github-Decky-Plugins-Updater](https://github.com/Steamdeckchecker/Github-Decky-Plugins-Updater) |
| Decky Manager | Utilities | [Ciphay/Decky-File-Manager](https://github.com/Ciphay/Decky-File-Manager) |
| eGPUBridge | Utilities | [WowOne987/eGPUBridge](https://github.com/WowOne987/eGPUBridge) |
| CreamDeck | Game Libraries | [Qiming-Liu/CreamDeck](https://github.com/Qiming-Liu/CreamDeck) |
| YouTube Music Player | Utilities | [artistro08/decky-youtube-music-player](https://github.com/artistro08/decky-youtube-music-player) |
| Spotify Connect | Utilities | [Janleyx/decky-spotify-connect](https://github.com/Janleyx/decky-spotify-connect) |
| Launch Options Recipes | Launch Options | [Wurielle/decky-launch-options-recipes](https://github.com/Wurielle/decky-launch-options-recipes) |
| Hibernado | Performance | [xXJSONDeruloXx/hibernado](https://github.com/xXJSONDeruloXx/hibernado) |
| FSR4 Injector | Frame Generation | [Rayekkk/FSR4Injector](https://github.com/Rayekkk/FSR4Injector) |
| BoneCast | Utilities | [Necrosiak/BoneCast](https://github.com/Necrosiak/BoneCast) |
| FileExplorer | Controllers | [60plus/Decky-FileExplorer](https://github.com/60plus/Decky-FileExplorer) |
| YouTube Music | Utilities | [artistro08/decky-youtube-music](https://github.com/artistro08/decky-youtube-music) |
| 4deus Mod | Mod Managers | [ptflp/4deus-mod](https://github.com/ptflp/4deus-mod) |
| Ally DSP | Utilities | [bassobr/decky-ally-dsp](https://github.com/bassobr/decky-ally-dsp) |
| Decky Streamer | Utilities | [deamos/decky-streamer](https://github.com/deamos/decky-streamer) |
| Pixel Faceplate | Utilities | [hodapp/pixel-faceplate](https://github.com/hodapp/pixel-faceplate) |
| Deck Play Badges | Controllers | [Rannius/ControllerXbox](https://github.com/Rannius/ControllerXbox) |
| DeckyTrainers | Utilities | [raygunjohn/decky-trainers](https://github.com/raygunjohn/decky-trainers) |
| DeckCast | Utilities | [dPacc/DeckCast](https://github.com/dPacc/DeckCast) |
| HA Deck | Utilities | [Marker284/ha-deck](https://github.com/Marker284/ha-deck) |
| MotionCueDots | Utilities | [matttt/steamdeck-motion-cues](https://github.com/matttt/steamdeck-motion-cues) |
| HV Launcher | Utilities | [RemakeCode/hv-launcher](https://github.com/RemakeCode/hv-launcher) |
| Finally 3D Game Cases | Game Libraries | [otisabiburada/finally-3d-game-cases-plugin](https://github.com/otisabiburada/finally-3d-game-cases-plugin) |
| Dimensions Toypad | Game Libraries | [SpiderNic96/dimensions-toypad-aio](https://github.com/SpiderNic96/dimensions-toypad-aio) |
| Ally Companion | Customization | [bassobr/Decky-Ally-Companion](https://github.com/bassobr/Decky-Ally-Companion) |
| Decky-Achievement | Game Libraries | [totallynotbakadestroyer/Decky-Achievement](https://github.com/totallynotbakadestroyer/Decky-Achievement) |
| SteamLED | Utilities | [thesirms/SteamLED](https://github.com/thesirms/SteamLED) |
| XG Mobile | Launch Options | [stensmir/xg-mobile-linux](https://github.com/stensmir/xg-mobile-linux) |
| GameThemeMusic-NG | Customization | [cmerino01/GameThemeMusic-NG](https://github.com/cmerino01/GameThemeMusic-NG) |
| Decky RenoDX | Launch Options | [Feelsrat/decky-renodx](https://github.com/Feelsrat/decky-renodx) |
| Decksight Brightness Fix | Utilities | [Xnopyt/decksight-brightness-fix](https://github.com/Xnopyt/decksight-brightness-fix) |
| Quest Compendium | Utilities | [TuriusX/Quest-Compendium-Decky](https://github.com/TuriusX/Quest-Compendium-Decky) |
| Grid Menu | Utilities | [D3SOX/decky-grid-menu](https://github.com/D3SOX/decky-grid-menu) |
| Deckygram | Utilities | [novasound6945/deckygram](https://github.com/novasound6945/deckygram) |
| DeckyBatteryHealth | Performance | [koda-git/DeckyBatteryHealth](https://github.com/koda-git/DeckyBatteryHealth) |
| CriticDeck | Game Libraries | [BrenticusMaximus/CriticDeck](https://github.com/BrenticusMaximus/CriticDeck) |
| Sonnenschein | Game Libraries | [Elias02345/sonnenschein](https://github.com/Elias02345/sonnenschein) |
| YouTube Cast Receiver | Utilities | [artistro08/youtube-cast-receiver](https://github.com/artistro08/youtube-cast-receiver) |
| NetDeck | Utilities | [fewtarius/NetDeck](https://github.com/fewtarius/NetDeck) |
| Snippets | Utilities | [xXJSONDeruloXx/snippets](https://github.com/xXJSONDeruloXx/snippets) |
| DeckyProxy | Performance | [18798aa12/DeckyProxy](https://github.com/18798aa12/DeckyProxy) |
| Armada LSFG Adaptive | Frame Generation | [drewano/armada-lsfg-adaptive](https://github.com/drewano/armada-lsfg-adaptive) |
| Twindeck | Utilities | [Twingate-Community/twindeck](https://github.com/Twingate-Community/twindeck) |
| NetBird VPN | Utilities | [MentallyOverwhelmed/decky-netbird](https://github.com/MentallyOverwhelmed/decky-netbird) |
| E-Ink Faceplate | Game Libraries | [v1k0d3n/monoink](https://github.com/v1k0d3n/monoink) |
| Steam Deck Checker | Utilities | [Steamdeckchecker/Steam-Deck-Checker-Video-Checker](https://github.com/Steamdeckchecker/Steam-Deck-Checker-Video-Checker) |
| FrickPad | Utilities | [xinkiex/Lego2-pad](https://github.com/xinkiex/Lego2-pad) |
| decky-ftpd | Utilities | [codevski/decky-ftpd](https://github.com/codevski/decky-ftpd) |
| DeckyMods | Mod Managers | [18798aa12/DeckyMods](https://github.com/18798aa12/DeckyMods) |
| SpotiDeck | Game Libraries | [Rayekkk/SpotiDeck](https://github.com/Rayekkk/SpotiDeck) |
| YouTube PiP | Utilities | [otisabiburada/decky-video-pip](https://github.com/otisabiburada/decky-video-pip) |
| slipstream | Utilities | [vindeckyy/slipstream](https://github.com/vindeckyy/slipstream) |
| Open Game Launcher | Performance | [MikeAdamRGB/Open-Game-Launcher](https://github.com/MikeAdamRGB/Open-Game-Launcher) |
| Decky Status | Utilities | [sadxpc/steamdeck-discord-status](https://github.com/sadxpc/steamdeck-discord-status) |
| DNS Unblock | Utilities | [Ch1mpleo/decky-dns-unblock](https://github.com/Ch1mpleo/decky-dns-unblock) |
| OMFG | Frame Generation | [xXJSONDeruloXx/omfg-deck](https://github.com/xXJSONDeruloXx/omfg-deck) |
| Nested Desktop | Utilities | [xXJSONDeruloXx/decky-nested-desktop](https://github.com/xXJSONDeruloXx/decky-nested-desktop) |
| GD Item Assistant | Utilities | [lbr88-labs/decky-grim-dawn-item-assistant](https://github.com/lbr88-labs/decky-grim-dawn-item-assistant) |
| 120 Hrtz Refresh Rate | Utilities | [xXJSONDeruloXx/decky-refresh-rate-expander](https://github.com/xXJSONDeruloXx/decky-refresh-rate-expander) |
| Zaparoo | Utilities | [ZaparooProject/zaparoo-decky](https://github.com/ZaparooProject/zaparoo-decky) |
| TunUp | Utilities | [Seraphli/TunUp](https://github.com/Seraphli/TunUp) |
| Start In Library | Game Libraries | [hyprlande/decky_boot_into_library_plugin](https://github.com/hyprlande/decky_boot_into_library_plugin) |
| Deck Muse | Utilities | [gloverthe/deck-muse](https://github.com/gloverthe/deck-muse) |
| VoidDeck | Customization | [AlejandroTenorioC/VoidDeck](https://github.com/AlejandroTenorioC/VoidDeck) |
| ROG Control | Performance | [D0minatorX/rogcontrol](https://github.com/D0minatorX/rogcontrol) |
| CachyOS Update | Utilities | [Felitendo/decky-cachyos-update](https://github.com/Felitendo/decky-cachyos-update) |
| Wake Dispatch | Utilities | [jedwards1230/decky-wake-dispatch](https://github.com/jedwards1230/decky-wake-dispatch) |
| X20 Fixes | Utilities | [ovenham/rog-ally-x20-steamos-speaker-qam-fix](https://github.com/ovenham/rog-ally-x20-steamos-speaker-qam-fix) |
| FriendsBar | Customization | [BrenticusMaximus/FriendsBar](https://github.com/BrenticusMaximus/FriendsBar) |
| AWiM Deck | Utilities | [ergolyam/awim-deck](https://github.com/ergolyam/awim-deck) |
| SSH Switch | Customization | [nicholasyoannou/decky-ssh-switch](https://github.com/nicholasyoannou/decky-ssh-switch) |
| DeckyCache | Performance | [60plus/DeckyCache](https://github.com/60plus/DeckyCache) |
| Controller Changer | Controllers | [lonsdaleite/steamos-controller-changer](https://github.com/lonsdaleite/steamos-controller-changer) |
| CapraLink | Utilities | [CapraAudio/CapraLink](https://github.com/CapraAudio/CapraLink) |
| ChatGPT Community | Utilities | [lbr88-labs/decky-chatgpt-community](https://github.com/lbr88-labs/decky-chatgpt-community) |
| Deck Live | Utilities | [VetTV-Studios/deck-live](https://github.com/VetTV-Studios/deck-live) |
| SteamOS_Friends_activity | Utilities | [AG69075/SteamOS_plugin_Friends_activity](https://github.com/AG69075/SteamOS_plugin_Friends_activity) |
| SDAchievement | Game Libraries | [Wariie/SDAchievement](https://github.com/Wariie/SDAchievement) |
| ScreenTime | Utilities | [jonathan-dd/screentime-decky-plugin](https://github.com/jonathan-dd/screentime-decky-plugin) |
| Steamder | Game Libraries | [otisabiburada/steamder](https://github.com/otisabiburada/steamder) |
| DeckTune | Utilities | [Brick098TheFirst/Decktune](https://github.com/Brick098TheFirst/Decktune) |
| Minimi Town | Game Libraries | [justinca92/minimi-town](https://github.com/justinca92/minimi-town) |
| Hyperion Capture | Utilities | [PatrikTheDev/HyperionCapture](https://github.com/PatrikTheDev/HyperionCapture) |
| KDEck | Utilities | [BRiAn3274/KDEck](https://github.com/BRiAn3274/KDEck) |
| Copyparty | Utilities | [heydemoura/decky-copyparty](https://github.com/heydemoura/decky-copyparty) |
| WiFi BandLock | Utilities | [joemossjr16/Decky-WiFi-BandLock](https://github.com/joemossjr16/Decky-WiFi-BandLock) |
| NetBird | Utilities | [JonathanHohimer/netbird-steamdeck](https://github.com/JonathanHohimer/netbird-steamdeck) |
| GyroParallax | Controllers | [kuchazefira-hub/GyroParallax-Decky-plugin](https://github.com/kuchazefira-hub/GyroParallax-Decky-plugin) |
| Decky Links | Utilities | [kmturley/decky-links](https://github.com/kmturley/decky-links) |
| Discord Lite | Utilities | [lopesleo/Discord-Lite](https://github.com/lopesleo/Discord-Lite) |
| EFI Boot Manager | Utilities | [f-ever/decky-efibootmgr](https://github.com/f-ever/decky-efibootmgr) |
| Decky Tools | Launch Options | [jinzhongjia/decky-tools](https://github.com/jinzhongjia/decky-tools) |
| Decky AI Assistant | Utilities | [Lukather/deck-ai-assistant](https://github.com/Lukather/deck-ai-assistant) |
| Screen Mirror PiP | Utilities | [otisabiburada/decky-screen-mirror](https://github.com/otisabiburada/decky-screen-mirror) |
| Deckyfin | Launch Options | [avivkilloz/deckyfin](https://github.com/avivkilloz/deckyfin) |
| potato-deals | Utilities | [koffcheck/potato-deals](https://github.com/koffcheck/potato-deals) |
| Decky Script Runner | Utilities | [Gr3gorywolf/decky-script-runner](https://github.com/Gr3gorywolf/decky-script-runner) |
| Decky EnvTest | Utilities | [wowitsjack/deckyloader-envtest](https://github.com/wowitsjack/deckyloader-envtest) |
| ROM Sync | Game Libraries | [hrhnick/decky-romsync](https://github.com/hrhnick/decky-romsync) |
| Deckamine | Utilities | [elyarim/Deckamine](https://github.com/elyarim/Deckamine) |
| Network Manager | Utilities | [erik-hasse/network-manager](https://github.com/erik-hasse/network-manager) |
| Decky Task Manager | Utilities | [Feelsrat/decky-task-manager](https://github.com/Feelsrat/decky-task-manager) |
| Colorblind | Performance | [jfrconley/decky-colorblind](https://github.com/jfrconley/decky-colorblind) |
| Ratings Decky | Utilities | [mathdecastilho/ratings-decky](https://github.com/mathdecastilho/ratings-decky) |
| Jedi LSFG-VK | Frame Generation | [sauliiin/Jedi-LSFG-VK](https://github.com/sauliiin/Jedi-LSFG-VK) |
| Video Uploader | Utilities | [SootyOwl/decky-video-uploader](https://github.com/SootyOwl/decky-video-uploader) |
| Second Screen Manager | Performance | [Misticenea/decky-second-screen](https://github.com/Misticenea/decky-second-screen) |
| Side Deck | Utilities | [RhanCandia/decky-sidedeck](https://github.com/RhanCandia/decky-sidedeck) |
| Japanese Lookup | Utilities | [scallsen/japanese-lookup](https://github.com/scallsen/japanese-lookup) |
| DeckyFileExplorer | Utilities | [barrence01/decky-file-explorer](https://github.com/barrence01/decky-file-explorer) |
| RetroAchievements | Game Libraries | [MarioWork/retroachievements-decky](https://github.com/MarioWork/retroachievements-decky) |
| AirDeck | Utilities | [matthieupoupin3704-alt/AirDeck](https://github.com/matthieupoupin3704-alt/AirDeck) |
| TetherBoost | Utilities | [ProblemFactory/decky-plugins](https://github.com/ProblemFactory/decky-plugins) |
| Manifest Downloader | Controllers | [Hintay/decky-manifest-downloader](https://github.com/Hintay/decky-manifest-downloader) |
| DeckPad | Controllers | [thedavidweng/DeckPad](https://github.com/thedavidweng/DeckPad) |
| Game Presence | Utilities | [YAHUkhannan/decky-game-presence](https://github.com/YAHUkhannan/decky-game-presence) |
| StripMine | Customization | [Alyenax/StripMine](https://github.com/Alyenax/StripMine) |
| Shoehorn | Performance | [catvitalio/shoehorn](https://github.com/catvitalio/shoehorn) |
| Rocknix LED Control | Game Libraries | [javierfurus/rocknix-led-control](https://github.com/javierfurus/rocknix-led-control) |
| Decky Cloud Reader | Utilities | [quietgear/decky-cloud-reader](https://github.com/quietgear/decky-cloud-reader) |
| Deck as Capture Card | Utilities | [SnakeTheDev/decky-capture](https://github.com/SnakeTheDev/decky-capture) |
| Navidrome Player | Game Libraries | [abduznik/decky-navidrome-player](https://github.com/abduznik/decky-navidrome-player) |
| Kettle Frame Generation | Frame Generation | [arunoruto/decky-kettle-framegen](https://github.com/arunoruto/decky-kettle-framegen) |
| Renpy Installer | Utilities | [jasmeralia/decky-renpy-installer](https://github.com/jasmeralia/decky-renpy-installer) |
| Immich Uploader | Utilities | [Seruschl/immich-uploader-deck](https://github.com/Seruschl/immich-uploader-deck) |
| Mercury | Launch Options | [adammhal/mercury-odin](https://github.com/adammhal/mercury-odin) |
| DeckyVault | Performance | [AdrianBonpin/deckyvault](https://github.com/AdrianBonpin/deckyvault) |
| ED Journal Monitor | Utilities | [AwaNoodle/ed-journal-monitor-decky](https://github.com/AwaNoodle/ed-journal-monitor-decky) |
| GeForce NOW | Game Libraries | [DimmKirr/decky-gfn](https://github.com/DimmKirr/decky-gfn) |
| Deck Backup | Launch Options | [nicholasyoannou/steamdeck-backup](https://github.com/nicholasyoannou/steamdeck-backup) |
| Close Games Remotely | Utilities | [SafetZahirovic/decky-close-games-remotely](https://github.com/SafetZahirovic/decky-close-games-remotely) |
| LocalSendPlus | Utilities | [Sudashiii/local-send-plus](https://github.com/Sudashiii/local-send-plus) |
| Web Terminal | Utilities | [annacode747/Deck-Web-Terminal](https://github.com/annacode747/Deck-Web-Terminal) |
| Croc Store | Game Libraries | [juliobonon/croc-store](https://github.com/juliobonon/croc-store) |
| XLM Setup | Launch Options | [PofMagicfingers/decky-xlm](https://github.com/PofMagicfingers/decky-xlm) |
| SpinShare | Utilities | [RealDishwash/SpinshareDecky](https://github.com/RealDishwash/SpinshareDecky) |
| DeckyDiscordIntegration | Utilities | [SafetZahirovic/decky-discord-integration](https://github.com/SafetZahirovic/decky-discord-integration) |
| WarpDeck | Utilities | [sonck201/warp-deck](https://github.com/sonck201/warp-deck) |
| DeckyNews | Utilities | [th3pajay/DeckyNews](https://github.com/th3pajay/DeckyNews) |
| VPN & Wake-on-LAN | Utilities | [TochaRude/VPN-WoL-Decky](https://github.com/TochaRude/VPN-WoL-Decky) |
| YASGM | Utilities | [viktor-malieichyk/yasgm](https://github.com/viktor-malieichyk/yasgm) |
| RomM Armada | Game Libraries | [abduznik/romm-armada](https://github.com/abduznik/romm-armada) |
| Travelling Deck | Utilities | [cernoh/travelling-deck](https://github.com/cernoh/travelling-deck) |
| RustDeck | Utilities | [Hintay/decky-rustdeck](https://github.com/Hintay/decky-rustdeck) |
| SteamDB Button | Utilities | [kedMertens/steamdbDeckyButton](https://github.com/kedMertens/steamdbDeckyButton) |
| Just Clock | Customization | [mysteriousHerb/just-clock](https://github.com/mysteriousHerb/just-clock) |
| Audio Switcher | Utilities | [SethPDA/Decky-Audio-Switcher](https://github.com/SethPDA/Decky-Audio-Switcher) |
| Deck as Display | Utilities | [SnakeTheDev/decky-display](https://github.com/SnakeTheDev/decky-display) |
| SteamU | Customization | [Vegetenks/SteamU](https://github.com/Vegetenks/SteamU) |
| decky-window-switcher | Controllers | [voidiz/decky-window-switcher](https://github.com/voidiz/decky-window-switcher) |
| Claudecky | Utilities | [Andarael/claudecky](https://github.com/Andarael/claudecky) |
| SteamProxy | Utilities | [chenpx976/steamproxy](https://github.com/chenpx976/steamproxy) |
| DeckSoundpad | Utilities | [chrpk/decksoundpad](https://github.com/chrpk/decksoundpad) |
| VaporType | Controllers | [dmitrii-galantsev/VaporType](https://github.com/dmitrii-galantsev/VaporType) |
| MoonProfile | Utilities | [egionCode/moon_profile](https://github.com/egionCode/moon_profile) |
| WhisPTT | Controllers | [PsykomantaBrain/WhisPTT](https://github.com/PsykomantaBrain/WhisPTT) |
| Deck Mic Toggle | Utilities | [SpookyJoshua/Deck-Mic-Toggle](https://github.com/SpookyJoshua/Deck-Mic-Toggle) |
| Decky API Caller | Utilities | [ZacTyAdams/Decky-API-Caller](https://github.com/ZacTyAdams/Decky-API-Caller) |
| decky-chen | Game Libraries | [evachxji/decky-chen](https://github.com/evachxji/decky-chen) |
| DeckStream | Performance | [hffgzktbcc-blip/deckstream](https://github.com/hffgzktbcc-blip/deckstream) |
| Deck Curfew | Utilities | [MichielSaey/deck-curfew](https://github.com/MichielSaey/deck-curfew) |
| FNV Settings | Utilities | [qahtni/decky-fnv-settings](https://github.com/qahtni/decky-fnv-settings) |
| Sort by HLTB | Game Libraries | [RedHatter/sort-by-hltb](https://github.com/RedHatter/sort-by-hltb) |
| Codex Remote | Utilities | [VovasaeXranitel/decky-codex-remote](https://github.com/VovasaeXranitel/decky-codex-remote) |
| Freedeck | Utilities | [YunGuiHe/freedeck-plugin-enhancements](https://github.com/YunGuiHe/freedeck-plugin-enhancements) |
| Decky Sunshine | Utilities | [s0t7x/decky-sunshine](https://github.com/s0t7x/decky-sunshine) |
| FusionHUD | Performance | [The412Banner/FusionHUD](https://github.com/The412Banner/FusionHUD) |
| XREAL | Utilities | [kevindurb/xreal-linux](https://github.com/kevindurb/xreal-linux) |
| SDH-Ludusavi | Utilities | [beallio/SDH-Ludusavi](https://github.com/beallio/SDH-Ludusavi) |
| Trailer Hero | Game Libraries | [Ak4ai/decky-trailer-hero](https://github.com/Ak4ai/decky-trailer-hero) |
| XMDeck | Utilities | [PrivateiFox/XMDeck](https://github.com/PrivateiFox/XMDeck) |
| DLSS Enabler | Launch Options | [xXJSONDeruloXx/decky-dlss-enabler](https://github.com/xXJSONDeruloXx/decky-dlss-enabler) |
| Audio Loader | Customization | [DeckThemes/SDH-AudioLoader](https://github.com/DeckThemes/SDH-AudioLoader) |
| WiFi Locker | Utilities | [felipejfc/decky-wifi-locker](https://github.com/felipejfc/decky-wifi-locker) |
| sub-deck | Utilities | [rosakodu/sub-deck](https://github.com/rosakodu/sub-deck) |
| HelixSR Manager | Frame Generation | [PeroTuncay/DeckyHelixSRManager](https://github.com/PeroTuncay/DeckyHelixSRManager) |
| Decky Cloud Save | Utilities | [GedasFX/decky-cloud-save](https://github.com/GedasFX/decky-cloud-save) |
| EmuDeck RomM Sync | Game Libraries | [chenasraf/decky-emudeck-romm](https://github.com/chenasraf/decky-emudeck-romm) |
| HelixSR Decky | Frame Generation | [dawoodtogoo2020-code/HelixSR-Decky](https://github.com/dawoodtogoo2020-code/HelixSR-Decky) |
| Reshadeck | Utilities | [mspeedo/Reshadeck](https://github.com/mspeedo/Reshadeck) |
| LumaDeck | Game Libraries | [jayool/LumaDeck](https://github.com/jayool/LumaDeck) |
| DeckyWindowsTools | Utilities | [namquang93/decky-windows-tool](https://github.com/namquang93/decky-windows-tool) |
| Ally Fix | Controllers | [lonsdaleite/Ally-Fix](https://github.com/lonsdaleite/Ally-Fix) |
| Armada LSFG | Frame Generation | [BakaPute/ArmadaLSFG](https://github.com/BakaPute/ArmadaLSFG) |
| NetMerge | Performance | [FlashWreck/net-merge-decky](https://github.com/FlashWreck/net-merge-decky) |
| Decky Bazaar | Utilities | [danielcamilo1/decky-bazaar](https://github.com/danielcamilo1/decky-bazaar) |
| DeckaTV | Utilities | [jeanbottein/DeckaTV](https://github.com/jeanbottein/DeckaTV) |
| eGPU-Switch | Performance | [TiPSilva/egpu-switch](https://github.com/TiPSilva/egpu-switch) |
| TrailerHero | Game Libraries | [LoZazaMastro/TrailerHero](https://github.com/LoZazaMastro/TrailerHero) |
| HelixSR Muse Plugin | Frame Generation | [enzodiloreto/helixsr-decky-plugin-muse](https://github.com/enzodiloreto/helixsr-decky-plugin-muse) |
| Now Playing | Game Libraries | [LoZazaMastro/Now-Playing](https://github.com/LoZazaMastro/Now-Playing) |
| SDC Benchmark | Performance | [Steamdeckchecker/SDC-Benchmark-](https://github.com/Steamdeckchecker/SDC-Benchmark-) |
| Stormbreaker | Utilities | [FAILINATOR5000/decky-stormbreaker](https://github.com/FAILINATOR5000/decky-stormbreaker) |
| Launch Curtain | Utilities | [LoZazaMastro/Launch-Curtain](https://github.com/LoZazaMastro/Launch-Curtain) |
| Forza DualSense Haptics | Controllers | [woodsi3/forza-dualsense-decky](https://github.com/woodsi3/forza-dualsense-decky) |
| Decky NVIDIA Update | Performance | [moi952/decky-nvidia-update](https://github.com/moi952/decky-nvidia-update) |
| ControllerPriority | Controllers | [FGOD1983/ControllerPriority](https://github.com/FGOD1983/ControllerPriority) |
| LiveTranslator-kun | Utilities | [neatsorg/livetranslate-decky](https://github.com/neatsorg/livetranslate-decky) |
| FSG | Game Libraries | [koua29/decky-fsg](https://github.com/koua29/decky-fsg) |
| Screen Colors | Customization | [PacificSilent/decky-screen-colors](https://github.com/PacificSilent/decky-screen-colors) |
| Decky Recorder | Utilities | [evanjs/decky-recorder-fork](https://github.com/evanjs/decky-recorder-fork) |
| AmneziaWG | Customization | [basuev/amneziawg-deck](https://github.com/basuev/amneziawg-deck) |
| Weather | Utilities | [LoZazaMastro/Weather](https://github.com/LoZazaMastro/Weather) |
| GFG Extreme | Frame Generation | [wavessevaw/GFG-Extreme](https://github.com/wavessevaw/GFG-Extreme) |
| CapyDeploy | Utilities | [lobinuxsoft/decky-capydeploy](https://github.com/lobinuxsoft/decky-capydeploy) |
| Home Assistant MQTT | Performance | [jamesbiederbeck/decky-plugin-homeassistant](https://github.com/jamesbiederbeck/decky-plugin-homeassistant) |
| Uran | Game Libraries | [niwia/Uran](https://github.com/niwia/Uran) |
| SpoutRemotePlay | Utilities | [justjoseorg/SpoutRemotePlay](https://github.com/justjoseorg/SpoutRemotePlay) |
| Armada Box64 | Launch Options | [Ken5998/armada-box64](https://github.com/Ken5998/armada-box64) |
| Playhub Surround | Utilities | [LoZazaMastro/Playhub-Surround](https://github.com/LoZazaMastro/Playhub-Surround) |
| Colorful | Game Libraries | [cedricdelpoux/steam-deck-colorful](https://github.com/cedricdelpoux/steam-deck-colorful) |
| Friend Plaza | Utilities | [otisabiburada/friend-plaza](https://github.com/otisabiburada/friend-plaza) |
| Time Changer | Utilities | [nanwangjkl/decky-time-changer](https://github.com/nanwangjkl/decky-time-changer) |
| Handheld RGB | Controllers | [drewano/decky-handheld-rgb](https://github.com/drewano/decky-handheld-rgb) |
| WaydroidToolbox | Utilities | [linkj-r/decky-waydroid-toolbox](https://github.com/linkj-r/decky-waydroid-toolbox) |
| STT Keyboard | Utilities | [sebastianuxd/decky-stt-keyboard](https://github.com/sebastianuxd/decky-stt-keyboard) |
| WiFi Optimizer Streaming | Utilities | [bassobr/Decky-Wifi-Streaming-Optimizer](https://github.com/bassobr/Decky-Wifi-Streaming-Optimizer) |
| Dolby Digital 5.1 | Utilities | [inthe92/decky-auto-ac3](https://github.com/inthe92/decky-auto-ac3) |
| Decky LLM Translator | Utilities | [Raindropx/Decky-LLM-Translator](https://github.com/Raindropx/Decky-LLM-Translator) |
| Translator LLM | Utilities | [worldnine/Decky-Translator-LLM](https://github.com/worldnine/Decky-Translator-LLM) |
| BC-250 Performance | Performance | [mix3d/bc250-perf-profile-switcher](https://github.com/mix3d/bc250-perf-profile-switcher) |
| CEC Remote | Game Libraries | [tayicknay/deck-cec-remote](https://github.com/tayicknay/deck-cec-remote) |
| Steam Deck HQ | Utilities | [DeckFilter/sdhq-plugin](https://github.com/DeckFilter/sdhq-plugin) |
| Caret Control | Utilities | [woovs-cg/CaretControl](https://github.com/woovs-cg/CaretControl) |
| Armada Installer | Utilities | [mydanyi/armada-installer](https://github.com/mydanyi/armada-installer) |
| PowerTools | Performance | [kmatzen/PowerTools](https://github.com/kmatzen/PowerTools) |
| ROG Xbox Ally X Center | Performance | [VitProg/allycenter](https://github.com/VitProg/allycenter) |
| Add Non-Steam Games | Launch Options | [danielcamilo1/decky-add-non-steam-games](https://github.com/danielcamilo1/decky-add-non-steam-games) |
| Podman Compose | Utilities | [dr1s/decky-podman-compose](https://github.com/dr1s/decky-podman-compose) |
| Decky Macro | Controllers | [olivervbk/decky-macro](https://github.com/olivervbk/decky-macro) |
| Playhub Notifications | Customization | [LoZazaMastro/Playhub-Notifications](https://github.com/LoZazaMastro/Playhub-Notifications) |
| Sharp Filter Selector | Frame Generation | [N3ruk/Sharp-Filter-Selector](https://github.com/N3ruk/Sharp-Filter-Selector) |
| CouchLink | Performance | [Nico8324/CouchLink](https://github.com/Nico8324/CouchLink) |
| DSH 鲸鱼娘桌宠 | Utilities | [228co/dsh-deck-pet](https://github.com/228co/dsh-deck-pet) |
| CarouFix | Customization | [vibekun/CarouFix](https://github.com/vibekun/CarouFix) |
| Wake on Controller | Controllers | [steve133t/decky-wake-on-controller](https://github.com/steve133t/decky-wake-on-controller) |
| Portal | Utilities | [ajustinjames/decky-portal](https://github.com/ajustinjames/decky-portal) |
| SaveWaypoint | Launch Options | [koua29/savewaypoint](https://github.com/koua29/savewaypoint) |
| Decky PiP | Utilities | [Raanh/DeckyPiP](https://github.com/Raanh/DeckyPiP) |
| Bitwarden Vault | Utilities | [Bluin0/DeckyWardenVault](https://github.com/Bluin0/DeckyWardenVault) |
| Deckycord | Controllers | [BwahFox/deckycord](https://github.com/BwahFox/deckycord) |
| Decky Trailers | Customization | [kEnder242/decky-trailers](https://github.com/kEnder242/decky-trailers) |
| decky-QAM | Utilities | [nphil/decky-QAM](https://github.com/nphil/decky-QAM) |
| DraFG | Frame Generation | [DraskeLabs/drafg-decky](https://github.com/DraskeLabs/drafg-decky) |
| Grimoire | Utilities | [Sabissimo/decky-grimoire](https://github.com/Sabissimo/decky-grimoire) |
| DeckOps | Utilities | [aanze/deckops-decky](https://github.com/aanze/deckops-decky) |
| VPN Decky | Utilities | [darkwolf3411/vpn-decky](https://github.com/darkwolf3411/vpn-decky) |
| Audiobookshelf | Controllers | [Zach-Allen/decky-audiobookshelf](https://github.com/Zach-Allen/decky-audiobookshelf) |
| Decky Sound Toasts | Utilities | [K1tsune12/decky-sound-toasts](https://github.com/K1tsune12/decky-sound-toasts) |
| Display Switcher | Utilities | [tomsch/decky-display-switcher](https://github.com/tomsch/decky-display-switcher) |
| DriveLabel | Game Libraries | [DavidDeNicola/decky-drive-label](https://github.com/DavidDeNicola/decky-drive-label) |
| SteamOS Companion | Performance | [tuthan/steamos-companion-decky](https://github.com/tuthan/steamos-companion-decky) |
| Wi-Fi Guard | Utilities | [drewboardman/decky-wifi-guard](https://github.com/drewboardman/decky-wifi-guard) |
| Odin Gyro | Controllers | [razoomnik/decky-odin-gyro](https://github.com/razoomnik/decky-odin-gyro) |
| FHDS Adaptive Triggers | Controllers | [Sci-fi-Borg/fhds-in-decky-loader](https://github.com/Sci-fi-Borg/fhds-in-decky-loader) |
| AllyFanControl | Performance | [PedroReyVarela/AllyFanControl-](https://github.com/PedroReyVarela/AllyFanControl-) |
| AmneziaVpnToggle | Utilities | [tyrypyrking/AmneziaVpnToggle](https://github.com/tyrypyrking/AmneziaVpnToggle) |
| Digimon Time Stranger Team Builder | Controllers | [danielcamilo1/decky-digimon-sts-team-builder](https://github.com/danielcamilo1/decky-digimon-sts-team-builder) |
| Web Browser | Controllers | [Lexodeus/DeckWebBrowser](https://github.com/Lexodeus/DeckWebBrowser) |
| DualSenseDeck | Controllers | [the8055u/DualSenseDeck](https://github.com/the8055u/DualSenseDeck) |
| SyncDeck | Utilities | [infernokun/SyncDeck](https://github.com/infernokun/SyncDeck) |
| STWebSRV | Utilities | [koua29/decky-stwebsrv](https://github.com/koua29/decky-stwebsrv) |
| Local Saves Sync | Game Libraries | [danielcamilo1/decky-local-saves-sync](https://github.com/danielcamilo1/decky-local-saves-sync) |
| Decky Prism | Game Libraries | [shadeov/decky-prism](https://github.com/shadeov/decky-prism) |
| ForzaHorizon-DualSense | Controllers | [ccc007ccc/ForzaHorizon-DualSense-SteamOS](https://github.com/ccc007ccc/ForzaHorizon-DualSense-SteamOS) |
| decky-speed-test-China | Utilities | [hayschan/decky-speed-test-China](https://github.com/hayschan/decky-speed-test-China) |
| Vibrance | Customization | [Pashka0950/vibrance-deck](https://github.com/Pashka0950/vibrance-deck) |
| SSH Helper | Controllers | [thegreat7man/ssh-helper-decky](https://github.com/thegreat7man/ssh-helper-decky) |
| Claude | Utilities | [RyanWReid/claude-deck](https://github.com/RyanWReid/claude-deck) |
| GCM-Launcher | Launch Options | [waynegeng/GCM-Launcher](https://github.com/waynegeng/GCM-Launcher) |
| HyperHDR Toggle | Utilities | [DarkTiengo/decky-hyperhdr-toggle](https://github.com/DarkTiengo/decky-hyperhdr-toggle) |
| decky-ukr-badge | Utilities | [yataktyni/decky-ukr-badge](https://github.com/yataktyni/decky-ukr-badge) |
| AYANEO 3 Companion | Controllers | [Rayekkk/Ayaneo3Companion](https://github.com/Rayekkk/Ayaneo3Companion) |
| Speaker Boost | Utilities | [beaglemoo/decky-speaker-boost](https://github.com/beaglemoo/decky-speaker-boost) |
| RainWave Buddy | Utilities | [BrenticusMaximus/RainWaveBuddy](https://github.com/BrenticusMaximus/RainWaveBuddy) |
| LG Wheel Switch | Controllers | [gabegm/lgwheel-switch](https://github.com/gabegm/lgwheel-switch) |
| OpenCode Web | Utilities | [impuls42/decky-opencode](https://github.com/impuls42/decky-opencode) |
| RetroArch AI Translate | Game Libraries | [wolfg1969/retroarch-ai-translate](https://github.com/wolfg1969/retroarch-ai-translate) |
| NonSteam Sync | Launch Options | [JoseArkadio/decky-nonsteam-sync](https://github.com/JoseArkadio/decky-nonsteam-sync) |
| Clearly Recent | Utilities | [D1zg/clearly-recent](https://github.com/D1zg/clearly-recent) |
| decky-claude | Launch Options | [TuxLux40/decky-claude](https://github.com/TuxLux40/decky-claude) |
| PongBar | Customization | [Alyenax/PongBar](https://github.com/Alyenax/PongBar) |
| eGPU Game Config Swap | Performance | [kanonjeong-ops/gfxprofile](https://github.com/kanonjeong-ops/gfxprofile) |
| DeckyEQ | Utilities | [Rayekkk/DeckyEQ](https://github.com/Rayekkk/DeckyEQ) |
| Reboot to Windows | Utilities | [branchingjade/reboot-to-windows](https://github.com/branchingjade/reboot-to-windows) |
| Azeroth Addons | Controllers | [mdeloughry/azeroth-addons](https://github.com/mdeloughry/azeroth-addons) |
| Mihomo | Customization | [ccc007ccc/mihomo-decky](https://github.com/ccc007ccc/mihomo-decky) |
| DeckBridge | Utilities | [Janleyx/DeckBridge](https://github.com/Janleyx/DeckBridge) |
| AutoWhite | Utilities | [GaricST/AutoWhite](https://github.com/GaricST/AutoWhite) |
| WoW Addons | Launch Options | [bassobr/decky-wowup](https://github.com/bassobr/decky-wowup) |
| BootVolume | Customization | [branchingjade/boot-volume](https://github.com/branchingjade/boot-volume) |
| DeckyAlly | Controllers | [XiaoMinghui/DeckyAlly](https://github.com/XiaoMinghui/DeckyAlly) |
| Hour Notifications | Utilities | [mpcallahan/DeckyHourNotifications](https://github.com/mpcallahan/DeckyHourNotifications) |
| Palia NPC Weekly Gifts Tracker | Utilities | [Mujtaba-Alsaleh/DeckyLoader-Plugin-Palia-NPC-Gift-Tracker](https://github.com/Mujtaba-Alsaleh/DeckyLoader-Plugin-Palia-NPC-Gift-Tracker) |
| Decky AI | Performance | [wankyo83/Decky-AI](https://github.com/wankyo83/Decky-AI) |
| STPlugin | Utilities | [username54321-dotcom/Decky-STPlugin](https://github.com/username54321-dotcom/Decky-STPlugin) |
| WF-Decky | Utilities | [Raanh/WF-Decky](https://github.com/Raanh/WF-Decky) |
| HostSleep | Performance | [Vahn84/decky-hostsleep](https://github.com/Vahn84/decky-hostsleep) |
| Decky Notes | Utilities | [michaelravecabrera/Decky-Notes](https://github.com/michaelravecabrera/Decky-Notes) |
| vkBasalt Manager | Utilities | [Vaddum/vkbasalt-decky](https://github.com/Vaddum/vkbasalt-decky) |
| vpn-decky | Utilities | [Gined44/vpn-decky](https://github.com/Gined44/vpn-decky) |
| decky-gitupdater | Utilities | [quentingeorgel/decky-gitupdater](https://github.com/quentingeorgel/decky-gitupdater) |
| Deck Wrapped | Game Libraries | [Sabissimo/decky-wrapped](https://github.com/Sabissimo/decky-wrapped) |
| DeckyRotateScreen | Utilities | [sanicki/decky-rotate-screen](https://github.com/sanicki/decky-rotate-screen) |
| eGPU Helper | Utilities | [M15t/decky-egpu-helper](https://github.com/M15t/decky-egpu-helper) |
| GPU Picker | Performance | [revenpl/decky-gpu-picker](https://github.com/revenpl/decky-gpu-picker) |
| Decky Flow | Utilities | [Congmeims/Decky-Flow](https://github.com/Congmeims/Decky-Flow) |
| PWMControl | Utilities | [pymmog/decky-pwm-control](https://github.com/pymmog/decky-pwm-control) |
| Decky Position Toasts | Customization | [K1tsune12/decky-position-toasts](https://github.com/K1tsune12/decky-position-toasts) |
| Smart Game Launcher | Utilities | [Marshy-Madness/decky-smart-launcher](https://github.com/Marshy-Madness/decky-smart-launcher) |
| gamescheap | Utilities | [redbrake/gamescheap-decky-plugin](https://github.com/redbrake/gamescheap-decky-plugin) |
| ZeroTier Manager | Utilities | [WuKavin/decky-zerotier-manager](https://github.com/WuKavin/decky-zerotier-manager) |
| Nothing Ear | Performance | [Josemolivaresc/decky-nothing-ear](https://github.com/Josemolivaresc/decky-nothing-ear) |
| Tower Control | Utilities | [matteocrippa/decky-tower-control](https://github.com/matteocrippa/decky-tower-control) |
| Roku Remote | Utilities | [UnforgettableJuan/Decky-Roku-Remote](https://github.com/UnforgettableJuan/Decky-Roku-Remote) |
| Game Optimizer | Performance | [jacobdonahoe/decky-game-optimizer](https://github.com/jacobdonahoe/decky-game-optimizer) |
| Deck Cloud Saves | Game Libraries | [danielcamilo1/decky-cloud-saves](https://github.com/danielcamilo1/decky-cloud-saves) |
| NAS Mount | Game Libraries | [joshmans/decky-nas-mount](https://github.com/joshmans/decky-nas-mount) |
| Reboot Menu | Utilities | [divanikus/decky-reboot-menu](https://github.com/divanikus/decky-reboot-menu) |
| Audio Output Switcher | Utilities | [xenophobentx/decky-audio-switcher](https://github.com/xenophobentx/decky-audio-switcher) |
| Backlog Picker | Game Libraries | [babi723/decky-backlog-picker](https://github.com/babi723/decky-backlog-picker) |
| APDetail | Utilities | [miguellara999/Decky-APDetail](https://github.com/miguellara999/Decky-APDetail) |
| Decky Guide | Utilities | [Logic-mle/decky-guide](https://github.com/Logic-mle/decky-guide) |
| 枫语幕 | Utilities | [Herzzzz/fengyumu-decky](https://github.com/Herzzzz/fengyumu-decky) |
| Decky Player | Utilities | [mdusmb/decky-player](https://github.com/mdusmb/decky-player) |
| SaveLocker | Launch Options | [SkorcherX/SaveLocker-Decky](https://github.com/SkorcherX/SaveLocker-Decky) |
| DSH Chat | Utilities | [gangoogle/decky-dsh-chat](https://github.com/gangoogle/decky-dsh-chat) |
| Dolphin Remote | Controllers | [Ma-Rang/dolphin-remote-decky](https://github.com/Ma-Rang/dolphin-remote-decky) |
| z13-decky | Performance | [timshen91/z13-decky](https://github.com/timshen91/z13-decky) |
| SSH Toggle | Utilities | [NeonPimpZ/decky-ssh-toggle](https://github.com/NeonPimpZ/decky-ssh-toggle) |
| Gyro DSU | Controllers | [christopherl/decky-gyro-dsu](https://github.com/christopherl/decky-gyro-dsu) |
| CCD Control 395 | Performance | [fishersonic/Decky-CCD-Control-395](https://github.com/fishersonic/Decky-CCD-Control-395) |
| Moonlight Sync | Game Libraries | [episode6/moonlight-steam-sync-decky](https://github.com/episode6/moonlight-steam-sync-decky) |
| New Suspend Mode | Controllers | [hileydson/New-Suspend-Mode](https://github.com/hileydson/New-Suspend-Mode) |
| DeckShock4 Toggle | Controllers | [lesnuages/deckshock4-toggle](https://github.com/lesnuages/deckshock4-toggle) |
| MemoryEditor | Utilities | [EdinH86/memoryeditor](https://github.com/EdinH86/memoryeditor) |
| OptiScaler | Frame Generation | [justradical/decky-optiscaler-arm64ec](https://github.com/justradical/decky-optiscaler-arm64ec) |
| jimmys-big-load | Performance | [bellyokelly-ship-it/jbl](https://github.com/bellyokelly-ship-it/jbl) |
| NewFreedeck | Utilities | [ddordie/NewFreedeck-arm64](https://github.com/ddordie/NewFreedeck-arm64) |
| Custom Resolution | Utilities | [shaka456/custom-resolution](https://github.com/shaka456/custom-resolution) |
| Showreel | Customization | [michpalm/showreel](https://github.com/michpalm/showreel) |
| HandheldFanTweaker | Performance | [sleoier/HandheldFanTweaker](https://github.com/sleoier/HandheldFanTweaker) |
| Dock Display | Performance | [Kernien/dock-display](https://github.com/Kernien/dock-display) |
| Steam Games Info | Launch Options | [lonsdaleite/steam-games-info](https://github.com/lonsdaleite/steam-games-info) |
| Profile Launcher | Launch Options | [JDLKMR/Decky-Profile-Launcher-Legacy-Legacy](https://github.com/JDLKMR/Decky-Profile-Launcher-Legacy-Legacy) |
| MusicControl | Utilities | [JobDestroyer/MusicControlol](https://github.com/JobDestroyer/MusicControlol) |
| Nimo RGB | Customization | [fewtarius/nimo-rgb](https://github.com/fewtarius/nimo-rgb) |
| 16:10 Fixes | Utilities | [nucat176/decky-16x10-fixes](https://github.com/nucat176/decky-16x10-fixes) |
| NTFS Mount Keeper | Utilities | [aaron-pengx/ntfs-mount-keeper](https://github.com/aaron-pengx/ntfs-mount-keeper) |
| CachyOS Updater | Utilities | [bassobr/Decky-CachyOS-Updater](https://github.com/bassobr/Decky-CachyOS-Updater) |
| Flight Mode Prep | Performance | [Sabissimo/decky-flight-mode-prep](https://github.com/Sabissimo/decky-flight-mode-prep) |
| Handheld Daemon | Utilities | [honjow/hhd-decky](https://github.com/honjow/hhd-decky) |
| RayNeo Control | Customization | [YifePlayte/RayNeo-Control](https://github.com/YifePlayte/RayNeo-Control) |
| NTS Radio | Utilities | [dylwww/decky-nts](https://github.com/dylwww/decky-nts) |
| Finally Screenshot Sound | Utilities | [otisabiburada/finally-screenshot-sound](https://github.com/otisabiburada/finally-screenshot-sound) |
| SpeechToDeck | Utilities | [rusagent/SpeechToDeck](https://github.com/rusagent/SpeechToDeck) |
| Decky Easytier | Utilities | [Weicoz/decky-easytier](https://github.com/Weicoz/decky-easytier) |
| Browsec Decky | Utilities | [soberdeer/browsec-decky](https://github.com/soberdeer/browsec-decky) |
| decky-onexgpu | Utilities | [anslwy/decky-onexgpu](https://github.com/anslwy/decky-onexgpu) |
| YomiDeck | Utilities | [m1kuk1m/decky-yomi-sync](https://github.com/m1kuk1m/decky-yomi-sync) |
| Decky CustomCloud | Utilities | [DoomTay/Decky-CustomCloud](https://github.com/DoomTay/Decky-CustomCloud) |
| Launch Options Injector | Frame Generation | [PacificSilent/decky-launch-options](https://github.com/PacificSilent/decky-launch-options) |
| Xbox Wireless Helper | Controllers | [m2aadhil/decky-xbox-wireless-helper](https://github.com/m2aadhil/decky-xbox-wireless-helper) |
| Claw EX Control | Performance | [Hardwell-L/decky-claw-ex-control](https://github.com/Hardwell-L/decky-claw-ex-control) |
| PlayTime Tracker | Game Libraries | [alf1995/PlayTime-Tracker](https://github.com/alf1995/PlayTime-Tracker) |

## Where the plugins come from

Plugins are suggested by people (issues and pull requests here) or found by the [discover workflow](.github/workflows/discover.yml) every day, through two community catalogs and our own GitHub search for repositories tagged or named like Decky plugins:

- [Decky Extended Plugins](https://decky-extended-plugins.beallio.com/) by [beallio](https://github.com/beallio), which also publishes a [security audit](https://decky-extended-plugins.beallio.com/audit) of the plugins it lists.
- [Decky Plugins Explorer](https://safetzahirovic.github.io/decky-plugins-explorer/) by [SafetZahirovic](https://github.com/SafetZahirovic), which finds every public GitHub repository with a Decky `plugin.json` every night ([MIT](https://github.com/SafetZahirovic/decky-plugins-explorer/blob/main/LICENSE)).

However a plugin was found, it's only added once `validate.py` passes for it (a stable release, exactly one plugin ZIP, a matching `plugin.json` name), and the discover workflow also skips plugins that look unfinished. Those are automatic checks for a working release; nobody reviews the plugins themselves. Thanks to both catalogs' authors for making their data available.

## Branches

`main` is what DeckyHub reads: every install fetches `registry/apps.json` from it, and the release index is built from it. Changes land on `develop` first: branch from `develop`, open the pull request against `develop`, and merge it with **Squash and merge**. A pull request from `develop` into `main` then ships them; after it's merged, merge `main` back into `develop` with **Create a merge commit**, so the next one doesn't conflict. The discover workflow opens its pull requests against `develop` too. `.githooks/pre-commit` blocks commits on `main` and `develop`; turn it on once per checkout with `git config core.hooksPath .githooks`.

## Adding a plugin

Open a pull request against `develop` that adds one entry to [`registry/apps.json`](registry/apps.json), plus its row in the table above (same order). Not sure about the details? [Open an issue](https://github.com/mazillka/deckyhub-registry/issues/new) with the plugin's repository instead.

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

CI runs on every pull request, on pushes to `main` and `develop`, and weekly because a plugin's new release can break its entry:

- **Schema:** DeckyHub's own parser and v1 schema test. Locally, from a [`deckyhub-plugin`](https://github.com/mazillka/deckyhub-plugin) checkout next to this one:
  ```bash
  DECKYHUB_REGISTRY=../deckyhub-registry/registry/apps.json python -m unittest tests.test_registry_schema
  ```
- **Entries:** `scripts/validate.py` checks each entry the way DeckyHub will see it: the repository exists, each channel's newest release has exactly one ZIP matching `asset`, and that ZIP's `plugin.json` name is in `detect.names`. It also rejects shared ids, repos and detect names, `DeckyHub` as a detect name, and a README table that doesn't match `apps.json`. `--offline` skips the GitHub checks.
  ```bash
  GITHUB_TOKEN=$(gh auth token) python scripts/validate.py
  ```
- **Tests:** `python -m unittest discover -s tests` covers the scripts, and also checks that `apps.json` stays under the 512 KB DeckyHub 3.0.0 and older accept, that the catalog page's script parses, and that `stats.json` keeps every field and warning the DeckyHub people run reads (against deckyhub-plugin's `main`, which CI checks out).

## Your own registry

DeckyHub's **Settings** → **Repositories** → **Custom Registries** accepts `owner/repo` for any repository laid out like this one (`registry/apps.json` on the default branch), or any HTTPS `.json` URL. Fork this repository as a starting point, or build a list in the [registry editor](https://mazillka.github.io/deckyhub-registry/editor.html) and host the file it exports. An added registry can add apps but never replace one from this list.

## Disclaimer

Not affiliated with Valve or the Decky Loader project. This list is collected from public GitHub repositories, and every plugin belongs to its own authors. Entries are checked for a working release, not reviewed for safety: DeckyHub doesn't own, endorse or take responsibility for any listed plugin. Plugins are installed at your own risk, so look at a plugin's repository before you install it.

## License

[GPL-3.0](LICENSE.md). Each listed plugin belongs to its authors and has its own license.
