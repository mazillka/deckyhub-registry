import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_release_index import WARNINGS, plugin_stats  # noqa: E402

WARNING_IDS = set(WARNINGS.values()) | {"blocked"}
# CI checks out deckyhub-plugin's default branch (what people run) here.
PLUGIN = Path(os.environ.get("DECKYHUB_PLUGIN", ROOT.parent / "deckyhub-plugin"))


class CatalogTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "needs Node")
    def test_every_page_script_parses(self):
        # A syntax error leaves the page broken with nothing in CI to say so.
        for page in (ROOT / "docs").rglob("*.html"):
            for index, script in enumerate(re.findall(r"<script>(.*?)</script>", page.read_text(encoding="utf-8"), re.S)):
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as file:
                    file.write(script)
                try:
                    result = subprocess.run(["node", "--check", file.name], capture_output=True, text=True)
                finally:
                    os.unlink(file.name)
                self.assertEqual(result.returncode, 0, f"{page.name} script {index}: {result.stderr}")


class WarningsFileTests(unittest.TestCase):
    def test_warnings_json_explains_every_warning_the_index_can_write(self):
        # DeckyHub, the browser extension and deckyhub.com check their copies against this file.
        warnings = json.loads((ROOT / "registry" / "warnings.json").read_text(encoding="utf-8"))["warnings"]
        self.assertEqual(set(warnings), WARNING_IDS)

    def test_the_shared_cases_name_only_known_warnings(self):
        cases = json.loads((ROOT / "registry" / "contract-cases.json").read_text(encoding="utf-8"))
        self.assertTrue(cases["scans"] and cases["warnings"])
        for case in cases["warnings"]:
            for badge in case["expect"]:
                self.assertIn(badge["id"], WARNING_IDS, case["name"])


class RegistryFileTests(unittest.TestCase):
    def test_no_two_plugins_share_a_description(self):
        # deckyhub.com builds a page per plugin, and its site audit refuses pages that share a description, which turns the
        # website repository's CI red. A fork or a sibling plugin needs a description of its own.
        seen: dict[str, list[str]] = {}
        for app in json.loads((ROOT / "registry" / "apps.json").read_text(encoding="utf-8"))["apps"]:
            seen.setdefault(app["description"].strip().casefold(), []).append(app["id"])
        shared = {description[:70]: ids for description, ids in seen.items() if len(ids) > 1}
        self.assertEqual(shared, {}, "these plugins share a description")

    def test_apps_json_fits_every_released_deckyhub(self):
        # DeckyHub refuses a registry over 4 MB (MAX_REMOTE_REGISTRY_BYTES in its registry.py) and keeps its
        # cached list. Releases up to 3.0.0 stopped at 512 KB; the project dropped them once the list passed it,
        # so they keep the list they had. Stay well under 4 MB, with room for months of discovery PRs.
        size = (ROOT / "registry" / "apps.json").stat().st_size
        self.assertLess(size, 3 * 1024 * 1024, f"apps.json is {size} bytes, close to the 4 MB DeckyHub accepts")


@unittest.skipUnless((PLUGIN / "src" / "types.ts").exists(), "needs a deckyhub-plugin checkout")
class PluginContractTests(unittest.TestCase):
    """What DeckyHub in people's hands reads from stats.json must keep coming."""

    def test_stats_keep_every_field_deckyhub_reads(self):
        fields = re.search(r"type PluginStats = \{([^}]*)\}", (PLUGIN / "src" / "types.ts").read_text(encoding="utf-8")).group(1)
        read = set(re.findall(r"(\w+)\?:", fields))
        written = set(plugin_stats({"repo": "o/a", "asset": {"include": [".zip"], "exclude": []}}, [], stars=lambda repo: 0, manifest=lambda asset: {}))
        # Written only when there's something to say.
        written |= {"warnings", "prereleaseWarnings", "fork", "ai", "store", "rust"}
        self.assertLessEqual(read, written)

    def test_registry_still_sends_every_warning_deckyhub_knows(self):
        types = (PLUGIN / "src" / "types.ts").read_text(encoding="utf-8")
        found = re.search(r"AUDIT_WARNINGS = \[([^\]]*)\]", types)
        known = set(re.findall(r'"([\w-]+)"', found.group(1))) if found else set()
        # An empty set would pass whatever the registry sends: fail if the list has moved.
        self.assertTrue(known, "AUDIT_WARNINGS not found in the plugin's src/types.ts")
        self.assertLessEqual(known, WARNING_IDS)


if __name__ == "__main__":
    unittest.main()
