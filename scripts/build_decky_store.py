#!/usr/bin/env python3
"""Writes this registry in the official Decky plugin store's format, for Decky Loader's Custom store.

Usage: build_decky_store.py [--prereleases] RELEASES_JSON OUT_DIR [STATS_JSON]

RELEASES_JSON is the releases.json build_release_index.py published; registry/apps.json says which plugins there
are. OUT_DIR gets what Decky Loader fetches from a custom store URL (Settings > General > Store > Custom):

  index.html       the plugin list (GET <store url>): [{id, name, author, description, tags, image_url, versions}]
  plugins.json     the same list, for people and other tools
  versions         the update check (GET <store url>/versions): {plugin name: [version, sha256, zip url]}

DeckyHub's website workflow (deckyhub-plugin's pages.yml) serves it as https://deckyhub.com/store, the URL to give Decky. (GitHub Pages sends /store to /store/,
which is index.html: a JSON body is fine, Decky parses it whatever the file is called.)

Only stable releases (with --prereleases, pre-releases too: the store for DeckyHub's Pre-release registry on develop), and only ZIPs GitHub published a SHA-256 for: Decky checks that hash before it installs, and
a version without one would install unchecked. Each version's `artifact` is the GitHub release ZIP itself.
A plugin's name, author, tags and image come from the plugin.json inside its newest ZIP, because Decky matches
installed plugins to the store by that name.

The store's format has no field for audit warnings or scans, so with STATS_JSON (the stats.json build_release_index.py
published) they go where Decky shows text: tags (`root`, `ai-assisted`, `deckyhub-warning`) and one line at the end
of the description with the warnings and the plugin's page on deckyhub.com, which has the full report and scans.
"""
import functools
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from validate import REGISTRY, channel_releases, load_registry_apps, matching_assets, plugin_version, zip_plugin_files

VERSION = re.compile(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?")  # what Decky's update check accepts as a version
SHA256 = re.compile(r"sha256:([0-9a-f]{64})")


def zip_of(entry: dict, release: dict) -> dict | None:
    """The release's plugin ZIP that has a published SHA-256, or None."""
    return next((asset for asset in matching_assets(entry, release) if SHA256.fullmatch(str(asset.get("digest")))), None)


def version_of(release: dict, own: str | None) -> str | None:
    """The version Decky should call this release: the plugin's own when the index read it, else the tag's."""
    for candidate in (own, release.get("pluginVersion"), release.get("tag_name")):
        if candidate and (found := VERSION.search(str(candidate))):
            return found.group()
    return None


PAGE = "https://deckyhub.com/plugins/{}.html"


def deckyhub_line(entry: dict, stats: dict | None) -> str:
    """The line DeckyHub adds to a description: what its audit found, and where the full report is."""
    warnings = (stats or {}).get("warnings") or []
    if warnings:
        found = f"warnings: {', '.join(warnings)}"
    else:
        found = "no audit warnings" if stats is not None else "audit and scans"
    return f"DeckyHub: {found}. Details: {PAGE.format(entry['id'])}"


def deckyhub_tags(stats: dict | None) -> list[str]:
    stats = stats or {}
    return [tag for tag, on in (("root", stats.get("root") is True), ("ai-assisted", bool(stats.get("ai"))), ("deckyhub-warning", bool(stats.get("warnings")))) if on]


def store_plugin(entry: dict, releases: list[dict], number: int, manifest, stats: dict | None = None, prereleases: bool = False) -> dict | None:
    """One plugin in the store's format, or None while it has no stable release Decky could check and install."""
    versions = []
    newest_manifest = None
    for release in sorted((r for r in releases if (prereleases or not r.get("prerelease")) and not r.get("draft")), key=lambda r: r.get("published_at") or "", reverse=True):
        asset = zip_of(entry, release)
        if asset is None:
            continue
        if newest_manifest is None:
            newest_manifest = manifest(asset) or {}
        name = version_of(release, plugin_version(newest_manifest, {}) if not versions else None)
        if name and all(name != seen["name"] for seen in versions):
            versions.append({"name": name, "hash": SHA256.fullmatch(asset["digest"]).group(1), "artifact": asset["browser_download_url"], "created": release.get("published_at")})
    # Only releases the plugin tags that way: channel_releases keeps the "newest stable" rule in one place.
    if not versions or channel_releases(entry, releases)["prerelease" if prereleases else "stable"] is None:
        return None
    publish = newest_manifest.get("publish") if isinstance(newest_manifest.get("publish"), dict) else {}
    tags = publish.get("tags") if isinstance(publish.get("tags"), list) else []
    author = newest_manifest.get("author")
    return {
        "id": number,
        "name": str(newest_manifest.get("name") or entry["name"]),
        "author": str(author) if author else entry["repo"].split("/")[0],
        "description": f"{publish.get('description') or entry.get('description') or ''}\n\n{deckyhub_line(entry, stats)}".strip(),
        "tags": list(dict.fromkeys([str(tag) for tag in tags] or [str(entry.get("category", "")).lower()]) | dict.fromkeys(deckyhub_tags(stats))),
        "image_url": str(publish.get("image") or ""),
        "versions": versions,
    }


def build(entries: list[dict], releases_by_repo: dict, manifest, stats_by_repo: dict | None = None, prereleases: bool = False) -> tuple[list[dict], dict]:
    """(the plugin list, the update map). manifest(asset): the plugin.json inside a ZIP, or {}.
    stats_by_repo: stats.json's plugins, or None when there are none to say anything about."""
    plugins = []
    for number, entry in enumerate(entries, 1):
        stats = None if stats_by_repo is None else stats_by_repo.get(entry["repo"].casefold(), {})
        plugin = store_plugin(entry, releases_by_repo.get(entry["repo"].casefold(), []), number, manifest, stats, prereleases)
        if plugin:
            plugins.append(plugin)
    # Two plugins can't share a name in the store, because Decky tells them apart by it: the first one stays.
    unique = list({plugin["name"].casefold(): plugin for plugin in reversed(plugins)}.values())
    plugins = sorted(unique, key=lambda plugin: plugin["id"])
    return plugins, {plugin["name"]: [plugin["versions"][0]["name"], plugin["versions"][0]["hash"], plugin["versions"][0]["artifact"]] for plugin in plugins}


def read_manifest(asset: dict) -> dict:
    try:
        return zip_plugin_files(asset)[0] or {}
    except Exception as error:  # noqa: BLE001 - a ZIP that can't be read just gets the registry's own names
        print(f"warning: {asset.get('browser_download_url')}: {error}", file=sys.stderr)
        return {}


def warm(entries: list[dict], releases_by_repo: dict, manifest, prereleases: bool = False) -> None:
    """Reads the newest stable ZIP's plugin.json of every plugin at once: build() asks for them one by one."""
    def newest(entry):
        shown = channel_releases(entry, releases_by_repo.get(entry["repo"].casefold(), []))["prerelease" if prereleases else "stable"]
        return zip_of(entry, shown) if shown else None

    assets = [asset for asset in map(newest, entries) if asset]
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(manifest, assets))


def main() -> int:
    prereleases = "--prereleases" in sys.argv
    sys.argv = [arg for arg in sys.argv if arg != "--prereleases"]
    if len(sys.argv) not in (3, 4):
        print(__doc__, file=sys.stderr)
        return 2
    releases = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["releases"]
    stats = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))["plugins"] if len(sys.argv) == 4 else None
    entries = load_registry_apps(REGISTRY)
    manifest = functools.lru_cache(maxsize=None)(lambda url, size: read_manifest({"browser_download_url": url, "size": size}))
    read = lambda asset: manifest(asset["browser_download_url"], asset["size"])  # noqa: E731
    warm(entries, releases, read, prereleases)
    plugins, updates = build(entries, releases, read, stats, prereleases)
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(plugins, separators=(",", ":"), ensure_ascii=False)
    for name in ("index.html", "plugins.json"):
        (out / name).write_text(text, encoding="utf-8")
    (out / "versions").write_text(json.dumps(updates, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"{len(plugins)} plugins with {sum(len(plugin['versions']) for plugin in plugins)} versions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
