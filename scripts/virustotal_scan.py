"""Backfill VirusTotal reports for the public ZIPs hashed by the registry scanner."""
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

API = "https://www.virustotal.com/api/v3"
MAX_ZIP = 650_000_000
REQUEST_BUDGET = 120


class BudgetExhausted(Exception):
    pass


class VirusTotal:
    def __init__(self, key):
        self.key = key
        self.remaining = REQUEST_BUDGET
        self.next_request = 0

    def request(self, url, body=None, content_type=None):
        endpoint = urlsplit(url)
        if endpoint.scheme != "https" or endpoint.hostname != "www.virustotal.com":
            raise ValueError("Unexpected VirusTotal endpoint")
        if not self.remaining:
            raise BudgetExhausted
        time.sleep(max(0, self.next_request - time.monotonic()))
        self.remaining -= 1
        self.next_request = time.monotonic() + 16
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=body, headers=headers)
        request.add_unredirected_header("x-apikey", self.key)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)["data"]
        except urllib.error.HTTPError as error:
            if error.code == 429:
                raise BudgetExhausted from error
            raise

    def upload(self, url, digest):
        with urllib.request.urlopen(url, timeout=120) as response:
            if urlsplit(response.geturl()).scheme != "https":
                raise ValueError("ZIP redirected off HTTPS")
            data = response.read(MAX_ZIP + 1)
        if len(data) > MAX_ZIP:
            return {"state": "unsupported", "reason": "ZIP exceeds VirusTotal's upload limit"}
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("ZIP checksum changed since the registry scan")
        endpoint = f"{API}/files"
        if len(data) > 32_000_000:
            endpoint = self.request(f"{API}/files/upload_url")
        boundary = os.urandom(24).hex()
        prefix = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="plugin.zip"\r\nContent-Type: application/zip\r\n\r\n'.encode()
        body = b"".join((prefix, data, f"\r\n--{boundary}--\r\n".encode()))
        analysis = self.request(endpoint, body, f"multipart/form-data; boundary={boundary}")
        return {"state": "pending", "analysisId": analysis["id"]}


def report(stats, scanned_at):
    return {"state": "complete", "stats": stats, "scannedAt": scanned_at}


def process(client, digest, url, previous):
    if previous.get("state") == "pending":
        analysis = client.request(f"{API}/analyses/{previous['analysisId']}")["attributes"]
        if analysis["status"] != "completed":
            return previous
        return report(analysis["stats"], analysis["date"])
    try:
        file = client.request(f"{API}/files/{digest}")["attributes"]
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        return client.upload(url, digest)
    if not file.get("last_analysis_stats"):
        return {"state": "waiting"}
    return report(file["last_analysis_stats"], file.get("last_analysis_date"))


def main(scans_path, reports_path):
    files = json.loads(scans_path.read_text(encoding="utf-8"))["files"]
    reports = json.loads(reports_path.read_text(encoding="utf-8"))["reports"] if reports_path.exists() else {}
    wanted = {}
    for url, scan in files.items():
        digest = (scan.get("sha256") or "").lower()
        if re.fullmatch(r"[0-9a-f]{64}", digest) and re.fullmatch(
            r"https://github\.com/[^/]+/[^/]+/releases/download/[^/]+/[^/?#]+", url
        ):
            wanted.setdefault(digest, url)
    client = VirusTotal(os.environ["VIRUSTOTAL_API_KEY"])
    # Give new hashes a turn before retrying earlier failures or pending analyses.
    for digest in sorted(wanted, key=lambda value: reports.get(value, {}).get("checkedAt", 0)):
        previous = reports.get(digest, {})
        if previous.get("state") in {"complete", "unsupported"}:
            continue
        try:
            result = process(client, digest, wanted[digest], previous)
        except BudgetExhausted:
            break
        except urllib.error.HTTPError as error:
            if error.code in {401, 403}:
                raise RuntimeError(f"VirusTotal or asset access denied (HTTP {error.code})") from None
            result = {**previous, "lastError": f"HTTP {error.code}"}
        except (OSError, ValueError) as error:
            result = {**previous, "lastError": type(error).__name__}
        reports[digest] = {"state": "error", **result, "checkedAt": int(time.time())}
    reports_path.write_text(json.dumps({"reports": reports}, separators=(",", ":")), encoding="utf-8")
    print(f"{len(wanted)} eligible ZIP hashes, {REQUEST_BUDGET - client.remaining} VirusTotal requests")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
