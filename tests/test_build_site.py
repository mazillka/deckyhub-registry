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

    def test_contributor_pages_and_editor_redirect_to_deckyhub(self):
        for old, new in (("index.html", "contribute/"), ("editor.html", "contribute/editor.html"), ("uk/index.html", "uk/contribute/"), ("uk/editor.html", "uk/contribute/editor.html")):
            self.assertIn(f'<link rel="canonical" href="https://deckyhub.com/{new}">', self.read(old))
        self.assertFalse((self.out / "sitemap.xml").exists())
        self.assertIn("https://deckyhub.com/contribute/", self.read("llms.txt"))


if __name__ == "__main__":
    unittest.main()
