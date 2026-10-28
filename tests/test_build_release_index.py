import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_release_index import build  # noqa: E402


class BuildReleaseIndexTests(unittest.TestCase):
    def test_index_keys_repos_lowercase_drops_drafts_and_failed_lookups(self):
        releases = {
            "o/a": [
                {"tag_name": "v2", "draft": True, "assets": []},
                {"tag_name": "v1", "published_at": "2026-01-01T00:00:00Z", "html_url": "u", "body": "notes", "uploader": {"login": "x"}, "assets": [{"name": "a.zip", "browser_download_url": "d", "size": 3, "digest": "sha256:ab", "id": 9}]},
            ],
        }

        def fetch(repo):
            if repo == "o/broken":
                raise OSError("HTTP Error 502")
            return releases[repo]

        index = build(["O/A", "o/a", "o/broken"], fetch)
        self.assertEqual(list(index["releases"]), ["o/a"])
        self.assertEqual(index["releases"]["o/a"], [{
            "tag_name": "v1", "name": None, "draft": False, "prerelease": False, "published_at": "2026-01-01T00:00:00Z", "html_url": "u", "body": "notes",
            "assets": [{"name": "a.zip", "browser_download_url": "d", "size": 3, "digest": "sha256:ab"}],
        }])
        self.assertRegex(index["generatedAt"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


if __name__ == "__main__":
    unittest.main()
