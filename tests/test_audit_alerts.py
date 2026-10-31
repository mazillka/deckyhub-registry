import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from audit_alerts import new_warnings, report  # noqa: E402


class AuditAlertTests(unittest.TestCase):
    def test_only_warnings_that_grew_are_reported(self):
        old = {"o/a": {"warnings": ["vulnerable"]}, "o/b": {"warnings": ["obfuscated"]}}
        new = {"o/a": {"warnings": ["vulnerable", "private-data"]}, "o/b": {"warnings": []}, "o/c": {"prereleaseWarnings": ["blocked"]}}
        found = new_warnings(old, new)
        self.assertEqual(found, {"o/a": ["private-data"], "o/c": ["blocked (pre-release)"]})
        text = report(found, {"o/a": "Plugin A"})
        self.assertIn("**Plugin A** ([o/a](https://github.com/o/a)): private-data", text)
        self.assertIn("**o/c**", text)

    def test_first_run_after_warnings_existed_reports_nothing(self):
        self.assertEqual(new_warnings({"o/a": {"downloads": 1}}, {"o/a": {"warnings": ["blocked"]}}), {})
        self.assertEqual(report({}, {}), "")


if __name__ == "__main__":
    unittest.main()
