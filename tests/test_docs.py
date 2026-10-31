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
        # A syntax error leaves the catalog on "Loading…" with nothing in CI to say so.
        for page in (ROOT / "docs").glob("*.html"):
            for index, script in enumerate(re.findall(r"<script>(.*?)</script>", page.read_text(encoding="utf-8"), re.S)):
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as file:
                    file.write(script)
                try:
                    result = subprocess.run(["node", "--check", file.name], capture_output=True, text=True)
                finally:
                    os.unlink(file.name)
                self.assertEqual(result.returncode, 0, f"{page.name} script {index}: {result.stderr}")

    def test_catalog_explains_every_warning(self):
        page = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        shown = set(re.findall(r'^  "([\w-]+)": \[', page.split("const WARNINGS = {", 1)[1].split("};", 1)[0], re.M))
        self.assertEqual(shown, WARNING_IDS)


class RegistryFileTests(unittest.TestCase):
    def test_apps_json_fits_every_released_deckyhub(self):
        # DeckyHub up to 3.0.0 refuses a registry over 512 KB (MAX_REMOTE_REGISTRY_BYTES in its
        # main.py; newer releases allow 4 MB) and keeps its cached list, and installed copies
        # never change. Stay under it with room for a few days of discovery PRs.
        size = (ROOT / "registry" / "apps.json").stat().st_size
        self.assertLess(size, 512 * 1024 - 64 * 1024, f"apps.json is {size} bytes, close to the 512 KB installed DeckyHub accepts")


@unittest.skipUnless((PLUGIN / "src" / "types.ts").exists(), "needs a deckyhub-plugin checkout")
class PluginContractTests(unittest.TestCase):
    """What DeckyHub in people's hands reads from stats.json must keep coming."""

    def test_stats_keep_every_field_deckyhub_reads(self):
        fields = re.search(r"type PluginStats = \{([^}]*)\}", (PLUGIN / "src" / "types.ts").read_text(encoding="utf-8")).group(1)
        read = set(re.findall(r"(\w+)\?:", fields))
        written = set(plugin_stats({"repo": "o/a", "asset": {"include": [".zip"], "exclude": []}}, [], stars=lambda repo: 0, manifest=lambda asset: {}))
        # Written only when there's something to say.
        written |= {"warnings", "prereleaseWarnings", "fork"}
        self.assertLessEqual(read, written)

    def test_registry_still_sends_every_warning_deckyhub_knows(self):
        badges = (PLUGIN / "src" / "components" / "AppBadges.tsx").read_text(encoding="utf-8")
        known = re.search(r"AUDIT_WARNINGS = \[([^\]]*)\]", badges)
        self.assertLessEqual(set(re.findall(r'"([\w-]+)"', known.group(1))) if known else set(), WARNING_IDS)


if __name__ == "__main__":
    unittest.main()
