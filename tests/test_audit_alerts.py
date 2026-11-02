import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import audit_alerts  # noqa: E402
from audit_alerts import body, changes  # noqa: E402


class AuditAlertTests(unittest.TestCase):
    def test_warnings_that_appeared_and_went_away(self):
        old = {"o/a": {"warnings": ["vulnerable"]}, "o/b": {"warnings": ["obfuscated"]}}
        new = {"o/a": {"warnings": ["vulnerable", "private-data"]}, "o/b": {"warnings": []}, "o/c": {"prereleaseWarnings": ["blocked"]}}
        self.assertEqual(changes(old, new), ({"o/a": ["private-data"], "o/c": ["blocked (pre-release)"]}, {"o/b": ["obfuscated"]}))

    def test_first_run_after_warnings_existed_reports_no_change(self):
        self.assertEqual(changes({"o/a": {"downloads": 1}}, {"o/a": {"warnings": ["blocked"]}}), ({}, {}))

    def test_body_puts_news_first_then_every_current_warning(self):
        old = {"o/a": {"warnings": ["vulnerable"]}, "o/b": {"warnings": ["obfuscated"]}}
        new = {"o/a": {"warnings": ["vulnerable", "private-data"]}, "o/b": {}, "o/d": {"warnings": ["persistence"]}}
        action, text = body(old, new, {"o/a": "Plugin A"}, "2026-11-02T03:00:00Z")
        self.assertEqual(action, "changed")
        news, current = text.split("## All current warnings")
        self.assertIn("**Plugin A** ([o/a](https://github.com/o/a)): private-data", news)
        self.assertIn("No longer flagged", news)
        self.assertIn("**o/b**", news)
        self.assertIn("(2 plugins)", current)
        self.assertIn("**Plugin A** ([o/a](https://github.com/o/a)): vulnerable, private-data", current)
        self.assertIn("**o/d**", current)
        self.assertIn("2026-11-02T03:00:00Z", text)

    def test_no_change_still_writes_the_whole_picture(self):
        same = {"o/a": {"warnings": ["vulnerable"]}}
        action, text = body(same, same, {}, "t")
        self.assertEqual(action, "same")
        self.assertIn("Nothing new.", text)
        self.assertIn("**o/a**", text)

    def test_nothing_flagged_closes_the_issue(self):
        action, text = body({"o/a": {"warnings": ["vulnerable"]}}, {"o/a": {}}, {}, "t")
        self.assertEqual(action, "clear")
        self.assertIn("None.", text)

    def test_a_huge_list_is_cut_to_fit_github(self):
        limit = audit_alerts.MAX_BODY
        audit_alerts.MAX_BODY = 500
        try:
            _, text = body({}, {f"o/p{number}": {"warnings": ["vulnerable"]} for number in range(100)}, {}, "t")
        finally:
            audit_alerts.MAX_BODY = limit
        self.assertLess(len(text), 700)
        self.assertIn("cut to fit", text)


if __name__ == "__main__":
    unittest.main()
