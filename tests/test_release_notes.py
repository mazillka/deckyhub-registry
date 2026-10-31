import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from release_notes import release_notes  # noqa: E402


def app(id, **fields):
    return {"id": id, "name": id.title(), "repo": f"o/{id}", "category": "Utilities", "description": "Does things", "asset": {"include": [".zip"]}, **fields}


class ReleaseNotesTests(unittest.TestCase):
    def test_lists_added_removed_and_changed_in_words(self):
        old = {a["id"]: a for a in [app("kept"), app("gone"), app("moved"), app("zip"), app("quiet")]}
        new = {a["id"]: a for a in [
            app("kept"), app("moved", name="Moved Too", category="Performance", description="New words."),
            app("zip", asset={"include": ["plugin", ".zip"]}), app("quiet", detect={"names": ["Q"]}),
            app("new"), app("other", category="Controllers", repo="Me/Other"),
        ]}
        text = release_notes(old, new, {"me/other": {"fork": "orig/other"}})
        self.assertIn("2 new plugins on Discover.", text)
        self.assertIn("### Utilities\n\n- **New**: Does things.", text)
        self.assertIn("- **Other**: Does things. A fork that carries on orig/other.", text)
        self.assertIn("## Removed\n\n- **Gone** (o/gone)", text)
        self.assertIn("- **Moved Too**: renamed from Moved, moved to Performance, clearer description.", text)
        self.assertIn("- **Zip**: installs the right ZIP.", text)
        self.assertNotIn("Quiet", text)
        self.assertTrue(text.endswith("The list now has **6 plugins**.\n"))

    def test_nothing_users_see_and_first_release(self):
        old = {"a": app("a")}
        self.assertIn("registry maintenance only", release_notes(old, {"a": app("a", detect={"names": ["A"]})}))
        self.assertIn("first registry release", release_notes(None, old))


if __name__ == "__main__":
    unittest.main()
