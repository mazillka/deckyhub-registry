"""Announce a registry release on Telegram (registry-release.yml, stable releases only).

    TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python scripts/telegram_post.py <notes.md> <release url> <date>

Without the two variables it only prints the message and exits 0, so the workflow step is harmless until a channel
and bot exist. A release with "No plugin changes" in its notes is not announced. The message is plain text: Telegram's
own markup needs escaping that release notes full of plugin names and descriptions would trip over.
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request

LIMIT = 3600  # Telegram allows 4096 characters; the header and link need room


def message(notes: str, url: str, date: str) -> str | None:
    notes = notes.strip()
    if not notes or notes.startswith("No plugin changes"):
        return None
    lines = []
    for line in notes.splitlines():
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        if line.startswith("### "):
            line = "\n" + line[4:] + ":"
        elif line.startswith("## "):
            line = "\n" + line[3:].upper()
        lines.append(line.rstrip())
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    if len(body) > LIMIT:
        body = body[:LIMIT].rsplit("\n", 1)[0].rstrip() + "\n…and more in the full notes."
    return f"DeckyHub plugin list updated ({date})\n\n{body}\n\nFull notes: {url}\nBrowse: https://deckyhub.com/plugins/"


def send(token: str, chat_id: str, text: str) -> None:
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data, timeout=30) as response:
        if not json.load(response).get("ok"):
            raise SystemExit("Telegram refused the message")


if __name__ == "__main__":
    notes_file, url, date = sys.argv[1:4]
    with open(notes_file, encoding="utf-8") as file:
        text = message(file.read(), url, date)
    if text is None:
        print("No plugin changes: nothing to announce.")
    elif not (os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")):
        print("No Telegram channel is set up; the message would be:\n\n" + text)
    else:
        send(os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"], text)
        print("Announced on Telegram.")
