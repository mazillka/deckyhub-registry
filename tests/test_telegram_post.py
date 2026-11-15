import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from telegram_post import LIMIT, message  # noqa: E402

URL = "https://github.com/mazillka/deckyhub-registry/releases/tag/registry-2026.11.15-55"
NOTES = "## Added\n\n2 new plugins on Discover.\n\n### Utilities\n\n- **DeckWarden**: Vaultwarden in Gaming Mode.\n- **Mixer**: Volume per app.\n"


class TelegramMessageTests(unittest.TestCase):
    def test_release_notes_become_plain_text_with_a_link_and_no_markdown(self):
        text = message(NOTES, URL, "2026-11-15")
        self.assertTrue(text.startswith("DeckyHub plugin list updated (2026-11-15)"))
        self.assertIn("\nADDED\n", text)
        self.assertIn("\nUtilities:\n", text)
        self.assertIn("- DeckWarden: Vaultwarden in Gaming Mode.", text)
        self.assertNotIn("**", text)
        self.assertIn(f"Full notes: {URL}", text)

    def test_a_release_without_plugin_changes_is_not_announced(self):
        self.assertIsNone(message("No plugin changes: registry maintenance only.\n\nThe list now has 629 plugins.", URL, "d"))
        self.assertIsNone(message("  \n", URL, "d"))

    def test_a_long_list_is_cut_at_a_line_and_points_to_the_full_notes(self):
        notes = "## Added\n\n" + "\n".join(f"- **Plugin {n}**: does a thing." for n in range(400))
        text = message(notes, URL, "d")
        self.assertLess(len(text), 4096)
        self.assertIn("…and more in the full notes.", text)
        self.assertLessEqual(len(text.split("\n…and more")[0]), LIMIT + 200)
        self.assertFalse(text.split("\n…and more")[0].endswith("- Plugin 3"), "cut mid-line")


if __name__ == "__main__":
    unittest.main()
