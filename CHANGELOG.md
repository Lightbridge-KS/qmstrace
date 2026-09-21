# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- The package skeleton: a `qmstrace` command with `--version` and plain-text help.
- Exit codes as a contract: `0` no failing findings, `1` the check failed, `2` could not judge,
  `3` internal error — never a bare traceback.
- The dry gate (`just dry`) and a pipeline that runs it: format, lint, types, tests with a
  coverage floor, and a check that the built wheel carries the package data.
- A test that enforces the import matrix between the package's layers.
- The trace configuration and the trace schema, parsed and validated from text: three forms of
  the schema (by path, a generated and verified copy, the repo's own), an error for any unknown
  key, an extractor the tool does not have, or an ID pattern where the extractor derives IDs —
  and refusals that say what is wrong and the next move. The annotated reference examples are
  the fixture project under `tests/fixtures/mini/`.
- `qmstrace status`: what was scanned per item type, what lies around the repo (the agreement,
  the project's other repos) and whether it was verified, and one line per requirement. It
  runs from any folder inside a product repo, or elsewhere with `qmstrace -C <path>`.
- Items and links read from Markdown headings and fields, from a module's docstring, and from
  pytest's own markers — each marker form the tool does not read is reported, never skipped.
- Violations found while reading a repo, each with the next move: an ID declared twice or
  malformed, a link to nothing or to the wrong kind of item, a missing or misspelled field, a
  test outside a level folder, an item in a file its type is not read from, a file that cannot
  be parsed, an origin the agreement does not declare, a link field that holds no ID.
- A citation of another repo's item that cannot be checked here — as in a pipeline with one repo
  checked out — passes as *not verified here* instead of failing.
- The user manual, built with Zensical from `contents/` and published on Netlify: a first-look
  tutorial, reference pages for `status`, findings, exit codes and configuration, and an
  explanation of what lies around a repo. Reference pages include the goldens and fixtures the
  tests own, so they cannot drift from what the tool prints.
- `qmstrace --help` ends with the exit codes, and `status` has a summary that fits the command
  list.
- `-C <path>` is accepted after the command as well as before it; given on both sides, it is a
  usage error.
- `qmstrace thread <ID>`: one item followed backward to what it derives from and forward to what
  hangs off it — each item once, nearest first — for a requirement, a test, a clause or a
  sibling's item. An ID nothing here can see exits `2` with the closest IDs.
- The user manual gains the `thread` reference and an explanation of the chain.
- `qmstrace check`: every violation and every gap, one line each with its next move. Gaps are
  judged from the project's coverage rules; they do not fail while authoring, and fail under
  `--strict`, the gate. `--quiet` prints the findings, and what could not be verified, only.
- `qmstrace rules`: what `check` holds a repo to — link types, required fields, coverage rules —
  and whose each part is; a rule the repo cannot meet says so.
- `status` counts gaps as well as violations. An `Implements:` written outside a module's
  docstring is reported as the reason for the gap it leaves.
- The user manual gains `check` and `rules`, a how-to for checking work before a commit, and an
  explanation of the kinds of finding.
- A coverage rule whose direction contradicts its link type is refused.
