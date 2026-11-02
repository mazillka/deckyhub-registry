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
  past ClamAV's size limits, so part of it wasn't looked at) or error (reason says why:
  the download failed, ClamAV couldn't read it, or ClamAV couldn't run at all). An error
  never fails the run; the ZIP is tried again next run, and a ZIP that already had a good
  report keeps it.
- engine / signatures: the ClamAV version and signature database version used.
- scannedAt: when. A report older than RESCAN_DAYS is scanned again with newer signatures.

Every plugin gets a report: each run downloads at most MAX_RUN_BYTES, every plugin's
Stable and Pre-release channel releases first (by_priority), then older ones, so the first runs work through the backlog over a
few hours and later runs only see new releases. A ZIP not scanned yet has no report:
DeckyHub says so rather than calling it clean. Each run logs how many plugins still have
none.
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
MAX_BATCH_BYTES = 512 * 1024**2
# The workflow's job stops at 120 minutes, and scans.json is only published at the end,
# so a run that overran would lose everything it scanned. No new batch starts after
# MAX_RUN_SECONDS, and one batch's clamscan gets at most BATCH_SECONDS; what's left waits
# for the next run.
MAX_RUN_SECONDS = 70 * 60
BATCH_SECONDS = 25 * 60
RESCAN_DAYS = 30
# Generous limits (GitHub release files go up to 2 GB), so a big plugin is still looked
# into rather than skipped; past them
# ClamAV raises Heuristics.Limits.Exceeded, reported as incomplete.
CLAMSCAN = ["clamscan", "--no-summary", "--stdout", "--max-filesize=2048M", "--max-scansize=4095M", "--max-files=200000", "--max-recursion=32", "--alert-exceeds-max=yes"]
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


def by_priority(releases: list[dict]) -> list[list[dict]]:
    """A repo's releases (newest first) in scan rounds: first the ones a card offers, the
    Pre-release channel's (the newest) and the Stable channel's (the newest stable, which
    the index may keep last), then the rest one per round, newest first."""
    stable = next((release for release in releases if not release.get("prerelease")), None)
    picks = releases[:1]
    if stable is not None and stable is not releases[0]:
        picks.append(stable)
    return [picks] + [[release] for release in releases if all(release is not pick for pick in picks)]


def channel_assets(indexes: list[dict]) -> dict[str, list[list[str]]]:
    """Per repo, the download URLs of each channel's release (newest, newest stable) in
    every index: what "every plugin has a report" is checked against."""
    picks: dict[str, list[list[str]]] = {}
    for index in indexes:
        for repo, releases in (index.get("releases") or {}).items():
            for release in (by_priority(releases)[0] if releases else []):
                picks.setdefault(repo.casefold(), []).append([asset.get("browser_download_url") or "" for asset in release.get("assets") or []])
    return picks


def wanted_assets(indexes: list[dict], entries: list[dict]) -> dict[str, dict]:
    """Every plugin ZIP in the indexes, keyed by download URL, in scan order: every repo's
    Pre-release and Stable channel releases first (by_priority), then each repo's next
    newest, and so on. A repo the registry no longer lists (only the other branch has it)
    is held to plain .zip."""
    filters = {entry["repo"].casefold(): entry for entry in entries}
    rounds: list[list[tuple[str, dict]]] = []
    for index in indexes:
        for repo, releases in (index.get("releases") or {}).items():
            entry = filters.get(repo.casefold(), {"asset": {"include": [], "exclude": []}})
            for rank, group in enumerate(by_priority(releases)):
                while len(rounds) <= rank:
                    rounds.append([])
                for release in group:
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
        # The first file always fits, however big, so a large plugin can't stall the queue.
        if total and total + bytes_ > MAX_RUN_BYTES:
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


def parse_clamscan(output: str, paths: list[str]) -> dict[str, list[str] | str]:
    """Per scanned path: what ClamAV found ([] when clean), or why it couldn't scan the
    file (a str). A ZIP's inner files are reported as 'path: Name FOUND' too, so matches
    are collected per scanned path."""
    found: dict[str, list[str] | str] = {path: "ClamAV said nothing about this file" for path in paths}
    for line in output.splitlines():
        path, _, verdict = line.rpartition(": ")
        path = next((candidate for candidate in paths if path == candidate or path.startswith(candidate + "/") or path.startswith(candidate + "!")), None)
        if path is None:
            continue
        previous = found[path] if isinstance(found[path], list) else []
        if verdict == "OK":
            found[path] = previous
        elif verdict.endswith(" FOUND"):
            found[path] = sorted({*previous, verdict.removesuffix(" FOUND")})
        elif verdict.endswith("ERROR"):
            found[path] = f"ClamAV: {verdict.removesuffix('ERROR').strip() or 'error'}"
    return found


def report_of(found: list[str] | str) -> dict:
    if isinstance(found, str):
        return {"result": "error", "reason": found}
    if not found:
        return {"result": "clean"}
    threats = [name for name in found if not name.startswith(LIMITS)]
    return {"result": "infected", "found": threats} if threats else {"result": "incomplete", "found": found}


def clamscan(paths: list[str]) -> str:
    # Exit 1 means something was found and 2 an error; both still print per-file lines.
    # Running out of BATCH_SECONDS raises, so the batch's ZIPs get error reports.
    return subprocess.run([*CLAMSCAN, *paths], capture_output=True, text=True, check=False, timeout=BATCH_SECONDS).stdout


def clamav_version() -> tuple[str, str]:
    """('ClamAV 1.4.3', '27806') from 'ClamAV 1.4.3/27806/Sun Nov  1 08:23:01 2026'.
    No signature version means ClamAV has no database to scan with."""
    parts = subprocess.run(["clamscan", "--version"], capture_output=True, text=True, check=True).stdout.strip().split("/")
    return parts[0], parts[1] if len(parts) > 1 else ""


def scan(batches: list[list[str]], scanner=clamscan, fetch=download, version=clamav_version, keep: frozenset[str] = frozenset(), deadline: float | None = None, clock=time.monotonic) -> dict[str, dict]:
    """A report for every URL in the batches it gets to. Nothing here fails the run: a ZIP
    that can't be downloaded or scanned, or a ClamAV that can't run at all, gets an error
    report saying why (scanned again next run). A URL in keep already has a good report,
    which a failed rescan leaves alone. Past deadline (a clock() time) no new batch starts,
    so the run can still publish; the rest have no report yet and come first next run."""
    reports: dict[str, dict] = {}
    if not batches:
        return reports
    try:
        engine, signatures = version()
        unavailable = None if signatures else "ClamAV couldn't load its virus signatures"
    except Exception as error:  # noqa: BLE001
        engine, signatures, unavailable = "", "", f"ClamAV couldn't run: {error}"

    def record(url: str, report: dict, sha256: str | None = None):
        if report["result"] == "error" and url in keep:
            print(f"kept the last report ({report['reason']}): {url}")
            return
        reports[url] = {**({"sha256": sha256} if sha256 else {}), **report, **({"engine": engine} if engine else {}), **({"signatures": signatures} if signatures else {}), "scannedAt": now()}
        print(f"{report['result']}: {url}" + (f" ({report['reason']})" if "reason" in report else ""))

    for number, batch in enumerate(batches):
        if deadline is not None and clock() > deadline:
            print(f"out of time: {sum(map(len, batches[number:]))} ZIPs left for the next run")
            break
        if unavailable:
            for url in batch:
                record(url, {"result": "error", "reason": unavailable})
            continue
        with tempfile.TemporaryDirectory() as folder:
            paths, digests = {}, {}
            for number, url in enumerate(batch):
                path = str(Path(folder) / f"{number}.zip")
                try:
                    digests[url] = fetch(url, Path(path))
                    paths[url] = path
                except Exception as error:  # noqa: BLE001 - one missing ZIP mustn't sink the run
                    record(url, {"result": "error", "reason": f"Couldn't download it: {error}"})
            try:
                found = parse_clamscan(scanner(list(paths.values())), list(paths.values())) if paths else {}
            except subprocess.TimeoutExpired:
                found = {path: f"ClamAV didn't finish within {BATCH_SECONDS // 60} minutes" for path in paths.values()}
            except Exception as error:  # noqa: BLE001
                found = {path: f"ClamAV couldn't run: {error}" for path in paths.values()}
            for url, path in paths.items():
                record(url, report_of(found[path]), digests[url])
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
    files = {**kept, **scan(batches, keep=frozenset(kept), deadline=time.monotonic() + MAX_RUN_SECONDS)}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # Compact: DeckyHub downloads the whole file for one Manage window.
    (out / "scans.json").write_text(json.dumps({"generatedAt": now(), "files": {url: files[url] for url in wanted if url in files}}, separators=(",", ":")), encoding="utf-8")
    results = [report["result"] for report in files.values()]
    picks = channel_assets(indexes)
    missing = sorted(repo for repo, releases in picks.items() if not all(any(url in files for url in urls) for urls in releases))
    print(f"{len(picks) - len(missing)} of {len(picks)} plugins have a report for both their Stable and Pre-release channel releases" + (f"; still to do: {', '.join(missing[:20])}{' …' if len(missing) > 20 else ''}" if missing else ""))
    print(f"{len(files)} of {len(wanted)} ZIPs have a report ({sum(map(len, batches))} scanned this run): " + ", ".join(f"{results.count(result)} {result}" for result in ("clean", "infected", "incomplete", "error")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
