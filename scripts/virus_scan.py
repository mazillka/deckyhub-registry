"""Scan every plugin ZIP DeckyHub can install with ClamAV, and publish one report per ZIP.

    python scripts/virus_scan.py OUT_DIR --index RELEASES_JSON [--index ...] [--old SCANS_JSON]

The virus-scan workflow passes the releases.json of both release-index branches (what
DeckyHub's version pickers offer, DeckyHub's own releases included) and the scans.json
it published last time, and publishes OUT_DIR/scans.json on the virus-scans branch.
DeckyHub's Manage window shows the report for the ZIP you'd install from it.

scans.json, keyed by the ZIP's download URL:
- sha256: of the file that was scanned. A ZIP replaced under the same URL (a rolling
  "nightly" tag) has a new digest in the index and is scanned again.
- result: clean, infected (found lists what ClamAV matched), incomplete (the ZIP went
  past ClamAV's size limits, so part of it wasn't looked at) or error.
- engine / signatures: the ClamAV version and signature database version used.
- scannedAt: when. A report older than RESCAN_DAYS is scanned again with newer signatures.

Each run downloads at most MAX_RUN_BYTES, newest releases first, so the first runs work
through the backlog over a few hours and later runs only see new releases. A ZIP not
scanned yet has no report: DeckyHub says so rather than calling it clean.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from build_release_index import EXTRA_ENTRIES
from validate import REGISTRY, matching_assets

MAX_RUN_BYTES = 6 * 1024**3
MAX_BATCH_BYTES = 1024**3
MAX_FILE_BYTES = 1024**3
RESCAN_DAYS = 30
# Generous limits, so a big plugin is still looked into rather than skipped; past them
# ClamAV raises Heuristics.Limits.Exceeded, reported as incomplete.
CLAMSCAN = ["clamscan", "--no-summary", "--stdout", "--max-filesize=1024M", "--max-scansize=4095M", "--max-files=200000", "--max-recursion=32", "--alert-exceeds-max=yes"]
LIMITS = "Heuristics.Limits.Exceeded"


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: str | None) -> dict:
    """A missing, empty or broken file reads as nothing: git show leaves an empty file
    when the branch doesn't exist yet."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")) if path else {}
    except (OSError, ValueError):
        return {}


def wanted_assets(indexes: list[dict], entries: list[dict]) -> dict[str, dict]:
    """Every plugin ZIP in the indexes, keyed by download URL, in scan order: each repo's
    newest release first, then the next newest, and so on. A repo the registry no longer
    lists (only the other branch has it) is held to plain .zip."""
    filters = {entry["repo"].casefold(): entry for entry in entries}
    rounds: list[list[tuple[str, dict]]] = []
    for index in indexes:
        for repo, releases in (index.get("releases") or {}).items():
            entry = filters.get(repo.casefold(), {"asset": {"include": [], "exclude": []}})
            for rank, release in enumerate(releases):
                while len(rounds) <= rank:
                    rounds.append([])
                for asset in matching_assets(entry, release):
                    if str(asset.get("browser_download_url") or "").startswith("https://"):
                        rounds[rank].append((asset["browser_download_url"], {"sha256": (asset.get("digest") or "").removeprefix("sha256:") or None, "size": asset.get("size") or 0}))
    wanted: dict[str, dict] = {}
    for found in rounds:
        for url, asset in found:
            wanted.setdefault(url, asset)
    return wanted


def plan(wanted: dict[str, dict], old: dict[str, dict], today: datetime) -> tuple[dict[str, dict], list[str]]:
    """The old reports still good for a wanted ZIP, and the URLs to scan: never-scanned
    ones (in wanted's order) before stale reports (oldest first)."""
    kept, new, stale = {}, [], []
    for url, asset in wanted.items():
        report = old.get(url)
        if not report or (asset["sha256"] and report.get("sha256") != asset["sha256"]) or report.get("result") == "error":
            new.append(url)
            continue
        kept[url] = report
        if datetime.strptime(report.get("scannedAt") or "1970-01-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) < today - timedelta(days=RESCAN_DAYS):
            stale.append(url)
    stale.sort(key=lambda url: kept[url].get("scannedAt") or "")
    return kept, new + stale


def budget(urls: list[str], wanted: dict[str, dict]) -> list[list[str]]:
    """The URLs this run gets to, in batches that fit on disk at once."""
    batches, size, total = [[]], 0, 0
    for url in urls:
        bytes_ = wanted[url]["size"]
        if bytes_ > MAX_FILE_BYTES:
            continue
        if total + bytes_ > MAX_RUN_BYTES:
            break
        if batches[-1] and size + bytes_ > MAX_BATCH_BYTES:
            batches.append([])
            size = 0
        batches[-1].append(url)
        size += bytes_
        total += bytes_
    return [batch for batch in batches if batch]


def download(url: str, path: Path) -> str:
    """Saves the file, returning its sha256."""
    digest = hashlib.sha256()
    request = urllib.request.Request(url, headers={"User-Agent": "deckyhub-registry-virus-scan"})
    with urllib.request.urlopen(request, timeout=120) as response, path.open("wb") as file:
        if not response.geturl().startswith("https://"):
            raise OSError(f"redirected off HTTPS: {response.geturl()}")
        while chunk := response.read(1 << 20):
            digest.update(chunk)
            file.write(chunk)
    return digest.hexdigest()


def parse_clamscan(output: str, paths: list[str]) -> dict[str, list[str] | None]:
    """Per scanned path: what ClamAV found ([] when clean), or None when it reported an
    error or nothing at all for that file. A ZIP's inner files are reported as
    'path: Name FOUND' too, so matches are collected per scanned path."""
    found: dict[str, list[str] | None] = {path: None for path in paths}
    for line in output.splitlines():
        path, _, verdict = line.rpartition(": ")
        path = next((candidate for candidate in paths if path == candidate or path.startswith(candidate + "/") or path.startswith(candidate + "!")), None)
        if path is None:
            continue
        if verdict == "OK":
            found[path] = found[path] or []
        elif verdict.endswith(" FOUND"):
            found[path] = sorted({*(found[path] or []), verdict.removesuffix(" FOUND")})
        elif verdict.endswith("ERROR"):
            found[path] = None
    return found


def report_of(found: list[str] | None) -> dict:
    if found is None:
        return {"result": "error"}
    if not found:
        return {"result": "clean"}
    threats = [name for name in found if not name.startswith(LIMITS)]
    return {"result": "infected", "found": threats} if threats else {"result": "incomplete", "found": found}


def clamscan(paths: list[str]) -> str:
    # Exit 1 means something was found and 2 an error; both still print per-file lines.
    return subprocess.run([*CLAMSCAN, *paths], capture_output=True, text=True, check=False).stdout


def clamav_version() -> tuple[str, str]:
    """('ClamAV 1.4.3', '27806') from 'ClamAV 1.4.3/27806/Sun Nov  1 08:23:01 2026'."""
    parts = subprocess.run(["clamscan", "--version"], capture_output=True, text=True, check=True).stdout.strip().split("/")
    return parts[0], parts[1] if len(parts) > 1 else ""


def scan(batches: list[list[str]], scanner=clamscan, fetch=download, version=clamav_version) -> dict[str, dict]:
    engine, signatures = version() if batches else ("", "")
    reports = {}
    for batch in batches:
        with tempfile.TemporaryDirectory() as folder:
            paths, digests = {}, {}
            for number, url in enumerate(batch):
                path = str(Path(folder) / f"{number}.zip")
                try:
                    digests[url] = fetch(url, Path(path))
                    paths[url] = path
                except Exception as error:  # noqa: BLE001 - one missing ZIP mustn't sink the run
                    print(f"warning: {url}: {error}", file=sys.stderr)
            found = parse_clamscan(scanner(list(paths.values())), list(paths.values())) if paths else {}
            for url, path in paths.items():
                reports[url] = {"sha256": digests[url], **report_of(found[path]), "engine": engine, "signatures": signatures, "scannedAt": now()}
                print(f"{reports[url]['result']}: {url}")
    return reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--index", action="append", default=[])
    parser.add_argument("--old")
    args = parser.parse_args()
    indexes = [index for index in map(read_json, args.index) if index.get("releases")]
    if not indexes:
        # Publishing now would drop every report: keep the last ones instead.
        print("error: no release index to scan", file=sys.stderr)
        return 1
    entries = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"] + EXTRA_ENTRIES
    wanted = wanted_assets(indexes, entries)
    kept, todo = plan(wanted, read_json(args.old).get("files") or {}, datetime.now(timezone.utc))
    batches = budget(todo, wanted)
    files = {**kept, **scan(batches)}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # Compact: DeckyHub downloads the whole file for one Manage window.
    (out / "scans.json").write_text(json.dumps({"generatedAt": now(), "files": {url: files[url] for url in wanted if url in files}}, separators=(",", ":")), encoding="utf-8")
    results = [report["result"] for report in files.values()]
    print(f"{len(files)} of {len(wanted)} ZIPs have a report ({sum(map(len, batches))} scanned this run): " + ", ".join(f"{results.count(result)} {result}" for result in ("clean", "infected", "incomplete", "error")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
