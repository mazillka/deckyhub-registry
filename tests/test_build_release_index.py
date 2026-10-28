import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_release_index import RECENT, build  # noqa: E402


def entry(repo, include=(".zip",), exclude=("source",)):
    return {"repo": repo, "asset": {"include": list(include), "exclude": list(exclude)}}


def release(tag, day, assets=(), draft=False):
    return {"tag_name": tag, "published_at": f"2026-01-{day:02}T00:00:00Z", "draft": draft, "uploader": {"login": "x"},
            "assets": [{"name": name, "browser_download_url": "d", "size": 3, "digest": "sha256:ab", "download_count": count, "id": 9} for name, count in assets]}


class BuildReleaseIndexTests(unittest.TestCase):
    def test_index_keys_repos_lowercase_drops_drafts_and_failed_lookups(self):
        releases = {"O/A": [release("v2", 2, draft=True), release("v1", 1, [("a.zip", 5)])]}

        def fetch(repo):
            if repo == "o/broken":
                raise OSError("HTTP Error 502")
            return releases[repo]

        index = build([entry("O/A"), entry("o/a"), entry("o/broken")], fetch)
        self.assertEqual(list(index["releases"]), ["o/a"])
        self.assertEqual(index["releases"]["o/a"], [{
            "tag_name": "v1", "name": None, "draft": False, "prerelease": False, "published_at": "2026-01-01T00:00:00Z", "html_url": None, "body": None,
            "assets": [{"name": "a.zip", "browser_download_url": "d", "size": 3, "digest": "sha256:ab"}],
        }])
        self.assertRegex(index["generatedAt"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_downloads_count_only_plugin_zips_across_every_release(self):
        history = [release(f"v{day}", day, [("plugin.zip", 10), ("plugin-source.zip", 7), ("Setup.exe", 3)]) for day in range(1, RECENT + 6)]
        index = build([entry("o/a")], lambda repo: history)
        self.assertEqual(index["downloads"], {"o/a": 10 * (RECENT + 5)})
        # Only the newest releases go in the index itself.
        self.assertEqual([item["tag_name"] for item in index["releases"]["o/a"]][:2], [f"v{RECENT + 5}", f"v{RECENT + 4}"])
        self.assertEqual(len(index["releases"]["o/a"]), RECENT)


if __name__ == "__main__":
    unittest.main()
