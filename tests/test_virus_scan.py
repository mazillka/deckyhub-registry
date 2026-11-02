import shutil
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import virus_scan  # noqa: E402
from virus_scan import Yara, badges, budget, channel_assets, parse_clamscan, parse_yara, plan, plugin_summary, report_of, rules_version, scan, unpack, wanted_assets  # noqa: E402

TODAY = datetime(2026, 11, 2, tzinfo=timezone.utc)
YARA_OK = {"result": "clean", "scannedAt": "2026-11-01T00:00:00Z"}


class FakeYara:
    engine, signatures, unavailable = "YARA 4.5.0", "YARA Forge core 2026-11-01", None

    def __init__(self, report=None):
        self.report = report or {"result": "clean"}

    def scan(self, path):
        return self.report


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


class ChannelOrderTests(unittest.TestCase):
    def test_stable_and_pre_release_picks_of_every_plugin_come_before_older_releases(self):
        # The index keeps the newest stable last when newer pre-releases came after it.
        index = {"releases": {
            "o/a": [{"prerelease": True, "assets": [asset("a3.zip", "https://x/a3")]}, {"prerelease": True, "assets": [asset("a2.zip", "https://x/a2")]}, {"assets": [asset("a1.zip", "https://x/a1")]}],
            "o/b": [{"assets": [asset("b2.zip", "https://x/b2")]}, {"assets": [asset("b1.zip", "https://x/b1")]}],
        }}
        self.assertEqual(list(wanted_assets([index], [])), ["https://x/a3", "https://x/a1", "https://x/b2", "https://x/a2", "https://x/b1"])

    def test_coverage_counts_both_channels(self):
        index = {"releases": {"o/a": [{"prerelease": True, "assets": [asset("a2.zip", "https://x/a2")]}, {"assets": [asset("a1.zip", "https://x/a1")]}], "o/b": []}}
        self.assertEqual(channel_assets([index]), {"o/a": [["https://x/a2"], ["https://x/a1"]]})


class PlanTests(unittest.TestCase):
    def test_keeps_fresh_reports_and_rescans_new_changed_failed_and_stale_ones(self):
        wanted = {url: {"sha256": "aa", "size": 1} for url in ("new", "same", "changed", "failed", "partial", "old", "older")}
        wanted["nodigest"] = {"sha256": None, "size": 1}
        old = {
            "same": {"sha256": "aa", "result": "clean", "scannedAt": "2026-11-01T00:00:00Z"},
            "changed": {"sha256": "bb", "result": "clean", "scannedAt": "2026-11-01T00:00:00Z"},
            "failed": {"sha256": "aa", "result": "error", "scannedAt": "2026-11-01T00:00:00Z"},
            "partial": {"sha256": "aa", "result": "incomplete", "found": ["Heuristics.Limits.Exceeded.MaxScanTime"], "scannedAt": "2026-11-01T00:00:00Z"},
            "old": {"sha256": "aa", "result": "clean", "scannedAt": "2026-09-01T00:00:00Z"},
            "older": {"sha256": "aa", "result": "clean", "scannedAt": "2026-08-01T00:00:00Z"},
            "nodigest": {"sha256": "cc", "result": "clean", "scannedAt": "2026-11-01T00:00:00Z"},
            "gone": {"sha256": "aa", "result": "clean", "scannedAt": "2026-11-01T00:00:00Z"},
        }
        old = {url: {**report, "yara": YARA_OK} for url, report in old.items()}
        kept, todo = plan(wanted, old, TODAY)
        self.assertEqual(set(kept), {"same", "partial", "old", "older", "nodigest"})
        self.assertEqual(todo, ["new", "changed", "failed", "partial", "older", "old"])

    def test_a_report_yara_hasnt_scanned_or_couldnt_is_scanned_again_and_kept_meanwhile(self):
        wanted = {url: {"sha256": "aa", "size": 1} for url in ("clam-only", "yara-failed", "yara-partial", "both")}
        clean = {"sha256": "aa", "result": "clean", "scannedAt": "2026-11-01T00:00:00Z"}
        old = {
            "clam-only": clean,
            "yara-failed": {**clean, "yara": {"result": "error", "reason": "x"}},
            "yara-partial": {**clean, "yara": {"result": "incomplete", "reason": "x"}},
            "both": {**clean, "yara": YARA_OK},
        }
        kept, todo = plan(wanted, old, TODAY)
        self.assertEqual(set(kept), set(wanted))
        # An incomplete YARA scan hit a size limit or an unreadable file: it would again.
        self.assertEqual(todo, ["clam-only", "yara-failed"])

    def test_budget_batches_and_stops_at_the_run_limit(self):
        gib = 1024**3
        wanted = {"a": {"size": gib // 2}, "b": {"size": gib // 2}, "c": {"size": gib // 2}, "d": {"size": gib}, "e": {"size": 1}}
        limits = virus_scan.MAX_RUN_BYTES, virus_scan.MAX_BATCH_BYTES
        virus_scan.MAX_RUN_BYTES, virus_scan.MAX_BATCH_BYTES = 2 * gib, gib
        try:
            self.assertEqual(budget(list(wanted), wanted), [["a", "b"], ["c"]])
        finally:
            virus_scan.MAX_RUN_BYTES, virus_scan.MAX_BATCH_BYTES = limits

    def test_a_file_bigger_than_a_run_is_still_scanned_on_its_own(self):
        wanted = {"huge": {"size": virus_scan.MAX_RUN_BYTES + 1}, "next": {"size": 1}}
        self.assertEqual(budget(list(wanted), wanted), [["huge"]])


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
            {"result": "error", "reason": "ClamAV: Can't open file or directory"},
            {"result": "error", "reason": "ClamAV said nothing about this file"},
        ])

    def test_a_real_threat_beside_a_limit_is_infected(self):
        self.assertEqual(report_of(["Heuristics.Limits.Exceeded.MaxFiles", "Unix.Malware-1"]), {"result": "infected", "found": ["Unix.Malware-1"]})


class ScanTests(unittest.TestCase):
    def test_every_zip_gets_a_report_even_when_its_download_fails(self):
        def fetch(url, path):
            if url == "https://x/missing":
                raise OSError("HTTP Error 404")
            path.write_bytes(b"zip")
            return f"digest-of-{url[-1]}"

        reports = scan([["https://x/a", "https://x/missing"], ["https://x/b"]], scanner=lambda paths: "\n".join(f"{path}: OK" for path in paths), fetch=fetch, version=lambda: ("ClamAV 1.4.3", "27806"), yara=FakeYara())
        self.assertEqual(sorted(reports), ["https://x/a", "https://x/b", "https://x/missing"])
        report = reports["https://x/a"]
        self.assertEqual({key: value for key, value in report.items() if key not in ("scannedAt", "yara")}, {"sha256": "digest-of-a", "result": "clean", "engine": "ClamAV 1.4.3", "signatures": "27806"})
        self.assertEqual({key: value for key, value in report["yara"].items() if key != "scannedAt"}, {"result": "clean", "engine": "YARA 4.5.0", "signatures": "YARA Forge core 2026-11-01"})
        self.assertEqual(reports["https://x/missing"]["result"], "error")
        self.assertEqual(reports["https://x/missing"]["reason"], "Couldn't download it: HTTP Error 404")
        self.assertEqual(reports["https://x/missing"]["yara"]["reason"], "Couldn't download it: HTTP Error 404")

    def test_each_scanner_reports_on_its_own(self):
        def fetch(url, path):
            path.write_bytes(b"zip")
            return "d"

        reports = scan([["https://x/a"]], scanner=lambda paths: "\n".join(f"{path}: OK" for path in paths), fetch=fetch, version=lambda: ("ClamAV 1.4.3", "27806"), yara=FakeYara({"result": "infected", "found": ["ELASTIC_Linux_Trojan_Test"]}))
        self.assertEqual((reports["https://x/a"]["result"], reports["https://x/a"]["yara"]["result"], reports["https://x/a"]["yara"]["found"]), ("clean", "infected", ["ELASTIC_Linux_Trojan_Test"]))

        # Without ClamAV's signatures, YARA still scans.
        reports = scan([["https://x/a"]], scanner=lambda paths: self.fail("ClamAV ran"), fetch=fetch, version=lambda: ("ClamAV 1.4.3", ""), yara=FakeYara())
        self.assertEqual((reports["https://x/a"]["result"], reports["https://x/a"]["reason"], reports["https://x/a"]["yara"]["result"]), ("error", "ClamAV couldn't load its virus signatures", "clean"))

        # Without YARA, ClamAV still scans, and the ZIP's YARA report says why.
        unavailable = FakeYara()
        unavailable.unavailable = "YARA's rules couldn't be downloaded"
        reports = scan([["https://x/a"]], scanner=lambda paths: "\n".join(f"{path}: OK" for path in paths), fetch=fetch, version=lambda: ("ClamAV 1.4.3", "27806"), yara=unavailable)
        self.assertEqual((reports["https://x/a"]["result"], reports["https://x/a"]["yara"]["result"], reports["https://x/a"]["yara"]["reason"]), ("clean", "error", "YARA's rules couldn't be downloaded"))

    def test_a_scanner_whose_rescan_fails_keeps_its_last_good_result(self):
        def fetch(url, path):
            path.write_bytes(b"zip")
            return "aa"

        old = {"sha256": "aa", "result": "clean", "engine": "ClamAV 1.4.2", "signatures": "1", "scannedAt": "2026-09-01T00:00:00Z", "yara": {"result": "clean", "engine": "YARA 4.5.0", "scannedAt": "2026-09-01T00:00:00Z"}}
        unavailable = FakeYara()
        unavailable.unavailable = "YARA's rules couldn't be downloaded"
        reports = scan([["https://x/a"]], scanner=lambda paths: "\n".join(f"{path}: OK" for path in paths), fetch=fetch, version=lambda: ("ClamAV 1.4.3", "27806"), yara=unavailable, keep={"https://x/a": old})
        self.assertEqual(reports["https://x/a"]["yara"], old["yara"])
        self.assertEqual(reports["https://x/a"]["engine"], "ClamAV 1.4.3")

        reports = scan([["https://x/a"]], scanner=lambda paths: self.fail("ClamAV ran"), fetch=fetch, version=lambda: ("ClamAV 1.4.3", ""), yara=FakeYara(), keep={"https://x/a": old})
        self.assertEqual({key: value for key, value in reports["https://x/a"].items() if key != "yara"}, {key: value for key, value in old.items() if key != "yara"})
        self.assertEqual(reports["https://x/a"]["yara"]["signatures"], "YARA Forge core 2026-11-01")

    def test_without_signatures_nothing_is_downloaded_and_every_zip_says_why(self):
        reports = scan([["https://x/a"], ["https://x/b"]], scanner=lambda paths: self.fail("scanned"), fetch=lambda url, path: self.fail("downloaded"), version=lambda: ("ClamAV 1.4.3", ""))
        self.assertEqual({url: (report["result"], report["reason"]) for url, report in reports.items()}, {url: ("error", "ClamAV couldn't load its virus signatures") for url in ("https://x/a", "https://x/b")})

    def test_a_missing_clamav_or_crashing_scanner_is_a_report_not_a_failure(self):
        def missing():
            raise FileNotFoundError("clamscan")

        reports = scan([["https://x/a"]], fetch=lambda url, path: self.fail("downloaded"), version=missing)
        self.assertEqual(reports["https://x/a"]["reason"], "ClamAV couldn't run: clamscan")

        def crash(paths):
            raise OSError("killed")

        reports = scan([["https://x/a"]], scanner=crash, fetch=lambda url, path: path.write_bytes(b"zip") or "d", version=lambda: ("ClamAV 1.4.3", "27806"))
        self.assertEqual((reports["https://x/a"]["result"], reports["https://x/a"]["reason"]), ("error", "ClamAV couldn't run: killed"))

    def test_no_batch_starts_after_the_deadline(self):
        times = iter([0, 5, 11])
        fetched = []

        def fetch(url, path):
            fetched.append(url)
            path.write_bytes(b"zip")
            return "d"

        reports = scan([["https://x/a"], ["https://x/b"], ["https://x/c"]], scanner=lambda paths: "\n".join(f"{path}: OK" for path in paths), fetch=fetch, version=lambda: ("ClamAV 1.4.3", "27806"), deadline=10, clock=lambda: next(times))
        self.assertEqual(fetched, ["https://x/a", "https://x/b"])
        self.assertEqual(sorted(reports), ["https://x/a", "https://x/b"])

    def test_a_failed_rescan_keeps_the_last_good_report(self):
        old = {"result": "clean", "scannedAt": "2026-11-01T00:00:00Z", "yara": YARA_OK}
        reports = scan([["https://x/old", "https://x/new"]], fetch=lambda url, path: self.fail("downloaded"), version=lambda: ("ClamAV 1.4.3", ""), keep={"https://x/old": old})
        self.assertEqual(sorted(reports), ["https://x/new"])

    def test_nothing_to_scan_needs_no_clamav(self):
        self.assertEqual(scan([], version=lambda: self.fail("asked ClamAV")), {})


class PluginSummaryTests(unittest.TestCase):
    def test_each_channel_gets_the_zip_it_installs_and_its_verdicts(self):
        entries = [{"repo": "O/A", "asset": {"include": [], "exclude": ["source"]}}]
        index = {"releases": {
            # A newer pre-release than the stable one: both channels, each with its own ZIP.
            "o/a": [
                {"tag_name": "v2-rc", "prerelease": True, "assets": [asset("source.zip", "https://x/src"), asset("a2.zip", "https://x/a2", digest="sha256:bb")]},
                {"tag_name": "v1", "assets": [asset("a1.zip", "https://x/a1")]},
            ],
            # Newest release is stable: one ZIP, so no separate pre-release line.
            "o/b": [{"tag_name": "v3", "assets": [asset("b.zip", "https://x/b")]}],
            "o/empty": [],
        }}
        develop = {"releases": {"o/b": [{"tag_name": "v9", "assets": [asset("other.zip", "https://x/other")]}]}}
        files = {
            "https://x/a1": {"sha256": "aa", "result": "clean", "engine": "ClamAV 1.4.3", "scannedAt": "2026-11-01T00:00:00Z", "yara": {"result": "infected", "found": ["Linux_Test"], "engine": "YARA 4.5.0", "scannedAt": "2026-11-01T00:00:00Z"}},
            "https://x/b": {"sha256": "cc", "result": "incomplete", "found": ["Heuristics.Limits.Exceeded.MaxFileSize"], "scannedAt": "2026-11-01T00:00:00Z", "yara": {"result": "error", "reason": "YARA's rules couldn't be downloaded", "scannedAt": "2026-11-01T00:00:00Z"}},
        }
        self.assertEqual(plugin_summary([index, develop], entries, files), {
            "o/a": {
                "stable": {"tag": "v1", "file": "a1.zip", "sha256": "aa", "clamav": {"result": "clean", "scannedAt": "2026-11-01T00:00:00Z"}, "yara": {"result": "infected", "found": ["Linux_Test"], "scannedAt": "2026-11-01T00:00:00Z"}},
                # Not scanned yet: no verdicts, the index's digest still names the file.
                "prerelease": {"tag": "v2-rc", "file": "a2.zip", "sha256": "bb"},
            },
            "o/b": {"stable": {"tag": "v3", "file": "b.zip", "sha256": "cc", "clamav": {"result": "incomplete", "found": ["Heuristics.Limits.Exceeded.MaxFileSize"], "scannedAt": "2026-11-01T00:00:00Z"}, "yara": {"result": "error", "reason": "YARA's rules couldn't be downloaded", "scannedAt": "2026-11-01T00:00:00Z"}}},
        })


class BadgeTests(unittest.TestCase):
    def test_a_badge_per_scanner_for_the_stable_zip_else_the_pre_release(self):
        plugins = {
            "o/a": {"stable": {"tag": "v1", "clamav": {"result": "clean"}, "yara": {"result": "infected"}}, "prerelease": {"tag": "v2-rc", "clamav": {"result": "error"}}},
            "o/b": {"prerelease": {"tag": "v0.1", "clamav": {"result": "incomplete"}}},
            "o/c": {"stable": {"tag": "v3"}},
        }
        self.assertEqual({path: (badge["label"], badge["message"], badge["color"]) for path, badge in badges(plugins).items()}, {
            "o/a/clamav.json": ("ClamAV", "no threats (v1)", "brightgreen"),
            "o/a/yara.json": ("YARA", "threat found (v1)", "red"),
            "o/b/clamav.json": ("ClamAV", "partly scanned (v0.1)", "orange"),
            "o/b/yara.json": ("YARA", "not scanned yet (v0.1)", "lightgrey"),
            "o/c/clamav.json": ("ClamAV", "not scanned yet (v3)", "lightgrey"),
            "o/c/yara.json": ("YARA", "not scanned yet (v3)", "lightgrey"),
        })
        self.assertTrue(all(badge["schemaVersion"] == 1 for badge in badges(plugins).values()))


class YaraTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)

    def zip(self, files: dict[str, bytes]) -> Path:
        path = self.folder / "plugin.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("Plugin/", b"")
            for name, data in files.items():
                archive.writestr(name, data)
        return path

    def test_unpacks_under_numbered_names_and_leaves_out_what_is_past_the_limits(self):
        path = self.zip({"Plugin/main.py": b"print()", "../../evil.sh": b"x" * 10, "Plugin/dist/index.js": b"y" * 10})
        out = self.folder / "out"
        out.mkdir()
        limit = virus_scan.YARA_MAX_BYTES
        virus_scan.YARA_MAX_BYTES = 17
        try:
            names, skipped = unpack(path, out)
        finally:
            virus_scan.YARA_MAX_BYTES = limit
        self.assertEqual((names, skipped), (["Plugin/main.py", "../../evil.sh"], ["Plugin/dist/index.js"]))
        self.assertEqual(sorted(file.name for file in out.iterdir()), ["0", "1"])
        self.assertEqual((out / "1").read_bytes(), b"x" * 10)

    def test_parses_matches_and_per_file_errors(self):
        stdout = "Linux_Trojan_Test /t/x/0\nOther_Rule /t/x/1\nLinux_Trojan_Test /t/x/1\nStray /elsewhere/1\n"
        stderr = "error scanning /t/x/2: timeout\n"
        self.assertEqual(parse_yara(stdout, stderr, "/t/x", ["a.py", "b.js", "c.so"]), (["Linux_Trojan_Test", "Other_Rule"], ["c.so"], None))
        self.assertEqual(parse_yara("", "could not open file\n", "/t/x", []), ([], [], "could not open file"))

    def test_reads_the_rule_package_version_from_its_header(self):
        rules = self.folder / "yara-rules-core.yar"
        rules.write_text("/*\n * YARA-Forge YARA Rule Package\n * Name: core \n * Creation Date: 2026-11-01\n * Number of Rules: 5134\n */\nrule a { condition: false }\n")
        self.assertEqual(rules_version(rules), "YARA Forge core 2026-11-01")
        (self.folder / "other.yar").write_text("rule a { condition: false }\n")
        self.assertEqual(rules_version(self.folder / "other.yar"), "other.yar")

    def test_missing_rules_make_yara_unavailable(self):
        self.assertEqual(Yara(None, self.folder).unavailable, "YARA's rules couldn't be downloaded")
        self.assertEqual(Yara(str(self.folder / "missing.yar"), self.folder).unavailable, "YARA's rules couldn't be downloaded")

    @unittest.skipUnless(shutil.which("yara") and shutil.which("yarac"), "needs yara and yarac")
    def test_scans_the_files_inside_a_zip_with_real_yara(self):
        rules = self.folder / "rules.yar"
        rules.write_text("/*\n * Name: test\n * Creation Date: 2026-11-01\n */\nrule DeckyHub_Test_Marker { strings: $a = \"deckyhub-yara-test-marker\" condition: $a }\n")
        yara = Yara(str(rules), self.folder)
        self.assertIsNone(yara.unavailable)
        self.assertTrue(yara.engine.startswith("YARA "))
        self.assertEqual(yara.signatures, "YARA Forge test 2026-11-01")
        self.assertEqual(yara.scan(str(self.zip({"Plugin/main.py": b"print('hello')"}))), {"result": "clean"})
        self.assertEqual(yara.scan(str(self.zip({"Plugin/main.py": b"print()", "Plugin/bin/tool": b"..deckyhub-yara-test-marker.."}))), {"result": "infected", "found": ["DeckyHub_Test_Marker"]})
        broken = self.folder / "broken.zip"
        broken.write_bytes(b"not a zip")
        self.assertEqual(yara.scan(str(broken))["result"], "incomplete")
        self.assertIn("YARA couldn't compile its rules", Yara(str(self.folder / "plugin.zip"), self.folder).unavailable)


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
