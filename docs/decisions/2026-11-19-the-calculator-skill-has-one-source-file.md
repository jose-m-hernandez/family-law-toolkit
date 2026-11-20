# The calculator skill has one source file

Date: 2026-11-19

## The rule

> **One skill source file in the repo. Each harness's discovery path is wired to that one file and proven by a recorded run in each harness from a fresh clone. No hand-kept copy; a drift test fails if any copy differs or any named command or flag is missing. The exact paths are measured at build, not assumed.**

## Why

The release carries one skill, for the calculator only: run the `support` calculator, report what it printed, refuse advice, and point to a lawyer, the court's self-help center or the family law facilitator. Two harnesses read a repo-level skill from different folders. Two copies would drift, and a skill that names a flag the command no longer has would send a person to a command that fails.

## The measured paths (2026-11-19)

Measured from local evidence on this machine only, with no model call:

- Claude Code reads `.claude/skills/<name>/` in the project. The main checkout's `.claude/skills` holds one directory-sized symlink per skill, each to a folder that contains `SKILL.md`.
- Codex reads `.codex/skills/<name>/` from the nearest git root down to the launch folder, never above it. The `.codex/skills` folder of a checkout on this machine has the same shape as the Claude one.

The source is `skills/support-calculator/SKILL.md`. Each path is a tracked relative symlink to the folder `skills/support-calculator`:

- `.claude/skills/support-calculator` -> `../../skills/support-calculator`
- `.codex/skills/support-calculator` -> `../../skills/support-calculator`

`.gitignore` ignores the rest of `.claude/skills/` and `.codex/`, so a local skill folder stays out of the repository, and un-ignores only these two links.

## What checks it

`tests/test_skill.py` checks that the source file has its frontmatter, that it is the only file under `skills/`, that each wired path is tracked (a symlink has git mode 120000) and resolves to the source, and that every `python3 -m family_law_toolkit.<module>` and every `--flag` the skill names exists. It also fails on an invented flag, as a positive control.

## What is not done

The recorded run from a fresh clone in each harness needs a model call. It was not made when this was built, and the rule above is not met until it is.
