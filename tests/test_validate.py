import io
import json
import sys
import tempfile
import unittest
import zipfile
from unittest import mock
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
    def test_a_rolling_pre_release_replaced_while_checking_is_a_warning_when_a_stable_release_exists(self):
        repo = {
            "full_name": "o/a",
            "releases": [
                release("v1", "2026-01-02T00:00:00Z", assets=("plugin.zip",)),
                release("dev", "2026-01-03T00:00:00Z", prerelease=True, assets=("plugin-abc1234.zip",)),
            ],
        }

        def read(asset):
            if asset["name"] == "plugin-abc1234.zip":
                raise zipfile.BadZipFile("File is not a zip file")
            return {"name": "A"}, {}

        with mock.patch.object(validate, "zip_plugin_files", read):
            errors, warnings = validate.github_problems(app(include=("plugin",)), repo)
        self.assertEqual(errors, [])
        self.assertTrue(any("plugin-abc1234.zip is not a ZIP any more" in warning for warning in warnings), warnings)
        # The stable release's ZIP still has to be a ZIP.
        with mock.patch.object(validate, "zip_plugin_files", side_effect=zipfile.BadZipFile("File is not a zip file")):
            with self.assertRaises(zipfile.BadZipFile):
                validate.github_problems(app(include=("plugin",)), repo)

    def test_static_errors_catch_clashing_ids_repos_and_detect_names(self):
        self.assertEqual(static_errors([app(), app(id="b", repo="o/b", names=("B",))]), [])
        self.assertEqual(static_errors([{**app(), "upstream": "orig/a"}]), [])
        for upstream in ["orig", "https://github.com/orig/a", "O/A", 5]:
            self.assertEqual(len(static_errors([{**app(repo="o/a"), "upstream": upstream}])), 1, upstream)
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


class PluginVersionTests(unittest.TestCase):
    def test_the_zip_gives_plugin_json_and_the_package_json_beside_it(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("A/plugin.json", json.dumps({"name": "A"}))
            archive.writestr("A/package.json", json.dumps({"version": "0.4.5"}))
            archive.writestr("A/node_modules/x/package.json", json.dumps({"version": "9.9.9"}))
        with mock.patch.object(validate, "RangedFile", lambda url, size: io.BytesIO(data.getvalue())):
            manifest, package = validate.zip_plugin_files({"browser_download_url": "https://x/a.zip", "size": 1})
        self.assertEqual(validate.plugin_version(manifest, package), "0.4.5")
        # plugin.json's own version wins, as in DeckyHub; none at all is None.
        self.assertEqual(validate.plugin_version({"version": "1.0"}, {"version": "2.0"}), "1.0")
        self.assertIsNone(validate.plugin_version(None, {}))

    def test_a_zip_with_backslash_paths_has_no_plugin_json_on_any_platform(self):
        # Built on Windows: Linux unpacks "A\plugin.json" as a file with that name, and so must this check, also on Windows,
        # where zipfile quietly turns a backslash into a slash.
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            for name in (r"A\plugin.json", r"A\main.py"):
                info = zipfile.ZipInfo("x")
                info.filename = name
                archive.writestr(info, json.dumps({"name": "A"}))
        with mock.patch.object(validate, "RangedFile", lambda url, size: io.BytesIO(data.getvalue())):
            self.assertEqual(validate.zip_plugin_files({"browser_download_url": "https://x/b.zip", "size": 1}), (None, {}))

    def test_is_decky_manifest(self):
        self.assertTrue(validate.is_decky_manifest({"name": "A", "flags": []}))
        self.assertTrue(validate.is_decky_manifest({"name": "A", "api_version": 1, "publish": {}}))
        for other in (None, [], {}, {"name": "A"}, {"api_version": 1}, {"flags": "root"}, {"api_version": 1, "publish": "x"}):
            self.assertFalse(validate.is_decky_manifest(other), other)

    def test_the_filter_error_names_the_word_that_tells_the_zips_apart_if_there_is_one(self):
        names = lambda *items: [{"name": name} for name in items]  # noqa: E731
        self.assertEqual(validate.filter_hint(names("T-v1.7.3_Installer.zip", "T-v1.7.3_Project.zip")), "; to pick one, include 'installer' or 'project'")
        self.assertEqual(validate.filter_hint(names("deck-1.4.7.zip", "deck.zip")), "")
        self.assertEqual(validate.filter_hint(names("a.zip")), "")

    def test_a_zip_read_before_is_not_downloaded_again_and_the_saved_cache_holds_only_what_was_used(self):
        asset = {"browser_download_url": "https://x/a.zip", "size": 1, "digest": "sha256:ab"}
        key = "https://x/a.zip|1|sha256:ab"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cache.json"
            path.write_text(json.dumps({key: [{"name": "A"}, {"version": "1"}], "https://x/old.zip|1|": [None, {}]}), encoding="utf-8")
            with mock.patch.dict(validate._cached, clear=True), mock.patch.dict(validate._used, clear=True):
                validate.load_zip_cache(str(path))
                with mock.patch.object(validate, "_read_zip_plugin_files", side_effect=AssertionError("downloaded")):
                    self.assertEqual(validate.zip_plugin_files(asset), ({"name": "A"}, {"version": "1"}))
                validate.save_zip_cache(str(path))
            self.assertEqual(list(json.loads(path.read_text(encoding="utf-8"))), [key])

    def test_a_missing_or_broken_cache_reads_everything_again(self):
        with mock.patch.dict(validate._cached, clear=True):
            validate.load_zip_cache(None)
            validate.load_zip_cache("no/such/file.json")
            self.assertEqual(validate._cached, {})

    def test_an_oversized_plugin_json_is_refused_unread_and_an_oversized_package_json_is_skipped(self):
        def files(plugin, package):
            data = io.BytesIO()
            with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("A/plugin.json", plugin)
                archive.writestr("A/package.json", package)
            with mock.patch.object(validate, "RangedFile", lambda url, size: io.BytesIO(data.getvalue())):
                return validate.zip_plugin_files({"browser_download_url": "https://x/a.zip", "size": 1})

        bomb = " " * (validate.MAX_MANIFEST_BYTES + 1)
        with self.assertRaises(ValueError):
            files(bomb, "{}")
        self.assertEqual(files('{"name": "A"}', bomb), ({"name": "A"}, {}))

    def test_a_tag_naming_another_version_number_is_a_mismatch(self):
        for tag, version in [("v0.45", "0.4.5"), ("v1.0.9", "1.0.8"), ("v0.2.0", "0.0.1")]:
            self.assertTrue(validate.version_mismatch(tag, version), tag)
        # Prefixes, suffixes and trailing zeros don't count; nothing to compare isn't a mismatch.
        for tag, version in [("v1.0", "1.0.0"), ("plugin-v3.3.0", "3.3.0"), ("v0.2.0-with-cache", "0.2"), ("v1.2.0-rc.1", "1.2.0-rc.1"), ("nightly", "1.0.0"), ("v1.0.0", None)]:
            self.assertFalse(validate.version_mismatch(tag, version), tag)


class AiFilesTests(unittest.TestCase):
    def test_finds_ai_assistant_files_at_the_root_and_in_dot_github(self):
        result = {
            "root": {"entries": [{"name": "README.md"}, {"name": "CLAUDE.md"}, {"name": ".cursorrules"}, {"name": "agents.MD"}, {"name": "src"}, {"name": "main.py"}]},
            "dotGithub": {"entries": [{"name": "workflows"}, {"name": "copilot-instructions.md"}]},
        }
        self.assertEqual(validate.ai_files(result), [".cursorrules", ".github/copilot-instructions.md", "CLAUDE.md", "agents.MD"])

    def test_rust_backend_is_a_cargo_toml_at_the_root_or_in_backend(self):
        tree = lambda *names: {"entries": [{"name": name} for name in names]}  # noqa: E731
        self.assertTrue(validate.rust_backend({"root": tree("main.py", "Cargo.toml")}))
        self.assertTrue(validate.rust_backend({"root": tree("main.py"), "backend": tree("Cargo.toml", "src")}))
        self.assertTrue(validate.rust_backend({"root": tree("main.py", "rust-toolchain.toml")}))
        self.assertFalse(validate.rust_backend({"root": tree("main.py"), "backend": tree("main.rs")}))
        self.assertFalse(validate.rust_backend({}))

    def test_a_readme_saying_it_is_made_with_ai_counts(self):
        result = {"root": {"entries": [{"name": "CLAUDE.md"}]}, "readme": {"text": "# GameVault\n\nThis plugin was vibe-coded with Claude."}}
        self.assertEqual(validate.ai_files(result), ["CLAUDE.md", 'README: "vibe-coded"'])
        self.assertEqual(validate.ai_files({"readmeLower": {"text": "Built  with\nClaude Code."}}), ['README: "Built with Claude Code"'])
        for text in ["This code is 100% AI.", "Made with the help of ChatGPT.", "The plugin was largely AI-written.", "Developed using AI assistants."]:
            self.assertIsNotNone(validate.ai_readme(text), text)

    def test_readme_wording_about_ai_features_or_a_denial_does_not_count(self):
        for text in ["Not vibe-coded!", "No AI was used, nor built with AI.", "Turns your screenshots into AI-generated wallpapers.", "Built with React and aiohttp.", "Uses the Gemini API.", "Made by aidan", None]:
            self.assertIsNone(validate.ai_readme(text), text)

    def test_more_assistants_files_and_readme_wording_count(self):
        result = {"root": {"entries": [{"name": name} for name in (".mcp.json", ".aiderignore", ".junie", "opencode.json", "src", ".airc")]},
                  "dotGithub": {"entries": [{"name": "instructions"}, {"name": "workflows"}]},
                  "readmeTitle": {"text": "Pair-programmed with Claude Code."}}
        self.assertEqual(validate.ai_files(result), [".aiderignore", ".github/instructions", ".junie", ".mcp.json", 'README: "Pair-programmed with Claude Code"', "opencode.json"])
        for text in ["AI-assisted development.", "Co-written with ChatGPT", "🤖 Generated with [Claude Code](https://claude.com/claude-code)", "Built with Windsurf."]:
            self.assertIsNotNone(validate.ai_readme(text), text)
        for text in ["Translation assisted by AI models.", "AI-assisted upscaling for games.", "Co-authored by Devin Smith"]:
            self.assertIsNone(validate.ai_readme(text), text)

    def test_an_ai_disclaimer_saying_ai_was_used_to_make_it_counts(self):
        for text in ["## AI disclaimer\nAI was used in the making of this project.", "Claude has been used for the development of this plugin.", "LLMs were heavily used to write most of it."]:
            self.assertIsNotNone(validate.ai_readme(text), text)
        for text in ["No AI was used in the making of this.", "AI was never used in development.", "AI is used to create wallpapers.", "Gemini is used for the images."]:
            self.assertIsNone(validate.ai_readme(text), text)

    def test_store_flag_must_be_true(self):
        app = {"id": "a", "repo": "o/a", "detect": {"names": ["A"]}}
        self.assertEqual(validate.static_errors([{**app, "store": True}]), [])
        self.assertTrue(validate.static_errors([{**app, "store": "yes"}]))

    def test_ai_tools_as_commit_authors_and_in_commit_notes(self):
        def commit(number, message="Fix", name="Dev", email="dev@example.com"):
            return {"message": message, "url": f"https://github.com/o/a/commit/{number}", "author": {"name": name, "email": email}}

        result = {"recentHistory": {"target": {"history": {"nodes": [
            commit(1, name="copilot-swe-agent[bot]", email="198982749+Copilot@users.noreply.github.com"),
            commit(2, "Feature\n\nCo-authored-by: Cursor Agent <cursoragent@cursor.com>"),
            commit(3, "Feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"),
            commit(4, "Feature\n\nCo-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"),
            commit(5, name="google-labs-jules[bot]", email="161369871+google-labs-jules[bot]@users.noreply.github.com"),
            commit(6, "aider: tidy imports", name="Dev (aider)"),
            commit(7, "Feature\n\nCo-authored-by: aider (gpt-4o) <aider@aider.chat>"),
            # People: a tool's name with someone's own address, and a tool only mentioned.
            commit(8, "Thanks Devin\n\nCo-authored-by: Devin Smith <devin@example.com>", name="Amp", email="amp@example.com"),
            commit(9, "Add Cursor theme and Claude Code docs"),
        ]}}}}
        self.assertEqual(validate.ai_files(result), [
            "Commit author: GitHub Copilot (https://github.com/o/a/commit/1)",
            "Commit author: Jules (https://github.com/o/a/commit/5)",
            "Commit co-author: Cursor (https://github.com/o/a/commit/2)",
            "Commit note: Aider (https://github.com/o/a/commit/6)",
            "Commit note: Claude (https://github.com/o/a/commit/3)",
        ])

    def test_a_repo_without_them_or_without_a_tree_has_none(self):
        self.assertEqual(validate.ai_files({"root": {"entries": [{"name": "README.md"}]}, "dotGithub": None}), [])
        self.assertEqual(validate.ai_files({"root": None, "dotGithub": None}), [])
        self.assertEqual(validate.ai_files({}), [])

    def test_recent_commit_coauthor_trailers_identify_ai_tools(self):
        result = {"recentHistory": {"target": {"history": {"nodes": [
            {"message": "Feature\n\nCo-authored-by: Claude Sonnet 5.5 <noreply@anthropic.com>", "url": "https://github.com/o/a/commit/1"},
            {"message": "Fix\n\nCo-authored-by: OpenAI Codex <123+codex@users.noreply.github.com>", "url": "https://github.com/o/a/commit/2"},
            {"message": "Fix\n\nCo-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>", "url": "https://github.com/o/a/commit/3"},
        ]}}}}
        self.assertEqual(validate.ai_files(result), [
            "Commit co-author: Claude (https://github.com/o/a/commit/1)",
            "Commit co-author: Codex (https://github.com/o/a/commit/2)",
            "Commit co-author: GitHub Copilot (https://github.com/o/a/commit/3)",
        ])

    def test_mentions_and_ordinary_coauthors_do_not_count_and_missing_history_is_safe(self):
        result = {"recentHistory": {"target": {"history": {"nodes": [
            {"message": "Claude helped here, but no trailer", "url": "u"},
            {"message": "Co-authored-by: Claude Monet <claude.monet@example.com>", "url": "u"},
            {"message": "Co-authored-by: Codex Smith <codex.smith@example.com>", "url": "u"},
            {"message": "Co-authored-by: Codex <123+someone@users.noreply.github.com>", "url": "u"},
            {"message": "Co-authored-by: Copilot <123+someone@users.noreply.github.com>", "url": "u"},
            {"message": "Co-authored-by: Claude <claude.staff@anthropic.com>", "url": "u"},
        ]}}}}
        self.assertEqual(validate.ai_files(result), [])
        self.assertEqual(validate.ai_files({"recentHistory": None}), [])


class RangedFileTests(unittest.TestCase):
    def setUp(self):
        self.original = validate.fetch
        self.addCleanup(setattr, validate, "fetch", self.original)

    def serve(self, answers):
        calls = []

        def fetch(url, headers=None, auth=True, *, byte_range=None):
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
