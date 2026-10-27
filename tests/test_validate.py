import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from validate import channel_releases, matching_assets, readme_errors, static_errors  # noqa: E402


def app(id="a", repo="o/a", names=("A",), include=(".zip",), exclude=("source",), tag=None):
    entry = {"id": id, "repo": repo, "detect": {"type": "decky-plugin", "names": list(names)}, "asset": {"include": list(include), "exclude": list(exclude)}}
    return {**entry, "releaseTagInclude": tag} if tag else entry


def release(tag, published, prerelease=False, draft=False, assets=()):
    return {"tag_name": tag, "published_at": published, "prerelease": prerelease, "draft": draft, "assets": [{"name": name} for name in assets]}


class ValidateTests(unittest.TestCase):
    def test_static_errors_catch_clashing_ids_repos_and_detect_names(self):
        self.assertEqual(static_errors([app(), app(id="b", repo="o/b", names=("B",))]), [])
        self.assertEqual(len(static_errors([app(), app(repo="o/b", names=("B",))])), 1)
        self.assertEqual(len(static_errors([app(), app(id="b", repo="O/A", names=("B",))])), 1)
        self.assertEqual(len(static_errors([app(), app(id="b", repo="o/b", names=("a",))])), 1)
        self.assertEqual(len(static_errors([app(names=("DeckyHub",))])), 1)

    def test_readme_table_must_match_entries_in_order(self):
        readme = "## Repositories\n\n| Tool | Category | Repository |\n| --- | --- | --- |\n| A | X | [o/a](https://github.com/o/a) |\n| B | X | [o/b](https://github.com/o/b) |\n\n## Next\n"
        self.assertEqual(readme_errors([app(), app(id="b", repo="o/b")], readme), [])
        self.assertEqual(len(readme_errors([app(id="b", repo="o/b"), app()], readme)), 1)
        self.assertEqual(len(readme_errors([app()], readme)), 1)

    def test_matching_assets_follows_deckyhubs_filter(self):
        assets = release("v1", "2026-01-01", assets=("Plugin.zip", "Plugin-source.zip", "Plugin.tar.gz", "Other.zip"))
        self.assertEqual([asset["name"] for asset in matching_assets(app(include=("plugin",)), assets)], ["Plugin.zip"])
        self.assertEqual(len(matching_assets(app(include=()), assets)), 2)

    def test_channels_pick_the_newest_release_they_can_see(self):
        releases = [release("v1", "2026-01-01"), release("v2-beta", "2026-03-01", prerelease=True), release("v3", "2026-04-01", draft=True), release("tools-v9", "2026-05-01")]
        channels = channel_releases(app(), releases)
        self.assertEqual((channels["stable"]["tag_name"], channels["prerelease"]["tag_name"]), ("tools-v9", "tools-v9"))
        channels = channel_releases(app(tag="v"), releases[:3])
        self.assertEqual((channels["stable"]["tag_name"], channels["prerelease"]["tag_name"]), ("v1", "v2-beta"))
        self.assertEqual(channel_releases(app(), [release("v2-beta", "2026-03-01", prerelease=True)])["stable"], None)


if __name__ == "__main__":
    unittest.main()
