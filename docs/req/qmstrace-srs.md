---
summary: The qmstrace subject's requirements (REQ-QMT-NN) — one checkable statement each, with its category, its origin in the ledger's agreement and how it is verified. The traced projection of the PRD's slice-1 capabilities.
read_when:
  - changing what a command promises, or adding a capability
  - writing a design element that must say which requirement it satisfies
  - tagging a test with the requirement it verifies
---

# qmstrace — Software Requirements Specification

Subject `qmstrace`, key `QMT`. Each requirement is one statement a test can fail; the *why*
and the priorities stay in the [PRD](qmstrace-prd.md), which carries no IDs. `Origin` cites a
clause of the agreement in the ledger repo (`AGR-n`). The design elements that satisfy these
requirements are in the [codebase blueprint](../structure/codebase-blueprint.md#11-design-elements--what-the-code-is-traced-to).

Scope: what slice 1 built — the product-repo half. Work-product state, events, the ledger's
import and emitted tables are slices 2 and 3 and are not specified here yet. No baseline has
been cut: nothing below is frozen.

## Rules as data

### REQ-QMT-01 — The rules are read, not built in

Item types, ID patterns, link types, required fields, coverage rules and baseline tag
patterns are read from the project's trace schema and the repo's trace configuration. A
project that renames an item type or an ID prefix is judged correctly with no change to the
engine.

- Category: functional-suitability
- Origin: AGR-6
- Verify-by: test

### REQ-QMT-02 — Markers are read where they are authored

A requirement or design element is declared by a Markdown heading that starts with its ID,
and its links by `Key: value` lines in its section; a component's links by `Implements:` in
its module docstring; a test case's links by a `pytest.mark.verifies` decorator with literal
IDs. A marker written in a form that is not read is reported, never silently dropped.

- Category: functional-suitability
- Origin: AGR-2
- Verify-by: test

## Checking

### REQ-QMT-03 — One check reports every finding, and the gate fails on gaps

`qmstrace check` reports every violation and gap in one run, each with its file, line and
next move. It exits 1 when there is a violation; gaps fail it only under `--strict`.

- Category: functional-suitability
- Origin: AGR-1, AGR-5
- Verify-by: test

### REQ-QMT-04 — Every rule in force is printable

`qmstrace rules` prints every link type, required field and coverage rule in force for the
repo, and says whether each comes from the project's trace schema or the repo's trace
configuration.

- Category: usability
- Origin: AGR-5, AGR-6
- Verify-by: test

### REQ-QMT-05 — Status is one compact view

`qmstrace status` prints what was scanned, one line per requirement, and the counts of
violations, gaps and suspects. What the run could not locate, read or verify is said in its
header.

- Category: usability
- Origin: AGR-5
- Verify-by: test

## Tracing

### REQ-QMT-06 — One item is traced both ways

`qmstrace thread ID` shows what the item derives from, as far as its origins, and what hangs
off it, as far as its test cases — each item once, labelled with the link that reached it.

- Category: functional-suitability
- Origin: AGR-1
- Verify-by: test

### REQ-QMT-07 — The impact set of several items at once

`qmstrace impact ID…` shows everything downstream of the given items, deduplicated, with a
candidate `Impacts:` line for a change request; the order and repetition of the given IDs do
not change the output.

- Category: functional-suitability
- Origin: AGR-5
- Verify-by: test

## Change control

### REQ-QMT-08 — A frozen item changes only under an accepted change request

A tag matching a configured baseline pattern and reachable from `HEAD` freezes the items its
scope covers. A frozen item whose text changed, or an item added to a controlled scope, is a
violation unless its section cites a change request that is accepted and lists it in
`Impacts`.

- Category: functional-suitability
- Origin: AGR-1
- Verify-by: test

### REQ-QMT-09 — What hangs off a changed item stays suspect until reviewed

When an item's text changed since the baseline that governs it, every item downstream of it
is reported as a suspect, with the reason. Editing the suspect item, adding tests or passing
them does not clear it.

- Category: functional-suitability
- Origin: AGR-1, AGR-10
- Verify-by: test

## Evidence

### REQ-QMT-10 — Test results come from a report, never typed

`qmstrace results REPORT` reads a pytest JUnit report and gives each requirement the verdict
of the test cases that directly verify it. A test that verifies only a design element gives
its requirement no verdict, and an unreadable report is not judged.

- Category: functional-suitability
- Origin: AGR-9
- Verify-by: test

### REQ-QMT-11 — Only what a commit could carry is read

In a Git repository the scan reads the files a commit could carry: an ignored file is never
read, and a Git variable pointing at another repository changes nothing.

- Category: functional-suitability
- Origin: AGR-7
- Verify-by: test

## Setting up

### REQ-QMT-12 — A product repo is set up by one command

`qmstrace init` writes the trace configuration, the agent guide's stanza and the skill, and
registers the pytest marker. Run again, it changes nothing; it refuses to replace a file it
did not write, and then writes nothing.

- Category: usability
- Origin: AGR-5
- Verify-by: test

### REQ-QMT-13 — The schema is authored once and copied, verified

`qmstrace ledger copy-schema`, run in the ledger repo, writes the project's trace schema into
every product repo the schema names, with a digest. A second run changes nothing; if one
repo cannot take the copy, no repo is written.

- Category: functional-suitability
- Origin: AGR-2, AGR-6
- Verify-by: test

## Surface

### REQ-QMT-14 — Exit codes an agent can branch on

Every command exits 0 when it completed, 1 when the check failed, 2 when it could not judge
— with the next move — and 3 on an internal error, never with a bare traceback.

- Category: usability
- Origin: AGR-5
- Verify-by: test

### REQ-QMT-15 — The same inputs give the same bytes

Two runs of a command on the same tree print identical bytes, with no path of the machine
it ran on.

- Category: reliability
- Origin: AGR-15
- Verify-by: test

### REQ-QMT-16 — An offline view of the trace graph

`qmstrace graph` writes one standalone HTML file that loads no script from elsewhere and
makes no connection, and never overwrites an existing file.

- Category: usability
- Origin: AGR-1
- Verify-by: test
