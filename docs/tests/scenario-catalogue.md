---
summary: The catalogue of scenarios the engine's tests are built from — every behaviour the throwaway stand-in was verified to have across four experiments, the behaviours it silently got wrong that the engine must report, and the Git situations it never met. Each line becomes at least one test; each finding code must be emitted by at least one fixture.
read_when:
  - writing or reviewing a test for the engine, or adding a finding code
  - checking whether a behaviour seen in an experiment is pinned by a test
  - a command misbehaves and the question is "was this ever specified?"
---

# Scenario catalogue

The stand-in's scenarios were run as inline commands while driving the experiments and were
never saved as files. They are recorded here so that they are not lost; the engine's tests
are their durable form. Codes follow the stand-in's numbering and may be renumbered once, in
the findings catalogue, before the first release. Terms follow
[`CONTEXT.md`](../../CONTEXT.md).

**Fixture project.** A hand-made miniature — three requirements, two design elements, two
modules, four tests — kept as plain files and turned into real Git repositories at test time.
Never a bundle of the test bed: opaque in review, and it would carry a tagger's identity.

## Scanning

| Scenario | Expected |
|---|---|
| The same ID declared twice | V01, naming the first declaration |
| A test function defined twice in one file — pytest runs only the second | V01 |
| An ID with this type's prefix, or its stem, that fails the pattern — `REQ-SVC-1`, `REQ-SCV-01` | V02 |
| A link to an ID that exists nowhere | V03 — "declare it here" only if the ID matches *this* repo's pattern; otherwise "it may belong to another repo" |
| A marker pointing at the wrong type of item | V04, naming the types it may point at |
| A marker carried by the wrong type of item — `Satisfies:` under a requirement | V04, naming who may carry it |
| A required field missing; a field value outside its list — spelled exactly, case included | V05, listing the allowed values |
| A test outside a level folder, including `tests/test_x.py` at the top | V06 |
| An item declared in a file that is not scanned for its type | V07, naming the file pattern that would have caught it |
| A test file or a module that cannot be parsed; a file that is not UTF-8 | V08 — never a crash |
| An origin its source does not declare | V09, listing the real ones, in numeric order |
| A heading inside a code fence | ignored |
| Fields written with bold keys; a document with frontmatter | parsed; tolerated |
| `verifies` on a test class | inherited by its tests |
| A parametrised test function | one test case |

## What the stand-in passed silently — the engine reports

| Scenario | Expected |
|---|---|
| `- Origin: TBD` — a required link field with no ID in it; `AGR-1, AGR-X` — one part not an ID | V14, naming the part; the rest of the line still links |
| A marker under the wrong kind of item — `Satisfies:` under a requirement | V04, naming who may carry it; the stand-in dropped it as an unknown field |
| `Implements:` outside the module docstring | not a marker (M2); if that leaves the module unlinked, the gap says why (M3) |
| `verifies` with a non-literal argument, through `pytestmark`, inside `pytest.param(marks=…)`, with no IDs, as a bare decorator, under another name, on something pytest does not collect | V15 — every `mark.<link marker>` in a test module is either read or reported |
| A module with a syntax error | V08, as a test file is |
| An ignore pattern that hides a file with logic in it | `status` shows ignored-file counts per item type |
| A configuration key that is not known | a configuration error — a mistyped `requird` is a hidden rule |
| A coverage rule that needs `Assumes` | a configuration error (D10) |

## Must never look alike

| Looks like | But is | Expected |
|---|---|---|
| Nothing declared yet | An item in a file that is not read | V07, and items *and files* scanned per type in the summary |
| An item declared in the repo | A note the repo ignores — a gitignored `_playground/` quoting a heading | never read: the working tree is what a commit could carry |
| External IDs are fine | Their source could not be reached | *not verified*, in the result line; survives `--quiet` |
| Nothing is frozen | A shallow clone, unfetched tags, or not a Git repository | said plainly, and the run **could not judge** when baselines are configured — a pipeline's default checkout is shallow and has no tags |
| Two counts that disagree | Test cases versus runs | every count labelled |
| This requirement failed | A test case that verifies several items failed | marked *shared*, with what else it verifies |
| No suspects | A file was touched | a suspect never clears itself |
| An empty project | A revision older than the repo's configuration | refused, with the reason |
| Covered | `Verify-by: inspection` with nothing recorded | listed apart from tested requirements, in `status` and `results` |

## Coverage

- Rules come from data; `where` narrows a rule by a field's value — exactly, as V05 spells it; an
  item missing the field gets V05 and no gap.
- No hidden exemption: a rule without `where` applies to every item of its type.
- A withdrawn item raises no coverage gap *(semantics settled in M5a, with change control; until
  then a withdrawn item still raises its gaps)*.
- Gaps are listed and the run does not fail while authoring; under the gate it fails — every gap,
  in slice 1.
- Rules are judged on this repo's items; a link to an item not verified here counts; `Assumes`
  counts toward no rule.
- A gap whose link was refused by a violation says to fix that violation first — never to add a
  second line. A gap on a module with an `Implements:` outside its docstring names that line.
- A rule no item type this repo scans can meet is still a gap, and says so; `rules` marks it.
- `rules` prints what is in force and says which part is the project's and which the repo's.
- A rule whose direction contradicts its link type is a configuration error.
- *Recorded for later:* a marker line in Markdown above the first heading, or under a heading
  with no ID, is dropped silently — the Markdown counterpart of the stray `Implements:`.

## Results

- Runs versus test cases; the worst verdict wins; untested requirements listed.
- A requirement declared in a sibling repo and verified here.
- **The regression:** `results` on any repo that has `verifies` links.
- Report cases that match no scanned test are reported, not dropped; a report whose class
  names match nothing says so instead of printing "no result" for everything.

## The baseline guard — the nine, and what D6 adds

| Scenario | Expected |
|---|---|
| No baseline tag | nothing frozen, said as such |
| Tagged, nothing changed | every covered item frozen |
| A frozen paragraph re-wrapped | **not** a change |
| Frozen text edited, no citation | V10 — put it back, or stop and ask for a change request |
| A cited change request that does not exist | V11 — never invent one |
| A cited change request not yet accepted | V11 |
| Accepted, but the item is missing from `Impacts` | V12 — the impact analysis is incomplete; do not edit the ledger |
| Accepted and listed | clean, with suspects listed |
| A frozen heading deleted; a new item added without a citation | V13; V10 |
| The `Change:` line added or extended, nothing else | not a change |
| `Origin` gains a clause | a change |
| **Only a fresh citation counts** — an item already citing CR-002 is edited again | V10: a permanent citation does not license a later edit |
| A tag pattern from the configuration; a release tag as the product baseline | recognised |
| Two scopes cover the same item | one governing baseline per item, no duplicate findings |
| A release tag from before the repo was traced | the subject is not judged against it — nothing becomes "new since" |
| A feature branch forked before the tag was cut | the tag is not reachable and is not applied |
| A maintenance line | sees its own last release only |
| A lightweight baseline tag | reported as weaker evidence — no tagger, no date of its own |
| The repo's configuration moved between the tag and `HEAD` | the tree at the tag is read with the configuration at the tag |
| The change-request register unreachable | a fresh citation passes with a notice; verified at the ledger's import |
| Detached `HEAD` | works |

## Suspects

- Item-level: a document item's text, a test function's own source, a module's file.
- Downstream of a changed frozen item, **transitively**, grouped by distance; the first hop
  listed in full, the rest counted.
- Existed at the baseline and unchanged → suspect. Existed and edited → still listed, worded
  differently. New since the baseline → not a suspect.
- Appending a comment to a file, or adding a test to it, clears nothing.
- A new baseline clears them all.
- *Recorded, not fixed:* a field-only change makes everything downstream suspect.

## Thread and impact

- `thread` prints the marker on each edge; an `Assumes` edge is labelled, and across repos
  carries "judged at import".
- `thread` shows each item once, nearest first, under the link that reaches it first; a second
  link into it is noted as `also` — a test that verifies a requirement and its design element.
- Forward, `thread` crosses an `Assumes` link and goes on; backward, it shows the assumed item and
  stops *(settled in M2b — otherwise `impact` would name unrelated clauses)*.
- `thread` on a sibling's item says that what hangs off it *there* is not shown. Any ID the run
  can see can be threaded: an uncited sibling item, an uncited clause the agreement declares.
- `thread` on an ID nothing here can see — could not judge, with the closest IDs; in a pipeline
  it says the sibling could not be read, never that the item does not exist.
- The header of `thread` says what could not be read, and how many links were refused as
  violations — an empty result never looks like a clean one.
- `impact` takes several IDs and returns their union, deduplicated: downstream grouped by item
  type, upstream origins included, and the `Impacts` line carrying only the item types a
  baseline covers. An ID reserved by a change request and not yet declared is reported as
  such. The output says that it stops at the repo's edge.
- `Assumes` is traversed and counts toward no coverage rule.

## Across repos

- A sibling's item cited from a design element or a test — accepted, and *not pinned* is said.
- A sibling's requirement re-declared locally — V01, "already declared in sibling … cite it; a
  requirement has one home".
- The sibling unreachable, its configuration unreadable, or the siblings not locatable at all (no
  ledger beside the repo) — said in the header. A citation of an ID that is not this repo's own
  then passes as *not verified here*, judged at the ledger's import; an ID matching this repo's
  own pattern is V03 regardless *(decided while planning M2 — a pipeline checks out one repo)*.
- A sibling's own findings are not reported, and its own siblings are never read.

## Configuration

- The project's trace schema by path; as an embedded generated copy; both present.
- The schema unreachable — could not judge, with the next move.
- No configuration — could not judge.
- A local pointer to the ledger absent — every external source *not verified*.
- A verb run in the wrong kind of repo says so and names the right place.
- An extractor the engine does not have; `markdown` with no ID pattern; a type whose IDs are
  derived given one — a configuration error.

## Command line

- One golden output per registered command; a meta-test fails when a command has none.
- A meta-test fails when a catalogue code has no fixture that emits it.
- A missing argument, a bad option, an interrupt, a raised exception — each maps to its code.
- `--quiet` prints findings only; notices about what could not be verified still appear.
- The root is found by walking up to the configuration; `-C <path>` runs elsewhere — before the
  verb, as with `git`, or after it; both at once is a usage error.
- Two consecutive runs of any command give identical bytes.

## Setting up a repo

- `init` writes the trace configuration and the stanza between markers, names the subject in
  it, registers the test framework's marker, and is idempotent.
- In a scratch copy of a test-bed repo it reproduces the committed stanza byte for byte.
- Every fenced marker example in the shipped skill parses with the real extractors; every
  finding code has catalogue text. The skill and the tool cannot drift apart.
