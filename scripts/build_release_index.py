"""Write every listed repo's recent releases to one JSON file for DeckyHub.

    GITHUB_TOKEN=$(gh auth token) python scripts/build_release_index.py OUT_DIR

Without a token DeckyHub may make 60 GitHub API calls an hour, and it needs one per
listed repo, so a big list runs out on a single page load. The release-index workflow
runs this every 30 minutes and publishes the file on the release-index branch, where DeckyHub
reads it from raw.githubusercontent.com (outside the API limit) in one request,
calling the API itself only for repos the file doesn't have.

It also writes stats.json for the catalog page, per plugin:
- downloads: all-time, summed over the plugin ZIPs (the entry's asset filter) of every
  release. GitHub counts every download of a file, from DeckyHub, Decky, a browser...
- stars: the repo's GitHub stars.
- updated: when the release DeckyHub shows (newest stable, else newest pre-release) came out.
- root: whether that release's plugin.json asks Decky to run it as root.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from validate import API, REGISTRY, channel_releases, fetch, fetch_releases, matching_assets, zip_plugin_manifest

# Not a registry entry, but DeckyHub checks its own releases too.
EXTRA_ENTRIES = [{"repo": "mazillka/deckyhub-plugin", "asset": {"include": ["deckyhub-"], "exclude": []}}]
# What DeckyHub's release pickers show per repo.
RECENT = 20


def fetch_all_releases(repo: str) -> list[dict]:
    """Every release, for the all-time download count: 100 a page."""
    releases, page = [], 1
    while True:
        batch = json.loads(fetch(f"{API}/repos/{repo}/releases?per_page=100&page={page}"))
        if page == 1 and not batch:
            # GitHub's occasional empty first answer; fetch_releases retries it (20 at most).
            return fetch_releases(repo)
        releases += batch
        if len(batch) < 100:
            return releases
        page += 1


def slim(release: dict) -> dict:
    """The fields DeckyHub reads from GitHub's releases list (fetchReleases in its utils.ts)."""
    return {
        "tag_name": release.get("tag_name"),
        "name": release.get("name"),
        "draft": release.get("draft", False),
        "prerelease": release.get("prerelease", False),
        "published_at": release.get("published_at"),
        "html_url": release.get("html_url"),
        "body": release.get("body"),
        "assets": [{key: asset.get(key) for key in ("name", "browser_download_url", "size", "digest")} for asset in release.get("assets", [])],
    }


def repo_stars(repo: str) -> int:
    return json.loads(fetch(f"{API}/repos/{repo}"))["stargazers_count"]


def best_effort(lookup, *args):
    """A stat that can't be read is left out rather than sinking its plugin's entry."""
    try:
        return lookup(*args)
    except Exception as error:  # noqa: BLE001
        print(f"warning: {lookup.__name__}{args[:1]}: {error}", file=sys.stderr)
        return None


def plugin_stats(entry: dict, releases: list[dict], stars=repo_stars, manifest=zip_plugin_manifest) -> dict:
    channels = channel_releases(entry, releases)
    shown = channels["stable"] or channels["prerelease"]
    assets = matching_assets(entry, shown) if shown else []
    flags = (best_effort(manifest, assets[0]) or {}).get("flags") if assets else None
    return {
        "downloads": sum(asset.get("download_count") or 0 for release in releases for asset in matching_assets(entry, release)),
        "stars": best_effort(stars, entry["repo"]),
        "updated": shown.get("published_at") if shown else None,
        "root": "root" in flags if isinstance(flags, list) else None,
    }


def build(entries: list[dict], fetch=fetch_all_releases, stats=plugin_stats) -> dict:
    """Keyed by lowercase owner/name: each repo's newest releases, and its stats (see the
    module docstring). A repo whose lookup fails is left out, so DeckyHub asks GitHub for
    it directly rather than trusting an empty list."""
    def one(entry):
        try:
            releases = sorted((release for release in fetch(entry["repo"]) if not release.get("draft")), key=lambda release: release.get("published_at") or "", reverse=True)
        except Exception as error:  # noqa: BLE001 - one broken repo mustn't sink the index
            print(f"warning: {entry['repo']}: {error}", file=sys.stderr)
            return None
        return entry["repo"].casefold(), [slim(release) for release in releases[:RECENT]], stats(entry, releases)

    unique: dict[str, dict] = {}
    for entry in entries:
        unique.setdefault(entry["repo"].casefold(), entry)
    with ThreadPoolExecutor(8) as pool:
        results = [result for result in pool.map(one, unique.values()) if result]
    return {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "releases": {repo: releases for repo, releases, _ in results},
        "stats": {repo: stats for repo, _, stats in results},
    }


def main() -> int:
    apps = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]
    index = build(apps + EXTRA_ENTRIES)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    # DeckyHub reads releases; the catalog page reads the much smaller stats file.
    (out / "releases.json").write_text(json.dumps({"generatedAt": index["generatedAt"], "releases": index["releases"]}, separators=(",", ":")), encoding="utf-8")
    (out / "stats.json").write_text(json.dumps({"generatedAt": index["generatedAt"], "plugins": index["stats"]}, separators=(",", ":")), encoding="utf-8")
    print(f"{len(index['releases'])} repos indexed, {sum(stat['downloads'] for stat in index['stats'].values())} downloads")
    return 0


if __name__ == "__main__":
    sys.exit(main())
