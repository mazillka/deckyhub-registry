"""Build registry.deckyhub.com into OUT_DIR: only redirects to deckyhub.com.

    python scripts/build_site.py OUT_DIR

Everything that used to be here lives on deckyhub.com now (built by mazillka/deckyhub-plugin):
the plugins at https://deckyhub.com/plugins/, how to contribute at https://deckyhub.com/contribute/
and the registry editor beside it, in English and Ukrainian. The old addresses keep working: each
is a small page that sends the visitor (and search engines, through the canonical link) to the
same page on deckyhub.com. The plugin list is this checkout's registry/apps.json.
"""
import json
import re
import shutil
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry" / "apps.json"
DECKYHUB = "https://deckyhub.com/"

# Old page on registry.deckyhub.com -> where it lives on deckyhub.com now.
PAGES = {
    "index.html": ("contribute/", "Contribute"),
    "editor.html": ("contribute/editor.html", "The registry editor"),
    "uk/index.html": ("uk/contribute/", "Contribute"),
    "uk/editor.html": ("uk/contribute/editor.html", "The registry editor"),
}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def redirect_page(target: str, what: str) -> str:
    """A page that sends the visitor to `target` and tells search engines it moved there."""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(what)} moved to deckyhub.com</title>
<meta name="description" content="{escape(what)} is now on deckyhub.com.">
<link rel="canonical" href="{escape(target)}">
<meta http-equiv="refresh" content="0; url={escape(target)}">
<script>location.replace({json.dumps(target)})</script>
</head>
<body>
<h1>{escape(what)} moved</h1>
<p><a href="{escape(target)}">Continue to {escape(target)}</a></p>
</body>
</html>
"""


def llms_txt() -> str:
    return "\n".join([
        "# DeckyHub Registry", "",
        "> This site moved to deckyhub.com. The list of Steam Deck plugins (Decky Loader plugins) behind DeckyHub's Discover tab, each with its own page, and how to add to it are all there.", "",
        f"- [DeckyHub for AI]({DECKYHUB}llms.txt): the plugin store, how to install it, and every plugin page",
        f"- [All plugins]({DECKYHUB}plugins/)",
        f"- [Contribute]({DECKYHUB}contribute/): suggest a plugin, add it yourself, or run your own list",
        f"- [Registry editor]({DECKYHUB}contribute/editor.html): build or edit a plugin list in the browser",
        "- [Plugin list as JSON](https://raw.githubusercontent.com/mazillka/deckyhub-registry/main/registry/apps.json)", ""])


def build(out: Path, apps: list[dict]) -> None:
    shutil.copytree(ROOT / "docs", out, dirs_exist_ok=True)
    for old, (new, what) in PAGES.items():
        (out / old).parent.mkdir(parents=True, exist_ok=True)
        (out / old).write_text(redirect_page(DECKYHUB + new, what), encoding="utf-8")
    (out / "plugins").mkdir(exist_ok=True)
    for app in apps:
        (out / "plugins" / f"{app['id']}.html").write_text(redirect_page(f"{DECKYHUB}plugins/{app['id']}.html", app["name"]), encoding="utf-8")
    (out / "categories").mkdir(exist_ok=True)
    for category in sorted({app["category"] for app in apps}):
        (out / "categories" / f"{slug(category)}.html").write_text(redirect_page(f"{DECKYHUB}plugins/#cat={slug(category)}", f"{category} plugins"), encoding="utf-8")
    (out / "llms.txt").write_text(llms_txt(), encoding="utf-8")


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    apps = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]
    build(out, apps)
    print(f"registry.deckyhub.com: {len(PAGES) + len(apps)} pages redirect to deckyhub.com; site written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
