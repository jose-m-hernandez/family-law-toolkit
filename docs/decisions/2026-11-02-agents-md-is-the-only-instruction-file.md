# AGENTS.md is the only instruction file

Date: 2026-11-02

Supersedes `2026-10-19-claude-md-is-a-one-line-bridge-to-agents-md.md`.

## The rule

> **`AGENTS.md` is the only instruction file. The repository has no `CLAUDE.md`.**

## Why

The earlier record kept a one-line `CLAUDE.md` containing `@AGENTS.md` so that
Claude Code would load `AGENTS.md`. Claude Code now reads `AGENTS.md` directly,
so the bridge is gone.

In a test on Claude Code 2.1.309 (2026-10-23), `CLAUDE.md` files in parent
folders stopped Claude Code from loading the repository's own `AGENTS.md`. A
`CLAUDE.md` inside the repository would sit in the same chain, so this
repository keeps none.

The earlier reason still holds: one instruction file means the instructions
cannot drift between agents.
