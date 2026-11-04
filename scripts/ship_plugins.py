"""Bring develop's plugin list onto a checkout of main, and nothing else of develop's.

    git fetch origin develop
    python scripts/ship_plugins.py origin/develop

Writes develop's registry/apps.json, and swaps the README's "## Repositories" table for
develop's, so plugins found on develop (discover PRs, plugin edits) can ship to main
without the scripts and workflows still waiting on develop. Prints how many plugins
were added and removed, or nothing when the list already matches. The ship-plugins
workflow runs it and opens the PR; the ship-registry skill has the manual steps.
"""
import json
import subprocess
import sys

from validate import load_registry_apps, README, REGISTRY

SECTION = "## Repositories"


def repositories_section(readme: str) -> str:
    """The README's Repositories section, heading included, up to the next heading."""
    start = readme.index(SECTION)
    end = readme.find("\n## ", start + len(SECTION))
    return readme[start:] if end == -1 else readme[start:end + 1]


def with_section(readme: str, section: str) -> str:
    """readme with its Repositories section replaced by section."""
    return readme.replace(repositories_section(readme), section, 1)


def show(ref: str, path: str) -> str:
    return subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True, check=True).stdout


def main() -> int:
    ref = sys.argv[1] if len(sys.argv) > 1 else "origin/develop"
    root = REGISTRY.parent.parent
    apps, readme = show(ref, REGISTRY.relative_to(root).as_posix()), show(ref, README.relative_to(root).as_posix())
    before = {app["id"] for app in load_registry_apps(REGISTRY)}
    after = {app["id"] for app in json.loads(apps)["apps"]}
    REGISTRY.write_text(apps, encoding="utf-8")
    README.write_text(with_section(README.read_text(encoding="utf-8"), repositories_section(readme)), encoding="utf-8")
    if after != before:
        print(f"{len(after - before)} added, {len(before - after)} removed, {len(after)} plugins")
    return 0


if __name__ == "__main__":
    sys.exit(main())
