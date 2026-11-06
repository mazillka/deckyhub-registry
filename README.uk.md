<div align="center">

<img src="docs/favicon.svg" width="72" height="72" alt="">

# Реєстр DeckyHub

**Список плагінів для Steam Deck, який [DeckyHub](https://github.com/mazillka/deckyhub-plugin) показує в розділі «Огляд».**

[English](README.md) · Українська

[![validate](https://github.com/mazillka/deckyhub-registry/actions/workflows/ci.yml/badge.svg)](https://github.com/mazillka/deckyhub-registry/actions/workflows/ci.yml)
[![apps](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmazillka%2Fdeckyhub-registry%2Frefs%2Fheads%2Fmain%2Fregistry%2Fapps.json&query=%24.apps.length&label=apps&color=1d75cc)](registry/apps.json)
[![registry release](https://img.shields.io/github/v/release/mazillka/deckyhub-registry?label=registry&color=1d75cc)](https://github.com/mazillka/deckyhub-registry/releases/latest)
[![license](https://img.shields.io/github/license/mazillka/deckyhub-registry?color=1d75cc)](LICENSE.md)
<br>
[![release index](https://img.shields.io/github/last-commit/mazillka/deckyhub-registry/release-index?label=release%20index%20updated&color=1d75cc)](https://github.com/mazillka/deckyhub-registry/tree/release-index)
[![virus scan](https://img.shields.io/github/last-commit/mazillka/deckyhub-registry/virus-scans?label=virus%20scan&color=1d75cc)](https://github.com/mazillka/deckyhub-registry/tree/virus-scans)
[![discover](https://github.com/mazillka/deckyhub-registry/actions/workflows/discover.yml/badge.svg)](https://github.com/mazillka/deckyhub-registry/actions/workflows/discover.yml)

[**Переглянути каталог**](https://deckyhub.com/plugins/) · [Долучитися](https://deckyhub.com/uk/contribute/) · [Редактор реєстру](https://deckyhub.com/uk/contribute/editor.html) · [Отримати DeckyHub](https://github.com/mazillka/deckyhub-plugin#installing-deckyhub) · [Запропонувати плагін](https://github.com/mazillka/deckyhub-registry/issues/new)

</div>

> [!CAUTION]
> **DeckyHub лише завантажує релізи з GitHub-репозиторіїв їхніх авторів. Він не створює, не перевіряє й не гарантує ці плагіни та не відповідає за те, що вони роблять із вашим пристроєм чи даними. Встановлюйте на власний ризик.**

## Встановлення DeckyHub

Уперше чуєте про DeckyHub? [Посібник зі встановлення](https://github.com/mazillka/deckyhub-plugin#installing-deckyhub) описує інсталятор для режиму Desktop і способи, доступні, коли Decky Loader уже встановлено. Інсталятор для режиму Desktop пояснює кожен крок і показує прогрес.

## Як це працює

DeckyHub завантажує [`registry/apps.json`](registry/apps.json) при кожному запуску й зберігає останню робочу копію для роботи офлайн. Зміна, випущена в `main`, потрапляє до кожного встановленого DeckyHub після наступного перезапуску, без нового релізу DeckyHub. Кожна зміна файлу також публікується як [реліз](https://github.com/mazillka/deckyhub-registry/releases) з описом змін ([workflow registry-release](.github/workflows/registry-release.yml)): DeckyHub 3.1.0 і новіші спершу читають `apps.json` з найновішого релізу, а якщо не вийшло, беруть файл із `main`, який старіші випуски читають напряму.

Тестувальники бачать зміни до їхнього випуску: необов'язковий **Канал реєстру: Пре-реліз** у власному вікні **Керувати** DeckyHub (швидкий доступ → DeckyHub → **Керувати**) читає `develop` замість `main` (найновіший реліз реєстру, разом із пре-релізами, інакше файл із `develop`): і його `registry/apps.json`, і індекс релізів, який той самий workflow публікує в гілці `release-index-develop` (копію з `main`, якщо гілки збігаються). Якщо файли з `develop` прочитати не вдається, береться `main`. За замовчуванням — **Стабільний**.

DeckyHub також читає останні релізи кожного плагіна зі списку з одного файлу (5 найновіших придатних до встановлення релізів плюс найновіший стабільний, якщо він старший), щоб не витрачати виклик GitHub API на кожен плагін (60 на годину без токена). [Workflow release-index](.github/workflows/release-index.yml) щогодини та після кожної зміни `apps.json` запускає [`scripts/build_release_index.py`](scripts/build_release_index.py) і публікує `releases.json` у гілці [`release-index`](https://github.com/mazillka/deckyhub-registry/tree/release-index). Новий реліз може з'явитися в DeckyHub із затримкою до години.

Та сама задача пише `stats.json` для [каталогу](https://deckyhub.com/plugins/), який показує ці дані на кожній картці й може за ними сортувати:

- **Завантаження:** за весь час, сума по ZIP-файлах плагіна (фільтр `asset` запису) у всіх релізах. GitHub рахує кожне завантаження файлу, чи то з DeckyHub, Decky, браузера або скрипта, тож це завантаження, а не встановлення.
- **Зірки:** зірки репозиторію на GitHub.
- **Востаннє оновлено:** коли вийшов реліз, який показує DeckyHub; якщо понад рік тому, показується **Немає релізів понад рік**.
- **Форк:** репозиторій є форком; каталог пише, чий саме. Пошук додає форк, лише поки він активний: його оригінал заархівовано, видалено або він давно не випускав релізів.
- **Працює від root:** у `plugin.json` цього релізу в `flags` є `"root"`, тож Decky Loader запускає бекенд плагіна від користувача `root`. Тоді він може читати й змінювати будь-що на Deck: системні файли, інші плагіни, ваші дані. Багатьом плагінам це справді потрібно (керування вентиляторами й живленням, драйвери, VPN, системні налаштування), тож саме по собі це не тривожний знак, але помилка чи шкідливе оновлення можуть завдати набагато більшої шкоди.
- **ШІ:** у репозиторії на гілці за замовчуванням є файли, що налаштовують його для ШІ-асистентів кодування (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.claude/`, `.cursor/`, `.github/copilot-instructions.md` тощо; `AI_FILES` у `validate.py`), тож, ймовірно, його розробляють за допомогою ШІ. Це нічого не каже про якість чи безпеку, а відсутність значка не доводить, що ШІ не використовували.
- **Попередження аудиту:** що [автоматичний аудит Decky Extended Plugins](https://decky-extended-plugins.beallio.com/audit) знайшов у цьому релізі (за sha256 ZIP, інакше за тегом) або в новішому пре-релізі, що варто попередження: **Заблоковано аудитом** (шкідливий код або зіпсований архів), **Читає приватні дані** (дані входу Steam, SSH-ключі, секрети середовища), **Змінює запуск системи** (профілі оболонки, `LD_PRELOAD`, модулі ядра, правила udev), **Код не з репозиторію** (скрипти чи програми в ZIP, яких немає у вихідному коді), **Прихований код** (закодований або запакований код), **Вимикає перевірку HTTPS**, **Запускає завантажені скрипти** (`curl … | sh`) і **Відомі вразливості** (вбудовані бібліотеки з опублікованими CVE). Звичайні знахідки на кшталт `sudo`, `mount` чи `systemctl` не показуються: багатьом плагінам вони потрібні на SteamOS, а **Працює від root** уже це охоплює. Відповідність задає `WARNINGS` у `build_release_index.py`. Попередження не доводить шкоди, а його відсутність не доводить безпечності. Workflow підтримує одну актуальну задачу **Audit warnings**: її редагують щоразу, коли змінюються попередження (спочатку нове, потім поточні попередження кожного плагіна), знову відкривають, коли з'являються нові, і закривають, коли нічого не позначено. Якщо сайт аудиту недоступний, статистика виходить без попереджень.

Кожен ZIP плагіна, який може встановити DeckyHub, також перевіряється на віруси за допомогою [ClamAV](https://www.clamav.net/), а файли всередині нього — за допомогою [YARA](https://virustotal.github.io/yara/) і основних правил [YARA Forge](https://github.com/YARAHQ/yara-forge) (набір, підібраний для малої кількості хибних спрацювань, з багатьма правилами для шкідливого ПЗ під Linux), включно з власними релізами DeckyHub. [Workflow virus-scan](.github/workflows/virus-scan.yml) кожні 3 години й після кожного push у `develop` або `main`, що змінює сканер, запускає [`scripts/virus_scan.py`](scripts/virus_scan.py) над `releases.json` обох гілок: завантажує кожен ZIP, для якого ще немає звіту (спершу релізи кожного плагіна зі Стабільного й Пре-реліз каналів, потім старіші пре-релізи та стабільні версії, кілька ГБ за запуск), перевіряє його сигнатурами ClamAV за той день і правилами YARA Forge за той тиждень та публікує по одному звіту на ZIP у вигляді `scans.json` у гілці [`virus-scans`](https://github.com/mazillka/deckyhub-registry/tree/virus-scans): його sha256, результат (**clean**; **infected** із тим, що знайшов ClamAV; **incomplete**, коли ZIP перевищив ліміти розміру ClamAV; або **error** з причиною: завантаження не вдалося, або ClamAV не зміг прочитати файл чи запуститися), версії ClamAV і сигнатур та час, а також те саме для YARA в полі `yara` (**infected** перелічує правила YARA, що спрацювали; **incomplete** називає файли в ZIP, які не вдалося переглянути). Поля верхнього рівня залишаються лише від ClamAV, тож випуски DeckyHub до появи YARA читають їх як і раніше. Невдала перевірка ніколи не зупиняє workflow: ZIP отримує звіт про помилку й перевіряється знову наступного запуску, а той, що вже мав справний звіт, зберігає його, для кожного сканера окремо. Звіт без результату YARA перевіряється знову, тож ZIP, перевірені до додавання YARA, отримають його за кілька наступних запусків. ZIP, замінений під тією самою назвою, перевіряється знову, а звіти старші за місяць переробляються з новішими сигнатурами. Кожен плагін зі списку врешті отримує звіт для обох каналів, включно з пре-релізами; журнал кожного запуску каже, скільки ще чекають. Також публікуються бейджі [shields.io](https://shields.io/badges/endpoint-badge) для Стабільного релізу кожного плагіна (інакше його Пре-реліз), по одному на сканер, які автори плагінів можуть вставити у свої README: `https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/mazillka/deckyhub-registry/virus-scans/badges/<owner>/<name>/clamav.json` (або `yara.json`), де `<owner>/<name>` пишеться малими літерами. Запуск також публікує там `plugins.json`: ті самі результати по кожному плагіну, для ZIP, який встановлює кожен канал; [каталог](https://deckyhub.com/plugins/) показує їх як бейдж **Загроз немає** / **Знайдено загрозу** / **Перевірено не повністю**, а результат кожного сканера видно при наведенні. Вікно **Керувати** в DeckyHub показує звіт для релізу, який ви збираєтеся встановити, або каже, що його ще не перевіряли. У ньому також є кнопка **VirusTotal**, що шукає sha256 цього ZIP на [VirusTotal](https://www.virustotal.com/) у браузері Steam. Нічого не завантажується, а VirusTotal знає лише файли, які хтось уже йому надсилав. Звіт — це інформація, а не блокування: чи встановлювати, вирішуєте ви. ClamAV гірше знає шкідливе ПЗ під Linux, ніж під Windows: чистий звіт не доводить безпечності.

Нові плагіни теж знаходяться автоматично. Щодня [workflow discover](.github/workflows/discover.yml) запускає [`scripts/discover.py`](scripts/discover.py) над двома каталогами спільноти: нічним списком [Decky Plugins Explorer](https://safetzahirovic.github.io/decky-plugins-explorer/) (кожен публічний репозиторій із Decky `plugin.json`) і [Decky Extended Plugins](https://decky-extended-plugins.beallio.com/) (магазин Decky плюс плагіни спільноти), а також нашим власним пошуком на GitHub: репозиторії з тегом чи назвою, схожими на плагіни Decky (`topic:decky-plugin`, `decky in:name` та ще кілька), з `plugin.json` у корені. Пошук зберігає роботу виявлення, навіть якщо обидва каталоги зникнуть. Плагіни, яких ще немає в списку, які проходять ті самі перевірки, що й `validate.py` (на їхньому найновішому стабільному релізі, інакше на найновішому пре-релізі, тож плагіни лише з пре-релізами теж знаходяться) і не виглядають незавершеними ([`scripts/quality.py`](scripts/quality.py): перший реліз молодший за 14 днів, жодної зірки й менше 10 завантажень, версія `0.0.x` або відсутній опис; їх перевіряють пізніше знову), відкриваються як pull request у `develop`, не більше 50 за раз. Без перевірки людиною нічого не зливається.

[Заповнення MetaDefender](.github/workflows/metadefender-scan.yml) шукає публічні ZIP плагінів за SHA-256 і завантажує ZIP у MetaDefender Cloud, якщо звіту немає. Завантажені файли передаються цьому сервісу. Воно розбирає чергу в межах квоти API й публікує окремі результати в `metadefender-reports`; відсутні, незавершені, завеликі чи невдалі перевірки не є «чистим» вердиктом. Щоб увімкнути його, задайте секрет `METADEFENDER_API_KEY` реєстру.

## Репозиторії

Повна таблиця плагінів (інструмент, категорія, репозиторій) ведеться автоматично в розділі [Repositories англійського README](README.md#repositories) і тут не дублюється, щоб дві копії не розходилися.

## Звідки беруться плагіни

Плагіни пропонують люди (issues і pull request-и тут) або щодня знаходить [workflow discover](.github/workflows/discover.yml) через два каталоги спільноти та наш власний пошук на GitHub репозиторіїв із тегом чи назвою, схожими на плагіни Decky:

- [Decky Extended Plugins](https://decky-extended-plugins.beallio.com/) від [beallio](https://github.com/beallio), який також публікує [аудит безпеки](https://decky-extended-plugins.beallio.com/audit) плагінів зі свого списку.
- [Decky Plugins Explorer](https://safetzahirovic.github.io/decky-plugins-explorer/) від [SafetZahirovic](https://github.com/SafetZahirovic), який щоночі знаходить кожен публічний репозиторій GitHub із Decky `plugin.json` ([MIT](https://github.com/SafetZahirovic/decky-plugins-explorer/blob/main/LICENSE)).

Як би плагін не знайшли, його додають лише коли для нього проходить `validate.py` (реліз, придатний до встановлення, стабільний чи пре-реліз, рівно з одним ZIP плагіна та відповідною назвою в `plugin.json`), а workflow discover ще й пропускає плагіни, що виглядають незавершеними. Це автоматичні перевірки робочого релізу; самі плагіни ніхто не перевіряє. Дякуємо авторам обох каталогів за відкриті дані.

## Гілки

`main` — це те, що читає DeckyHub: кожне встановлення бере з нього `registry/apps.json`, і з нього ж будується індекс релізів. Зміни спершу потрапляють у `develop`: створіть гілку від `develop`, відкрийте pull request у `develop` і зливайте його через **Squash and merge**. Потім pull request із `develop` у `main` випускає їх; після його злиття злийте `main` назад у `develop` через **Create a merge commit**, щоб наступний не мав конфліктів. Workflow discover теж відкриває свої pull request-и в `develop`. Щоб випустити лише список плагінів, [workflow ship-plugins](.github/workflows/ship-plugins.yml) (запускається у вкладці Actions) відкриває pull request у `main` з `registry/apps.json` та таблицею Repositories цього README з `develop` і більше нічим, тож нові плагіни не мусять чекати на скрипти й workflow з `develop`; після нього теж злийте `main` назад у `develop`. `.githooks/pre-commit` блокує коміти в `main` і `develop`; увімкніть його один раз для кожного клону командою `git config core.hooksPath .githooks`.

## Додавання плагіна

Відкрийте pull request у `develop`, що додає один запис до [`registry/apps.json`](registry/apps.json) і його рядок до таблиці в [англійському README](README.md#repositories) (у тому самому порядку). Не впевнені в деталях? Натомість [відкрийте issue](https://github.com/mazillka/deckyhub-registry/issues/new) з репозиторієм плагіна.

```json
{
  "id": "decksmb",
  "name": "DeckSMB",
  "description": "Manages a Samba (SMB) file-sharing server on the Steam Deck.",
  "repo": "bonorca/DeckSMB",
  "category": "Utilities",
  "detect": {
    "type": "decky-plugin",
    "names": [
      "DeckSMB"
    ]
  },
  "asset": {
    "include": [
      ".zip"
    ],
    "exclude": [
      "source"
    ]
  }
}
```

| Ключ | Для чого він |
| --- | --- |
| `id` | Унікальний, малими літерами, у kebab-case. |
| `name`, `description`, `category` | Що показує «Огляд». Використовуйте наявну категорію, якщо вона підходить. |
| `repo` | `owner/name` плагіна на GitHub. DeckyHub завантажує лише файли релізів цього репозиторію. |
| `detect.names` | Назва плагіна точно так, як її повідомляє його `plugin.json`, щоб DeckyHub впізнав його після встановлення. |
| `asset.include` / `asset.exclude` | Слова, що вибирають рівно один ZIP релізу. |
| `releaseTagInclude` | Необов'язково: лише релізи, тег яких містить це, для репозиторіїв, що публікують і інші релізи. |

Усі випущені DeckyHub читають цей файл, тож зміни мають бути додавальними. Зміна, яку старіші версії не можуть прочитати, повинна збільшити `schemaVersion` (вони відхиляють її й зберігають кешований список), а не змінювати форму версії 1.

### Перевірки

CI запускається для кожного pull request, при push у `main` і `develop` та щотижня, бо новий реліз плагіна може зламати його запис:

- **Схема:** власний парсер DeckyHub і тест схеми v1. Локально, з клону [`deckyhub-plugin`](https://github.com/mazillka/deckyhub-plugin) поруч із цим:
  ```bash
  DECKYHUB_REGISTRY=../deckyhub-registry/registry/apps.json python -m unittest tests.test_registry_schema
  ```
- **Записи:** `scripts/validate.py` перевіряє кожен запис так, як його побачить DeckyHub: репозиторій існує, найновіший реліз кожного каналу має рівно один ZIP, що відповідає `asset`, а назва `plugin.json` цього ZIP є в `detect.names`. Також він відхиляє спільні id, repo та detect-назви, `DeckyHub` як detect-назву й таблицю README, що не збігається з `apps.json`. `--offline` пропускає перевірки GitHub.
  ```bash
  GITHUB_TOKEN=$(gh auth token) python scripts/validate.py
  ```
- **Вебсайт:** усе на deckyhub.com, який будує mazillka/deckyhub-plugin: [плагіни](https://deckyhub.com/plugins/), [як долучитися](https://deckyhub.com/uk/contribute/) і [редактор реєстру](https://deckyhub.com/uk/contribute/editor.html). registry.deckyhub.com лише перенаправляє туди, тож старі посилання працюють: [`scripts/build_site.py`](scripts/build_site.py) пише перенаправлення для кожної старої сторінки, плагіна й категорії, а розгортає їх [workflow pages](.github/workflows/pages.yml) із `main`.
- **Тести:** `python -m unittest discover -s tests` покриває скрипти, а також перевіряє, що `apps.json` лишається меншим за 512 КБ, які приймає DeckyHub 3.0.0 і старіші, що скрипт сторінки каталогу розбирається й що `stats.json` зберігає кожне поле й попередження, які читає запущений людьми DeckyHub (відносно `main` deckyhub-plugin, який CI клонує).

## Власний реєстр

У **Налаштування** → **Репозиторії** → **Власні реєстри** DeckyHub приймає `owner/repo` для будь-якого репозиторію з такою самою структурою (`registry/apps.json` на гілці за замовчуванням) або будь-яку HTTPS-адресу `.json`. Зробіть форк цього репозиторію як відправну точку або складіть список у [редакторі реєстру](https://deckyhub.com/uk/contribute/editor.html) і розмістіть експортований файл. Доданий реєстр може додавати плагіни, але ніколи не замінює плагін із цього списку.

## Застереження

Не пов'язано з Valve чи проєктом Decky Loader. Цей список зібрано з публічних GitHub-репозиторіїв, і кожен плагін належить своїм авторам. Записи перевіряються на робочий реліз, а не на безпечність: DeckyHub не володіє жодним плагіном зі списку, не схвалює його й не несе за нього відповідальності. Плагіни встановлюються на ваш власний ризик, тож перегляньте репозиторій плагіна, перш ніж його встановлювати.

## Ліцензія

Copyright © 2026 Andrii Shevchuk-Yuhanets ([mazillka](https://github.com/mazillka)).

[GPL-3.0](LICENSE.md). Кожен плагін зі списку належить своїм авторам і має власну ліцензію.
