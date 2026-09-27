# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `ledger copy-schema [REPO…]`, the first verb of the `ledger` group: run in the ledger, it
  writes the project's trace schema into each product repo as a generated, verified copy
  between `# qmstrace:begin` / `# qmstrace:end`, keeping every other byte. All repos or
  none; a second run changes nothing. A product repo carrying the copy is judged on its own,
  and at a baseline tag cut after it. A how-to, *Share the project's schema*, and a
  reference page for the group.
- Docs written the way architecture guides are written are traced: an item is its section,
  down to the next heading at the same or a higher level, so sub-sections, tables and
  diagrams are its text and its fields and links may sit in any sub-section. The ID may
  follow a section number (`4.2`), be wrapped in emphasis or backticks, and the heading may
  end with a Pandoc attribute (`{#…}`, `{.…}`, `{-}`); decoration is not a change.
- `V16`: an ID of this repo's kind, declared nowhere, written where it declares nothing —
  later in a heading or as a table row's first cell. It never stops a baseline tag's tree
  being read.
- A link marker in Markdown written outside every item's section, or as a table row, is
  named by the gap it leaves.
- The user manual gains *Write traced docs with diagrams and tables*, with a fixture repo
  written that way.

- `init`: conservative, idempotent repository setup, managed agent guidance, packaged skill
  and registration of pytest's `verifies` marker while preserving other settings.
- `graph [ID] --out FILE`: a self-contained, offline trace browser with search, keyboard
  selection, node-title hover, type/link/depth filters, evidence notices and full finding
  inspectors. Untitled nodes show their full ID on hover.
- `impact ID…`: combined downstream reach and a baseline-type-filtered candidate Impacts
  line; any unseen start rejects the entire request.
- `results REPORT`: safe pytest JUnit parsing, exact source-test matching and direct
  requirement verdicts; labelled case/run counts, partial matches and missing results.
- Baseline selection by Git ancestry, historical configuration/schema reads, frozen-item
  comparisons and change-request guards V10–V13, with offline evidence limits.
- Withdrawn items remain in history and traversal while being exempt from coverage.
- Informational downstream suspects (S01), combining independent baseline/current walks
  with per-root provenance; edits, test passes and file touches do not clear review needs.
- Diátaxis pages for setup, impact, results, controlled changes, suspect review and the browser;
  command reference output is tested against goldens.

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

### Changed

- `qmstrace --help` summarises `thread` as tracing one item, so a reader looking for *trace*
  finds it.
- A heading ends an item only when it starts with one of this repo's kinds of ID, or is at
  the item's level or higher; `#### IEC-62304 …` stays inside the item. **An item with a
  deeper heading inside it now has a larger text and a different digest**; an item without
  one keeps its digest. A stricter reading can make an older baseline tag unreadable — cut a
  new baseline, never rewrite the tag.
- A decorated heading with this repo's ID in a file not scanned for its type is `V07`; when
  the ID is declared where it is read, the fix says not to start a heading with it.
- A second `Change:` line in an item names the first.
- While the schema copy's begin marker stands, `[schema]` must carry its digest; an unmarked
  copy from before stays valid.
- The shipped skill states these rules. A repo that installed the previous skill must remove
  `.qmstrace/skill/SKILL.md` before `init` refreshes it.

### Fixed

- A code fence closes only on a line of its own character, at least as long as its opener,
  with nothing after it; a fenced example holding a shorter fence no longer hides or exposes
  the headings after it.
- An ID pattern, `id_prefix`, agreement prefix or change-request prefix that no ID can start
  with — underscores, lower case, a space — is refused with the ID shape and the next move,
  instead of being accepted and silently matching nothing.
