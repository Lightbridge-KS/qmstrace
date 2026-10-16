---
summary: ADR-0005 — `results` reads several reports in one run, combined in core, each run keeping its source report (label and sha256) and, at the ledger, the repo it reports; and the ledger emits the traceability matrix, the requirements register and the coverage summary as versioned JSON (`qmstrace ledger table`, format `qmstrace.table/1`), columns derived from the schema, read from working trees with each repo's commit recorded, never committed. Amends the results contract and the surface architecture's "machine-readable output comes later".
read_when:
  - changing how `results` reads, combines or reports on test reports
  - adding or changing `ledger table`, its tables, columns or JSON format
  - adding any machine-readable output, or deciding its versioning
---

# ADR-0005 — Tables as data, and several reports

- **Status:** accepted, 2026-10-15
- **Amends:** [surface architecture](../design/surface-architecture.md) — the *Results contract*
  ("`results REPORT` reads one explicitly supplied file", "M4 does not persist results, combine
  reports …", "No gate, quiet or JSON option is added") and §7 ("Machine-readable output comes
  later … which commands get the form, and its versioning, are decided then"); requirement
  REQ-QMT-10, and a new REQ-QMT-23, under CR-004
- **Decided by:** the developer, 2026-10-15 (the seven #49 decisions; the two-slice plan)

## Context

The PRD's P0 *emit tables as data for the existing render machine* has a success criterion: the
pilot's traceability record renders with zero hand-typed IDs. The first C# adopter's record is
a hand-typed matrix, one row per requirement, design element and test case, whose two result
columns — unit, and integration or system — are empty in every row: nobody can keep test
verdicts by hand.

Two things stand in the way. qmstrace emits no machine-readable form at all — by design until
now, since line output served every agent in the experiments. And `results` reads one report
for one repo, while that adopter's unit and integration tests live in separate test projects,
each writing its own TRX file (#40).

## Decision

**Several reports, combined in core** (#40):

- `results` reads several reports in one run. They are combined into one view **in core**, so
  every consumer of verdicts — the text view, the tables below — applies the same rule (ADR-0003:
  an item's verdict is the worst of every automated test that reaches it).
- **Each run keeps its source report**: the label it was given — relative, never a path of the
  machine — and the sha256 of the report's bytes. A verdict can then point at its evidence
  (AGR-8) without copying it.
- **A report can name the repo it reports.** At the ledger, run identities can collide across
  repos (two Python repos may both report `tests.unit.test_x`); in a product repo every report
  belongs to that repo.
- **Order never matters.** Verdicts and counts are the same whatever order the reports are
  given in; a run reported in two files combines by its worst verdict and counts once as a
  duplicate, as a repeated entry within one file does today.
- The view's header lists each report read, with its entry count, so a missing or truncated file
  is visible. The report's commit stays **NOT VERIFIED**: nothing records which build wrote it.

**Tables as data** (#49):

- **One ledger verb:** `qmstrace ledger table matrix | requirements | coverage`, run in the
  ledger, reading every repo as `ledger check` does. Output to stdout, or `--out FILE`, which
  never overwrites.
- **The format is JSON, `qmstrace.table/1`:** one document carrying its metadata — the
  project, the schema's digest, each repo read with its commit and whether its working tree was
  clean, `pinned: false`, the violation and gap counts, every notice — then its columns and its
  rows. Deterministic (REQ-QMT-15): pretty-printed, sorted, no timestamp, no machine path.
- **Versioning:** a new key, column, table or notice keeps `/1`; consumers look columns up by
  name and ignore what they do not know. Removing or renaming anything, changing a cell's JSON
  type, the row grain or the sort, or what `clean`, `pinned` or `draft` mean, is `/2`.
- **Columns are derived from the schema** (AGR-6). The anchors are the two `results` already
  uses — the `requirement` type and the `verifies` link. A type that is both a source and a
  target of `verifies` is a test case; a source only, an automated test. The other coverage
  links, walked from the requirement, give the rest of the chain, each column named after its
  item type. A project adds the requirement fields it wants with `[tables.matrix] fields`.
- **The matrix's grain** is one row per requirement × design element × test case,
  requirement-major. An automated test that verifies directly, with no test case between, gets a
  row of its own; a test case nothing runs still has one; a test case that verifies the
  requirement itself repeats on each of its design rows.
- **Verdict columns** (slice #49b): `--report REPO=FILE`, several; one column per level; each
  cell names the reports its verdict came from.
- **Read from working trees, not pinned**, each repo's commit recorded. A dirty tree is stated,
  not refused: the table is a draft either way (AGR-13), and its `draft` field says so.
- **Never committed by qmstrace.** A render layer consumes it; the issued document is the
  traceability record under document control. The trace lock (D1) stays the one committed,
  generated listing.
- **A project with violations is still tabled**, exit 0, the counts and a notice saying the
  links they refuse are not in the table — as `graph` and `results` do.

## Evidence

- A probe of today's model (2026-10-15) on the `cases` fixture: the project graph, joined with the
  agent's TRX fixture and a pytest run of the service, gives the matrix's five rows, a unit
  verdict for one requirement and an integration verdict for the other, and a planned test case
  with no runs.
- `core/results.py` takes one report for one repo's assessment, and no run records its source.

## Consequences

- The results contract and surface §7 are amended here; the surface architecture follows in the
  same change.
- CR-004 amends REQ-QMT-10 (frozen) and adds REQ-QMT-23. DSN-QMT-16, the table emitter, joins the
  blueprint with #49a's code.
- `[tables.matrix]` is part of the trace schema, so setting it changes the schema's digest: every
  verified copy is re-copied before `ledger check` accepts it.
- The first JSON goldens; the meta check that every verb has a golden accepts `.json`.

## Rejected alternatives

- **CSV, or a Markdown table.** CSV opens in Excel, but has nowhere for the commits read, the
  reports used and the draft notice; Markdown is already presentation, with English headers the
  render layer would have to undo. CSV may come later as a second encoding of the same rows.
- **Three verbs** (`ledger matrix`, `ledger register`, `ledger coverage`). The group grows by
  one verb per table; one verb with a table name does not.
- **Fixed columns.** Simplest, but a schema whose types or levels differ gets empty or wrong
  columns.
- **A committed, verified table in the ledger.** Its verdicts change with every run, so it would
  be stale after every run, or carry no verdicts.
- **Refusing dirty trees, or waiting for pinned imports.** The first blocks a preview while
  authoring; the second waits on unscheduled work.
- **Combining reports in the command line.** Every other consumer of verdicts would repeat it.

## Open

- When an automated test's type has levels and the test case's own level field disagrees, which
  one names the verdict column — settled in #49b.
- A CSV encoding, once a reader asks for one.
