# AGENTS.md is the only instruction file

Date: 2026-11-02

Supersedes `2026-10-19-claude-md-is-a-one-line-bridge-to-agents-md.md`.

## The rule

> **`AGENTS.md` is the only instruction file. The repository has no `CLAUDE.md`.**

## Why

The earlier record kept a one-line `CLAUDE.md` containing `@AGENTS.md` so that
Claude Code would load `AGENTS.md`. Claude Code now reads `AGENTS.md` directly,
so the bridge is gone.

Any `CLAUDE.md` in the repository, even a one-line one, stops Claude Code
(measured on 2.1.309) from loading `AGENTS.md` files on its own. Adding one back
would break that.

The earlier reason still holds: one instruction file means the instructions
cannot drift between agents.
