"""Backfill MetaDefender reports for public plugin ZIPs from the registry scanner."""
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

API = "https://api.metadefender.com/v4"
MAX_ZIP = 650_000_000
REQUEST_BUDGET = 120


class BudgetExhausted(Exception):
    pass


class HttpsRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != "https":
            raise ValueError("ZIP redirected off HTTPS")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class MetaDefender:
    def __init__(self, key):
        self.key = key
        self.remaining = REQUEST_BUDGET
        self.next_request = 0

    def request(self, path, data=None):
        if not re.fullmatch(r"/(?:hash/[0-9a-f]{64}|file(?:/[A-Za-z0-9_-]+)?)", path):
            raise ValueError("Unexpected MetaDefender endpoint")
        if not self.remaining:
            raise BudgetExhausted
        time.sleep(max(0, self.next_request - time.monotonic()))
        self.remaining -= 1
        self.next_request = time.monotonic() + 16
        headers = {"Content-Type": "application/octet-stream", "filename": "plugin.zip"} if data is not None else {}
        request = urllib.request.Request(API + path, data=data, headers=headers)
        request.add_unredirected_header("apikey", self.key)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 429:
                raise BudgetExhausted from error
            raise

    def upload(self, url, digest):
        opener = urllib.request.build_opener(HttpsRedirect())
        with opener.open(url, timeout=120) as response:
            data = response.read(MAX_ZIP + 1)
        if len(data) > MAX_ZIP:
            return {"state": "unsupported", "reason": "ZIP exceeds the upload limit"}
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("ZIP checksum changed since the registry scan")
        try:
            result = self.request("/file", data)
        except urllib.error.HTTPError as error:
            if error.code == 413:
                return {"state": "unsupported", "reason": "ZIP exceeds MetaDefender's upload limit"}
            raise
        return {"state": "pending", "dataId": result["data_id"]}


def process(client, digest, url, previous):
    if previous.get("state") == "pending":
        result = client.request(f"/file/{previous['dataId']}")
    else:
        try:
            result = client.request(f"/hash/{digest}")
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            return client.upload(url, digest)
    scan = result.get("scan_results") or {}
    if scan.get("progress_percentage") != 100:
        data_id = result.get("data_id") or previous.get("dataId")
        return {"state": "pending", "dataId": data_id} if data_id else {"state": "waiting"}
    flagged, total = scan.get("total_detected_avs"), scan.get("total_avs")
    if not isinstance(flagged, int) or not isinstance(total, int) or total <= 0 or flagged < 0 or flagged > total:
        return {"state": "waiting"}
    # A zero detection count is not a clean verdict if the service skipped or
    # could not fully scan the archive (encrypted, size limits, errors, etc.).
    if flagged == 0 and scan.get("scan_all_result_i") != 0:
        return {"state": "waiting"}
    return {"state": "complete", "flagged": flagged, "total": total, "dataId": result.get("data_id") or previous.get("dataId"), "scannedAt": scan.get("start_time")}


def main(scans_path, reports_path):
    files = json.loads(scans_path.read_text(encoding="utf-8"))["files"]
    reports = json.loads(reports_path.read_text(encoding="utf-8"))["reports"] if reports_path.exists() else {}
    wanted = {}
    for url, scan in files.items():
        digest = (scan.get("sha256") or "").lower()
        if re.fullmatch(r"[0-9a-f]{64}", digest) and re.fullmatch(r"https://github\.com/[^/]+/[^/]+/releases/download/[^/]+/[^/?#]+", url):
            wanted.setdefault(digest, url)
    client = MetaDefender(os.environ["METADEFENDER_API_KEY"])
    # Pending uploads first: they only need one poll each, and new hashes (never checked, so
    # checkedAt 0) would otherwise take the whole daily budget until every one was seen.
    order = lambda value: (reports.get(value, {}).get("state") != "pending", reports.get(value, {}).get("checkedAt", 0))
    for digest in sorted(wanted, key=order):
        previous = reports.get(digest, {})
        if previous.get("state") in {"complete", "unsupported"}:
            continue
        try:
            result = process(client, digest, wanted[digest], previous)
        except BudgetExhausted:
            break
        except urllib.error.HTTPError as error:
            if error.code in {401, 403}:
                raise RuntimeError(f"MetaDefender or asset access denied (HTTP {error.code})") from None
            result = {**previous, "lastError": f"HTTP {error.code}"}
        except (OSError, ValueError, KeyError) as error:
            result = {**previous, "lastError": type(error).__name__}
        reports[digest] = {"state": "error", **result, "checkedAt": int(time.time())}
    reports_path.write_text(json.dumps({"reports": reports}, separators=(",", ":")), encoding="utf-8")
    print(f"{len(wanted)} eligible ZIP hashes, {REQUEST_BUDGET - client.remaining} MetaDefender requests")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
