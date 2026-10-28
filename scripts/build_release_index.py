"""Write every listed repo's recent releases to one JSON file for DeckyHub.

    GITHUB_TOKEN=$(gh auth token) python scripts/build_release_index.py releases.json

Without a token DeckyHub may make 60 GitHub API calls an hour, and it needs one per
listed repo, so a big list runs out on a single page load. The release-index workflow
runs this hourly and publishes the file on the release-index branch, where DeckyHub
reads it from raw.githubusercontent.com (outside the API limit) in one request,
calling the API itself only for repos the file doesn't have.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from validate import REGISTRY, fetch_releases

# Not a registry entry, but DeckyHub checks its own releases too.
EXTRA_REPOS = ["mazillka/deckyhub-plugin"]


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


def build(repos: list[str], fetch=fetch_releases) -> dict:
    """Keyed by lowercase owner/name. A repo whose lookup fails is left out, so DeckyHub
    asks GitHub for it directly rather than trusting an empty list."""
    def one(repo):
        try:
            return repo, [slim(release) for release in fetch(repo) if not release.get("draft")]
        except Exception as error:  # noqa: BLE001 - one broken repo mustn't sink the index
            print(f"warning: {repo}: {error}", file=sys.stderr)
            return repo, None

    unique = list(dict.fromkeys(repo.casefold() for repo in repos))
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(one, unique))
    return {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "releases": {repo: releases for repo, releases in results if releases is not None},
    }


def main() -> int:
    apps = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]
    index = build([app["repo"] for app in apps] + EXTRA_REPOS)
    Path(sys.argv[1]).write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")
    print(f"{len(index['releases'])} repos indexed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
