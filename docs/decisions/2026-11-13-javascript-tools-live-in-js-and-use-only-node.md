# JavaScript tools live in js/ and use only Node

Date: 2026-11-13

## The rule

> **JavaScript tools live under `js/`, use only Node's standard library (no `package.json` dependencies, no `node_modules`), and are tested with Node's built-in test runner; CI runs those tests on the current Node LTS. Each JavaScript source file carries the same licence and copyright lines as the Python files, as `//` comments.**

## Why

The fifth-week counter already worked in JavaScript, and it is kept in JavaScript
for now. Using only Node's standard library means installing the tools still
needs nothing but Node. A separate `js/` folder keeps the Python package
Python-only. The licence and copyright lines keep every source file stating who
holds the copyright and under what licence, as the Python files do.
