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

Releases and stars come from GitHub's GraphQL API, BATCH repos per query: a REST run
took two calls per repo (over 600 for the list), against the workflow token's 1,000
an hour, which CI and discovery share. A query costs about 0.2 points per repo.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from validate import API, REGISTRY, channel_releases, matching_assets, zip_plugin_manifest

# Not a registry entry, but DeckyHub checks its own releases too.
EXTRA_ENTRIES = [{"repo": "mazillka/deckyhub-plugin", "asset": {"include": ["deckyhub-"], "exclude": []}}]
# What DeckyHub's release pickers show per repo.
RECENT = 20
# Repos per GraphQL query. At 25, GitHub cut parts of the answer for resource limits.
BATCH = 10
RELEASE_FIELDS = "tagName name isDraft isPrerelease publishedAt url description releaseAssets(first: 50) { nodes { name downloadUrl size digest downloadCount } }"


def graphql(query: str) -> tuple[dict, set[str]]:
    """One GraphQL query, retried (GitHub answers a slow one with a 502, and a burst
    with a 403 secondary rate limit that says how long to wait), and the
    top-level aliases whose answer is incomplete: a repo that's gone, or one GitHub cut
    short (RESOURCE_LIMITS_EXCEEDED), comes back null or partly null with an error."""
    request = urllib.request.Request(f"{API}/graphql", json.dumps({"query": query}).encode(), {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": "deckyhub-registry-index"})
    for attempt in (1, 2, 3):
        wait = 5
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read())
            if body.get("data") is None:
                raise RuntimeError(body.get("errors"))
            return body["data"], {str(error["path"][0]) for error in body.get("errors") or [] if error.get("path")}
        except urllib.error.HTTPError as error:
            headers = {key: error.headers.get(key) for key in ("retry-after", "x-ratelimit-remaining", "x-ratelimit-reset") if error.headers.get(key)}
            print(f"warning: GraphQL HTTP {error.code} {headers}: {error.read()[:300]!r}", file=sys.stderr)
            if attempt == 3:
                raise
            if error.headers.get("retry-after"):
                wait = int(error.headers["retry-after"])
            elif error.headers.get("x-ratelimit-remaining") == "0":
                wait = max(0, int(error.headers["x-ratelimit-reset"]) - int(time.time())) + 1
            elif error.code == 403:
                wait = 60
        except Exception:
            if attempt == 3:
                raise
        time.sleep(min(wait, 600))


def rest_shape(node: dict) -> dict:
    """A GraphQL release in the shape of GitHub's REST releases list, which the rest of
    this script and DeckyHub read."""
    return {
        "tag_name": node["tagName"],
        "name": node.get("name"),
        "draft": node["isDraft"],
        "prerelease": node["isPrerelease"],
        "published_at": node.get("publishedAt"),
        "html_url": node.get("url"),
        "body": node.get("description"),
        "assets": [{"name": asset["name"], "browser_download_url": asset["downloadUrl"], "size": asset["size"], "digest": asset.get("digest"), "download_count": asset["downloadCount"]} for asset in node["releaseAssets"]["nodes"]],
    }


def releases_query(repo: str, first: int, after: str | None = None) -> str:
    owner, name = repo.split("/")
    cursor = f", after: {json.dumps(after)}" if after else ""
    return (f"repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) {{ stargazerCount "
            f"releases(first: {first}{cursor}, orderBy: {{field: CREATED_AT, direction: DESC}}) {{ pageInfo {{ hasNextPage endCursor }} nodes {{ {RELEASE_FIELDS} }} }} }}")


def fetch_github(repos: list[str]) -> dict[str, dict]:
    """Every repo's releases (all of them, for the all-time download count) and stars,
    keyed by lowercase owner/name. A repo GitHub doesn't answer for is left out."""
    found: dict[str, dict] = {}
    for start in range(0, len(repos), BATCH):
        batch = repos[start:start + BATCH]
        data, failed = graphql("{ " + " ".join(f"r{index}: {releases_query(repo, RECENT)}" for index, repo in enumerate(batch)) + " }")
        for index, repo in enumerate(batch):
            try:
                result = data.get(f"r{index}")
                if f"r{index}" in failed:
                    # Asked again on its own, where it may fit the limits.
                    alone, failed_alone = graphql("{ r: " + releases_query(repo, RECENT) + " }")
                    result = None if failed_alone else alone["r"]
                if not result:
                    raise RuntimeError("not found or incomplete")
                releases, page = result["releases"]["nodes"], result["releases"]["pageInfo"]
                # ponytail: one query per extra page; only the few repos with over 20 releases need one.
                while page["hasNextPage"]:
                    more, failed_more = graphql("{ r: " + releases_query(repo, 100, page["endCursor"]) + " }")
                    if failed_more:
                        raise RuntimeError("older releases incomplete")
                    releases, page = releases + more["r"]["releases"]["nodes"], more["r"]["releases"]["pageInfo"]
            except Exception as error:  # noqa: BLE001 - left out, so DeckyHub asks GitHub for it directly
                print(f"warning: {repo}: {error}", file=sys.stderr)
                continue
            found[repo.casefold()] = {"releases": [rest_shape(node) for node in releases], "stars": result["stargazerCount"]}
    return found


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


def best_effort(lookup, *args):
    """A stat that can't be read is left out rather than sinking its plugin's entry."""
    try:
        return lookup(*args)
    except Exception as error:  # noqa: BLE001
        print(f"warning: {lookup.__name__}{args[:1]}: {error}", file=sys.stderr)
        return None


def plugin_stats(entry: dict, releases: list[dict], stars, manifest=zip_plugin_manifest) -> dict:
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


def build(entries: list[dict], fetch, stats) -> dict:
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
    entries = apps + EXTRA_ENTRIES
    github = fetch_github(list({entry["repo"].casefold(): entry["repo"] for entry in entries}.values()))
    if len(github) < len(entries) / 2:
        # Something's wrong on GitHub's side: keep the published index rather than replace it with a thin one.
        print(f"error: only {len(github)} of {len(entries)} repos answered", file=sys.stderr)
        return 1
    index = build(entries, lambda repo: github[repo.casefold()]["releases"], lambda entry, releases: plugin_stats(entry, releases, lambda repo: github[repo.casefold()]["stars"]))
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    # DeckyHub reads releases; the catalog page reads the much smaller stats file.
    (out / "releases.json").write_text(json.dumps({"generatedAt": index["generatedAt"], "releases": index["releases"]}, separators=(",", ":")), encoding="utf-8")
    (out / "stats.json").write_text(json.dumps({"generatedAt": index["generatedAt"], "plugins": index["stats"]}, separators=(",", ":")), encoding="utf-8")
    print(f"{len(index['releases'])} repos indexed, {sum(stat['downloads'] for stat in index['stats'].values())} downloads")
    return 0


if __name__ == "__main__":
    sys.exit(main())
