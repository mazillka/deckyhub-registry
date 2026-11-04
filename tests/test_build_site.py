import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_site import build, slug  # noqa: E402

APPS = [
    {"id": "mako-decky", "name": "MAKO Decky", "repo": "eugeniosegala/MAKO", "category": "Frame Generation"},
    {"id": "evil", "name": "Evil <script>", "repo": "o/evil", "category": "Utilities & Tools"},
]


class BuildSiteTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.out)
        build(self.out, APPS)

    def read(self, path):
        return (self.out / path).read_text(encoding="utf-8")

    def test_old_plugin_and_category_addresses_redirect_to_deckyhub(self):
        page = self.read("plugins/mako-decky.html")
        self.assertIn('<link rel="canonical" href="https://deckyhub.com/plugins/mako-decky.html">', page)
        self.assertIn('content="0; url=https://deckyhub.com/plugins/mako-decky.html"', page)
        self.assertIn('location.replace("https://deckyhub.com/plugins/mako-decky.html")', page)
        self.assertIn("https://deckyhub.com/plugins/#cat=frame-generation", self.read("categories/frame-generation.html"))
        self.assertEqual(slug("Utilities & Tools"), "utilities-tools")

    def test_names_are_escaped_in_redirects(self):
        self.assertNotIn("<script>Evil", self.read("plugins/evil.html"))
        self.assertIn("Evil &lt;script&gt;", self.read("plugins/evil.html"))

    def test_contributor_pages_get_the_shared_menu_and_footer(self):
        for name in ("index.html", "editor.html", "404.html"):
            page = self.read(name)
            self.assertNotIn("<!-- site-", page)
            self.assertNotIn("/* site-nav-style */", page)
        index = self.read("index.html")
        self.assertIn('class="site-nav"', index)
        self.assertIn('aria-current="page">Contribute', index)
        self.assertIn("<footer", index)

    def test_sitemap_lists_only_contributor_pages(self):
        sitemap = self.read("sitemap.xml")
        self.assertIn("<loc>https://registry.deckyhub.com/editor.html</loc>", sitemap)
        self.assertNotIn("/plugins/", sitemap)
        self.assertIn("https://deckyhub.com/plugins/", self.read("llms.txt"))


if __name__ == "__main__":
    unittest.main()
