import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from discover import candidates, category, entry_json, extended_items, ignored_repos, pick, short_description  # noqa: E402

NOW = datetime(2026, 10, 28, tzinfo=timezone.utc)


def item(repo, name, published="2026-10-01T00:00:00Z", downloads=0, archived=False):
    return {"repo": repo, "plugin": {"name": name}, "archived": archived, "downloads": downloads, "latest_release": {"published_at": published} if published else None}


LISTED = [{"repo": "o/listed", "detect": {"names": ["Taken"]}}]


class DiscoverTests(unittest.TestCase):
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
        body = "- Busy (Utilities): https://github.com/O/Busy (via explorer)\n- Other: https://github.com/o/other.git"
        self.assertEqual(ignored_repos(body), {"o/busy", "o/other"})
        explorer = [item("o/busy", "Busy"), item("o/quiet", "Quiet")]
        self.assertEqual([found["repo"] for found in candidates(explorer, LISTED, NOW, ignored_repos(body))], ["o/quiet"])

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


if __name__ == "__main__":
    unittest.main()
