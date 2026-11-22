"""Spot plugins that look unfinished: a placeholder version or no description.
Passing validate.py only proves a release installs.

    GITHUB_TOKEN=$(gh auth token) python scripts/quality.py   # report on registry/apps.json

discover.py skips candidates this flags (a skipped plugin is proposed again once it
grows out of it); run on its own, it lists registry entries that look unfinished for a
person to judge. It never changes apps.json and always exits 0.
"""
import re
import sys

from validate import load_registry_apps, REGISTRY, channel_releases, fetch_github

# A version that says it isn't ready: 0.0.x, or a tag with no number at all ("Initial").
PLACEHOLDER = re.compile(r"^\D*0\.0(\.|$)|^\D*$")


def unfinished(entry: dict, repo: dict) -> list[str]:
    """Why this registry entry (or candidate) looks unfinished; empty when it doesn't.
    repo is its fetch_github() answer."""
    channels = channel_releases(entry, repo["releases"])
    shown = channels["stable"] or channels["prerelease"]
    reasons = []
    if shown and PLACEHOLDER.search(shown["tag_name"]):
        reasons.append(f"placeholder version {shown['tag_name']!r}")
    if not (repo.get("description") or "").strip() and entry.get("description", "").endswith(" for Decky Loader."):
        reasons.append("no description")
    return reasons


def main() -> int:
    apps = load_registry_apps(REGISTRY)
    github = fetch_github(list({app["repo"].casefold(): app["repo"] for app in apps}.values()), every_release=True)
    flagged = 0
    for app in apps:
        repo = github.get(app["repo"].casefold())
        reasons = unfinished(app, repo) if repo else []
        if reasons:
            flagged += 1
            print(f"{app['id']}: {'; '.join(reasons)} (https://github.com/{app['repo']})")
    print(f"{len(apps)} entries, {flagged} look unfinished")
    return 0


if __name__ == "__main__":
    sys.exit(main())
