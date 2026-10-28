import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_release_index import RECENT, build, plugin_stats  # noqa: E402


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

    def test_index_keeps_only_the_newest_releases(self):
        history = [release(f"v{day}", day, [("plugin.zip", 1)]) for day in range(1, RECENT + 6)]
        tags = [item["tag_name"] for item in build([entry()], lambda repo: history, no_stats)["releases"]["o/a"]]
        self.assertEqual(len(tags), RECENT)
        self.assertEqual(tags[:2], [f"v{RECENT + 5}", f"v{RECENT + 4}"])

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


if __name__ == "__main__":
    unittest.main()
