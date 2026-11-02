import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from ship_plugins import repositories_section, with_section  # noqa: E402
from validate import README  # noqa: E402

MAIN = "# Registry\n\nIntro.\n\n## Repositories\n\n| Tool | Category | Repository |\n| --- | --- | --- |\n| A | X | [o/a](https://github.com/o/a) |\n\n## Branches\n\nmain's own text.\n"
DEVELOP = "# Registry\n\nNewer intro on develop.\n\n## Repositories\n\n| Tool | Category | Repository |\n| --- | --- | --- |\n| A | X | [o/a](https://github.com/o/a) |\n| B | Y | [o/b](https://github.com/o/b) |\n\n## Branches\n\ndevelop's newer text.\n"


class ShipPluginsTests(unittest.TestCase):
    def test_only_the_repositories_table_comes_from_develop(self):
        shipped = with_section(MAIN, repositories_section(DEVELOP))
        self.assertIn("[o/b](https://github.com/o/b)", shipped)
        self.assertIn("Intro.", shipped)
        self.assertIn("main's own text.", shipped)
        self.assertNotIn("develop's newer text.", shipped)
        self.assertNotIn("Newer intro", shipped)

    def test_a_last_section_runs_to_the_end(self):
        self.assertEqual(repositories_section("x\n## Repositories\n\n| t |\n"), "## Repositories\n\n| t |\n")

    def test_the_real_readme_has_the_section(self):
        section = repositories_section(README.read_text(encoding="utf-8"))
        self.assertTrue(section.startswith("## Repositories"))
        self.assertIn("| Tool | Category | Repository |", section)
        self.assertNotIn("\n## ", section.rstrip("\n").removeprefix("## Repositories"))


if __name__ == "__main__":
    unittest.main()
