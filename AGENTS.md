# DeckyHub registry agent guide

Read [README.md](README.md) for the registry format, validation, branching and publishing workflows. Keep registry changes compatible with released DeckyHub versions and validate the affected entries as described there.

Repository skills live only in `.agents/skills/`; `.claude/skills` is a symlink to it for Claude Code (on Windows, run `git config core.symlinks true` before checking out). Edit them there; apply a skill when it is relevant to the task. For multi-file changes use `plan-then-implement`: plan with the strongest model, implement with a cheaper one.
