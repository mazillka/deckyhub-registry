"""Build registry.deckyhub.com (the contributor site) into OUT_DIR as static HTML.

    python scripts/build_site.py OUT_DIR

Plugins are browsed on deckyhub.com (https://deckyhub.com/plugins/), which has a page for
every plugin in this list. This site is for the people who add and fix entries: how to
contribute and the registry editor, with the same menu and footer as deckyhub.com
(site_shell.py, a copy of mazillka/deckyhub-plugin's devtools/site_shell.py: change both together).

The old addresses keep working: plugins/<id>.html and categories/<slug>.html are small
pages that send the visitor (and search engines, through the canonical link) to the same
plugin or category on deckyhub.com. The plugin list is this checkout's registry/apps.json.
"""
import json
import re
import shutil
import sys
import time
from html import escape
from pathlib import Path

import site_shell

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry" / "apps.json"
SITE = "https://registry.deckyhub.com/"
DECKYHUB = "https://deckyhub.com/"


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


def llms_txt(count: int) -> str:
    return "\n".join([
        "# DeckyHub Registry", "",
        f"> The list of {count} Steam Deck plugins (Decky Loader plugins) behind DeckyHub's Discover tab, and how to add to it. Browse the plugins, each with its own page, on deckyhub.com.", "",
        f"- [All plugins]({DECKYHUB}plugins/): every plugin, most downloaded first, with its details, notes and security scans",
        f"- [DeckyHub]({DECKYHUB}): the plugin store itself, and how to install it ({DECKYHUB}llms.txt)",
        f"- [Contribute]({SITE}): suggest a plugin, add it yourself, or run your own list",
        f"- [Registry editor]({SITE}editor.html): build or edit a plugin list in the browser",
        "- [Plugin list as JSON](https://raw.githubusercontent.com/mazillka/deckyhub-registry/main/registry/apps.json)",
        "- [Suggest a plugin](https://github.com/mazillka/deckyhub-registry/issues/new)", ""])


def build(out: Path, apps: list[dict]) -> None:
    shutil.copytree(ROOT / "docs", out, dirs_exist_ok=True)
    for name in ("index.html", "editor.html", "404.html"):
        page = (out / name).read_text(encoding="utf-8").replace("<!-- plugin-count -->", str(len(apps)))
        (out / name).write_text(site_shell.apply(page), encoding="utf-8")

    (out / "plugins").mkdir(exist_ok=True)
    for app in apps:
        (out / "plugins" / f"{app['id']}.html").write_text(redirect_page(f"{DECKYHUB}plugins/{app['id']}.html", app["name"]), encoding="utf-8")
    (out / "categories").mkdir(exist_ok=True)
    for category in sorted({app["category"] for app in apps}):
        (out / "categories" / f"{slug(category)}.html").write_text(redirect_page(f"{DECKYHUB}plugins/#cat={slug(category)}", f"{category} plugins"), encoding="utf-8")

    (out / "llms.txt").write_text(llms_txt(len(apps)), encoding="utf-8")
    today = time.strftime("%Y-%m-%d", time.gmtime())
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "".join(f"<url><loc>{SITE}{path}</loc><lastmod>{today}</lastmod></url>\n" for path in ("", "editor.html")) + "</urlset>\n", encoding="utf-8")


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    apps = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]
    build(out, apps)
    print(f"{len(apps)} plugin addresses redirect to deckyhub.com; site written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
