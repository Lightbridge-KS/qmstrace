# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- A next move that says no repo declares an item type gives it its article:
  `no repo of the project declares an automated test`, where it read `declares a automated test`.

## [0.1.0] - 2026-10-15

### Added

- C# repos are traced (ADR-0004). `csharp-file` reads one component per `.cs` file, its ID the
  path, linked by a field line in the first type's leading `///` comment. `xunit` reads one
  automated test per `[Fact]` or `[Theory]` method, linked by the ID that starts a literal
  `DisplayName`; a Theory is one automated test, its rows its runs. A form it does not read is
  reported, never skipped: a non-literal `DisplayName`, a `[Trait]` named after a link, a
  custom test attribute and a test inside `#if` are `V15`, and a commented-out test attribute
  is a stray. Newer syntax outside what is read, such as C# 14 extension blocks, does not stop
  a file being read. A how-to, *Trace a C# repo*.
- `results` reads the TRX file `dotnet test --logger trx` writes, as well as JUnit XML; the
  root element picks the reader. A run is matched by its class and method, so a Theory's rows
  are runs of one test. `Passed` is a pass, `NotExecuted` a skip, and any other outcome a
  failure that keeps the raw outcome. Only the first line of an error message is read; paths,
  machine and user names, output and stack traces never are. One report per run: a solution
  with several test projects writes one TRX file each ([#40](https://github.com/Lightbridge-KS/qmstrace/issues/40)).
- Test cases and automated tests (ADR-0003). A test case is planned, an entry in a Test
  Specification; an automated test is the code that runs it and names it. `results` follows
  `verifies` links through test cases: a requirement's verdict is the worst of every automated
  test that reaches it, and its row names the test cases on the way, each with its own verdict.
  A test case nothing runs adds nothing. Test cases and tests that reach no requirement are
  listed apart.
- Dotted IDs (ADR-0002): a number may carry dotted parts, `TC-FLT-04.1-01`. An ID is read
  whole or not at all — `TC-BAG-03.1a` is no ID, never `TC-BAG-03` — and a heading whose
  first word starts as this repo's kind of ID and runs on is `V02`. Listings sort dotted
  numbers as numbers: `AGR-1.2` before `AGR-1.10`.
- An incoming gap's next move lists every way to meet it — each item type that can make the
  link, the form its extractor reads, and the repos that read it.

- `ledger check [--strict] [--quiet]`, run in the ledger: every repo the schema lists under
  `[repos]` — the ledger too, when it lists itself as `"."` — is read from its working tree
  and judged as one project. A coverage rule is met by a link in any repo; each repo's own
  violations are reported, located from the ledger; a change to a frozen item makes what hangs
  off it suspect in every repo — in another repo than the change, by today's links only,
  labelled *not pinned*. A module's or a test's ID carries its repo there
  (`service:tests/unit/test_api.py::test_x`). A repo that cannot be read, or holds other rules
  than the ledger's schema, stops the check with exit 2, every problem named. A how-to,
  *Check the whole project*; the ledger reference, suspects, configuration and *Around the
  repo* pages cover the layout where the ledger holds the documents.
- `ledger thread ID` and `ledger impact ID…`, run in the ledger: the walks of `thread` and
  `impact` over the whole project, crossing every repo's edge — from a requirement to every
  repo's tests, from a module back to its origin clause. A judged item says which repo it is
  in; a module's or a test's ID given without its repo is answered with the qualified IDs it
  may mean.
- `init` in a ledger sets it up to hold the project's documents (#30): with no `qmstrace.toml`
  it writes the ledger's own — requirements and design elements, `ledger = "."`, the schema
  by path — and in every ledger it writes a stanza naming the ledger's verbs:
  `ledger check --strict` as the gate, `ledger thread` and `ledger impact` as the walks. It
  never edits the schema; a `next:` line names the `[repos]` entry to add. A product repo's
  stanza is unchanged.
- A test fixture in the layout of ADR-0001: a traced ledger that holds the requirements and
  the design, and product repos that hold code and tests and cite the ledger's IDs.

- `init` links `.claude/skills/qmstrace` to the installed skill when the repo already has a
  `.claude/` folder, so Claude Code lists it. The link is created once and left alone;
  anything else at that path is refused before any write.
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

- The starter calls tests `automated_test`, not `test_case`; `status` and `results` count
  *automated tests*. A schema that calls them `test_case` keeps working: item type names are
  data.
- `init` registers pytest's `verifies` marker only where the repo's tests are pytest.
- A baseline tag whose snapshot has more than three problems is refused with a count by code,
  the first three, and where to see the rest, instead of one line per problem.
- An outgoing gap whose targets this repo declares none of, while a sibling repo does, names
  that sibling: *this repo declares no … for it to point at, but ledger does*. It no longer
  says to write the design here.

- The stanza and the skill say the same thing about checking a marker: break the behavior in a
  disposable copy of the repo — never the checkout you work in — confirm its tagged test fails
  there, then delete the copy. The stanza used to say "a disposable test", and an agent read it
  as breaking the live checkout. `init` rewrites the stanza in every traced repo on its next run.
- A gap that only another repo of the project can meet now points at `qmstrace ledger check`,
  run in the ledger, instead of the import; so does the footer of `qmstrace rules`.

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
- The shipped skill states these rules.
- `init` installs the skill at `.agents/skills/qmstrace/SKILL.md`, the folder a coding
  agent's harness reads for a repo's skills; the stanza points there. A repo set up earlier
  keeps a copy in `.qmstrace/skill/`, and `init` refuses until `.qmstrace/` is removed.

### Fixed

- `ledger check` no longer lets the last repo read decide how an item type is written, when two
  repos read it with different extractors.
- A test's gap cites only a finding about that test, never the first one in its file.

- The refusals of `ledger copy-schema` and `ledger check` — and so of `ledger thread` and
  `ledger impact` — no longer end a repo's reason in two full stops when that reason closes
  its own sentence: `… Fix: use one of those.. Fix: …` reads `… Fix: use one of those. Fix: …`,
  and two such reasons are joined by `; ` alone.
- `ledger copy-schema` no longer rewrites the ledger's own `qmstrace.toml` when the ledger
  lists itself under `[repos]` as `"."`: that entry is skipped, and its line says why — or,
  where an older run wrote a copy there, how to restore the path.
- A code fence closes only on a line of its own character, at least as long as its opener,
  with nothing after it; a fenced example holding a shorter fence no longer hides or exposes
  the headings after it.
- An ID pattern, `id_prefix`, agreement prefix or change-request prefix that no ID can start
  with — underscores, lower case, a space — is refused with the ID shape and the next move,
  instead of being accepted and silently matching nothing.

[Unreleased]: https://github.com/Lightbridge-KS/qmstrace/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Lightbridge-KS/qmstrace/releases/tag/v0.1.0
