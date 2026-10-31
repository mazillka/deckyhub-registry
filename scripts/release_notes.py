"""Release notes for a registry release: what changed in apps.json since the channel's
previous release, in words a Steam Deck user reads (registry-release.yml).

    python scripts/release_notes.py <previous apps.json or -> <new apps.json> [stats.json]

`-` for the first release of a channel. stats.json (from the release-index branch) only
adds which new plugins are forks; without it they're listed like the rest.
"""

import json
import sys
from collections import defaultdict


def load_apps(path):
    with open(path, encoding="utf-8") as file:
        return {app["id"]: app for app in json.load(file)["apps"]}


def sentence(text):
    text = text.strip()
    return text if text.endswith((".", "!", "?", "…")) else text + "."


def changes(old, new):
    """What a user notices about an app listed in both; detect rules and the like aren't."""
    found = []
    if old["name"] != new["name"]:
        found.append(f"renamed from {old['name']}")
    if old.get("category") != new.get("category"):
        found.append(f"moved to {new.get('category')}")
    if old.get("description") != new.get("description"):
        found.append("clearer description")
    if old["repo"] != new["repo"]:
        found.append(f"now installs from {new['repo']}")
    elif old.get("asset") != new.get("asset") or old.get("releaseTagInclude") != new.get("releaseTagInclude"):
        found.append("installs the right ZIP")
    return found


def release_notes(old, new, stats=None):
    if old is None:
        return f"The first registry release on this channel.\n\nThe list has **{len(new)} plugins**.\n"
    forks = {repo.lower(): line.get("fork") for repo, line in (stats or {}).items()}
    added = defaultdict(list)
    for app in sorted((new[i] for i in new.keys() - old.keys()), key=lambda app: app["name"].lower()):
        fork = forks.get(app["repo"].lower())
        added[app.get("category", "Other")].append(
            f"- **{app['name']}**: {sentence(app.get('description', ''))}" + (f" A fork that carries on {fork}." if fork else ""))
    removed = sorted(f"- **{old[i]['name']}** ({old[i]['repo']})" for i in old.keys() - new.keys())
    changed = []
    for i in sorted(old.keys() & new.keys(), key=lambda i: new[i]["name"].lower()):
        found = changes(old[i], new[i])
        if found:
            changed.append(f"- **{new[i]['name']}**: {', '.join(found)}.")

    lines = []
    if added:
        total = sum(map(len, added.values()))
        lines += ["## Added", "", f"{total} new plugin{'s' if total != 1 else ''} on Discover.", ""]
        for category, apps in sorted(added.items(), key=lambda item: (-len(item[1]), item[0])):
            lines += ([f"### {category}", ""] if len(added) > 1 else []) + apps + [""]
    if removed:
        lines += ["## Removed", ""] + removed + [""]
    if changed:
        lines += ["## Changed", ""] + changed + [""]
    if not lines:
        lines = ["No plugin changes: registry maintenance only.", ""]
    return "\n".join(lines + [f"The list now has **{len(new)} plugins**.", ""])


if __name__ == "__main__":
    old = None if sys.argv[1] == "-" else load_apps(sys.argv[1])
    stats = None
    if len(sys.argv) > 3:
        with open(sys.argv[3], encoding="utf-8") as file:
            stats = json.load(file).get("plugins", {})
    sys.stdout.reconfigure(encoding="utf-8")
    print(release_notes(old, load_apps(sys.argv[2]), stats), end="")
