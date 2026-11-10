import json
import io
import sys
import unittest
from unittest import mock
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import discover  # noqa: E402
from discover import active_fork, candidates, check, category, entry_json, extended_items, github_items, ignored_repos, pick, reddit_items, reddit_repo_links, search_queries, search_repos, short_description  # noqa: E402

NOW = datetime(2026, 10, 28, tzinfo=timezone.utc)


def item(repo, name, published="2026-10-01T00:00:00Z", downloads=0, archived=False):
    return {"repo": repo, "plugin": {"name": name}, "archived": archived, "downloads": downloads, "latest_release": {"published_at": published} if published else None}


LISTED = [{"repo": "o/listed", "detect": {"names": ["Taken"]}}]


class DiscoverTests(unittest.TestCase):
    def test_reddit_link_extraction_normalizes_repo_paths_and_rejects_other_urls(self):
        text = "https://github.com/Owner/Project/releases/tag/v1.0 .git https://evil.com/a/b https://github.com/topics/decky https://github.com/Owner/Project.git"
        self.assertEqual(reddit_repo_links(text), ["Owner/Project"])

    def test_reddit_requires_both_credentials_without_stopping_other_work(self):
        errors = io.StringIO()
        with mock.patch.object(discover.sys, "stderr", errors):
            self.assertEqual(reddit_items("id", ""), [])
        self.assertIn("not configured", errors.getvalue())

    def test_reddit_auth_failure_does_not_expose_credentials(self):
        def fail(*args, **kwargs):
            raise OSError("private-client-secret")
        errors = io.StringIO()
        with mock.patch.object(discover.sys, "stderr", errors):
            self.assertEqual(reddit_items("client", "private-client-secret", fail), [])
        self.assertIn("unavailable", errors.getvalue())
        self.assertNotIn("private-client-secret", errors.getvalue())

    def test_reddit_skips_listed_repositories_before_fetching_manifests(self):
        def request(url, data=None, headers=None):
            if url.endswith("access_token"):
                return b'{"access_token":"token"}'
            return b'{"data":{"children":[{"data":{"url":"https://github.com/O/Listed"}}]}}'
        with mock.patch.object(discover.sys, "stderr", io.StringIO()):
            self.assertEqual(reddit_items("id", "secret", request, manifest=lambda repo: self.fail("listed repo fetched"), listed={"o/listed"}), [])

    def test_reddit_posts_and_limited_comments_produce_deduplicated_sources(self):
        calls = []
        def request(url, data=None, headers=None):
            calls.append((url, data, headers or {}))
            if url.endswith("access_token"):
                return b'{"access_token":"secret-token"}'
            if "/new?" in url:
                return json.dumps({"data": {"children": [
                    {"data": {"id": "abc123", "url": "https://github.com/a/one/releases/tag/v1", "selftext": "also https://github.com/a/two"}},
                    {"data": {"id": "bad/id", "url": "https://github.com/a/ignored", "selftext": ""}},
                ]}}).encode()
            self.assertEqual(url, "https://oauth.reddit.com/comments/abc123?limit=20&depth=2")
            return json.dumps([{}, {"data": {"children": [
                {"data": {"body": "https://github.com/a/two/releases/tag/v2 and https://github.com/b/three.git"}},
                {"data": {"body": "https://notgithub.com/c/four", "replies": {"data": {"children": [
                    {"data": {"body": "https://github.com/c/reply"}}
                ]}}}},
            ]}}]).encode()
        errors = io.StringIO()
        with mock.patch.object(discover.sys, "stderr", errors):
            found = reddit_items("client", "pass", request, manifest=lambda repo: {"name": repo.split("/")[-1]})
        self.assertEqual([entry["repo"] for entry in found], ["a/one", "a/two", "a/ignored", "b/three", "c/reply"])
        self.assertTrue(all(entry["source"] == "r/deckyloader" and entry["plugin"]["name"] for entry in found))
        self.assertEqual(len(calls), 3)
        self.assertIn("Bearer secret-token", calls[1][2]["Authorization"])
        self.assertNotIn("pass", errors.getvalue())
        self.assertNotIn("secret-token", errors.getvalue())

    def test_reddit_comment_failure_isolated_and_candidate_uses_existing_checks(self):
        # Individual comment endpoint failures do not discard the post link.
        calls = 0
        def request(url, data=None, headers=None):
            nonlocal calls
            calls += 1
            if url.endswith("access_token"):
                return b'{"access_token":"token"}'
            if "/new?" in url:
                return b'{"data":{"children":[{"data":{"id":"abc","url":"https://github.com/o/plugin","selftext":""}}]}}'
            raise OSError("offline")
        with mock.patch.object(discover.sys, "stderr", io.StringIO()):
            reddit = reddit_items("id", "secret", request, manifest=lambda repo: {"name": "Plugin"})
        eligible = candidates(reddit, LISTED, NOW)
        self.assertEqual([entry["repo"] for entry in eligible], ["o/plugin"])
        release = {"tag_name": "v1.0.0", "published_at": "2026-10-01T00:00:00Z", "prerelease": False, "draft": False,
                   "assets": [{"name": "plugin.zip", "browser_download_url": "https://example.invalid/plugin.zip", "size": 1}]}
        repo = {"full_name": "o/plugin", "name": "plugin", "description": "A useful Decky plugin", "archived": False,
                "fork": False, "releases": [release]}
        with mock.patch.object(discover, "zip_plugin_name", return_value="Plugin"), mock.patch.object(discover, "github_problems", return_value=([], [])):
            self.assertEqual(check(eligible[0], repo)["source"], "r/deckyloader")
    def test_candidates_skip_listed_archived_templates_taken_names_and_stale_ones(self):
        explorer = [
            item("o/listed", "New name"),
            item("o/archived", "Archived", archived=True),
            item("o/template", "Example Plugin"),
            item("o/copy", "taken"),
            item("o/stale", "Stale", published="2024-01-01T00:00:00Z"),
            item("o/never", "Never released", published=None),
            item("o/self", "DeckyHub"),
            item("o/quiet", "Quiet", downloads=5),
            item("o/busy", "Busy", downloads=500),
        ]
        self.assertEqual([found["repo"] for found in candidates(explorer, LISTED, NOW)], ["o/busy", "o/quiet"])

    def test_repos_from_closed_discovery_prs_are_skipped(self):
        body = """Discovery results are here: https://github.com/o/unrelated
- Busy (Utilities): https://github.com/O/Busy (via explorer)
- Fork (Utilities): https://github.com/o/fork (via GitHub search, fork of https://github.com/o/parent)
- Other (Utilities): https://github.com/o/other.git (via explorer)"""
        self.assertEqual(ignored_repos(body), {"o/busy", "o/fork", "o/other"})
        explorer = [item("o/busy", "Busy"), item("o/quiet", "Quiet")]
        self.assertEqual([found["repo"] for found in candidates(explorer, LISTED, NOW, ignored_repos(body))], ["o/quiet"])

    def test_github_search_queries_continue_after_a_query_fails(self):
        errors = io.StringIO()
        def search(query):
            if query == "middle":
                raise RuntimeError("temporary API error")
            return [{"full_name": query}]
        with mock.patch.object(discover.sys, "stderr", errors):
            found = search_queries(["first", "middle", "last"], search)
        self.assertEqual([repo["full_name"] for repo in found], ["first", "last"])
        self.assertIn("middle", errors.getvalue())

    def test_search_keeps_successful_pages_when_a_later_page_fails(self):
        calls = []
        def search(url):
            calls.append(url)
            if len(calls) == 2:
                raise RuntimeError("temporary API error")
            return {"items": [{"full_name": f"o/{n}"} for n in range(100)]}
        with mock.patch.object(discover.time, "sleep"), mock.patch.object(discover.sys, "stderr", io.StringIO()):
            self.assertEqual(len(search_repos("topic:decky", search)), 100)

    def test_candidates_tolerate_bad_dates_and_prefer_highest_eligible_duplicate(self):
        malformed = item("o/date", "Date Plugin", published="not-a-date", downloads=2)
        malformed_type = item("o/type", "Type Plugin", published=42, downloads=1)
        good = item("o/date", "Date Plugin", published="2026-10-01T00:00:00", downloads=9)
        invalid = item("o/duplicate", "Example Plugin", downloads=100)
        later_valid = item("O/DUPLICATE", "Duplicate", downloads=3)
        items = [malformed, malformed_type, good, invalid, later_valid]
        found = candidates(items, LISTED, NOW)
        self.assertEqual([(entry["repo"], entry["downloads"]) for entry in found], [("o/date", 9), ("O/DUPLICATE", 3), ("o/type", 1)])
        self.assertEqual(malformed["latest_release"]["published_at"], "not-a-date")

    def test_extended_items_take_the_main_repo_and_store_details(self):
        storefront = {"plugins": {
            "a": {"name": "A", "versions": [{"repository": "o/a"}, {"repository": "o/a"}, {"repository": "fork/a"}]},
            "b": {"name": "B", "versions": [], "source_urls": ["https://github.com/o/b.git"]},
            "c": {"name": "C", "versions": []},
        }}
        store = [{"name": "a", "description": "Does A.", "tags": ["x"], "downloads": 7, "versions": [{"created": "2026-01-01T00:00:00Z"}, {"created": "2026-03-01T00:00:00Z"}]}]
        items = extended_items(storefront, store)
        self.assertEqual([item["repo"] for item in items], ["o/a", "o/b"])
        self.assertEqual(items[0]["latest_release"], {"published_at": "2026-03-01T00:00:00Z"})
        self.assertEqual((items[0]["plugin"]["publish"]["description"], items[0]["downloads"]), ("Does A.", 7))
        # No store details: unknown date, still a candidate; one item per repo across catalogs.
        self.assertEqual(items[1]["latest_release"], {"published_at": None})
        found = candidates([item("o/a", "A"), *items], LISTED, NOW)
        self.assertEqual([entry["repo"] for entry in found], ["o/a", "o/b"])

    def test_pick_skips_zip_names_already_listed_and_renames_clashing_ids(self):
        apps = [{"id": "a", "repo": "o/listed", "detect": {"names": ["Taken"]}}]
        passed = [
            {"id": "x", "name": "taken", "repo": "o/x"},
            {"id": "a", "name": "New", "repo": "p/a"},
            {"id": "y", "name": "NEW", "repo": "o/y"},
            {"id": "z", "name": "Last", "repo": "o/z"},
        ]
        self.assertEqual([(entry["id"], entry["name"]) for entry in pick(passed, apps, 1)], [("p-a", "New")])

    def test_category_takes_the_first_matching_rule_and_defaults_to_utilities(self):
        self.assertEqual(category("Fan curve and TDP control"), "Performance")
        self.assertEqual(category("Gyro for the controller, with TDP presets"), "Controllers")
        self.assertEqual(category("Share files over LAN"), "Utilities")

    def test_short_description_strips_markdown_and_cuts_at_a_sentence(self):
        self.assertEqual(short_description("**bold**  `code`\nnext"), "Bold code next")
        long = "First sentence that is long enough to keep. " + "Second " * 40
        self.assertEqual(short_description(long), "First sentence that is long enough to keep.")
        self.assertTrue(short_description("word " * 60).endswith("..."))

    def test_entry_json_is_valid_json_in_the_registry_style(self):
        entry = {"id": "a", "name": "Ä", "description": "d", "repo": "o/a", "category": "Utilities", "detect": {"type": "decky-plugin", "names": ["Ä"]}, "asset": {"include": [".zip"], "exclude": ["source"]}}
        text = entry_json(entry)
        self.assertEqual(json.loads(text), entry)
        self.assertIn('"detect": { "type": "decky-plugin", "names": ["Ä"] }', text)


    def test_github_search_keeps_repos_with_a_named_root_plugin_json(self):
        found = [
            {"full_name": "o/plugin", "description": "Repo text", "stargazers_count": 7, "pushed_at": "2026-10-01T00:00:00Z", "archived": False},
            {"full_name": "O/Plugin", "description": "same repo from a second search"},
            {"full_name": "o/no-manifest"},
            {"full_name": "o/broken", "description": None},
        ]
        manifests = {"o/plugin": {"name": "Plugin", "publish": {"description": "Does things", "tags": ["x"]}}, "o/broken": ["not", "a", "dict"]}
        items = github_items(found, lambda repo: manifests.get(repo))
        self.assertEqual(items, [{"repo": "o/plugin", "plugin": {"name": "Plugin", "publish": {"description": "Does things", "tags": ["x"]}}, "downloads": 7,
                                  "archived": False, "latest_release": {"published_at": "2026-10-01T00:00:00Z"}, "source": "GitHub search"}])
        # The last push stands in for the release date, so an untouched repo is skipped.
        stale = github_items([{"full_name": "o/old", "pushed_at": "2023-01-01T00:00:00Z"}], lambda repo: {"name": "Old"})
        self.assertEqual(candidates(stale, LISTED, NOW), [])

    def test_search_pages_until_a_short_page(self):
        pages = []

        def search(url):
            pages.append(url)
            return {"items": [{"full_name": f"o/{len(pages)}-{n}"} for n in range(100 if len(pages) < 3 else 4)]}

        import discover
        discover.SEARCH_PAUSE = 0
        self.assertEqual(len(search_repos("topic:decky", search)), 204)
        self.assertEqual(len(pages), 3)
        # Forks included (fork:true); active_fork() later keeps only the active ones.
        self.assertIn("fork%3Atrue", pages[0])

    def test_a_fork_is_listed_only_while_it_carries_the_plugin_on(self):
        mine = {"published_at": "2026-10-01T00:00:00Z"}
        def fork(parent):
            return {"fork": True, "parent": parent}
        self.assertTrue(active_fork(fork({"full_name": "o/a", "archived": True, "released": "2026-10-20T00:00:00Z"}), mine))
        self.assertTrue(active_fork(fork({"full_name": "o/a", "archived": False, "released": "2024-01-01T00:00:00Z"}), mine))
        self.assertTrue(active_fork(fork({"full_name": "o/a", "archived": False, "released": None}), mine))
        # The original was deleted: GitHub reports no parent.
        self.assertTrue(active_fork(fork(None), mine))
        # The original released after this fork did: the fork is a copy that fell behind.
        self.assertFalse(active_fork(fork({"full_name": "o/a", "archived": False, "released": "2026-10-20T00:00:00Z"}), mine))

    def test_a_plugin_with_pre_releases_only_qualifies(self):
        def release(tag, prerelease):
            return {"tag_name": tag, "published_at": "2026-10-01T00:00:00Z", "prerelease": prerelease, "draft": False,
                    "assets": [{"name": "plugin.zip", "browser_download_url": "https://example.invalid/plugin.zip", "size": 1}]}
        def repo(*releases):
            return {"full_name": "o/a", "name": "a", "description": "Does A for the Deck.", "archived": False, "fork": False, "releases": list(releases)}
        read = []
        with mock.patch.object(discover, "zip_plugin_name", lambda asset: read.append(asset) or "A"), mock.patch.object(discover, "github_problems", lambda entry, repo: ([], [])):
            entry = check(item("o/a", "A"), repo(release("v1.0.0-beta.1", True)))
            self.assertEqual((entry["name"], entry["repo"]), ("A", "o/a"))
            # Nothing installable at all still fails.
            self.assertIsNone(check(item("o/a", "A"), repo({**release("v1.0.0", True), "assets": []})))
        self.assertEqual(len(read), 1)

if __name__ == "__main__":
    unittest.main()
