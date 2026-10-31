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
- warnings / prereleaseWarnings: what Decky Extended Plugins' audit found in that release
  (and in a newer pre-release, if any) that's worth warning about (see WARNINGS). Matched
  by the ZIP's sha256, else by tag. Missing when there's nothing to warn about.

Releases and stars come from GitHub's GraphQL API (fetch_github in validate.py).
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from validate import RECENT, REGISTRY, channel_releases, fetch, fetch_github, matching_assets, zip_plugin_manifest

AUDIT_URL = "https://decky-extended-plugins.beallio.com/audit.json"
# The audit's rule ID prefixes worth a warning on a card, like Runs as root. Routine ones
# (sudo, mount, systemctl, subprocess) aren't: many useful plugins need them on SteamOS,
# and Runs as root already says the plugin has the system.
WARNINGS = {
    "SENSITIVE_": "private-data",  # Steam login data, SSH keys, environment secrets
    "PERSIST_": "persistence",  # shell profiles, LD_PRELOAD, kernel modules, udev rules
    "ZIP_ONLY_": "not-in-source",  # scripts or programs in the ZIP but not the repo
    "MODIFIED_SOURCE_FILE": "not-in-source",
    "OBFUSCATION_": "obfuscated",
    "NETWORK_DISABLED_TLS": "no-tls-check",
    "SHELL_CURL_PIPE": "runs-downloads",
    "TRIVY_": "vulnerable",  # bundled libraries with published CVEs
}

# Not a registry entry, but DeckyHub checks its own releases too.
EXTRA_ENTRIES = [{"repo": "mazillka/deckyhub-plugin", "asset": {"include": ["deckyhub-"], "exclude": []}}]
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


def audit_index(data: dict) -> dict:
    """Each audited release's warnings, keyed by artifact sha256 and by (lowercase
    owner/name, tag). A rolling tag (nightly, dev-build) is audited once per upload, so
    the newest wins."""
    index = {}
    for record in sorted(data.get("releases", []), key=lambda record: record.get("audited_at") or ""):
        found = {warning for rule in record.get("rule_ids") or [] for prefix, warning in WARNINGS.items() if rule.startswith(prefix)}
        verdict = (["blocked"] if record["classification"] == "BLOCK" else []) + sorted(found)
        repo = record["repository"].removeprefix("https://github.com/").casefold()
        index[(repo, record["tag"])] = verdict
        if record.get("current_artifact_sha256"):
            index[record["current_artifact_sha256"]] = verdict
    return index


def warnings_of(entry: dict, release: dict | None, audits: dict) -> list[str]:
    if not release:
        return []
    for asset in matching_assets(entry, release):
        warnings = audits.get((asset.get("digest") or "").removeprefix("sha256:"))
        if warnings is not None:
            return warnings
    return audits.get((entry["repo"].casefold(), release.get("tag_name"))) or []


def plugin_stats(entry: dict, releases: list[dict], stars, manifest=zip_plugin_manifest, audits: dict | None = None) -> dict:
    channels = channel_releases(entry, releases)
    shown = channels["stable"] or channels["prerelease"]
    assets = matching_assets(entry, shown) if shown else []
    flags = (best_effort(manifest, assets[0]) or {}).get("flags") if assets else None
    stats = {
        "downloads": sum(asset.get("download_count") or 0 for release in releases for asset in matching_assets(entry, release)),
        "stars": best_effort(stars, entry["repo"]),
        "updated": shown.get("published_at") if shown else None,
        "root": "root" in flags if isinstance(flags, list) else None,
    }
    if audits:
        if warnings := warnings_of(entry, shown, audits):
            stats["warnings"] = warnings
        if channels["prerelease"] is not shown and (warnings := warnings_of(entry, channels["prerelease"], audits)):
            stats["prereleaseWarnings"] = warnings
    return stats


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
    github = fetch_github(list({entry["repo"].casefold(): entry["repo"] for entry in entries}.values()), every_release=True)
    if len(github) < len(entries) / 2:
        # Something's wrong on GitHub's side: keep the published index rather than replace it with a thin one.
        print(f"error: only {len(github)} of {len(entries)} repos answered", file=sys.stderr)
        return 1
    # The audit is someone else's site: without it the index just goes out without verdicts.
    audits = audit_index(best_effort(lambda url: json.loads(fetch(url, auth=False)), AUDIT_URL) or {})
    index = build(entries, lambda repo: github[repo.casefold()]["releases"], lambda entry, releases: plugin_stats(entry, releases, lambda repo: github[repo.casefold()]["stars"], audits=audits))
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    # DeckyHub reads releases; the catalog page reads the much smaller stats file.
    (out / "releases.json").write_text(json.dumps({"generatedAt": index["generatedAt"], "releases": index["releases"]}, separators=(",", ":")), encoding="utf-8")
    (out / "stats.json").write_text(json.dumps({"generatedAt": index["generatedAt"], "plugins": index["stats"]}, separators=(",", ":")), encoding="utf-8")
    print(f"{len(index['releases'])} repos indexed, {sum(stat['downloads'] for stat in index['stats'].values())} downloads")
    return 0


if __name__ == "__main__":
    sys.exit(main())
