"""Build registry.deckyhub.com (the catalog site) into OUT_DIR as static HTML.

    python scripts/build_site.py OUT_DIR

Copies docs/, then writes what search engines and AI assistants read without running
JavaScript:
- index.html: the catalog already filled in (the page's script still loads the live
  list and redraws it), links to every category page, and schema.org JSON-LD (an
  ItemList of every plugin page).
- plugins/<id>.html: a page per plugin, with what the catalog knows about it
  (description, category, downloads, stars, last release, Runs as root, Fork, AI and
  audit warning badges, the virus scan of the release DeckyHub installs) and how to
  install it with DeckyHub.
- categories/<slug>.html: the plugins in each category.
- sitemap.xml and llms.txt (every plugin as plain text, for AI assistants).

The plugin list is this checkout's registry/apps.json. Stats (stats.json) and scans
(plugins.json) are fetched from the release-index and virus-scans branches; without
them the pages go out without numbers or badges. The pages workflow runs this on every
push to main that changes the site or the list, and daily.
"""
import json
import re
import shutil
import sys
import time
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry" / "apps.json"
SITE = "https://registry.deckyhub.com/"
DECKYHUB = "https://deckyhub.com/"
STATS_URL = "https://raw.githubusercontent.com/mazillka/deckyhub-registry/release-index/stats.json"
SCANS_URL = "https://raw.githubusercontent.com/mazillka/deckyhub-registry/virus-scans/plugins.json"
SCAN_LABELS = {"clean": ("No threats", "clean"), "infected": ("Threat found", "stale"), "partial": ("Not fully scanned", "warn")}
SCAN_RESULTS = {"clean": "no threats found", "infected": "threat found", "incomplete": "only partly scanned", "error": "couldn't be scanned"}


def fetch_json(url: str, key: str) -> dict:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "deckyhub-registry-site"}), timeout=60) as response:
            return json.load(response).get(key) or {}
    except Exception as error:  # noqa: BLE001 - the site goes out without that data
        print(f"warning: {url}: {error}", file=sys.stderr)
        return {}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-") or "other"


def warning_labels(page: str) -> dict[str, tuple[str, str]]:
    """The catalog script's WARNINGS (id: [label, hint]), so both say the same."""
    block = page.split("const WARNINGS = {", 1)[1].split("};", 1)[0]
    return {key: (label, hint) for key, label, hint in re.findall(r'^\s*"([\w-]+)": \["([^"]+)", "([^"]+)"\]', block, re.M)}


def compact(number: int) -> str:
    for size, suffix in ((1_000_000, "M"), (1_000, "K")):
        if number >= size:
            return f"{number / size:.1f}".rstrip("0").rstrip(".") + suffix
    return str(number)


def nice_date(iso: str | None) -> str:
    return time.strftime("%B %-d, %Y", time.strptime(iso[:10], "%Y-%m-%d")) if iso else ""


def scan_kind(channel: dict) -> str:
    results = [scan["result"] for scan in (channel.get("clamav"), channel.get("yara")) if scan]
    return "infected" if "infected" in results else "partial" if any(result != "clean" for result in results) else "clean"


def json_ld(data: dict) -> str:
    # No "<" at all inside the script element, so nothing in a name or description can end it.
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", **data}, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c") + "</script>"


STYLE = """:root{color-scheme:dark;--bg:#10151f;--panel:#182131;--line:#2e405a;--text:#eef4ff;--muted:#b6c3d4;--dim:#8a9bb2;--accent:#1d75cc;--accent2:#4b9cf0;--warn:#e8b54a}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}a{color:var(--accent2)}
.wrap{max-width:900px;margin:auto;padding:0 20px}
nav{border-bottom:1px solid var(--line)}nav .wrap{display:flex;align-items:center;gap:20px;height:56px;max-width:1100px}
nav .brand{font-weight:700;color:var(--text);text-decoration:none;margin-right:auto}nav a{color:var(--muted);text-decoration:none}
.crumbs{color:var(--dim);font-size:.9rem;margin:28px 0 6px}.crumbs a{color:var(--dim)}
h1{font-size:clamp(1.9rem,5vw,2.6rem);line-height:1.15;margin:0 0 10px}h2{font-size:1.25rem;margin:32px 0 10px}
.lead{font-size:1.15rem;color:var(--muted);margin:0 0 18px}
.facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;margin:0;padding:0;list-style:none}
.facts li{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 14px;color:var(--muted);font-size:.9rem}.facts strong{display:block;color:var(--text);font-size:1.05rem}
.badges{display:grid;gap:8px;margin:0;padding:0;list-style:none}.badges li{color:var(--muted)}
.badge{padding:1px 8px;border-radius:999px;border:1px solid currentColor;font-size:.8rem;white-space:nowrap;margin-right:6px}
.root{color:#ffb35c}.stale{color:#ff8a8a}.warn{color:var(--warn)}.fork{color:var(--muted)}.clean{color:#6bcb6b}.ai{color:#c49bff}
.btn{display:inline-block;padding:11px 18px;border-radius:8px;background:var(--accent);color:#fff;text-decoration:none;font-weight:600;margin:4px 8px 4px 0}.btn.ghost{background:transparent;border:1px solid var(--line);color:var(--text)}
.list{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px;padding:0;list-style:none}
.list a{display:block;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--text);height:100%}
.list a:hover{border-color:var(--accent2)}.list small{display:block;color:var(--muted);margin-top:4px}
code{background:#0f1724;border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:.88em;overflow-wrap:anywhere}
.note{color:var(--dim);font-size:.9rem}
footer{margin-top:48px;padding:28px 0;border-top:1px solid var(--line);color:var(--dim);font-size:.88rem}"""


def page(title: str, description: str, path: str, body: str, data: list[str]) -> str:
    url = SITE + path
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#10151f">
<meta property="og:type" content="website"><meta property="og:site_name" content="DeckyHub Registry">
<meta property="og:url" content="{url}"><meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}">
<meta name="twitter:card" content="summary">
{"".join(data)}
<style>{STYLE}</style>
</head>
<body>
<nav><div class="wrap"><a class="brand" href="/">DeckyHub Registry</a><a href="/#catalog">Catalog</a><a href="{DECKYHUB}">Get DeckyHub</a></div></nav>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap"><strong>Disclaimer:</strong> Not affiliated with Valve or the Decky Loader project. DeckyHub lists plugins from their authors' public GitHub repositories; it doesn't make, review or vouch for them, and they install at your own risk. Plugins belong to their authors. <a href="/">DeckyHub Registry</a> · <a href="{DECKYHUB}">DeckyHub</a> · <a href="https://github.com/mazillka/deckyhub-registry">Source</a></div></footer>
</body>
</html>
"""


def crumbs(*parts: tuple[str, str | None]) -> tuple[str, str]:
    links = " › ".join(f'<a href="{escape(href)}">{escape(name)}</a>' if href else escape(name) for name, href in parts)
    data = json_ld({"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": index + 1, "name": name, **({"item": SITE + href.lstrip("/")} if href else {})} for index, (name, href) in enumerate(parts)]})
    return f'<p class="crumbs">{links}</p>', data


def badges_of(app: dict, stats: dict, scans: dict, warnings: dict) -> list[str]:
    items = []
    if stats.get("root"):
        items.append('<li><span class="badge root">Runs as root</span> Its plugin.json asks Decky Loader to run its backend as root, with full access to the Deck. Many plugins need that for real reasons; install it only if you trust the author.</li>')
    if stats.get("fork"):
        items.append(f'<li><span class="badge fork">Fork</span> A fork of <a href="https://github.com/{escape(stats["fork"])}">{escape(stats["fork"])}</a> that carries the plugin on after its original stopped.</li>')
    if stats.get("ai"):
        items.append(f'<li><span class="badge ai">AI</span> Its repository has instructions for AI coding assistants ({escape(", ".join(stats["ai"]))}), so it\'s likely developed with AI help. That says nothing about its quality or safety.</li>')
    for key, prefix in [*((key, "") for key in stats.get("warnings") or []), *((key, "Pre-release: ") for key in stats.get("prereleaseWarnings") or [] if key not in (stats.get("warnings") or []))]:
        if key in warnings:
            label, hint = warnings[key]
            items.append(f'<li><span class="badge {"stale" if key == "blocked" else "warn"}">{escape(prefix + label)}</span> {escape(hint)} (from <a href="https://decky-extended-plugins.beallio.com/audit">Decky Extended Plugins\' audit</a>)</li>')
    for channel, prefix in ((scans.get("stable"), ""), (scans.get("prerelease"), "Pre-release: ")):
        if not channel or not channel.get("clamav"):
            continue
        kind = scan_kind(channel)
        if prefix and (scans.get("stable") or {}).get("clamav") and kind == "clean":
            continue
        label, css = SCAN_LABELS[kind]
        results = "; ".join(f"{name}: {SCAN_RESULTS.get(scan['result'], scan['result'])}" + (f" ({', '.join(scan['found'])})" if scan.get("found") else "") for name, scan in (("ClamAV", channel.get("clamav")), ("YARA", channel.get("yara"))) if scan)
        items.append(f'<li><span class="badge {css}">{escape(prefix + label)}</span> Virus scan of <code>{escape(channel.get("file", ""))}</code> ({escape(channel.get("tag", ""))}): {escape(results)}. A clean scan isn\'t proof of safety.</li>')
    return items


def plugin_page(app: dict, stats: dict, scans: dict, warnings: dict, others: list[dict]) -> str:
    name, repo, category, description = app["name"], app["repo"], app["category"], app.get("description") or ""
    repo_url = f"https://github.com/{repo}"
    trail, trail_data = crumbs(("Catalog", "/"), (category, f"/categories/{slug(category)}.html"), (name, None))
    facts = [f'<li><strong><a href="/categories/{slug(category)}.html">{escape(category)}</a></strong>Category</li>']
    if stats.get("downloads") is not None:
        facts.append(f'<li><strong>{compact(stats["downloads"])}</strong>Downloads</li>')
    if stats.get("stars") is not None:
        facts.append(f'<li><strong>{compact(stats["stars"])}</strong>GitHub stars</li>')
    if stats.get("updated"):
        facts.append(f'<li><strong>{nice_date(stats["updated"])}</strong>Latest release</li>')
    badges = badges_of(app, stats, scans, warnings)
    related = [other for other in others if other["id"] != app["id"]][:6]
    body = f"""{trail}
<h1>{escape(name)}</h1>
<p class="lead">{escape(description)}</p>
<p><a class="btn" href="{DECKYHUB}#install">Install with DeckyHub</a><a class="btn ghost" href="{escape(repo_url)}">Source on GitHub</a></p>
<ul class="facts">{"".join(facts)}<li><strong><a href="{escape(repo_url)}">{escape(repo)}</a></strong>Repository</li></ul>
<h2>Install {escape(name)} on Steam Deck</h2>
<p>{escape(name)} is a <a href="https://decky.xyz/">Decky Loader</a> plugin. With <a href="{DECKYHUB}">DeckyHub</a> installed, open DeckyHub's <strong>Discover</strong> tab in Gaming Mode, search for <strong>{escape(name)}</strong> and press <strong>Install</strong>. DeckyHub installs the latest release from <a href="{escape(repo_url)}">{escape(repo)}</a> through Decky Loader, and tells you when there's an update.</p>
<h2>Safety information</h2>
{"<ul class='badges'>" + "".join(badges) + "</ul>" if badges else "<p>No badges: it doesn't run as root, and no audit warnings or virus scan findings are known for it.</p>"}
<p class="note">DeckyHub doesn't make, review or vouch for {escape(name)}; it installs at your own risk. Check its repository before installing.</p>
{f'<h2>More {escape(category)} plugins</h2><ul class="list">' + "".join(f'<li><a href="/plugins/{escape(other["id"])}.html">{escape(other["name"])}<small>{escape(other.get("description") or "")}</small></a></li>' for other in related) + "</ul>" if related else ""}"""
    data = {
        "@type": "SoftwareApplication", "name": name, "description": description, "url": f"{SITE}plugins/{app['id']}.html",
        "applicationCategory": "UtilitiesApplication", "applicationSubCategory": f"Decky Loader plugin: {category}", "operatingSystem": "SteamOS",
        "sameAs": [repo_url], "isAccessibleForFree": True,
    }
    if stats.get("downloads") is not None:
        data["interactionStatistic"] = {"@type": "InteractionCounter", "interactionType": "https://schema.org/DownloadAction", "userInteractionCount": stats["downloads"]}
    if stats.get("updated"):
        data["dateModified"] = stats["updated"]
    title = f"{name}: {category} plugin for Steam Deck (Decky Loader) | DeckyHub"
    summary = f"{description.rstrip('.')}. A Decky Loader plugin for Steam Deck: install and update it from Gaming Mode with DeckyHub." if description else f"{name}, a {category} Decky Loader plugin for Steam Deck. Install and update it from Gaming Mode with DeckyHub."
    return page(title, summary, f"plugins/{app['id']}.html", body, [trail_data, json_ld(data)])


def category_page(category: str, apps: list[dict], stats: dict) -> str:
    trail, trail_data = crumbs(("Catalog", "/"), (category, None))
    ordered = sorted(apps, key=lambda app: -((stats.get(app["repo"].casefold()) or {}).get("downloads") or 0))
    body = f"""{trail}
<h1>{escape(category)} plugins for Steam Deck</h1>
<p class="lead">{len(apps)} Decky Loader plugin{"s" if len(apps) != 1 else ""} in {escape(category)}, most downloaded first. Install and update any of them from Gaming Mode with <a href="{DECKYHUB}">DeckyHub</a>.</p>
<ul class="list">{"".join(f'<li><a href="/plugins/{escape(app["id"])}.html">{escape(app["name"])}<small>{escape(app.get("description") or "")}</small></a></li>' for app in ordered)}</ul>"""
    data = json_ld({"@type": "CollectionPage", "name": f"{category} plugins for Steam Deck", "url": f"{SITE}categories/{slug(category)}.html",
                    "mainEntity": {"@type": "ItemList", "numberOfItems": len(apps), "itemListElement": [{"@type": "ListItem", "position": index + 1, "url": f"{SITE}plugins/{app['id']}.html", "name": app["name"]} for index, app in enumerate(ordered)]}})
    return page(f"{category} plugins for Steam Deck (Decky Loader) | DeckyHub", f"{len(apps)} {category} Decky Loader plugins for Steam Deck, with downloads, stars and safety badges. Install them from Gaming Mode with DeckyHub.", f"categories/{slug(category)}.html", body, [trail_data, data])


def catalog_cards(apps: list[dict]) -> str:
    """The catalog as the page's script draws it (render()), so it's there without JavaScript."""
    return "".join(f'<a class="app" href="/plugins/{escape(app["id"])}.html"><small>{escape(app["category"])}</small><strong>{escape(app["name"])}</strong><p>{escape(app.get("description") or "")}</p><code>{escape(app["repo"])}</code></a>'
                   for app in sorted(apps, key=lambda app: app["name"].casefold()))


def llms_txt(apps: list[dict], categories: dict[str, list[dict]]) -> str:
    lines = [
        "# DeckyHub Registry", "",
        f"> The list of {len(apps)} Steam Deck plugins (Decky Loader plugins) that DeckyHub shows on Discover, including plugins that aren't on the official Decky Loader store. Each one installs and updates from Gaming Mode with DeckyHub ({DECKYHUB}).", "",
        "Every plugin installs from its author's GitHub releases. DeckyHub doesn't make, review or vouch for these plugins. Each plugin's page has its downloads, GitHub stars, last release date, and safety information: a ClamAV and YARA virus scan of the release DeckyHub installs, warnings from Decky Extended Plugins' security audit, whether it runs as root, and whether its repository is set up for AI coding assistants.", "",
        f"- [DeckyHub]({DECKYHUB}): the plugin store itself, and how to install it ({DECKYHUB}llms.txt)",
        f"- [Plugin list as JSON](https://raw.githubusercontent.com/mazillka/deckyhub-registry/main/registry/apps.json)",
        f"- [Suggest a plugin](https://github.com/mazillka/deckyhub-registry/issues/new)", "",
    ]
    for category in sorted(categories):
        lines += [f"## {category}", ""]
        lines += [f"- [{app['name']}]({SITE}plugins/{app['id']}.html): {app.get('description') or ''} (github.com/{app['repo']})" for app in sorted(categories[category], key=lambda app: app["name"].casefold())]
        lines.append("")
    return "\n".join(lines)


def build(out: Path, apps: list[dict], stats: dict, scans: dict) -> None:
    shutil.copytree(ROOT / "docs", out, dirs_exist_ok=True)
    index = out / "index.html"
    html = index.read_text(encoding="utf-8")
    warnings = warning_labels(html)
    categories: dict[str, list[dict]] = {}
    for app in apps:
        categories.setdefault(app["category"], []).append(app)

    (out / "plugins").mkdir(exist_ok=True)
    for app in apps:
        key = app["repo"].casefold()
        (out / "plugins" / f"{app['id']}.html").write_text(plugin_page(app, stats.get(key) or {}, scans.get(key) or {}, warnings, categories[app["category"]]), encoding="utf-8")
    (out / "categories").mkdir(exist_ok=True)
    for category, members in categories.items():
        (out / "categories" / f"{slug(category)}.html").write_text(category_page(category, members, stats), encoding="utf-8")

    for placeholder in ("<!-- catalog -->", "<!-- categories -->", "<!-- structured-data -->", "/* plugin-pages */"):
        if placeholder not in html:
            sys.exit(f"docs/index.html is missing the {placeholder} placeholder")
    category_links = "".join(f'<li><a href="/categories/{slug(category)}.html">{escape(category)}</a> <span>{len(categories[category])}</span></li>' for category in sorted(categories))
    item_list = json_ld({"@type": "CollectionPage", "name": "DeckyHub Registry: Steam Deck plugin catalog", "url": SITE,
                         "description": f"{len(apps)} Decky Loader plugins for Steam Deck, the list behind DeckyHub's Discover tab.",
                         "mainEntity": {"@type": "ItemList", "numberOfItems": len(apps), "itemListElement": [
                             {"@type": "ListItem", "position": index + 1, "url": f"{SITE}plugins/{app['id']}.html", "name": app["name"]} for index, app in enumerate(sorted(apps, key=lambda app: app["name"].casefold()))]}})
    html = (html.replace("<!-- catalog -->", catalog_cards(apps)).replace("<!-- categories -->", category_links)
            .replace("<!-- structured-data -->", item_list).replace("/* plugin-pages */", json.dumps(sorted(app["id"] for app in apps))))
    index.write_text(html, encoding="utf-8")

    (out / "llms.txt").write_text(llms_txt(apps, categories), encoding="utf-8")
    today = time.strftime("%Y-%m-%d", time.gmtime())
    urls = [(SITE, today), (f"{SITE}editor.html", today)]
    urls += [(f"{SITE}categories/{slug(category)}.html", today) for category in sorted(categories)]
    urls += [(f"{SITE}plugins/{app['id']}.html", ((stats.get(app["repo"].casefold()) or {}).get("updated") or today)[:10]) for app in apps]
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "".join(f"<url><loc>{escape(url)}</loc><lastmod>{date}</lastmod></url>\n" for url, date in urls) + "</urlset>\n", encoding="utf-8")


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    apps = json.loads(REGISTRY.read_text(encoding="utf-8"))["apps"]
    build(out, apps, fetch_json(STATS_URL, "plugins"), fetch_json(SCANS_URL, "plugins"))
    print(f"{len(apps)} plugin pages written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
