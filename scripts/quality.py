"""Spot plugins that look unfinished: too new, nobody using them, a placeholder version
or no description. Passing validate.py only proves a release installs.

    GITHUB_TOKEN=$(gh auth token) python scripts/quality.py   # report on registry/apps.json

discover.py skips candidates this flags (a skipped plugin is proposed again once it
grows out of it); run on its own, it lists registry entries that look unfinished for a
person to judge. It never changes apps.json and always exits 0.
"""
import json
import re
import sys
from datetime import datetime, timedelta, timezone

from validate import REGISTRY, channel_releases, fetch_github, matching_assets

# Give a first release this long before proposing it: brand-new plugins are often
# test builds, renamed or pulled within days.
MIN_AGE = timedelta(days=14)
# Under this many downloads (all releases' plugin ZIPs), with no stars either, nobody
# but the author seems to have tried it.
MIN_DOWNLOADS = 10
# A version that says it isn't ready: 0.0.x, or a tag with no number at all ("Initial").
PLACEHOLDER = re.compile(r"^\D*0\.0(\.|$)|^\D*$")


def unfinished(entry: dict, repo: dict, now: datetime) -> list[str]:
    """Why this registry entry (or candidate) looks unfinished; empty when it doesn't.
    repo is its fetch_github() answer."""
    releases = [release for release in repo["releases"] if not release.get("draft") and matching_assets(entry, release)]
    stable = channel_releases(entry, repo["releases"])["stable"]
    reasons = []
    first = min((release["published_at"] for release in releases if release.get("published_at")), default=None)
    if first and now - datetime.fromisoformat(first.replace("Z", "+00:00")) < MIN_AGE:
        reasons.append(f"first release under {MIN_AGE.days} days old")
    downloads = sum(asset.get("download_count") or 0 for release in releases for asset in matching_assets(entry, release))
    if not repo.get("stars") and downloads < MIN_DOWNLOADS:
        reasons.append(f"no stars and {downloads} downloads")
    if stable and PLACEHOLDER.search(stable["tag_name"]):
        reasons.append(f"placeholder version {stable['tag_name']!r}")
    if not (repo.get("description") or "").strip() and entry.get("description", "").endswith(" for Decky Loader."):
        reasons.append("no description")
    return reasons


def main() -> int:
    apps = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]
    github = fetch_github(list({app["repo"].casefold(): app["repo"] for app in apps}.values()), every_release=True)
    now = datetime.now(timezone.utc)
    flagged = 0
    for app in apps:
        repo = github.get(app["repo"].casefold())
        reasons = unfinished(app, repo, now) if repo else []
        if reasons:
            flagged += 1
            print(f"{app['id']}: {'; '.join(reasons)} (https://github.com/{app['repo']})")
    print(f"{len(apps)} entries, {flagged} look unfinished")
    return 0


if __name__ == "__main__":
    sys.exit(main())
