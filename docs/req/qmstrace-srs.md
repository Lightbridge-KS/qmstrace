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

Scope: what slice 1 built — the product-repo half — and the project-wide check over working
trees (M10). Work-product state, events, the ledger's import at pins and emitted tables are
slices 2 and 3 and are not specified here yet. REQ-QMT-01…16 are frozen by the baseline tag
`baseline/requirements/1`; a requirement added or changed since cites an accepted change request
in the ledger under `Change:`.

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

A requirement, a design element or a test case in a Test Specification is declared by a
Markdown heading that starts with its ID, and its links by `Key: value` lines in its section; a
component's links by `Implements:` in its module docstring; an automated test's links by a
`pytest.mark.verifies` decorator with literal IDs, naming the test case it runs or what it
verifies directly. A marker written in a form that is not read is reported, never silently
dropped.

- Category: functional-suitability
- Origin: AGR-2
- Verify-by: test
- Change: CR-003

### REQ-QMT-20 — An ID is read whole, dotted parts and all

An ID's number may carry dotted parts — `TC-SVC-04.1-01`, `DSN-SVC-04.1`. An ID is read whole
wherever it is written — a heading, a field, a table, prose, a marker in code, a change
request — or not read as an ID at all; it is never cut short. A heading that starts with a
malformed ID of the repo's kind is reported, not read as prose.

- Category: functional-suitability
- Origin: AGR-6, AGR-11
- Verify-by: test
- Change: CR-003

### REQ-QMT-21 — A C# repo is read where its markers are authored

In a C# repo, a component is a `.cs` file whose links are field lines (`Implements: …`) in the
leading `///` doc comment of its first type, and an automated test is an xUnit `[Fact]` or
`[Theory]` method whose link is the ID at the start of its `DisplayName`, written as a string
literal. A marker in a form that is not read — a `DisplayName` that is not a literal, a
`[Trait]` named after a link, a test attribute other than xUnit's, a test inside conditional
compilation — is reported, never silently dropped.

- Category: functional-suitability
- Origin: AGR-2, AGR-6
- Verify-by: test
- Change: CR-003

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

`qmstrace results REPORT` reads a pytest JUnit report and gives each requirement the worst
verdict of the automated tests that reach it along `verifies` links — directly, or through the
test cases they run, each named with its own verdict. A test that reaches only a design element
gives no requirement a verdict and is still shown; a test case no automated test runs adds
nothing; an unreadable report is not judged.

- Category: functional-suitability
- Origin: AGR-9
- Verify-by: test
- Change: CR-003

### REQ-QMT-11 — Only what a commit could carry is read

In a Git repository the scan reads the files a commit could carry: an ignored file is never
read, and a Git variable pointing at another repository changes nothing.

- Category: functional-suitability
- Origin: AGR-7
- Verify-by: test

## Setting up

### REQ-QMT-12 — A product repo is set up by one command

`qmstrace init` writes the trace configuration, the agent guide's stanza and the skill, and
registers the pytest marker where the repo's automated tests are pytest functions. Run again, it
changes nothing; it refuses to replace a file it did not write, and then writes nothing.

- Category: usability
- Origin: AGR-5
- Verify-by: test
- Change: CR-003

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

## The project

### REQ-QMT-17 — The project is judged as a whole, from its ledger

`qmstrace ledger check`, run in the ledger repo, reads the working tree of every repo the trace
schema lists under `[repos]` — the ledger itself too, when it lists itself as `"."` — and
reports the project's violations, gaps and suspects in one run. A coverage rule is met by a
link in any of those repos; each repo's own violations are reported with it; a change to a
frozen item makes what hangs off it suspect in every repo. A listed repo that cannot be read,
or holds rules other than the ledger's schema, stops the check with exit 2. The output says it
read working trees, not pins.

- Category: functional-suitability
- Origin: AGR-1, AGR-15
- Verify-by: test
- Change: CR-001

### REQ-QMT-18 — One item is traced across the whole project

`qmstrace ledger thread ID` and `qmstrace ledger impact ID…`, run in the ledger repo, walk the
project's repos as one graph — backward to the origin clauses, forward to the design, the code
and the tests of every repo — with a module's or a test's ID written with its repo. An ID that
no repo declares or cites is refused with exit 2, naming the qualified IDs a module's or a
test's ID given without its repo may mean. The output says it read working trees, not pins.

- Category: functional-suitability
- Origin: AGR-1, AGR-15
- Verify-by: test
- Change: CR-001

### REQ-QMT-19 — A ledger that holds the documents is set up by the same command

`qmstrace init`, run in a ledger repo, writes the ledger's own trace configuration when it has
none — declaring requirements and design elements, with the schema beside it read by path —
and, in every ledger, an agent guide's stanza that names `qmstrace ledger check --strict` as
the gate and `ledger thread` and `ledger impact` as the walks. It never edits the trace
schema; while `[repos]` does not list the ledger, it says which line to add. A product repo's
stanza is unchanged.

- Category: usability
- Origin: AGR-5
- Verify-by: test
- Change: CR-002
