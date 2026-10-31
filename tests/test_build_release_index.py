import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_release_index import KEEP, audit_index, build, plugin_stats  # noqa: E402
from validate import rest_shape  # noqa: E402


def entry(repo="o/a", include=(".zip",), exclude=("source",)):
    return {"repo": repo, "asset": {"include": list(include), "exclude": list(exclude)}}


def release(tag, day, assets=(), draft=False, prerelease=False):
    return {"tag_name": tag, "published_at": f"2026-01-{day:02}T00:00:00Z", "draft": draft, "prerelease": prerelease, "uploader": {"login": "x"},
            "assets": [{"name": name, "browser_download_url": "d", "size": 3, "digest": "sha256:ab", "download_count": count, "id": 9} for name, count in assets]}


def no_stats(entry, releases):
    return {}


class BuildReleaseIndexTests(unittest.TestCase):
    def test_index_keys_repos_lowercase_drops_drafts_and_failed_lookups(self):
        releases = {"O/A": [release("v2", 2, draft=True), release("v1", 1, [("a.zip", 5)])]}

        def fetch(repo):
            if repo == "o/broken":
                raise OSError("HTTP Error 502")
            return releases[repo]

        index = build([entry("O/A"), entry("o/a"), entry("o/broken")], fetch, no_stats)
        self.assertEqual(list(index["releases"]), ["o/a"])
        self.assertEqual(index["releases"]["o/a"], [{
            "tag_name": "v1", "name": None, "draft": False, "prerelease": False, "published_at": "2026-01-01T00:00:00Z", "html_url": None, "body": None,
            "assets": [{"name": "a.zip", "browser_download_url": "d", "size": 3, "digest": "sha256:ab"}],
        }])
        self.assertEqual(index["stats"], {"o/a": {}})
        self.assertRegex(index["generatedAt"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_index_keeps_the_newest_installable_releases_and_the_newest_stable_one(self):
        history = [release(f"v{day}-beta", day, [("plugin.zip", 1)], prerelease=True) for day in range(10, 10 + KEEP + 3)]
        history += [release("v9-windows", 9, [("Setup.exe", 1)]), release("v8", 8, [("plugin.zip", 1)]), release("v7", 7, [("plugin.zip", 1)])]
        tags = [item["tag_name"] for item in build([entry()], lambda repo: history, no_stats)["releases"]["o/a"]]
        # The KEEP newest with the plugin ZIP (all pre-releases here), then the newest
        # stable one so the Stable channel still finds it; no ZIP-less or older ones.
        self.assertEqual(tags, [f"v{day}-beta" for day in range(9 + KEEP + 3, 9 + 3, -1)] + ["v8"])
        stable = [release(f"v{day}", day, [("plugin.zip", 1)]) for day in range(1, KEEP + 4)]
        self.assertEqual(len(build([entry()], lambda repo: stable, no_stats)["releases"]["o/a"]), KEEP)
        # Nothing installable: an empty list, which DeckyHub reads as "no release" without asking GitHub.
        self.assertEqual(build([entry()], lambda repo: [release("v1", 1, [("Setup.exe", 1)])], no_stats)["releases"]["o/a"], [])

    def test_stats_count_plugin_zips_over_every_release_and_read_the_shown_release(self):
        history = [release(f"v{day}", day, [("plugin.zip", 10), ("plugin-source.zip", 7), ("Setup.exe", 3)]) for day in range(1, 26)]
        history.insert(0, release("v99-beta", 28, [("plugin.zip", 1)], prerelease=True))
        seen = []
        stats = plugin_stats(entry(), history, stars=lambda repo: 42, manifest=lambda asset: seen.append(asset) or {"flags": ["root", "debug"]})
        self.assertEqual(stats, {"downloads": 10 * 25 + 1, "stars": 42, "updated": "2026-01-25T00:00:00Z", "root": True})
        # The stable release's ZIP is the one read, not the newer pre-release's.
        self.assertEqual(len(seen), 1)

    def test_stats_tell_no_root_from_unknown(self):
        history = [release("v1", 1, [("plugin.zip", 1)])]
        self.assertFalse(plugin_stats(entry(), history, stars=lambda repo: 0, manifest=lambda asset: {"name": "A"})["root"])

        def broken(*args):
            raise OSError("HTTP Error 502")

        stats = plugin_stats(entry(), history, stars=broken, manifest=broken)
        self.assertIsNone(stats["root"])
        self.assertIsNone(stats["stars"])
        self.assertEqual(plugin_stats(entry(), [], stars=lambda repo: 0, manifest=broken), {"downloads": 0, "stars": 0, "updated": None, "root": None})

    def test_stats_warn_about_the_audit_of_the_shown_release_and_a_newer_prerelease(self):
        history = [release("v1", 1, [("plugin.zip", 1)]), release("v2-beta", 2, [("plugin.zip", 1)], prerelease=True)]
        history[0]["assets"][0]["digest"] = "sha256:aa"
        audits = audit_index({"releases": [
            {"repository": "https://github.com/O/A", "tag": "v1", "classification": "MANUAL_REVIEW", "audited_at": "2026-01-01", "current_artifact_sha256": "aa",
             "rule_ids": ["PRIVILEGE_SUDO", "SENSITIVE_STEAM_AUTH", "TRIVY_CVE_2026_1", "TRIVY_GHSA_X"]},
            # Same tag, older upload: the sha256 match still picks the v1 ZIP's own audit.
            {"repository": "https://github.com/o/a", "tag": "v1", "classification": "PASS", "rule_ids": [], "audited_at": "2025-01-01", "current_artifact_sha256": "bb"},
            {"repository": "https://github.com/o/a", "tag": "v2-beta", "classification": "BLOCK", "rule_ids": ["ZIP_ONLY_SCRIPT"], "audited_at": "", "current_artifact_sha256": None},
        ]})
        stats = plugin_stats(entry(), history, stars=lambda repo: 0, manifest=lambda asset: {}, audits=audits)
        # Routine rules (sudo) aren't warnings.
        self.assertEqual(stats["warnings"], ["private-data", "vulnerable"])
        self.assertEqual(stats["prereleaseWarnings"], ["blocked", "not-in-source"])
        self.assertNotIn("warnings", plugin_stats(entry(), [release("v9", 9, [("plugin.zip", 1)])], stars=lambda repo: 0, manifest=lambda asset: {}, audits=audits))

    def test_graphql_releases_take_the_rest_shape(self):
        node = {"tagName": "v1", "name": "One", "isDraft": False, "isPrerelease": True, "publishedAt": "2026-01-01T00:00:00Z", "url": "u", "description": "notes",
                "releaseAssets": {"nodes": [{"name": "a.zip", "downloadUrl": "d", "size": 3, "digest": "sha256:ab", "downloadCount": 5}]}}
        self.assertEqual(rest_shape(node), {
            "tag_name": "v1", "name": "One", "draft": False, "prerelease": True, "published_at": "2026-01-01T00:00:00Z", "html_url": "u", "body": "notes",
            "assets": [{"name": "a.zip", "browser_download_url": "d", "size": 3, "digest": "sha256:ab", "download_count": 5}],
        })


if __name__ == "__main__":
    unittest.main()
