"""Print the listed plugins whose audit warnings grew since the last published stats.json.

    python scripts/audit_alerts.py OLD_STATS NEW_STATS

The release-index workflow passes the stats.json it's about to replace and the new one,
and opens an issue with whatever this prints, so a plugin that newly reads private data
or gets blocked is looked at before many people install it. Prints nothing when
nothing grew.
"""
import json
import sys
from pathlib import Path

from validate import REGISTRY


def new_warnings(old: dict, new: dict) -> dict[str, list[str]]:
    """Per repo, warnings in new that old didn't have (pre-release ones marked as such).
    An old file without any warnings is from before they existed: nothing is new then,
    or the first run would report every plugin at once."""
    if not any("warnings" in stats or "prereleaseWarnings" in stats for stats in old.values()):
        return {}
    found = {}
    for repo, stats in new.items():
        before = old.get(repo, {})
        added = [warning for warning in stats.get("warnings", []) if warning not in before.get("warnings", [])]
        added += [f"{warning} (pre-release)" for warning in stats.get("prereleaseWarnings", []) if warning not in before.get("prereleaseWarnings", [])]
        if added:
            found[repo] = added
    return found


def report(found: dict[str, list[str]], names: dict[str, str]) -> str:
    lines = [f"- **{names.get(repo, repo)}** ([{repo}](https://github.com/{repo})): {', '.join(warnings)}" for repo, warnings in sorted(found.items())]
    return "\n".join([
        "Decky Extended Plugins' audit (https://decky-extended-plugins.beallio.com/audit) found new warnings in these listed plugins' releases:",
        "",
        *lines,
        "",
        "Look at each release, then keep, pin an older release with `releaseTagInclude`, or remove the entry. The warnings are explained in the README.",
    ]) if found else ""


def main() -> int:
    old, new = (json.loads(Path(path).read_text(encoding="utf-8")).get("plugins", {}) for path in sys.argv[1:3])
    names = {app["repo"].casefold(): app["name"] for app in json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]}
    print(report(new_warnings(old, new), names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
