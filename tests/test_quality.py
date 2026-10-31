import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from quality import unfinished  # noqa: E402

NOW = datetime(2026, 10, 31, tzinfo=timezone.utc)
ENTRY = {"repo": "o/a", "description": "Does things.", "asset": {"include": [".zip"], "exclude": ["source"]}}


def release(tag, published, downloads=0, assets=("plugin.zip",), prerelease=False):
    return {"tag_name": tag, "published_at": published, "prerelease": prerelease, "draft": False,
            "assets": [{"name": name, "download_count": downloads} for name in assets]}


def repo(*releases, stars=0, description="A plugin"):
    return {"releases": list(releases), "stars": stars, "description": description}


class QualityTests(unittest.TestCase):
    def test_an_established_plugin_passes(self):
        self.assertEqual(unfinished(ENTRY, repo(release("v1.2.0", "2026-06-01T00:00:00Z", downloads=40)), NOW), [])
        # Stars alone show people use it, whatever the download count.
        self.assertEqual(unfinished(ENTRY, repo(release("v1.2.0", "2026-06-01T00:00:00Z"), stars=3), NOW), [])

    def test_each_sign_of_an_unfinished_plugin(self):
        new = repo(release("v1.0.0", "2026-10-25T00:00:00Z", downloads=50))
        self.assertEqual(unfinished(ENTRY, new, NOW), ["first release under 14 days old"])
        # The age counts from the first release with the plugin ZIP, not a newer one.
        grown = repo(release("v1.1.0", "2026-10-30T00:00:00Z", downloads=50), release("v1.0.0", "2026-01-01T00:00:00Z", downloads=50))
        self.assertEqual(unfinished(ENTRY, grown, NOW), [])
        unused = repo(release("v1.0.0", "2026-06-01T00:00:00Z", downloads=4, assets=("plugin.zip", "plugin-source.zip")))
        self.assertEqual(unfinished(ENTRY, unused, NOW), ["no stars and 4 downloads"])
        for tag in ("v0.0.3", "0.0", "Initial"):
            self.assertEqual(unfinished(ENTRY, repo(release(tag, "2026-06-01T00:00:00Z", downloads=50)), NOW), [f"placeholder version {tag!r}"], tag)
        self.assertEqual(unfinished(ENTRY, repo(release("v0.1.0", "2026-06-01T00:00:00Z", downloads=50)), NOW), [])
        nameless = {**ENTRY, "description": "Thing for Decky Loader."}
        self.assertEqual(unfinished(nameless, repo(release("v1.0.0", "2026-06-01T00:00:00Z", downloads=50), description=None), NOW), ["no description"])


if __name__ == "__main__":
    unittest.main()
