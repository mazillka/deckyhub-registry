"""Scan every plugin ZIP DeckyHub can install with ClamAV and YARA, and publish one report per ZIP.

    python scripts/virus_scan.py OUT_DIR --index RELEASES_JSON [--index ...] [--old SCANS_JSON] [--yara-rules RULES_YAR]

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
- yara: the same fields (but sha256) for YARA's scan of the files inside the ZIP, with
  YARA Forge's core rules (--yara-rules, which the workflow downloads each run). found
  lists the rules that matched (infected); incomplete means YARA couldn't look at some
  of the files (reason says which). The top-level fields stay ClamAV's alone, as every
  DeckyHub release before this one reads them ("Scanned by ClamAV"); a report without
  yara, or with a YARA error, is scanned again. Each scanner's last good result is kept
  when only its rescan fails.

OUT_DIR/plugins.json is the same reports per plugin, for the registry's catalog page
(docs/index.html): keyed by lowercase owner/name, the ZIP each channel installs (stable:
the newest stable release; prerelease: the newest release, only when it's another ZIP),
with its tag, file name, sha256, and ClamAV's and YARA's verdicts (result, found,
reason, scannedAt). A ZIP not scanned yet has no verdicts.

OUT_DIR/badges/<owner>/<name>/clamav.json and yara.json are shields.io endpoint badges
(https://shields.io/badges/endpoint-badge) for the ZIP the plugin's Stable channel installs
(else its Pre-release one), for READMEs, DeckyHub's own included:
https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/mazillka/deckyhub-registry/virus-scans/badges/<owner>/<name>/clamav.json

Every plugin gets a report: each run downloads at most MAX_RUN_BYTES, every plugin's
Stable and Pre-release channel releases first (by_priority), then older ones, so the first runs work through the backlog over a
few hours and later runs only see new releases. A ZIP not scanned yet has no report:
DeckyHub says so rather than calling it clean. Each run logs how many plugins still have
none.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

from build_release_index import EXTRA_ENTRIES
from validate import load_registry_apps, REGISTRY, matching_assets

MAX_RUN_BYTES = 6 * 1024**3
MAX_BATCH_BYTES = 512 * 1024**2
# The workflow's job stops at 120 minutes, and scans.json is only published at the end,
# so a run that overran would lose everything it scanned. No new batch starts after
# MAX_RUN_SECONDS, and one batch's clamscan gets at most BATCH_SECONDS; what's left waits
# for the next run.
MAX_RUN_SECONDS = 70 * 60
BATCH_SECONDS = 25 * 60
RESCAN_DAYS = 30
# Generous limits (GitHub release files go up to 2 GB, and a plugin bundling many small
# files can take ClamAV minutes: its default of 2 minutes a file left 10 ZIPs half-scanned
# on the first run), so a big plugin is still looked into rather than skipped; past them
# ClamAV raises Heuristics.Limits.Exceeded, reported as incomplete.
CLAMSCAN = ["clamscan", "--no-summary", "--stdout", "--max-filesize=2048M", "--max-scansize=4095M", "--max-files=200000", "--max-recursion=32", "--max-scantime=600000", "--alert-exceeds-max=yes"]
LIMITS = "Heuristics.Limits.Exceeded"
# YARA doesn't open archives, so each ZIP's files are unpacked (one at a time, under
# numbered names, never the ZIP's own paths) and scanned. Past these limits the rest of a
# ZIP is left out and its report is incomplete. YARA_FILE_SECONDS is yara's own timeout
# per file; YARA_ZIP_SECONDS stops a whole ZIP's scan.
AUDIT_MAX_FILES = 10000
AUDIT_MAX_FILE_BYTES = 2 * 1024**2
AUDIT_MAX_BYTES = 64 * 1024**2
AUDIT_MAX_FINDINGS = 200
YARA_MAX_FILES = 200000
YARA_MAX_BYTES = 4 * 1024**3
YARA_FILE_SECONDS = 60
YARA_ZIP_SECONDS = 10 * 60


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


def verdict(report: dict) -> dict:
    return {key: report[key] for key in ("result", "found", "reason", "scannedAt") if report.get(key)}


def plugin_summary(indexes: list[dict], entries: list[dict], files: dict[str, dict]) -> dict[str, dict]:
    """Per repo, the ZIP each channel installs and what the scanners made of it (see the
    docstring above). The first index that lists a repo wins, as in DeckyHub."""
    filters = {entry["repo"].casefold(): entry for entry in entries}
    plugins: dict[str, dict] = {}
    for index in indexes:
        for repo, releases in (index.get("releases") or {}).items():
            if repo.casefold() in plugins or not releases:
                continue
            entry = filters.get(repo.casefold(), {"asset": {"include": [], "exclude": []}})
            stable = next((release for release in releases if not release.get("prerelease")), None)
            channels, urls = {}, {}
            for channel, release in (("stable", stable), ("prerelease", releases[0])):
                assets = [asset for asset in matching_assets(entry, release) if str(asset.get("browser_download_url") or "").startswith("https://")] if release else []
                if not assets or assets[0]["browser_download_url"] in urls.values():
                    continue
                url = urls[channel] = assets[0]["browser_download_url"]
                report = files.get(url) or {}
                sha256 = report.get("sha256") or (assets[0].get("digest") or "").removeprefix("sha256:")
                channels[channel] = {"tag": release.get("tag_name") or "", "file": assets[0].get("name") or "", **({"sha256": sha256} if sha256 else {})}
                if report:
                    channels[channel]["clamav"] = verdict(report)
                    if report.get("yara"):
                        channels[channel]["yara"] = verdict(report["yara"])
                    if report.get("audit"):
                        channels[channel]["audit"] = report["audit"]
            if channels:
                plugins[repo.casefold()] = channels
    return plugins


BADGE_MESSAGES = {"clean": ("no threats", "brightgreen"), "infected": ("threat found", "red"), "incomplete": ("partly scanned", "orange"), "error": ("not scanned", "orange")}


def badges(plugins: dict[str, dict]) -> dict[str, dict]:
    """A shields.io endpoint badge per plugin and scanner, keyed by its path under badges/."""
    out = {}
    for repo, channels in plugins.items():
        channel = channels.get("stable") or channels.get("prerelease") or {}
        for scanner, label in (("clamav", "ClamAV"), ("yara", "YARA")):
            message, color = BADGE_MESSAGES.get((channel.get(scanner) or {}).get("result"), ("not scanned yet", "lightgrey"))
            out[f"{repo}/{scanner}.json"] = {"schemaVersion": 1, "label": label, "message": f"{message} ({channel['tag']})" if channel.get("tag") else message, "color": color}
    return out


def plan(wanted: dict[str, dict], old: dict[str, dict], today: datetime) -> tuple[dict[str, dict], list[str]]:
    """The old reports still good for a wanted ZIP, and the URLs to scan: never-scanned,
    failed and incomplete ones, and ones YARA hasn't scanned or couldn't (in wanted's
    order), before stale reports (oldest first). Those reports are kept meanwhile, so a
    failed retry doesn't take them away."""
    kept, new, stale = {}, [], []
    for url, asset in wanted.items():
        report = old.get(url)
        if not report or (asset["sha256"] and report.get("sha256") != asset["sha256"]) or report.get("result") == "error":
            new.append(url)
            continue
        kept[url] = report
        if report.get("result") == "incomplete" or (report.get("yara") or {}).get("result") in (None, "error") or (report.get("audit") or {}).get("result") in (None, "error"):
            new.append(url)
            continue
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


def rules_version(rules: Path) -> str:
    """'YARA Forge core 2026-11-01' from the header YARA Forge writes atop its rule file."""
    header = {}
    with rules.open(encoding="utf-8", errors="replace") as file:
        for line, _ in zip(file, range(40)):
            key, _, value = line.strip(" */\n").partition(": ")
            header[key] = value.strip()
    return " ".join(part for part in ("YARA Forge", header.get("Name"), header.get("Creation Date")) if part) if header.get("Name") else rules.name


def unpack(zip_path: Path, folder: Path) -> tuple[list[str], list[str]]:
    """Writes the ZIP's files into folder as 0, 1, 2…: their names in the ZIP, in that
    order, and the ones left out (unreadable, encrypted, or past the limits)."""
    names, skipped, total = [], [], 0
    with zipfile.ZipFile(zip_path) as archive:
        members = [info for info in archive.infolist() if not info.is_dir()]
        for info in members:
            if len(names) >= YARA_MAX_FILES or total + info.file_size > YARA_MAX_BYTES:
                skipped.append(info.filename)
                continue
            target = folder / str(len(names))
            try:
                # ZipExtFile stops at the size the ZIP states, so a bomb can't fill the disk.
                with archive.open(info) as source, target.open("wb") as out:
                    while chunk := source.read(1 << 20):
                        out.write(chunk)
            except (RuntimeError, NotImplementedError, zipfile.BadZipFile, zlib.error, EOFError, OSError):
                target.unlink(missing_ok=True)
                skipped.append(info.filename)
                continue
            names.append(info.filename)
            total += info.file_size
    return names, skipped


def parse_yara(stdout: str, stderr: str, folder: str, names: list[str]) -> tuple[list[str], list[str], str | None]:
    """The rules that matched, the files (by their name in the ZIP) YARA couldn't scan,
    and anything else it complained about. A match is 'RuleName /folder/7'."""
    def name_of(path: str) -> str | None:
        number = path.removeprefix(folder.rstrip("/") + "/")
        return names[int(number)] if number.isdigit() and int(number) < len(names) else None

    found, failed, other = set(), [], []
    for line in stdout.splitlines():
        rule, _, path = line.partition(" ")
        if rule and name_of(path.strip()) is not None:
            found.add(rule)
    for line in stderr.splitlines():
        if line.startswith("error scanning "):
            path, _, _ = line.removeprefix("error scanning ").rpartition(": ")
            failed.append(name_of(path) or path)
        elif line.strip():
            other.append(line.strip())
    return sorted(found), failed, "; ".join(other) or None


class Yara:
    """YARA with one compiled rule file. unavailable says why it can't scan this run."""

    def __init__(self, rules: str | None, folder: Path):
        self.engine, self.signatures, self.unavailable, self.compiled = "", "", None, str(folder / "rules.yarc")
        if not rules or not Path(rules).is_file():
            self.unavailable = "YARA's rules couldn't be downloaded"
            return
        try:
            self.engine = "YARA " + subprocess.run(["yara", "--version"], capture_output=True, text=True, check=True).stdout.strip()
            compiled = subprocess.run(["yarac", "-w", rules, self.compiled], capture_output=True, text=True, check=False)
            if compiled.returncode:
                self.unavailable = f"YARA couldn't compile its rules: {(compiled.stderr or compiled.stdout).strip()[:300]}"
            self.signatures = rules_version(Path(rules))
        except Exception as error:  # noqa: BLE001
            self.unavailable = f"YARA couldn't run: {error}"

    def scan(self, zip_path: str) -> dict:
        """One ZIP's YARA report: clean, infected (found: the rules that matched),
        incomplete (reason: the files it couldn't look at) or error (reason)."""
        with tempfile.TemporaryDirectory() as folder:
            try:
                names, skipped = unpack(Path(zip_path), Path(folder))
            except (zipfile.BadZipFile, OSError) as error:
                return {"result": "incomplete", "reason": f"YARA couldn't open the ZIP: {error}"}
            try:
                done = subprocess.run(["yara", "-C", "-w", "-r", "-p", "4", "-a", str(YARA_FILE_SECONDS), self.compiled, folder], capture_output=True, text=True, check=False, timeout=YARA_ZIP_SECONDS) if names else None
            except subprocess.TimeoutExpired:
                return {"result": "error", "reason": f"YARA didn't finish within {YARA_ZIP_SECONDS // 60} minutes"}
            found, failed, other = parse_yara(done.stdout, done.stderr, folder, names) if done else ([], [], None)
            if done and done.returncode and other and not found:
                return {"result": "error", "reason": f"YARA: {other[:300]}"}
            if found:
                return {"result": "infected", "found": found}
            if skipped or failed:
                left = skipped + failed
                return {"result": "incomplete", "reason": f"YARA couldn't look at {len(left)} file{'s' if len(left) != 1 else ''} in it: {', '.join(left[:5])}{' …' if len(left) > 5 else ''}"}
            return {"result": "clean"}


def audit_zip(path: str) -> dict:
    """Bounded static inspection of ZIP members, without extracting or executing them."""
    result = {"result": "complete", "root": None, "findings": [], "scannedAt": now()}
    try:
        with zipfile.ZipFile(path) as archive:
            members = [i for i in archive.infolist() if not i.is_dir()]
            manifests = [i for i in members if i.filename.split("/")[-1] == "plugin.json" and "node_modules" not in i.filename.split("/")[:-1]]
            if manifests:
                depth = min(i.filename.count("/") for i in manifests)
                candidates = [i for i in manifests if i.filename.count("/") == depth]
            else:
                candidates = []
            selected = candidates[0] if len(candidates) == 1 else None
            total = 0
            for number, info in enumerate(members):
                if number >= AUDIT_MAX_FILES or info.file_size > AUDIT_MAX_FILE_BYTES or total + info.file_size > AUDIT_MAX_BYTES or info.flag_bits & 1:
                    result["result"] = "incomplete"
                    continue
                total += info.file_size
                try:
                    data = archive.read(info)
                    if b"\x00" in data:
                        result["result"] = "incomplete"
                        continue
                    content = data.decode("utf-8")
                except (UnicodeError, RuntimeError, NotImplementedError, zipfile.BadZipFile, zlib.error, EOFError, OSError):
                    result["result"] = "incomplete"
                    continue
                if info is selected:
                    try:
                        manifest = json.loads(content)
                        flags = manifest.get("flags") if isinstance(manifest, dict) else None
                        if isinstance(flags, list) and all(isinstance(f, str) for f in flags):
                            result["root"] = "root" in flags
                    except ValueError:
                        result["result"] = "incomplete"
                for line_number, line in enumerate(content.splitlines(), 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith(("#", "//", "*")):
                        continue
                    tls = re.search(r"\brequests\.(?:get|post|put|delete|patch|head|options|request)\s*\([^\n]*\bverify\s*=\s*False\b|\bssl\.CERT_NONE\b|\bcurl\b[^|;\n]*(?:\s-k(?:\s|$)|\s--insecure(?:\s|$))", line)
                    pipe = re.search(r"\b(?:curl|wget)\b[^|;\n]*\|\s*(?:/bin/|/usr/bin/)?(?:ba)?sh\b", line)
                    for rule, match in (("no-tls-check", tls), ("runs-downloads", pipe)):
                        if match:
                            if len(result["findings"]) < AUDIT_MAX_FINDINGS:
                                result["findings"].append({"rule": rule, "path": info.filename, "line": line_number})
                            else:
                                result["result"] = "incomplete"
    except (zipfile.BadZipFile, OSError, ValueError):
        result["result"] = "error"
    return result


def scan(batches: list[list[str]], scanner=clamscan, fetch=download, version=clamav_version, yara=None, keep: dict[str, dict] | None = None, deadline: float | None = None, clock=time.monotonic) -> dict[str, dict]:
    """A report for every URL in the batches it gets to, from ClamAV and from yara (a
    Yara; None: not set up). Nothing here fails the run: a ZIP that can't be downloaded
    or scanned, or a scanner that can't run at all, gets an error saying why (scanned
    again next run). keep has the URLs' last reports: a scanner's good result there stays
    when its rescan fails. Past deadline (a clock() time) no new batch starts, so the run
    can still publish; the rest have no report yet and come first next run."""
    keep = keep or {}
    reports: dict[str, dict] = {}
    if not batches:
        return reports
    try:
        engine, signatures = version()
        unavailable = None if signatures else "ClamAV couldn't load its virus signatures"
    except Exception as error:  # noqa: BLE001
        engine, signatures, unavailable = "", "", f"ClamAV couldn't run: {error}"
    yara_unavailable = yara.unavailable if yara is not None else "YARA wasn't set up for this run"

    def stamped(report: dict, engine: str, signatures: str) -> dict:
        return {**report, **({"engine": engine} if engine else {}), **({"signatures": signatures} if signatures else {}), "scannedAt": now()}

    def record(url: str, clam: dict, found_by_yara: dict, sha256: str | None = None, audit: dict | None = None):
        old = keep.get(url) or {}
        if sha256 and old.get("sha256") != sha256:
            old = {}
        old_yara = old.get("yara") or {}
        old_audit = old.get("audit") or {}
        if (not audit or audit.get("result") == "error") and old_audit.get("result") in ("complete", "incomplete"):
            audit = old_audit
        kept_clam = clam["result"] == "error" and old and old.get("result") != "error"
        kept_yara = found_by_yara["result"] == "error" and old_yara and old_yara.get("result") != "error"
        if kept_clam and kept_yara and not audit:
            print(f"kept the last report ({clam['reason']}; {found_by_yara['reason']}): {url}")
            return
        clam = {key: value for key, value in old.items() if key not in ("sha256", "yara", "audit")} if kept_clam else stamped(clam, engine, signatures)
        found_by_yara = old_yara if kept_yara else stamped(found_by_yara, yara.engine if yara else "", yara.signatures if yara else "")
        sha256 = sha256 or old.get("sha256")
        reports[url] = {**({"sha256": sha256} if sha256 else {}), **clam, "yara": found_by_yara, **({"audit": audit} if audit else {})}
        print(f"ClamAV {clam['result']}, YARA {found_by_yara['result']}: {url}" + "".join(f" ({part['reason']})" for part in (clam, found_by_yara) if "reason" in part))

    for number, batch in enumerate(batches):
        if deadline is not None and clock() > deadline:
            print(f"out of time: {sum(map(len, batches[number:]))} ZIPs left for the next run")
            break
        with tempfile.TemporaryDirectory() as folder:
            paths, digests = {}, {}
            for number, url in enumerate(batch):
                path = str(Path(folder) / f"{number}.zip")
                try:
                    digests[url] = fetch(url, Path(path))
                    paths[url] = path
                except Exception as error:  # noqa: BLE001 - one missing ZIP mustn't sink the run
                    failed = {"result": "error", "reason": f"Couldn't download it: {error}"}
                    record(url, failed, failed)
            try:
                if unavailable:
                    found = {path: unavailable for path in paths.values()}
                else:
                    found = parse_clamscan(scanner(list(paths.values())), list(paths.values())) if paths else {}
            except subprocess.TimeoutExpired:
                found = {path: f"ClamAV didn't finish within {BATCH_SECONDS // 60} minutes" for path in paths.values()}
            except Exception as error:  # noqa: BLE001
                found = {path: f"ClamAV couldn't run: {error}" for path in paths.values()}
            for url, path in paths.items():
                if yara_unavailable:
                    found_by_yara = {"result": "error", "reason": yara_unavailable}
                else:
                    try:
                        found_by_yara = yara.scan(path)
                    except Exception as error:  # noqa: BLE001
                        found_by_yara = {"result": "error", "reason": f"YARA couldn't run: {error}"}
                try:
                    audit = audit_zip(path)
                except Exception:  # audit failure must not prevent publication
                    audit = {"result": "error", "root": None, "findings": [], "scannedAt": now()}
                record(url, report_of(found[path]), found_by_yara, digests[url], audit)
    return reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--index", action="append", default=[])
    parser.add_argument("--old")
    parser.add_argument("--yara-rules", help="YARA Forge's rule file (.yar); without it every scanned ZIP gets a YARA error")
    args = parser.parse_args()
    indexes = [index for index in map(read_json, args.index) if index.get("releases")]
    if not indexes:
        # Publishing now would drop every report: keep the last ones instead.
        print("error: no release index to scan", file=sys.stderr)
        return 1
    entries = load_registry_apps(REGISTRY) + EXTRA_ENTRIES
    wanted = wanted_assets(indexes, entries)
    kept, todo = plan(wanted, read_json(args.old).get("files") or {}, datetime.now(timezone.utc))
    batches = budget(todo, wanted)
    with tempfile.TemporaryDirectory() as folder:
        yara = Yara(args.yara_rules, Path(folder)) if batches else None
        if yara and yara.unavailable:
            print(f"warning: {yara.unavailable}", file=sys.stderr)
        files = {**kept, **scan(batches, yara=yara, keep=kept, deadline=time.monotonic() + MAX_RUN_SECONDS)}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # Compact: DeckyHub downloads the whole file for one Manage window.
    (out / "scans.json").write_text(json.dumps({"generatedAt": now(), "files": {url: files[url] for url in wanted if url in files}}, separators=(",", ":")), encoding="utf-8")
    plugins = plugin_summary(indexes, entries, files)
    (out / "plugins.json").write_text(json.dumps({"generatedAt": now(), "plugins": plugins}, separators=(",", ":")), encoding="utf-8")
    for path, badge in badges(plugins).items():
        target = out / "badges" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(badge, separators=(",", ":")), encoding="utf-8")
    results = [report["result"] for report in files.values()]
    picks = channel_assets(indexes)
    missing = sorted(repo for repo, releases in picks.items() if not all(any(url in files for url in urls) for urls in releases))
    print(f"{len(picks) - len(missing)} of {len(picks)} plugins have a report for both their Stable and Pre-release channel releases" + (f"; still to do: {', '.join(missing[:20])}{' …' if len(missing) > 20 else ''}" if missing else ""))
    yara_results = [(report.get("yara") or {}).get("result") for report in files.values()]
    print(f"{len(files)} of {len(wanted)} ZIPs have a report ({sum(map(len, batches))} scanned this run): ClamAV " + ", ".join(f"{results.count(result)} {result}" for result in ("clean", "infected", "incomplete", "error")) + "; YARA " + ", ".join(f"{yara_results.count(result)} {result}" for result in ("clean", "infected", "incomplete", "error")) + f", {yara_results.count(None)} not yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
