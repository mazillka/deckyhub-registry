import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from quality import unfinished  # noqa: E402

ENTRY = {"repo": "o/a", "description": "Does things.", "asset": {"include": [".zip"], "exclude": ["source"]}}


def release(tag, published, downloads=0, assets=("plugin.zip",), prerelease=False):
    return {"tag_name": tag, "published_at": published, "prerelease": prerelease, "draft": False,
            "assets": [{"name": name, "download_count": downloads} for name in assets]}


def repo(*releases, stars=0, description="A plugin"):
    return {"releases": list(releases), "stars": stars, "description": description}


class QualityTests(unittest.TestCase):
    def test_a_plugin_with_a_real_version_and_a_description_passes(self):
        self.assertEqual(unfinished(ENTRY, repo(release("v1.2.0", "2026-06-01T00:00:00Z", downloads=40))), [])

    def test_age_and_use_are_not_signs_of_an_unfinished_plugin(self):
        # A release from yesterday, no stars and no downloads: nothing says it isn't ready.
        self.assertEqual(unfinished(ENTRY, repo(release("v1.0.0", "2026-10-30T00:00:00Z"))), [])

    def test_each_sign_of_an_unfinished_plugin(self):
        for tag in ("v0.0.3", "0.0", "Initial"):
            self.assertEqual(unfinished(ENTRY, repo(release(tag, "2026-06-01T00:00:00Z", downloads=50))), [f"placeholder version {tag!r}"], tag)
        self.assertEqual(unfinished(ENTRY, repo(release("v0.1.0", "2026-06-01T00:00:00Z", downloads=50))), [])
        # Pre-releases only: the newest pre-release's version is the one judged.
        self.assertEqual(unfinished(ENTRY, repo(release("v0.0.1-beta", "2026-06-01T00:00:00Z", downloads=50, prerelease=True))), ["placeholder version 'v0.0.1-beta'"])
        self.assertEqual(unfinished(ENTRY, repo(release("v0.2.0-beta", "2026-06-01T00:00:00Z", downloads=50, prerelease=True))), [])
        nameless = {**ENTRY, "description": "Thing for Decky Loader."}
        self.assertEqual(unfinished(nameless, repo(release("v1.0.0", "2026-06-01T00:00:00Z", downloads=50), description=None)), ["no description"])


if __name__ == "__main__":
    unittest.main()
