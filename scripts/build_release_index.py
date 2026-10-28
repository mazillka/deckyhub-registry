"""Write every listed repo's recent releases to one JSON file for DeckyHub.

    GITHUB_TOKEN=$(gh auth token) python scripts/build_release_index.py OUT_DIR

Without a token DeckyHub may make 60 GitHub API calls an hour, and it needs one per
listed repo, so a big list runs out on a single page load. The release-index workflow
runs this every 30 minutes and publishes the file on the release-index branch, where DeckyHub
reads it from raw.githubusercontent.com (outside the API limit) in one request,
calling the API itself only for repos the file doesn't have.

It also writes downloads.json: each plugin's all-time download count, summed over
the plugin ZIPs (the entry's asset filter) of every release, for the catalog page.
GitHub counts every download of a file, from DeckyHub, Decky, a browser or a script.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from validate import API, REGISTRY, fetch, fetch_releases, matching_assets

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


def build(entries: list[dict], fetch=fetch_all_releases) -> dict:
    """Keyed by lowercase owner/name: each repo's newest releases, and its plugin ZIPs'
    download count over all of them. A repo whose lookup fails is left out, so DeckyHub
    asks GitHub for it directly rather than trusting an empty list."""
    def one(entry):
        try:
            releases = sorted((release for release in fetch(entry["repo"]) if not release.get("draft")), key=lambda release: release.get("published_at") or "", reverse=True)
        except Exception as error:  # noqa: BLE001 - one broken repo mustn't sink the index
            print(f"warning: {entry['repo']}: {error}", file=sys.stderr)
            return None
        downloads = sum(asset.get("download_count") or 0 for release in releases for asset in matching_assets(entry, release))
        return entry["repo"].casefold(), [slim(release) for release in releases[:RECENT]], downloads

    unique: dict[str, dict] = {}
    for entry in entries:
        unique.setdefault(entry["repo"].casefold(), entry)
    with ThreadPoolExecutor(8) as pool:
        results = [result for result in pool.map(one, unique.values()) if result]
    return {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "releases": {repo: releases for repo, releases, _ in results},
        "downloads": {repo: downloads for repo, _, downloads in results},
    }


def main() -> int:
    apps = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]
    index = build(apps + EXTRA_ENTRIES)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    (out / "releases.json").write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")
    # Small on its own, for the catalog page, which doesn't need the release lists.
    (out / "downloads.json").write_text(json.dumps({"generatedAt": index["generatedAt"], "downloads": index["downloads"]}, separators=(",", ":")), encoding="utf-8")
    print(f"{len(index['releases'])} repos indexed, {sum(index['downloads'].values())} downloads")
    return 0


if __name__ == "__main__":
    sys.exit(main())
