# Published files

Every file this repository publishes for others to read. Installed copies of DeckyHub and the extension can't be changed, so a path, branch or field that one of them reads is only ever added to: see the [compatibility skill](.agents/skills/compatibility/SKILL.md).

Addresses start with `https://raw.githubusercontent.com/mazillka/deckyhub-registry/`. "Plugin" is the DeckyHub app, "site" is deckyhub.com and "extension" is the browser extension.

| File | Branch | Written by | Read by | Schema |
| --- | --- | --- | --- | --- |
| `registry/apps.json` | `main`, `develop` | pull requests | plugin, site, extension (`main` only) | [apps](registry/apps.schema.json) |
| `apps.json` on a `registry-*` release | releases | `registry-release.yml` | plugin | [apps](registry/apps.schema.json) |
| `releases.json` | `release-index`, `release-index-develop` | `release-index.yml` | plugin, site, registry workflows | [releases](registry/releases.schema.json) |
| `stats.json` | `release-index`, `release-index-develop` | `release-index.yml` | plugin, site, extension (`release-index` only), registry workflows | [stats](registry/stats.schema.json) |
| `scans.json` | `virus-scans` | `virus-scan.yml` | plugin, external scan workflows, people (the extension links to it) | [scans](registry/scans.schema.json) |
| `plugins.json` | `virus-scans` | `virus-scan.yml` | site, released versions of the extension | [plugins](registry/plugins.schema.json) |
| `plugins-lite.json` | `virus-scans` | `virus-scan.yml` | extension | [plugins](registry/plugins.schema.json) |
| `badges/<owner>/<repo>/{clamav,yara}.json` | `virus-scans` | `virus-scan.yml` | README badges, through shields.io | [shields.io endpoint](https://shields.io/badges/endpoint-badge) |
| `reports.json` | `virustotal-reports` | `virustotal-scan.yml` | plugin, site, extension | [virustotal](registry/virustotal.schema.json) |
| `reports.json` | `metadefender-reports` | `metadefender-scan.yml` | plugin, site, extension | [metadefender](registry/metadefender.schema.json) |
| `registry/warnings.json` | `main`, `develop` | pull requests | site at build time; tests in the plugin, site and extension | [warnings](registry/warnings.schema.json) |
| `registry/contract-cases.json` | `main`, `develop` | pull requests | tests in the plugin, site and extension | none |

Scheduled workflows run from `main`, and the scan branch is replaced on every run. A file that only `develop`'s code writes disappears at the next scheduled run until the change reaches `main`.

## Shared warning texts and cases

- `registry/warnings.json` is the English label, explanation and tone of each audit warning. The plugin and the extension keep their own copy, and the site keeps one for when it can't read this file. Their tests compare the copies with this file. The plugin's translations stay in the plugin.
- `registry/contract-cases.json` is input data and what every reader must make of it. `scans`: each scanner's result (`virusTotal` and `metaDefender` are the number of engines that flagged the ZIP, `null` without a report), the badge, and how many scanners found nothing. `warnings`: stats fields, and the warnings to show in order.
- To change a text or a rule, change it here first, then in each reader. A reader's tests fail until its copy matches.
