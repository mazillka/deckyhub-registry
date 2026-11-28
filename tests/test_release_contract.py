"""Check the registry's release selection against the plugin's actual filters."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = Path(os.environ.get("DECKYHUB_PLUGIN", ROOT.parent / "deckyhub-plugin"))
sys.path.insert(0, str(ROOT / "scripts"))
from validate import channel_releases, matching_assets  # noqa: E402


class ReleaseContractTests(unittest.TestCase):
    def test_plugin_and_registry_agree_on_release_selection(self):
        filters = PLUGIN / "src" / "releaseFilters.ts"
        version = PLUGIN / "src" / "version.ts"
        releases = PLUGIN / "src" / "releases.ts"
        # A plugin from before releaseFilters.ts keeps the filters inside releases.ts.
        if releases.exists() and "function matchingAssets(" in releases.read_text(encoding="utf-8"):
            self.skipTest("this plugin version has no separate release filters")
        # CI names the plugin, so anything missing there fails below instead of skipping.
        if "DECKYHUB_PLUGIN" not in os.environ and (not PLUGIN.exists() or not shutil.which("node")):
            self.skipTest("no plugin checkout or Node")
        cases = [
            {"app": {"asset": {"include": ["plugin"], "exclude": ["source"]}}, "releases": [
                {"tag_name": "v1", "published_at": "2026-01-01", "assets": [{"name": "Plugin.zip"}]},
                {"tag_name": "v2-beta", "published_at": "2026-03-01", "prerelease": True, "assets": [{"name": "Plugin.ZIP"}, {"name": "plugin-source.zip"}]},
                {"tag_name": "v3", "published_at": "2026-04-01", "draft": True, "assets": [{"name": "plugin.zip"}]},
                {"tag_name": "v4", "published_at": "2026-05-01", "assets": [{"name": "setup.exe"}]},
            ]},
            {"app": {"asset": {"include": [], "exclude": []}, "releaseTagInclude": "beta"}, "releases": [
                {"tag_name": "BETA-1", "published_at": "2026-01-01", "prerelease": True, "assets": [{"name": "one.zip"}, {"name": "two.ZIP"}]},
                {"tag_name": "stable", "published_at": "2026-02-01", "assets": [{"name": "one.zip"}]},
            ]},
        ]
        expected = []
        for case in cases:
            channels = channel_releases(case["app"], case["releases"])
            expected.append({channel: ({"tag": item.get("tag_name") or item.get("name"), "assets": [a["name"] for a in matching_assets(case["app"], item)]} if item else None) for channel, item in channels.items()})
        result = subprocess.run(["node", "--experimental-strip-types", str(ROOT / "tests" / "release_contract.mjs"), str(filters.resolve()), str(version.resolve())], input=json.dumps(cases), text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), expected)
