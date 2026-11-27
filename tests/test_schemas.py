import json
import os
import re
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_release_index import WARNINGS, plugin_stats, store_entry  # noqa: E402
from virus_scan import lite_summary, plugin_summary  # noqa: E402

# CI checks out the readers next to this repository; without a checkout their tests are skipped.
PLUGIN = Path(os.environ.get("DECKYHUB_PLUGIN", ROOT.parent / "deckyhub-plugin"))
EXT = Path(os.environ.get("DECKYHUB_EXT", ROOT.parent / "deckyhub-ext"))


def schema(name):
    data = json.loads((ROOT / "registry" / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(data)
    return Draft202012Validator(data)


APPS, STATS = schema("apps.schema.json"), schema("stats.schema.json")
ENTRY = {"repo": "o/a", "asset": {"include": [".zip"], "exclude": []}}
FULL = plugin_stats(
    ENTRY,
    [],
    stars=lambda repo: 3,
    manifest=lambda asset: {},
    fork="o/b",
    ai=["CLAUDE.md"],
    store={"downloads": 5, "activity": {"downloads": 7, "updates": 3}},
)


def stats_file(entry):
    return {"generatedAt": "2026-11-15T00:00:00Z", "plugins": {"o/a": entry}}


def field_names(source: str, type_name: str) -> set[str]:
    body = re.search(rf"(?:type|interface) {type_name}\s*=?\s*\{{([^}}]*)\}}", source).group(1)
    return set(re.findall(r"(\w+)\??:", body))


class SchemaTests(unittest.TestCase):
    def test_every_schema_is_valid_and_warnings_json_matches_its_own(self):
        for path in (ROOT / "registry").glob("*.schema.json"):
            with self.subTest(path.name):
                schema(path.name)
        schema("warnings.schema.json").validate(json.loads((ROOT / "registry" / "warnings.json").read_text(encoding="utf-8")))

    def test_what_the_scanner_publishes_matches_the_plugins_schema(self):
        asset = {"name": "plugin.zip", "browser_download_url": "https://x/plugin.zip", "size": 1, "digest": None}
        index = {"releases": {"o/a": [{"tag_name": "v1", "prerelease": False, "assets": [asset]}]}}
        audit = {"result": "complete", "source": {"result": "complete", "findings": [{"rule": "source_file_differs", "path": "a.py"}]}}
        files = {asset["browser_download_url"]: {"result": "clean", "sha256": "a" * 64, "audit": audit}}
        plugins = plugin_summary([index], [ENTRY], files)
        for summary in (plugins, lite_summary(plugins)):
            schema("plugins.schema.json").validate({"generatedAt": "2026-11-27T00:00:00Z", "plugins": summary})
        schema("scans.schema.json").validate({"generatedAt": "2026-11-27T00:00:00Z", "files": files})

    def test_apps_json_matches_its_schema(self):
        APPS.validate(json.loads((ROOT / "registry" / "apps.json").read_text(encoding="utf-8")))

    def test_apps_schema_rejects_what_older_deckyhub_would_choke_on(self):
        app = json.loads((ROOT / "registry" / "apps.json").read_text(encoding="utf-8"))["apps"][0]
        for label, bad in {"unknown key": {**app, "new": 1}, "no repo": {k: v for k, v in app.items() if k != "repo"}}.items():
            with self.subTest(label):
                self.assertFalse(APPS.is_valid({"schemaVersion": 1, "apps": [bad]}))
        self.assertFalse(APPS.is_valid({"schemaVersion": 2, "apps": [app]}))

    def test_what_the_index_builder_writes_matches_the_stats_schema(self):
        STATS.validate(stats_file(FULL))
        STATS.validate(stats_file(plugin_stats(ENTRY, [], stars=lambda repo: 0, manifest=lambda asset: {})))
        self.assertFalse(STATS.is_valid(stats_file({**FULL, "surprise": 1})))
        # What the builder writes for a store listing: the larger count, and the summed activity beside it.
        self.assertEqual(FULL["store"], {"downloads": 5, "activity": {"downloads": 7, "updates": 3}})

    def test_a_store_listing_as_the_builder_writes_it_matches_the_stats_schema(self):
        entry = {"name": "Plugin", "detect": {"names": ["Plugin"]}}
        store = store_entry(entry, {"plugin": 5}, {"plugin": {"downloads": 7, "updates": 3}})
        self.assertEqual(store, {"downloads": 5, "activity": {"downloads": 7, "updates": 3}})
        STATS.validate(stats_file({**plugin_stats(ENTRY, [], stars=lambda repo: 0, manifest=lambda asset: {}), "store": store}))
        # Without the activity counters it is the shape every released DeckyHub reads.
        STATS.validate(stats_file({**FULL, "store": store_entry(entry, {"plugin": 5})}))

    def test_the_schema_knows_every_warning_the_builder_can_write(self):
        known = set(STATS.schema["$defs"]["warnings"]["items"]["enum"])
        self.assertEqual(known, set(WARNINGS.values()) | {"blocked"})

    @unittest.skipUnless((PLUGIN / "src" / "types.ts").exists(), "needs a deckyhub-plugin checkout")
    def test_deckyhub_reads_only_fields_the_schema_has(self):
        read = field_names((PLUGIN / "src" / "types.ts").read_text(encoding="utf-8"), "PluginStats")
        self.assertLessEqual(read, set(STATS.schema["$defs"]["plugin"]["properties"]))

    @unittest.skipUnless((EXT / "extension" / "src" / "types.ts").exists(), "needs a deckyhub-ext checkout")
    def test_the_extension_reads_only_fields_the_schema_has(self):
        read = field_names((EXT / "extension" / "src" / "types.ts").read_text(encoding="utf-8"), "Stats")
        self.assertLessEqual(read, set(STATS.schema["$defs"]["plugin"]["properties"]))


if __name__ == "__main__":
    unittest.main()
