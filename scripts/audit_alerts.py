"""Write the body of the rolling "Audit warnings" issue from the last published stats.json
and the new one, and say what the workflow should do with it.

    python scripts/audit_alerts.py OLD_STATS NEW_STATS BODY_FILE

The release-index workflow passes the stats.json it's about to replace and the new one,
and keeps one issue titled ISSUE_TITLE: this prints one word, and BODY_FILE holds the body.
- changed: a warning appeared or went away; edit the issue (create or reopen it if needed).
- same: nothing changed; leave the issue alone (create it if there's none yet).
- clear: no listed plugin has a warning any more; close the issue.

The body lists what's new since the last run first (and what went away), then every
plugin's current warnings, so the issue always shows the whole picture without piling up
one issue per run. A warning informs; whether to keep, pin or remove a plugin is a person's
call (the audit-warnings skill).
"""
import json
import sys
from pathlib import Path

from validate import REGISTRY

ISSUE_TITLE = "Audit warnings"
AUDIT_URL = "https://decky-extended-plugins.beallio.com/audit"
# GitHub refuses issue bodies over 65,536 characters.
MAX_BODY = 60_000


def labelled(stats: dict) -> list[str]:
    """A plugin's warnings, its newer pre-release's marked as such."""
    return [*stats.get("warnings", []), *(f"{warning} (pre-release)" for warning in stats.get("prereleaseWarnings", []))]


def changes(old: dict, new: dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Per repo, warnings new has that old didn't, and ones old had that new doesn't.
    An old file without any warnings is from before they existed: nothing has changed
    then, or the first run would report every plugin at once."""
    if not any(labelled(stats) for stats in old.values()):
        return {}, {}
    added, gone = {}, {}
    for repo in sorted({*old, *new}):
        before, after = labelled(old.get(repo, {})), labelled(new.get(repo, {}))
        if more := [warning for warning in after if warning not in before]:
            added[repo] = more
        if fewer := [warning for warning in before if warning not in after]:
            gone[repo] = fewer
    return added, gone


def lines(found: dict[str, list[str]], names: dict[str, str]) -> list[str]:
    return [f"- **{names.get(repo, repo)}** ([{repo}](https://github.com/{repo})): {', '.join(warnings)}" for repo, warnings in sorted(found.items())]


def body(old: dict, new: dict, names: dict[str, str], generated: str) -> tuple[str, str]:
    """(action, issue body); see the module docstring for the actions."""
    current = {repo: warnings for repo, stats in new.items() if (warnings := labelled(stats))}
    added, gone = changes(old, new)
    action = "clear" if not current else "changed" if added or gone else "same"
    news = [*lines(added, names)] or ["Nothing new."]
    if gone:
        news += ["", "No longer flagged:", "", *lines(gone, names)]
    text = "\n".join([
        f"Warnings from [Decky Extended Plugins' audit]({AUDIT_URL}) on the listed plugins' releases, kept up to date by the release-index workflow: edited whenever they change (this list is from {generated}). DeckyHub and the catalog show them as badges; they inform, they don't block anything.",
        "",
        "## New since the previous change",
        "",
        *news,
        "",
        f"## All current warnings ({len(current)} plugins)",
        "",
        *(lines(current, names) or ["None."]),
        "",
        "For each new one, look at the release, then keep it, pin an older release with `releaseTagInclude`, or remove the entry. The warnings are explained in the README.",
    ])
    if len(text) > MAX_BODY:
        text = text[:MAX_BODY].rsplit("\n", 1)[0] + "\n\n… (cut to fit GitHub's limit; stats.json on the release-index branch has them all)"
    return action, text


def main() -> int:
    old, new = (json.loads(Path(path).read_text(encoding="utf-8")) for path in sys.argv[1:3])
    names = {app["repo"].casefold(): app["name"] for app in json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]}
    action, text = body(old.get("plugins", {}), new.get("plugins", {}), names, new.get("generatedAt", "?"))
    Path(sys.argv[3]).write_text(text, encoding="utf-8")
    print(action)
    return 0


if __name__ == "__main__":
    sys.exit(main())
