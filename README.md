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

DeckyHub downloads [`registry/apps.json`](registry/apps.json) from `main` every time it starts and keeps the last good copy for offline use. A merged change reaches every installed DeckyHub on its next restart, with no DeckyHub release needed.

DeckyHub also reads every listed plugin's recent releases from one file, so it doesn't spend a GitHub API call per plugin (60 an hour without a token). The [release-index workflow](.github/workflows/release-index.yml) runs [`scripts/build_release_index.py`](scripts/build_release_index.py) every 30 minutes and whenever `apps.json` changes, and publishes `releases.json` on the [`release-index`](https://github.com/mazillka/deckyhub-registry/tree/release-index) branch. A new release can take up to 30 minutes to show up in DeckyHub.

The same job writes `stats.json` for the [catalog](https://mazillka.github.io/deckyhub-registry/), which shows these on each card and can sort by them:

- **Downloads:** all-time, summed over the plugin's ZIPs (the entry's `asset` filter) across every release. GitHub counts every download of a file, whether from DeckyHub, Decky, a browser or a script, so these are downloads, not installs.
- **Stars:** the repository's GitHub stars.
- **Last updated:** when the release DeckyHub shows came out; over a year ago reads **No release in a year**.
- **Runs as root:** that release's `plugin.json` has `"root"` in its `flags`, so Decky Loader runs the plugin's backend as the `root` user. It can then read and change anything on the Deck: system files, other plugins, your data. Plenty of plugins need that for real reasons (fan and power control, drivers, VPNs, system settings), so it isn't a red flag by itself, but a bug or a malicious update can do far more harm.

New plugins are found automatically too. Every day the [discover workflow](.github/workflows/discover.yml) runs [`scripts/discover.py`](scripts/discover.py) over two community catalogs: [Decky Plugins Explorer](https://safetzahirovic.github.io/decky-plugins-explorer/)'s nightly list of every public repository with a Decky `plugin.json`, and [Decky Extended Plugins](https://decky-extended-plugins.beallio.com/) (the Decky store plus community plugins). Plugins that aren't listed yet and pass the same checks as `validate.py` (and have a stable release) are opened as a pull request, at most 25 at a time. Nothing is merged without review.

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

## Where the plugins come from

Plugins are suggested by people (issues and pull requests here) or found through two community catalogs, which the [discover workflow](.github/workflows/discover.yml) checks every day:

- [Decky Extended Plugins](https://decky-extended-plugins.beallio.com/) by [beallio](https://github.com/beallio), which also publishes a [security audit](https://decky-extended-plugins.beallio.com/audit) of the plugins it lists.
- [Decky Plugins Explorer](https://safetzahirovic.github.io/decky-plugins-explorer/) by [SafetZahirovic](https://github.com/SafetZahirovic), which finds every public GitHub repository with a Decky `plugin.json` every night ([MIT](https://github.com/SafetZahirovic/decky-plugins-explorer/blob/main/LICENSE)).

However a plugin was found, it's only added once `validate.py` passes for it (a stable release, exactly one plugin ZIP, a matching `plugin.json` name). Those are automatic checks for a working release; nobody reviews the plugins themselves. Thanks to both catalogs' authors for making their data available.

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
