# AGENTS.md is the only instruction file

Date: 2026-11-02

Supersedes `2026-10-19-claude-md-is-a-one-line-bridge-to-agents-md.md`.

## The rule

> **`AGENTS.md` is the only instruction file. The repository has no `CLAUDE.md`.**

## Why

The earlier record kept a one-line `CLAUDE.md` holding `@AGENTS.md`, so that
Claude Code would load `AGENTS.md`. Claude Code now reads `AGENTS.md` directly.
That bridge is no longer needed, and the one-line `CLAUDE.md` has been removed.

A `CLAUDE.md` in the repository, even a one-line one, stops Claude Code from
loading `AGENTS.md` files on its own (measured on Claude Code 2.1.309). Adding
one back would bring back the indirection the change removed.

The reason from the earlier record still holds: one instruction file means the
instructions cannot drift between agents.
