import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate  # noqa: E402
from validate import TABLE_HEADER, channel_releases, matching_assets, readme_errors, static_errors  # noqa: E402


def app(id="a", repo="o/a", names=("A",), include=(".zip",), exclude=("source",), tag=None):
    entry = {"id": id, "repo": repo, "detect": {"type": "decky-plugin", "names": list(names)}, "asset": {"include": list(include), "exclude": list(exclude)}}
    return {**entry, "releaseTagInclude": tag} if tag else entry


def release(tag, published, prerelease=False, draft=False, assets=("plugin.zip",)):
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
        self.assertEqual(len(readme_errors([app(), app(id="b", repo="o/b")], readme.replace(TABLE_HEADER, ""))), 1)

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

    def test_channels_skip_a_newer_release_without_the_plugin_zip(self):
        releases = [release("v1", "2026-01-01"), release("windows-v2", "2026-02-01", assets=("Setup.exe", "windows.zip.sha256"))]
        self.assertEqual(channel_releases(app(), releases)["stable"]["tag_name"], "v1")
        self.assertIsNone(channel_releases(app(), releases[1:])["prerelease"])


class AiFilesTests(unittest.TestCase):
    def test_finds_ai_assistant_files_at_the_root_and_in_dot_github(self):
        result = {
            "root": {"entries": [{"name": "README.md"}, {"name": "CLAUDE.md"}, {"name": ".cursorrules"}, {"name": "agents.MD"}, {"name": "src"}, {"name": "main.py"}]},
            "dotGithub": {"entries": [{"name": "workflows"}, {"name": "copilot-instructions.md"}]},
        }
        self.assertEqual(validate.ai_files(result), [".cursorrules", ".github/copilot-instructions.md", "CLAUDE.md", "agents.MD"])

    def test_a_repo_without_them_or_without_a_tree_has_none(self):
        self.assertEqual(validate.ai_files({"root": {"entries": [{"name": "README.md"}]}, "dotGithub": None}), [])
        self.assertEqual(validate.ai_files({"root": None, "dotGithub": None}), [])
        self.assertEqual(validate.ai_files({}), [])


class RangedFileTests(unittest.TestCase):
    def setUp(self):
        self.original = validate.fetch
        self.addCleanup(setattr, validate, "fetch", self.original)

    def serve(self, answers):
        calls = []

        def fetch(url, headers=None, auth=True):
            calls.append(headers["Range"])
            answer = answers.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return answer

        validate.fetch = fetch
        return calls

    def test_a_wrong_or_failed_answer_is_tried_once_more(self):
        calls = self.serve([b"<html>error</html>", b"abcd"])
        self.assertEqual(validate.RangedFile("https://x/a.zip", 10).read(4), b"abcd")
        self.assertEqual(calls, ["bytes=0-3", "bytes=0-3"])
        self.serve([OSError("HTTP Error 502"), b"abcd"])
        self.assertEqual(validate.RangedFile("https://x/a.zip", 10).read(4), b"abcd")

    def test_a_second_bad_answer_fails(self):
        self.serve([b"x", b"y"])
        with self.assertRaises(OSError):
            validate.RangedFile("https://x/a.zip", 10).read(4)
        self.serve([OSError("HTTP Error 502"), OSError("HTTP Error 503")])
        with self.assertRaisesRegex(OSError, "503"):
            validate.RangedFile("https://x/a.zip", 10).read(4)


if __name__ == "__main__":
    unittest.main()
