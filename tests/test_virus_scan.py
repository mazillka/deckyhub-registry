import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import virus_scan  # noqa: E402
from virus_scan import budget, parse_clamscan, plan, report_of, scan, wanted_assets  # noqa: E402

TODAY = datetime(2026, 11, 2, tzinfo=timezone.utc)


def asset(name, url, size=10, digest="sha256:aa"):
    return {"name": name, "browser_download_url": url, "size": size, "digest": digest}


class WantedAssetsTests(unittest.TestCase):
    def test_newest_release_of_every_repo_comes_first_and_filters_apply(self):
        entries = [{"repo": "O/A", "asset": {"include": [], "exclude": ["source"]}}]
        index = {"releases": {
            "o/a": [{"assets": [asset("a2.zip", "https://x/a2"), asset("source.zip", "https://x/src"), asset("notes.txt", "https://x/t")]}, {"assets": [asset("a1.zip", "https://x/a1")]}],
            "o/b": [{"assets": [asset("b2.zip", "https://x/b2")]}],
        }}
        develop = {"releases": {"o/b": [{"assets": [asset("b2.zip", "https://x/b2"), asset("b3.zip", "http://x/b3")]}]}}
        self.assertEqual(list(wanted_assets([index, develop], entries)), ["https://x/a2", "https://x/b2", "https://x/a1"])
        self.assertEqual(wanted_assets([index], entries)["https://x/a2"], {"sha256": "aa", "size": 10})


class PlanTests(unittest.TestCase):
    def test_keeps_fresh_reports_and_rescans_new_changed_failed_and_stale_ones(self):
        wanted = {url: {"sha256": "aa", "size": 1} for url in ("new", "same", "changed", "failed", "old", "older")}
        wanted["nodigest"] = {"sha256": None, "size": 1}
        old = {
            "same": {"sha256": "aa", "result": "clean", "scannedAt": "2026-11-01T00:00:00Z"},
            "changed": {"sha256": "bb", "result": "clean", "scannedAt": "2026-11-01T00:00:00Z"},
            "failed": {"sha256": "aa", "result": "error", "scannedAt": "2026-11-01T00:00:00Z"},
            "old": {"sha256": "aa", "result": "clean", "scannedAt": "2026-09-01T00:00:00Z"},
            "older": {"sha256": "aa", "result": "clean", "scannedAt": "2026-08-01T00:00:00Z"},
            "nodigest": {"sha256": "cc", "result": "clean", "scannedAt": "2026-11-01T00:00:00Z"},
            "gone": {"sha256": "aa", "result": "clean", "scannedAt": "2026-11-01T00:00:00Z"},
        }
        kept, todo = plan(wanted, old, TODAY)
        self.assertEqual(set(kept), {"same", "old", "older", "nodigest"})
        self.assertEqual(todo, ["new", "changed", "failed", "older", "old"])

    def test_budget_batches_skips_huge_files_and_stops_at_the_run_limit(self):
        gib = 1024**3
        wanted = {"a": {"size": gib // 2}, "b": {"size": gib // 2}, "c": {"size": gib // 2}, "huge": {"size": 2 * gib}, "d": {"size": gib}, "e": {"size": 1}}
        limit = virus_scan.MAX_RUN_BYTES
        virus_scan.MAX_RUN_BYTES = 2 * gib
        try:
            self.assertEqual(budget(list(wanted), wanted), [["a", "b"], ["c"]])
        finally:
            virus_scan.MAX_RUN_BYTES = limit


class ParseTests(unittest.TestCase):
    def test_results_per_scanned_file(self):
        paths = ["/t/0.zip", "/t/1.zip", "/t/2.zip", "/t/3.zip", "/t/4.zip"]
        output = "\n".join([
            "/t/0.zip: OK",
            "/t/1.zip: Win.Test.EICAR_HDB-1 FOUND",
            "/t/1.zip: Unix.Trojan.Agent-1 FOUND",
            "/t/2.zip: Heuristics.Limits.Exceeded.MaxFileSize FOUND",
            "/t/3.zip: Can't open file or directory ERROR",
            "LibClamAV Warning: something unrelated",
        ])
        found = parse_clamscan(output, paths)
        self.assertEqual([report_of(found[path]) for path in paths], [
            {"result": "clean"},
            {"result": "infected", "found": ["Unix.Trojan.Agent-1", "Win.Test.EICAR_HDB-1"]},
            {"result": "incomplete", "found": ["Heuristics.Limits.Exceeded.MaxFileSize"]},
            {"result": "error"},
            {"result": "error"},
        ])

    def test_a_real_threat_beside_a_limit_is_infected(self):
        self.assertEqual(report_of(["Heuristics.Limits.Exceeded.MaxFiles", "Unix.Malware-1"]), {"result": "infected", "found": ["Unix.Malware-1"]})


class ScanTests(unittest.TestCase):
    def test_reports_carry_digest_engine_and_skip_failed_downloads(self):
        def fetch(url, path):
            if url == "https://x/missing":
                raise OSError("HTTP Error 404")
            path.write_bytes(b"zip")
            return f"digest-of-{url[-1]}"

        reports = scan([["https://x/a", "https://x/missing"], ["https://x/b"]], scanner=lambda paths: "\n".join(f"{path}: OK" for path in paths), fetch=fetch, version=lambda: ("ClamAV 1.4.3", "27806"))
        self.assertEqual(sorted(reports), ["https://x/a", "https://x/b"])
        self.assertEqual({key: value for key, value in reports["https://x/a"].items() if key != "scannedAt"}, {"sha256": "digest-of-a", "result": "clean", "engine": "ClamAV 1.4.3", "signatures": "27806"})

    def test_nothing_to_scan_needs_no_clamav(self):
        self.assertEqual(scan([], version=lambda: self.fail("asked ClamAV")), {})


class MainTests(unittest.TestCase):
    def test_refuses_to_publish_without_an_index(self):
        argv = sys.argv
        sys.argv = ["virus_scan.py", "/nonexistent-out", "--index", "/nonexistent.json"]
        try:
            self.assertEqual(virus_scan.main(), 1)
        finally:
            sys.argv = argv


if __name__ == "__main__":
    unittest.main()
