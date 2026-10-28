"""Find Decky plugins that aren't listed yet and add the ones that pass validation.

    GITHUB_TOKEN=$(gh auth token) python scripts/discover.py [--limit N] [--dry-run]

The candidates come from decky-plugins-explorer
(https://github.com/SafetZahirovic/decky-plugins-explorer, MIT), which finds every
public GitHub repository with a Decky plugin.json through code search, nightly. Each
candidate is checked the way validate.py checks an entry (its own releases, one
plugin ZIP, the ZIP's plugin.json name), and needs a stable release. Passing ones are
appended to registry/apps.json and the README table; the discover workflow then opens
a pull request, so a person still reviews every addition before it's merged.
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from validate import API, README, REGISTRY, channel_releases, fetch, fetch_releases, github_problems, matching_assets, zip_plugin_name

EXPLORER_URL = "https://raw.githubusercontent.com/SafetZahirovic/decky-plugins-explorer/HEAD/data/plugins.json"
# A plugin last released longer ago than this is probably abandoned.
MAX_AGE = timedelta(days=730)
# Names a plugin template ships with, or that never got changed from it.
TEMPLATE = re.compile(r"example|template|my plugin|hello world|plugin name", re.I)
DEFAULT_ASSET = {"include": [".zip"], "exclude": ["source"]}

# First match wins; anything else is Utilities. A person fixes the odd miss in review.
CATEGORIES = [
    ("Frame Generation", r"frame ?gen|lsfg|fsr\b|upscal|optiscaler"),
    ("Controllers", r"controller|gamepad|gyro|rumble|vibrat|joystick|dualsense|haptic|trackpad|button remap"),
    ("Performance", r"\btdp\b|\bfan\b|battery|power|\bcpu\b|\bgpu\b|performance|undervolt|overclock|thermal|suspend|charg"),
    ("Launch Options", r"launch option|proton|\bwine\b|prefix|compatibility tool"),
    ("Mod Managers", r"\bmods?\b|mod manager|nexus"),
    ("Game Libraries", r"librar|non-steam|emulat|\brom|epic|\bgog\b|achievement|collection|playtime|game ?store|backlog|retro"),
    ("Customization", r"theme|\bcss\b|colou?r|\bled\b|rgb|wallpaper|boot ?video|animation|\bicon|\bui\b|font|startup"),
]


def category(text: str) -> str:
    return next((name for name, pattern in CATEGORIES if re.search(pattern, text, re.I)), "Utilities")


def short_description(text: str) -> str:
    """One line for a card: markdown stripped, cut at a sentence end near 140 characters."""
    text = re.sub(r"\s+", " ", re.sub(r"[*_`#>\[\]]", "", text or "")).strip()
    if len(text) > 140:
        sentence = re.match(r"(.{30,140}?[.!?])(\s|$)", text)
        text = sentence.group(1) if sentence else text[:137].rsplit(" ", 1)[0] + "..."
    return text[:1].upper() + text[1:]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def candidates(explorer: list[dict], apps: list[dict], now: datetime) -> list[dict]:
    """The explorer's repos worth a GitHub check: not listed, not archived, not a
    template, released within MAX_AGE, and a plugin name nobody here uses yet.
    Most downloaded first, so the busiest of two same-named repos is tried first."""
    listed = {app["repo"].casefold() for app in apps}
    names = {name.casefold() for app in apps for name in app["detect"]["names"]} | {"deckyhub"}
    picked = []
    for item in explorer:
        name = ((item.get("plugin") or {}).get("name") or "").strip()
        release = item.get("latest_release") or {}
        published = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00")) if release.get("published_at") else None
        if item["repo"].casefold() in listed or item.get("archived") or not name or TEMPLATE.search(name) or name.casefold() in names or not published or now - published > MAX_AGE:
            continue
        picked.append(item)
    return sorted(picked, key=lambda item: -(item.get("downloads") or 0))


def check(item: dict) -> dict | None:
    """A registry entry for the candidate if it passes validate.py's checks, else None."""
    repo = json.loads(fetch(f"{API}/repos/{item['repo']}"))
    if repo.get("archived") or repo.get("fork"):
        return None
    plugin = item.get("plugin") or {}
    entry = {"repo": repo["full_name"], "asset": DEFAULT_ASSET}
    stable = channel_releases(entry, fetch_releases(entry["repo"]))["stable"]
    assets = matching_assets(entry, stable) if stable else []
    if len(assets) != 1:
        return None
    # What Decky will report once it's installed, which can differ from the repo's copy.
    name = zip_plugin_name(assets[0])
    if not name:
        return None
    description = (plugin.get("publish") or {}).get("description") or ""
    if len(description) < 8 or sum(ord(char) > 127 for char in description) > 5:
        description = repo.get("description") or description
    tags = ",".join((plugin.get("publish") or {}).get("tags") or [])
    entry = {
        "id": slug(repo["name"]),
        "name": name,
        "description": short_description(description) or f"{name} for Decky Loader.",
        "repo": repo["full_name"],
        "category": category(" ".join([name, description, repo.get("description") or "", tags])),
        "detect": {"type": "decky-plugin", "names": [name]},
        "asset": DEFAULT_ASSET,
    }
    errors, _ = github_problems(entry)
    return None if errors else entry


def entry_json(entry: dict) -> str:
    """One entry in apps.json's house style (detect and asset on one line each)."""
    lines = [f'      "{key}": {json.dumps(value, ensure_ascii=False)}' for key, value in entry.items() if key not in ("detect", "asset")]
    lines.append(f'      "detect": {{ "type": "decky-plugin", "names": {json.dumps(entry["detect"]["names"], ensure_ascii=False)} }}')
    lines.append(f'      "asset": {{ "include": {json.dumps(entry["asset"]["include"])}, "exclude": {json.dumps(entry["asset"]["exclude"])} }}')
    return "    {\n" + ",\n".join(lines) + "\n    }"


def add(entries: list[dict]) -> None:
    source = REGISTRY.read_text(encoding="utf-8")
    end = source.rstrip().rfind("]")
    source = source[:end].rstrip() + ",\n" + ",\n".join(entry_json(entry) for entry in entries) + "\n  ]\n}\n"
    json.loads(source)
    REGISTRY.write_text(source, encoding="utf-8", newline="\n")
    readme = README.read_text(encoding="utf-8")
    last = [line for line in readme.split("\n") if line.startswith("| ") and "](https://github.com/" in line][-1]
    rows = [f"| {entry['name'].replace('|', '/')} | {entry['category']} | [{entry['repo']}](https://github.com/{entry['repo']}) |" for entry in entries]
    README.write_text(readme.replace(last, "\n".join([last, *rows]), 1), encoding="utf-8", newline="\n")


def main() -> int:
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 25
    apps = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]
    found = candidates(json.loads(fetch(EXPLORER_URL, auth=False)), apps, datetime.now(timezone.utc))

    def safe_check(item):
        try:
            return check(item)
        except Exception as error:  # noqa: BLE001 - one bad repo mustn't stop the run
            print(f"warning: {item['repo']}: {error}", file=sys.stderr)
            return None

    with ThreadPoolExecutor(8) as pool:
        passed = [entry for entry in pool.map(safe_check, found) if entry]
    ids, names, picked = {app["id"] for app in apps}, set(), []
    for entry in passed:
        if entry["name"].casefold() in names:
            continue
        if entry["id"] in ids:
            entry["id"] = slug(entry["repo"])
        if entry["id"] in ids:
            continue
        ids.add(entry["id"])
        names.add(entry["name"].casefold())
        picked.append(entry)
    picked = picked[:limit]
    print(f"{len(found)} candidates, {len(passed)} passed, adding {len(picked)}")
    for entry in picked:
        print(f"- {entry['name']} ({entry['category']}): https://github.com/{entry['repo']}")
    if picked and "--dry-run" not in sys.argv:
        add(picked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
