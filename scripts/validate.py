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


def installable_releases(app: dict, releases: list[dict]) -> list[dict]:
    """The releases DeckyHub can install from, newest first: not drafts, matching
    releaseTagInclude, with a ZIP the asset filter matches."""
    tag = (app.get("releaseTagInclude") or "").lower()
    return sorted((release for release in releases if not release.get("draft") and tag in str(release.get("tag_name") or release.get("name")).lower() and matching_assets(app, release)), key=lambda release: release.get("published_at") or "", reverse=True)


def channel_releases(app: dict, releases: list[dict]) -> dict[str, dict | None]:
    """The release each channel's card shows: newest of the last 20 (stable sees stable only)
    with a matching ZIP. DeckyHub skips a newer one without it (a Windows-only build, say)."""
    candidates = installable_releases(app, releases)
    return {"stable": next((release for release in candidates if not release.get("prerelease")), None), "prerelease": next(iter(candidates), None)}


def fetch(url: str, headers: dict | None = None, auth: bool = True) -> bytes:
    token = os.environ.get("GITHUB_TOKEN", "") if auth else ""
    headers = {"User-Agent": "deckyhub-registry-validate", **(headers or {})}
    if token and url.startswith(API):
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        return response.read()




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


def zip_plugin_manifest(asset: dict) -> dict | None:
    """The ZIP's top-level plugin.json, which Decky Loader reads once it's installed."""
    with zipfile.ZipFile(RangedFile(asset["browser_download_url"], asset["size"])) as archive:
        manifests = sorted((name for name in archive.namelist() if name.endswith("plugin.json") and "node_modules/" not in name), key=lambda name: name.count("/"))
        return json.loads(archive.read(manifests[0])) if manifests else None


def zip_plugin_name(asset: dict) -> str | None:
    return (zip_plugin_manifest(asset) or {}).get("name")


def github_problems(app: dict, repo: dict | None = None) -> tuple[list[str], list[str]]:
    """repo: the entry's fetch_github() answer, looked up here when not given."""
    errors, warnings = [], []
    label = app["id"]
    if repo is None:
        repo = fetch_github([app["repo"]]).get(app["repo"].casefold())
    if not repo:
        return [f"{label}: repository {app['repo']} not found, or GitHub didn't answer for it"], []
    if repo["full_name"].casefold() != app["repo"].casefold():
        warnings.append(f"{label}: {app['repo']} was renamed to {repo['full_name']}; update repo")
    if repo.get("archived"):
        warnings.append(f"{label}: {repo['full_name']} is archived")
    channels = channel_releases(app, repo["releases"])
    if not channels["prerelease"]:
        where = f" matching releaseTagInclude {app.get('releaseTagInclude')!r}" if app.get("releaseTagInclude") else ""
        return [f"{label}: no release{where} has a ZIP the asset filter matches"], warnings
    if not channels["stable"]:
        warnings.append(f"{label}: no stable release; the default (stable) channel shows an error")
    checked = set()
    for channel, release in channels.items():
        if not release or release["tag_name"] in checked:
            continue
        checked.add(release["tag_name"])
        where = f"{label} {release['tag_name']} ({channel})"
        assets = matching_assets(app, release)
        if len(assets) != 1:
            errors.append(f"{where}: asset filter matches {len(assets)} ZIPs {[asset['name'] for asset in assets]}, needs exactly 1")
            continue
        if not assets[0].get("digest"):
            warnings.append(f"{where}: {assets[0]['name']} has no SHA-256 digest; Decky installs it unverified")
        name = zip_plugin_name(assets[0])
        if name is None:
            errors.append(f"{where}: {assets[0]['name']} has no plugin.json")
        elif name.casefold() not in {detect.casefold() for detect in app["detect"]["names"]}:
            errors.append(f"{where}: plugin.json name {name!r} isn't in detect.names {app['detect']['names']}")
    return errors, warnings


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
    request = urllib.request.Request(f"{API}/graphql", json.dumps({"query": query}).encode(), {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": "deckyhub-registry"})
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
    return (f"repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) {{ nameWithOwner name description isArchived isFork stargazerCount "
            f"parent {{ nameWithOwner isArchived isTemplate releases(first: 1, orderBy: {{field: CREATED_AT, direction: DESC}}) {{ nodes {{ publishedAt }} }} }} "
            f"releases(first: {first}{cursor}, orderBy: {{field: CREATED_AT, direction: DESC}}) {{ pageInfo {{ hasNextPage endCursor }} nodes {{ {RELEASE_FIELDS} }} }} }}")


def fetch_github(repos: list[str], every_release: bool = False) -> dict[str, dict]:
    """Each repo's facts and newest RECENT releases (every_release: all of them, for an
    all-time download count), in the REST API's shape, keyed by the lowercase owner/name
    asked for. A repo GitHub doesn't answer for, or answers only partly, is left out.

    GraphQL, BATCH repos per query: the REST API took two calls per repo, over 600 for
    the list, against the workflow token's 1,000 an hour shared by every job here. A
    query costs about 0.2 points per repo."""
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
                while every_release and page["hasNextPage"]:
                    more, failed_more = graphql("{ r: " + releases_query(repo, 100, page["endCursor"]) + " }")
                    if failed_more:
                        raise RuntimeError("older releases incomplete")
                    releases, page = releases + more["r"]["releases"]["nodes"], more["r"]["releases"]["pageInfo"]
            except Exception as error:  # noqa: BLE001 - left out; callers say what that means
                print(f"warning: {repo}: {error}", file=sys.stderr)
                continue
            found[repo.casefold()] = {
                "full_name": result["nameWithOwner"], "name": result["name"], "description": result["description"],
                "archived": result["isArchived"], "stars": result["stargazerCount"],
                # A fork of a template (Decky's plugin template) is a new plugin, not a copy of one.
                "fork": result["isFork"] and not (result["parent"] or {}).get("isTemplate"),
                # The repo it was forked from: its name, whether it's archived and its newest release date.
                "parent": result["parent"] and {"full_name": result["parent"]["nameWithOwner"], "archived": result["parent"]["isArchived"],
                                                "released": next((node["publishedAt"] for node in result["parent"]["releases"]["nodes"]), None)},
                "releases": [rest_shape(node) for node in releases],
            }
    return found


def main() -> int:
    apps = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]
    errors, warnings = static_errors(apps) + readme_errors(apps, README.read_text(encoding="utf-8")), []
    if "--offline" not in sys.argv:
        github = fetch_github(list({app["repo"].casefold(): app["repo"] for app in apps}.values()))
        for app in apps:
            try:
                app_errors, app_warnings = github_problems(app, github.get(app["repo"].casefold(), {}))
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
