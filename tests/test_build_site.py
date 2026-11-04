import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_site import build, slug  # noqa: E402

APPS = [
    {"id": "mako-decky", "name": "MAKO Decky", "repo": "eugeniosegala/MAKO", "category": "Frame Generation", "description": "Boosts frame rates with Lossless Scaling frame generation."},
    {"id": "evil", "name": "Evil <script>", "repo": "o/evil", "category": "Frame Generation", "description": "</script><img src=x onerror=alert(1)>"},
    {"id": "tool", "name": "Tool", "repo": "o/tool", "category": "Utilities"},
]
STATS = {
    "eugeniosegala/mako": {"downloads": 73981, "stars": 680, "updated": "2026-01-01T00:00:00Z", "root": True, "fork": "orig/mako", "ai": ["CLAUDE.md"], "warnings": ["private-data", "unknown-id"]},
}
SHA = "c" * 64
SCANS = {
    "eugeniosegala/mako": {"stable": {"tag": "v2", "file": "mako.zip", "sha256": SHA, "clamav": {"result": "clean", "scannedAt": "2026-11-02T15:07:49Z"}, "yara": {"result": "infected", "found": ["Linux_Test"], "scannedAt": "2026-11-02T15:07:49Z"}}},
}
REPORTS = {SHA: {"state": "complete", "flagged": 1, "total": 20, "dataId": "abc123"}}


class BuildSiteTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.out)
        build(self.out, APPS, STATS, SCANS, REPORTS)

    def read(self, path):
        return (self.out / path).read_text(encoding="utf-8")

    def test_a_page_per_plugin_with_what_the_catalog_knows(self):
        page = self.read("plugins/mako-decky.html")
        self.assertIn("<title>MAKO Decky: Frame Generation plugin for Steam Deck (Decky Loader) | DeckyHub</title>", page)
        self.assertIn('<link rel="canonical" href="https://registry.deckyhub.com/plugins/mako-decky.html">', page)
        for text in ("74K", "680", "January 1, 2026", "Runs as root", "Fork", "orig/mako", "CLAUDE.md", "Reads private data", "Threat found", "YARA: threat found (Linux_Test)", "Install MAKO Decky on Steam Deck"):
            self.assertIn(text, page)
        # A warning the page doesn't know yet (the registry adds them first) shows nothing.
        self.assertNotIn("unknown-id", page)
        self.assertIn('href="/plugins/evil.html"', page)  # more from its category
        self.assertIn("No badges", self.read("plugins/tool.html"))

    def test_a_long_repository_name_gets_a_full_width_tile_that_wraps(self):
        page = self.read("plugins/mako-decky.html")
        self.assertIn('<li class="wide"><strong><a href="https://github.com/eugeniosegala/MAKO">eugeniosegala/MAKO</a></strong>Repository</li>', page)
        self.assertIn(".facts li.wide{grid-column:1/-1}", page)
        self.assertIn("overflow-wrap:anywhere", page.split(".facts li{", 1)[1].split("}", 1)[0])

    def test_plugin_pages_show_the_security_scans(self):
        page = self.read("plugins/mako-decky.html")
        for text in ("Security scans", "Stable release", "mako.zip", SHA, "ClamAV", "No threats found", "Threat found (Linux_Test)", "November 2, 2026",
                     f'href="https://www.virustotal.com/gui/file/{SHA}"', "nothing is uploaded", "1 of 20 engines flagged this file",
                     'href="https://metadefender.opswat.com/results/file/abc123/regular/overview"'):
            self.assertIn(text, page)
        # A plugin that hasn't been scanned says so instead of looking clean.
        self.assertIn("Not scanned yet", self.read("plugins/tool.html"))
        self.assertNotIn("virustotal.com/gui/file", self.read("plugins/tool.html"))

    def test_a_report_without_a_safe_id_gets_no_link(self):
        out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out)
        build(out, APPS, STATS, SCANS, {SHA: {"state": "complete", "flagged": 0, "total": 20, "dataId": '"><script>'}})
        page = (out / "plugins" / "mako-decky.html").read_text(encoding="utf-8")
        self.assertIn("0 of 20 engines flagged this file", page)
        self.assertNotIn("results/file/", page)

    def test_shared_navigation_on_catalog_pages(self):
        for path in ("index.html", "editor.html", "plugins/mako-decky.html", "categories/frame-generation.html"):
            page = self.read(path)
            for link in ("https://deckyhub.com/", "https://registry.deckyhub.com/", "https://registry.deckyhub.com/editor.html", "https://deckyhub.com/#install", "https://deckyhub.com/releases.html"):
                self.assertIn(f'href="{link}"', page, path)

    def test_text_from_the_list_is_escaped(self):
        page = self.read("plugins/evil.html")
        self.assertNotIn("<img src=x", page)
        self.assertNotIn("Evil <script>", page)
        self.assertIn("Evil &lt;script&gt;", page)
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
            self.assertEqual(json.loads(block)["@context"], "https://schema.org")

    def test_category_pages_index_catalog_sitemap_and_llms_txt(self):
        self.assertEqual(slug("Frame Generation"), "frame-generation")
        category = self.read("categories/frame-generation.html")
        self.assertIn("2 Decky Loader plugins in Frame Generation", category)
        self.assertLess(category.index("MAKO Decky"), category.index("Evil &lt;script&gt;"))  # most downloaded first
        index = self.read("index.html")
        for placeholder in ("<!-- catalog -->", "<!-- categories -->", "<!-- structured-data -->", "/* plugin-pages */"):
            self.assertNotIn(placeholder, index)
        self.assertIn('<a class="app" href="/plugins/mako-decky.html">', index)
        self.assertIn('const PAGES = new Set(["evil", "mako-decky", "tool"]);', index)
        self.assertIn('href="/categories/utilities.html"', index)
        sitemap = self.read("sitemap.xml")
        self.assertEqual(sitemap.count("<url>"), 2 + 2 + len(APPS))
        self.assertIn("<loc>https://registry.deckyhub.com/plugins/mako-decky.html</loc><lastmod>2026-01-01</lastmod>", sitemap)
        llms = self.read("llms.txt")
        self.assertTrue(llms.startswith("# DeckyHub Registry\n\n> "))
        self.assertIn("- [MAKO Decky](https://registry.deckyhub.com/plugins/mako-decky.html): Boosts frame rates", llms)
        self.assertIn("Sitemap: https://registry.deckyhub.com/sitemap.xml", self.read("robots.txt"))

    def test_without_stats_or_scans_the_pages_still_build(self):
        out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out)
        build(out, APPS, {}, {})
        self.assertIn("Category", (out / "plugins" / "mako-decky.html").read_text(encoding="utf-8"))
        self.assertNotIn("Downloads", (out / "plugins" / "mako-decky.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
