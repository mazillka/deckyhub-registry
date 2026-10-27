"""Check registry/apps.json against GitHub: what DeckyHub will actually find for each entry.

    python scripts/validate.py            # static checks + GitHub checks
    python scripts/validate.py --offline  # static checks only

Set GITHUB_TOKEN (CI does; locally `GITHUB_TOKEN=$(gh auth token)`) to get past the
60 requests/hour unauthenticated limit. The shape of each entry is checked separately
by deckyhub-plugin's tests/test_registry_schema.py; this covers what it can't:
entries that clash with each other and entries that don't match their repository.
Exits 1 on any error; warnings are printed but don't fail.
"""
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry" / "apps.json"
README = ROOT / "README.md"
API = "https://api.github.com"


def static_errors(apps: list[dict]) -> list[str]:
    """Clashes between entries. DeckyHub matches installed plugins by detect name, so two
    entries sharing one would fight over the same plugin; "DeckyHub" is reserved."""
    errors, ids, repos, names = [], {}, {}, {"deckyhub": "DeckyHub itself"}
    for app in apps:
        for key, seen, value in (("id", ids, app["id"]), ("repo", repos, app["repo"].casefold())):
            if value in seen:
                errors.append(f"{app['id']}: {key} {value!r} is already used by {seen[value]}")
            seen[value] = app["id"]
        for name in app["detect"]["names"]:
            if name.casefold() in names:
                errors.append(f"{app['id']}: detect name {name!r} is already claimed by {names[name.casefold()]}")
            names[name.casefold()] = app["id"]
    return errors



TABLE_HEADER = "| Tool | Category | Repository |\n| --- | --- | --- |\n"


def readme_errors(apps: list[dict], readme: str) -> list[str]:
    """README's Repositories table must list every entry, in apps.json order."""
    section = readme.split("## Repositories", 1)[-1].split("\n## ", 1)[0]
    listed = re.findall(r"^\|.*\|.*\| \[([^\]]+)\]", section, re.M)
    expected = [app["repo"] for app in apps]
    errors = [] if listed == expected else [f"README's Repositories table lists {listed}, expected {expected}"]
    # Without its header and separator rows GitHub renders the table as plain text.
    if TABLE_HEADER not in section:
        errors.append("README's Repositories table is missing its '| Tool | Category | Repository |' header and '| --- |' separator rows")
    return errors


# The same rules as DeckyHub's frontend (listAppReleases/matchingAssets/inChannel in
# deckyhub-plugin's src/utils.ts and src/version.ts): keep these in step with it.
def matching_assets(app: dict, release: dict) -> list[dict]:
    include = [word.lower() for word in app["asset"]["include"]]
    exclude = [word.lower() for word in app["asset"]["exclude"]]
    return [asset for asset in release.get("assets", []) if (name := asset["name"].lower()).endswith(".zip") and not any(word in name for word in exclude) and all(word in name for word in include)]


def channel_releases(app: dict, releases: list[dict]) -> dict[str, dict | None]:
    """The release each channel's card shows: newest of the last 20 (stable sees stable only)."""
    tag = (app.get("releaseTagInclude") or "").lower()
    candidates = sorted((release for release in releases if not release.get("draft") and tag in str(release.get("tag_name") or release.get("name")).lower()), key=lambda release: release.get("published_at") or "", reverse=True)
    return {"stable": next((release for release in candidates if not release.get("prerelease")), None), "prerelease": next(iter(candidates), None)}


def fetch(url: str, headers: dict | None = None, auth: bool = True) -> bytes:
    token = os.environ.get("GITHUB_TOKEN", "") if auth else ""
    headers = {"User-Agent": "deckyhub-registry-validate", **(headers or {})}
    if token and url.startswith(API):
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        return response.read()


def fetch_releases(repo: str) -> list[dict]:
    """GitHub's releases list sometimes answers [] to an authenticated request for a repo
    that has releases (about 1 in 4 in October 2026), while unauthenticated requests got the
    list every time. So an empty answer is asked again without the token, then once more
    with it, before it's believed."""
    url = f"{API}/repos/{repo}/releases?per_page=20"
    for auth in (True, False, True):
        if releases := json.loads(fetch(url, auth=auth)):
            return releases
        time.sleep(1)
    return []


class RangedFile(io.RawIOBase):
    """Just enough of a seekable file for zipfile to read a remote ZIP's index via HTTP
    Range requests, so a 200 MB plugin costs a few KB to inspect."""

    def __init__(self, url: str, size: int):
        self.url, self.size, self.position = url, size, 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        self.position = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}[whence] + offset
        return self.position

    def read(self, size=-1):
        end = self.size if size is None or size < 0 else min(self.size, self.position + size)
        if end <= self.position:
            return b""
        data = fetch(self.url, {"Range": f"bytes={self.position}-{end - 1}"})
        self.position += len(data)
        return data


def zip_plugin_name(asset: dict) -> str | None:
    """The name Decky Loader reads from the ZIP's top-level plugin.json once installed."""
    with zipfile.ZipFile(RangedFile(asset["browser_download_url"], asset["size"])) as archive:
        manifests = sorted((name for name in archive.namelist() if name.endswith("plugin.json") and "node_modules/" not in name), key=lambda name: name.count("/"))
        return json.loads(archive.read(manifests[0])).get("name") if manifests else None


def github_problems(app: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    label = app["id"]
    try:
        repo = json.loads(fetch(f"{API}/repos/{app['repo']}"))
    except urllib.error.HTTPError as error:
        return [f"{label}: repository {app['repo']} not found (HTTP {error.code})"], []
    if repo["full_name"].casefold() != app["repo"].casefold():
        warnings.append(f"{label}: {app['repo']} was renamed to {repo['full_name']}; update repo")
    if repo.get("archived"):
        warnings.append(f"{label}: {repo['full_name']} is archived")
    channels = channel_releases(app, fetch_releases(app["repo"]))
    if not channels["prerelease"]:
        return [f"{label}: no release matches releaseTagInclude {app.get('releaseTagInclude')!r}" if app.get("releaseTagInclude") else f"{label}: no releases"], warnings
    if not channels["stable"]:
        warnings.append(f"{label}: no stable release; the default (stable) channel shows an error")
    checked = set()
    for channel, release in channels.items():
        if not release or release["id"] in checked:
            continue
        checked.add(release["id"])
        where = f"{label} {release['tag_name']} ({channel})"
        assets = matching_assets(app, release)
        if len(assets) != 1:
            errors.append(f"{where}: asset filter matches {len(assets)} ZIPs {[asset['name'] for asset in assets]}, needs exactly 1")
            continue
        if not asset_digest(assets[0]):
            warnings.append(f"{where}: {assets[0]['name']} has no SHA-256 digest; Decky installs it unverified")
        name = zip_plugin_name(assets[0])
        if name is None:
            errors.append(f"{where}: {assets[0]['name']} has no plugin.json")
        elif name.casefold() not in {detect.casefold() for detect in app["detect"]["names"]}:
            errors.append(f"{where}: plugin.json name {name!r} isn't in detect.names {app['detect']['names']}")
    return errors, warnings


def asset_digest(asset: dict) -> str:
    return str(asset.get("digest") or "").removeprefix("sha256:")


def main() -> int:
    apps = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]
    errors, warnings = static_errors(apps) + readme_errors(apps, README.read_text(encoding="utf-8")), []
    if "--offline" not in sys.argv:
        for app in apps:
            try:
                app_errors, app_warnings = github_problems(app)
            except Exception as error:  # one unreachable repo shouldn't hide the rest
                app_errors, app_warnings = [f"{app['id']}: {type(error).__name__}: {error}"], []
            errors += app_errors
            warnings += app_warnings
            print(f"{'FAIL' if app_errors else 'ok  '} {app['id']}", flush=True)
    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")
    print(f"{len(apps)} entries, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
