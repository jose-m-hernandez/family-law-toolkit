# family-law-toolkit

Tools for people preparing California family-law paperwork. Today: a guideline child-support calculator (steps 1 and 2: the support amount, and its allocation per child). Not built yet: comparing drafts, and assembling exhibit packets and binders.

Educational; not legal advice; not certified for court filing; consult counsel.

Early development, and not ready for other people to use. This repository is
private and not yet published. One command exists: steps 1 and 2 of a guideline
child-support calculator. Nothing else is built yet.

- What changes, and when: [CHANGELOG.md](CHANGELOG.md)
- How changes are made: [CONTRIBUTING.md](CONTRIBUTING.md)

## Licence

GNU Affero General Public License v3.0 or later; see [LICENSE](LICENSE).
A commercial licence is also available from the copyright holder.

## Development

Run the tests:

    python3 -m unittest discover -s tests -t . -v

The tests use invented data.

CI also runs a private-string scan on every push and pull request; contributors do not run it, CI does. How it works and how to try it: [docs/barred-strings-scan.md](docs/barred-strings-scan.md).
