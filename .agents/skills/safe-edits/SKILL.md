---
name: safe-edits
description: Avoid the editing mistakes that have bitten this repo - CRLF line endings breaking scripted edits, apps.json with silently duplicated keys from a hand-merged conflict, work on the wrong branch, and pushes to a third party's fork or a made-up remote. Use before bulk-editing files with a script, resolving a merge conflict in apps.json or the README, committing, or pushing.
---

# Safe edits

- **Line endings.** On Windows files are often CRLF while a search string in a script is LF, so `str.replace` finds nothing. Read the file, note whether it had `\r\n`, edit the LF text, write it back the same way (`newline=""`).
- **`apps.json` conflicts.** Hunks split entries in half. Never join the two sides: take one side of the file whole and re-add your entry and its README row, last in both. Python's `json.loads` accepts a repeated key and keeps the last, so a mangled merge can still parse: after editing, check duplicates with `object_pairs_hook`, the entry count, and that `git diff origin/develop --stat` shows only what you meant.
- **Branch.** Check `git branch --show-current`; start each topic with `git switch -c <topic> origin/develop`. Never commit to `develop` or `main`.
- **A contributor's PR** (a branch on their fork): push only after the user says so, to the PR's own head repository, and only when the PR allows maintainer edits. Never push to a URL typed from memory.
- **Releases and merges.** A merge, a `develop` → `main` ship and a release edit each need the user's OK for that action. Release notes are plain language (`ship-registry` step 5).
- **Secrets.** Never print or commit a token; `GITHUB_TOKEN=$(gh auth token)` stays in the command line.
