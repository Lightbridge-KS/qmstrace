---
summary: The single active qmstrace tracker — slice 1 landed through M9c, qmstrace traced by its own ledger and its first requirements baseline cut; E6 dogfooding cancelled after run A; now qmstrace applied in real development and shaped as it goes, targeting the layout where the ledger holds the documents (ADR-0001); M10, the project-wide check, landed (ledger check, thread, impact; init in a ledger); configuration, judge, graph, setup, Markdown, Python extractor, text renderer, workspace and CLI package refactors plus shared graph assembly verified and awaiting draft review, then the first real project and M11 mentions; M12, the C# capability — its test bed beacon-dotnet built and measures fixed, slices M12-0 to M12e planned; what landed work left open; deferred slice-2 work.
read_when:
  - starting a session in this repo — read this first
  - planning or finishing a milestone, or checking whether slice 1 is done
  - deciding what is next or which verification remains
---

# qmstrace — progress

**Updated 2026-10-14 · Slice 1, the product-repo half: landed. M10, the project-wide check:
landed.** Now: [package refactors](#now--package-refactors). Next:
[real-world use](#next--real-world-use), in the layout of ADR-0001, and
[M12 · the C# capability](#next--m12--the-c-capability), whose test bed is built. After: M11 · mentions. Commit hashes locate work. Verification claims refer to checks
that were actually run.

## Now — package refactors

The accumulated refactors are ready for draft review on `codex/config-package`.
The verification records below describe each extraction; no refactoring ADRs were added.

### CLI package

**CLI package implemented and verified 2026-10-13.** Included in the accumulated refactors on
`codex/config-package`. Root registration, local/ledger handlers and shared
invocation/exit policy have separate owners. The installed entry point remains
`qmstrace.cli:app`; the [blueprint](../structure/codebase-blueprint.md) records ownership and
compatibility directly, without an ADR.

- [x] Extract application, local/ledger handlers and shared invocation/exit policy.
- [x] Compare original/new command outputs and disposable write effects.
- [x] Pin exports, registration, dependencies and installed entry-point behavior.
- [x] Update design ownership; run dry and strict trace checks without ADRs.

**CLI verification:**

- The existing 161 CLI/browser/setup tests pass before extraction; 172 pass afterward,
  including eleven new compatibility, registration and stream cases. All sixteen function
  definitions retain identical syntax trees after relocating eight root registration
  decorators unchanged. Constants, the directory annotation and Typer construction expressions
  retain identical syntax trees.
- A differential run passes 172 tests: **161 CLI invocations** match exit code, separate
  stdout/stderr bytes and combined output bytes, covering exits 0–3. Twenty-four mutating
  invocations remain in ordinary tests and are excluded from double execution.
- Fifteen CLI write scenarios on restored disposable copies match streams and complete
  filesystem state, including setup, schema copies, graph HTML, symlinks and refusal cases.
  Refused writes leave the original state intact.
- Architecture checks pass 156 cases. All 22 public exports forward their implementation
  objects; command registration order, wrapped signatures, eager version handling and
  no-argument/duplicate-directory output channels are pinned. Negative fixtures reject
  extra exports, nested initializer code and dependency back edges.
- Built-wheel checks pass across 23 fresh import orders. A separately installed console
  script outside the source tree matches the original for all fourteen help views, two
  no-argument cases and version output; imports resolve to the installed wheel. Console
  comparisons use identical terminal conditions; the existing CliRunner help goldens remain
  byte-for-byte unchanged.
- A deliberate exit-code fault fails the existing DSN-QMT-01/REQ-QMT-14 tagged test in a
  disposable copy; the copy was removed.
- Final `just dry`: **959 Python tests, 4 browser tests, 98.85% coverage**; formatting, lint,
  strict typing, wheel checks and manual build pass. Goldens, `findings.py`, dependencies
  and the console entry-point declaration remain unchanged.
- Local and ledger strict trace gates: **570 items, 0 violations, 0 gaps, 0 suspects**;
  16 frozen, 0 changed, 3 new, 0 removed. The ledger still lists one repo; remote-tag
  completeness and historical external evidence remain unverified.

### Workspace package

**Workspace package implemented and verified 2026-10-13.** Included in the accumulated refactors on
`codex/config-package`. Shared reading, baseline, project and setup operations
have private owners; the public class keeps local assessment and command sequencing together.
The [blueprint](../structure/codebase-blueprint.md) records ownership and compatibility directly,
without an ADR.

- [x] Extract owners with exact compatibility exports and no new services.
- [x] Verify values, diagnostics, output bytes and setup side effects against the original.
- [x] Pin dispatch, read order, dependency direction and built-wheel behavior.
- [x] Update architecture ownership; run dry and strict trace gates. No ADRs.

**Workspace verification:**

- The existing 260 workspace/project/baseline/setup/results/CLI tests pass before and after
  extraction. Twenty-seven definitions retain identical syntax trees; four extracted bodies
  differ only by receiver/configuration-callback substitution. All eleven public method
  signatures, decorators and dataclass slots match the original.
- A differential run passes 213 tests and compares **329 calls**, including full ordered
  assessment values, refusal types/messages and rendered bytes. Fifteen setup, schema-copy
  and view-write scenarios on restored disposable copies match return values, refusals,
  file bytes, permissions and symlinks; refused writes leave the original state intact.
- Nine contract cases pin compatibility exports, subclass construction and dispatch, tree/Git
  injection, immutability, empty project impact and report reading before assessment. The
  historical scan-count test now instruments the scanner at its new lookup site and still
  proves one scan per selected commit.
- Architecture checks pass 139 cases, including rejecting fixtures for broad exports,
  nested initializer code and back edges. Built-wheel checks pass across eighteen fresh
  import orders outside the source tree, exercising setup, scanning, walks and view writes.
- Disabling file selection in a disposable copy fails the existing DSN-QMT-02 tagged
  integration test; the copy was removed.
- Final `just dry`: **931 Python tests, 4 browser tests, 98.84% coverage**; formatting, lint,
  strict typing, wheel checks and manual build pass. Goldens, `findings.py` and dependencies
  remain unchanged.
- Local and ledger strict trace gates: **559 items, 0 violations, 0 gaps, 0 suspects**;
  16 frozen, 0 changed, 3 new, 0 removed. The ledger still lists one repo; remote-tag
  completeness and historical external evidence remain unverified.

### Text renderer package

**Text renderer package implemented and verified 2026-10-13.** Included in the accumulated refactors
on `codex/config-package`. Status, walks, checks, results and schema views
have independent owners; shared evidence and presentation formatting serve text and browser
output. Ownership and compatibility rules are recorded in the
[blueprint](../structure/codebase-blueprint.md), without an ADR.

- [x] Extract command owners and shared evidence/presentation without rewriting behavior.
- [x] Preserve eleven functions and six constants through exact compatibility exports.
- [x] Compare all renderers and browser evidence against the original; pin dependency rules.
- [x] Update architecture ownership; run focused checks, dry gate and strict trace checks.

**Text renderer verification:**

- The existing 192 CLI/baseline/suspect/project tests pass before extraction. All 71 moved
  definitions retain identical syntax trees. A differential run passes 196 tests and compares
  **136 text-rendering calls and 11 browser-evidence calls** against the original: identical
  strings and UTF-8 bytes, ordering, quiet notices and evidence tuples across all eleven
  public functions.
- Focused CLI/browser checks pass 88 tests; architecture and compatibility checks pass 127.
  Exact exports, independent command owners and shared evidence dependencies are pinned;
  negative fixtures reject broad exports, nested initializer code and back edges.
- Deliberately corrupting finding-code output fails the existing REQ-QMT-03 tagged CLI golden
  test in a disposable copy; the copy was removed.
- Final `just dry`: **903 Python tests, 4 browser tests, 98.78% coverage**; formatting, lint,
  strict typing, wheel checks and manual build pass. Goldens, `findings.py` and dependencies
  remain unchanged.
- Built-wheel checks exercise all text views, strict/quiet combinations and browser evidence
  across fourteen fresh import orders outside the source tree. All seventeen compatibility
  exports retain their implementation objects.
- Local and ledger strict trace gates: **545 items, 0 violations, 0 gaps, 0 suspects**;
  16 frozen, 0 changed, 3 new, 0 removed. The ledger still lists one repo; remote-tag
  completeness and historical external evidence remain unverified.

### Python extractor package

**Python extractor package implemented and verified 2026-10-13.** Included in the accumulated refactors
on `codex/config-package`. Language-specific owners live in `extract/python/`;
the old modules forward the supported functions directly. Ownership and compatibility rules
are recorded in the [blueprint](../structure/codebase-blueprint.md), without an ADR.

- [x] Move module and pytest extraction unchanged; update canonical production callers.
- [x] Pin compatibility, dependency direction and built-wheel import behavior.
- [x] Compare complete extraction and report identity results with the originals.
- [x] Update architecture ownership; run focused checks, dry gate and strict trace checks.

**Python extractor verification:**

- Both implementation modules are byte-for-byte identical to the originals. The existing
  87 Python/form/JUnit/results tests pass before and after the move, including reports
  generated by real pytest for xunit1 and xunit2.
- A differential run passes 106 tests and compares **356 calls**: 83 module extractions,
  104 pytest extractions, 148 report identities and 21 form renderings. All returned values,
  digests, ordering and complete diagnostics match. Two parametrized compatibility cases are
  excluded from instrumentation and pass separately in the ordinary suite.
- Focused Python/form/JUnit/architecture checks pass 162 tests. Exact compatibility imports,
  registry identity, independent language owners, canonical production imports and an empty
  Python package initializer are pinned; negative fixtures reject wrappers and back edges.
- Disabling module docstring links and disabling pytest test-name recognition each fail the
  corresponding DSN-QMT-04 tagged test in a disposable copy; the copy was removed.
- Final `just dry`: **876 Python tests, 4 browser tests, 98.77% coverage**; formatting, lint,
  strict typing, wheel checks and manual build pass. Goldens, `findings.py`, dependencies and
  configured extractor names remain unchanged.
- Built-wheel checks exercise old/new imports, registry identity, docstring links/strays,
  inherited pytest markers and report identities across eleven fresh import orders outside
  the source tree. Extraction does not import pytest at runtime.
- Local and ledger strict trace gates: **535 items, 0 violations, 0 gaps, 0 suspects**;
  16 frozen, 0 changed, 3 new, 0 removed. The ledger still lists one repo; remote-tag
  completeness and historical external evidence remain unverified.

### Markdown extraction

**Markdown extraction implemented and verified 2026-10-13.** Included in the accumulated refactors on
`codex/config-package`. The main section loop is intact; the
[blueprint](../structure/codebase-blueprint.md) records ownership and the narrow compatibility
exception directly, without an ADR.

- [x] Extract heading and table syntax into private owners; retain section assembly together.
- [x] Characterize boundary interactions and compare with the original extractor.
- [x] Pin compatibility exports, internal dependencies and built-wheel imports.
- [x] Update design ownership; run focused checks, dry gate and strict trace checks.

**Markdown verification:**

- The existing 147 Markdown, forms, baseline and workspace tests pass before editing. Two
  new characterization tests pass against the original extractor, pinning mention locations
  across sections/fences and duplicate-field values, links and diagnostic order.
- All 22 moved definitions have identical syntax trees. A differential run passes 149 tests
  and compares 624 complete extraction results with the original, including ordering,
  fields, source lines, findings and digest bytes. The import-identity test is excluded from
  instrumentation and passes separately in the ordinary suite.
- Focused extractor/forms/architecture checks pass 176 tests. The architecture gate allows
  only `extract`, `form` and `CHANGE` exports; rejecting fixtures cover broad exports,
  nested initializer code and back edges. The registry retains the implementation objects.
- Disabling heading ID recognition in a disposable copy fails the existing DSN-QMT-04
  tagged declaration test; the copy was removed.
- Final `just dry`: **857 Python tests, 4 browser tests, 98.76% coverage**; formatting, lint,
  strict typing, wheel checks and manual build pass. Goldens and `findings.py` are unchanged.
- Built-wheel checks exercise extraction, tables, fences and compatibility imports outside
  the source tree, across seven fresh import orders including Markdown and its registry first.
- Local and ledger strict trace gates: **529 items, 0 violations, 0 gaps, 0 suspects**;
  16 frozen, 0 changed, 3 new, 0 removed. The ledger still lists one repo; remote-tag
  completeness and historical external evidence remain unverified.

### Setup extraction and graph assembly

**Setup extraction and graph assembly consolidation implemented and verified 2026-10-13.**
Included in the accumulated refactors on `codex/config-package`. Public imports, generated bytes,
diagnostics, ordering and subclass construction are preserved. Ownership is recorded directly
in the [blueprint](../structure/codebase-blueprint.md); no refactoring ADRs.

- [x] Extract setup into guide, pytest registration and schema-copy owners with exact exports.
- [x] Consolidate graph indexes and traversal metadata behind one private assembly method.
- [x] Verify old/new behavior, dependency rules and installed-distribution compatibility.
- [x] Update design ownership; run focused tests, dry gate and strict trace checks.

**Setup/assembly verification:**

- The existing 138 setup, schema-copy, workspace and graph tests pass before editing; the
  82 setup-related tests pass immediately after extraction. All 20 moved setup definitions
  retain identical syntax trees. Graph changes are limited to build/join delegating their
  assembly; existing queries and walk algorithms retain identical syntax trees.
- A differential run passes 201 tests: 319 setup calls, 177 graph builds, 17 joins and 4,678
  walks match the originals, including generated bytes, complete diagnostics and ordered
  graph values. Three compatibility/subclass tests are excluded from instrumentation and
  pass separately in the ordinary suite.
- The architecture gate pins all 18 setup exports and independent internal owners; negative
  fixtures reject extra exports and dependencies between setup modules. Regressions cover
  empty/populated graphs, duplicate links, adjacency ordering and subclass construction.
- Deliberately dropping repeated links from indexes and dropping guide prefixes each fail
  the corresponding tagged test in a disposable copy; the copy was removed.
- Final `just dry`: **842 Python tests, 4 browser tests, 98.76% coverage**; formatting, lint,
  strict typing, wheel checks and manual build pass. Command/findings goldens and
  `findings.py` remain unchanged.
- Built-wheel and independently installed-wheel checks exercise all setup owners, schema
  round-tripping and graph/judgment behavior in five fresh import orders outside the source
  tree. Source notices and the public import identities remain intact.
- Local and ledger strict trace gates: **524 items, 0 violations, 0 gaps, 0 suspects**;
  16 frozen, 0 changed, 3 new, 0 removed. The ledger still lists one repo; prior evidence
  limits remain.
- A new wheel probe exposed existing marker-registration behavior for an empty pytest
  section header with no final newline: generated text joins the header and assignment,
  and registration is not idempotent (TOML fails on the second call). Both original and
  extracted implementations reproduce it. The distribution smoke fixture uses a
  newline-terminated header; this refactor includes no behavioral fix for that edge case.

### Judge and graph extraction

**Judge and graph extraction implemented and verified 2026-10-13 on
`codex/config-package`.** Public imports are preserved through narrow compatibility exports;
the [blueprint](../structure/codebase-blueprint.md) records ownership and dependency rules.
The earlier configuration refactor remains in the same working tree. `findings.py` is
byte-for-byte unchanged. Refactoring ownership and compatibility rules are documented
directly in the architecture docs; the two refactoring ADRs were removed.

- [x] Extract coverage, baseline guards and suspects into independent judge modules.
- [x] Compare judge outputs against the original implementation.
- [x] Extract graph node values and validation; retain construction, joining and traversal together.
- [x] Pin compatibility, dependency direction and isolated distribution imports.
- [x] Update design ownership and record the limited export exception.
- [x] Run focused parity, the dry gate and strict trace checks; inspect golden diffs.

**Judge/graph verification:**

- The existing 96 judge/baseline/project tests and 54 graph tests pass before and after
  extraction. Focused runs exclude the suite-wide coverage floor; the full gate enforces it.
- All 24 moved definitions have identical syntax trees. Before graph extraction, 449 judge
  calls match the original implementation. After both moves, 188 tests replay 315 builds,
  15 joins, 8,358 walks and 469 judgment calls against the originals, with identical values,
  ordering, alternate links and complete diagnostics.
- Architecture gates enforce exact compatibility exports, independent judge policies and
  one-way graph dependencies; negative fixtures reject nested initializer code, extra exports
  and back edges, including parent-package and type-only imports. Object identity and
  `TraceGraph.build`/`join` subclass dispatch are pinned.
- Two deliberate faults in a disposable copy (coverage condition and graph constructor
  dispatch) fail their tagged tests; the copy was removed.
- `just dry`: **831 Python tests, 4 browser tests, 98.75% coverage**; formatting, lint, strict
  typing, distribution checks and manual build pass. Command and findings goldens are unchanged.
- Built-distribution and independently installed-wheel checks pass with graph, judge,
  baselines and findings imported first in fresh isolated interpreters. Each run exercises
  configuration, graph admission, walks, joining and judgment outside the source tree.
- Local and ledger strict trace gates: **520 items, 0 violations, 0 gaps, 0 suspects**;
  16 frozen, 0 changed, 3 new, 0 removed. Existing evidence limits remain; the ledger lists
  one repo, so this does not repeat the multi-repo acceptance experiment.

### Configuration extraction

**Implemented and verified 2026-10-13 on `codex/config-package`.** Split
`core/config.py` by responsibility while preserving its public imports and behavior.
The [blueprint](../structure/codebase-blueprint.md#8-what-is-deliberately-absent) records the
approved narrow compatibility-export exception. Real-project onboarding remains next.

- [x] Extract records, strict TOML reading, section readers, schema-copy helpers and parsing.
- [x] Preserve constructors, ordering, digest bytes and exact refusal diagnostics; keep #25
  and #26 as separate behavior changes.
- [x] Pin compatibility and internal dependencies; compare against the pre-refactor parser.
- [x] Update DSN-QMT-03, architecture ownership and the compatibility-export rule.
- [x] Run focused tests, full dry gate, installed-wheel and strict trace checks.

**Verification:**

- The existing 98 configuration/schema-copy tests pass before and after extraction.
- 157 configuration, schema-copy, baseline and ledger tests replayed 379 parser calls against
  the pre-refactor implementation: identical values, ordering, regexes and complete diagnostics.
  All 35 moved class/function/constant definitions have identical syntax trees.
- Architecture gates cover nested initializers and one-way configuration imports, with
  rejecting fixtures. Public exports forward the same objects; classmethod dispatch survives.
- A disposable-copy mutation accepting booleans as integers fails the tagged diagnostic test;
  the copy was removed.
- `just dry`: 810 Python tests, 4 browser tests, 98.74% coverage; formatting, lint, strict
  typing, wheel checks and manual build pass. CLI goldens are unchanged.
- An independently installed wheel passes public-import identity, all three schema forms and
  schema-copy round-trip checks outside the source tree.
- Local and ledger strict trace gates: 513 items, 0 violations, 0 gaps, 0 suspects;
  16 frozen, 0 changed, 3 new, 0 removed. Four extra modules and six extra test functions
  account for the increase from the pre-refactor trace. Existing evidence limits remain.

## Next — real-world use

qmstrace is applied to real development in the developer's own workflow, and reshaped by what
that use finds. Findings become issues, and changes to settled design go through the design docs.
The first real project is not yet chosen.

**Target layout — [ADR-0001](../adr/0001-the-ledger-holds-the-documents.md), 2026-09-28:**
- **The ledger repo holds the documents:** the SRS and the design documents, beside the
  agreement, the change requests and the schema. It is traced itself, and lists itself in
  `[repos]` as `"."`.
- **Product repos hold code and tests.** Their markers cite the ledger's IDs.

M10 supports this layout through `ledger check`, `ledger thread` and `ledger impact` over
working trees. The ADR's failed checks describe the pre-M10 probe, not the current engine.
Pinned imports and historical cross-repo edit comparisons remain deferred.

**Next onboarding steps** (project selection still open):

1. Choose a project, its ledger and product repos, and one small feature to trace end to end.
2. Build and install the current engine; confirm `ledger --help` lists `check`, `thread`
   and `impact` before onboarding with it.
3. Settle subjects and ID patterns before authoring and before the first baseline. Review
   #25 and #26: malformed IDs can escape detection, and unknown subject ownership can make
   a frozen snapshot unusable.
4. Set up the ledger and code/test repos, then trace the feature and run the project gate.
   Product `init` still generates a repo-owned starter; joining an existing ledger needs
   configuration edits followed by `ledger copy-schema`. See the
   [project how-to](../../contents/how-to/check-the-project.md).
5. Record observed friction as issues; choose fixes from that evidence before expanding to
   M11. Baseline only after the IDs, trace and review are ready.

**Fixed from use:**
- [x] 2026-10-14, seen at `75ba627`: the refusals of `ledger copy-schema` and `ledger check`
  (so `ledger thread` and `ledger impact`) ended a reason that closes its own sentence in two
  full stops — `… Fix: use one of those.. Fix: …`. Each reason now gives up its own stop
  before the join. A regression test per command; no golden held a doubled stop.

**Reconciled 2026-10-13:** the September 29 onboarding handoff names `94fd827`, still both
local and remote `main`. M10 PRs #27–#29 and #31 are merged; #30 is closed. Issues #16,
#20–#22, #25 and #26 remain open. The handoff's project choice remains a proposal, not a
selected project; E6 remains cancelled.

Before the extraction, checks at `94fd827`: `status` and `check --strict --quiet`, plus
`ledger check --strict --quiet` from the QMT ledger, succeed. Both gates report 503 items,
0 violations, 0 gaps and 0 suspects; 16 frozen, 0 changed, 3 new and 0 removed document
items. The QMT ledger currently lists one repo; this check does not repeat beacon-split's
multi-repo acceptance. Remote-tag completeness and historical external evidence remain
unverified. The handoff's 794-test dry-gate result and the acceptance records below are
historical evidence; the later refactor verification is recorded above.

## Next — M12 · the C# capability

The first C# adopter writes xUnit `[Fact]`/`[Theory]` tests. Each `DisplayName` starts with the
ID of a test case planned in a document outside the code, and its IDs are dotted (`NN.m`).

Settled 2026-10-14:
- the `DisplayName` ID names a **test case** in a **Test Specification**, a Markdown document in
  the ledger, whose `verifies:` line says what it verifies;
- the code that runs a test case is an **automated test**;
- an ID may contain **dotted number segments**, read whole or reported;
- C# is parsed with **tree-sitter** (0.26 + tree-sitter-c-sharp 0.23.5), behind one private
  module;
- results are read from **TRX**, joined on class and method.

Test bed: [beacon-dotnet](../tests/beacon-dotnet.md).

- [x] Build the test bed and record M0 on today's engine (2026-10-14). Bed: ledger `493fc47`
  (tag `dotnet/requirements/1`), gateway `bac8d3f`, agent `76f610b`.
  - 53 automated tests run 49 test cases, all passing.
  - Parity with the Python agent's (level, target) pairs, checked by script.
  - Seven mutation checks, each caught by the expected test cases.
  - On today's engine, 49 V02 on the dotted register, which disappear in an undotted copy.
- [x] Fix the measures before the run (2026-10-14).
  - C1–C13, with an oracle from beacon-split on `75ba627`: 177 items, 208 links.
  - beacon-dotnet expects 226 items and 257 links.
  - C6 is revised to the settled verdict rule. C12 (setup) and C13 (no regression) are new.

**Slices** — each a branch and a draft PR, as M10 was. Each changed or added requirement cites
CR-003 (`Impacts: REQ-QMT-02, 10, 12, 20, 21, 22`), which must be accepted in
`../qmstrace-ledger` before any SRS edit lands.

- [ ] **M12-0** — decisions and vocabulary, in draft review: [#34](https://github.com/Lightbridge-KS/qmstrace/pull/34) on `docs/m12-0-decisions`:
  - [x] S1: tree-sitter parses all 19 of the bed's files with no error node; each
    `DisplayName` form is its own node kind; mypy strict and a universal `uv lock` pass. C# 14
    extension blocks give error nodes, and a test after them is still read.
  - [x] S2: four TRX captures from the bed, sanitised (no path, user or host name; gitleaks
    clean), kept for M12e's fixtures.
  - [x] [ADR-0002](../adr/0002-dotted-ids.md), [ADR-0003](../adr/0003-test-cases-and-automated-tests.md)
    and [ADR-0004](../adr/0004-reading-csharp.md), accepted 2026-10-14.
  - [x] *Test Specification* and *Automated Test* in `CONTEXT.md`; *Test Case*, *Test Result*,
    *Item*, *Marker* and *Qualified ID* follow; the ADR rule in `AGENTS.md`.
  - [x] CR-003 drafted in `../qmstrace-ledger` as `evaluated`. **The developer accepts it**
    before M12a's SRS edit.
  - [x] The bed's wording ("test specification"); measure C9 amended before the run, with its
    reason.
- [ ] **M12a** — dotted IDs, engine-wide; nothing cut short; a malformed lead is reported;
  the refusal at a baseline tag summarised. REQ-QMT-20.
- [ ] **M12b** — test cases in the trace:
  - `test_case` → `automated_test` in qmstrace's own schema and in the starter;
  - a G02 fix that names every way the link can be made;
  - the ledger forms bug fixed.
  REQ-QMT-02.
- [ ] **M12c** — verdicts through test cases in `results`, on Python; sibling-declared links;
  the per-test run identities. REQ-QMT-10.
- [ ] **M12d** — C# source: `csharp-file` and `xunit` on tree-sitter; DSN-QMT-15; SKILL.md
  and the manual. REQ-QMT-21, REQ-QMT-12.
- [ ] **M12e** — the TRX reader and report dispatch; no path or machine name ever shown.
  REQ-QMT-22.
- [ ] **M12-R** — run C1–C13 on beacon-dotnet and record the results.

## Landed — M10 · the project-wide check

Verbs run in the ledger repo: `qmstrace ledger check|thread|impact`. They read the working
tree of every repo listed in `[repos]`, the ledger itself included, and judge them as one
project. This is the first half of the ledger's import at pins (D2). Planned 2026-09-28.

**Decided:**
- **Plain commands keep their scope.** `check`, `thread` and `impact` still mean "this repo".
- **The ledger's gate is `ledger check --strict`.** Its own `check` is unchanged, and the fix
  text of its G02–G04 points at `ledger check`.
- **Derived IDs are qualified as `<repo>:<id>`** in the project view, e.g.
  `gateway:tests/unit/test_config.py::test_x`. Authored IDs never are. Locations are paths as
  seen from the ledger.
- **Each repo is built against the others, then the parts are joined.** The checks that depend
  on one repo's configuration stay per repo. Coverage, walks and suspects run on the union.
- **Exit 2 if any listed repo cannot be read or holds rules other than the ledger's schema.** A
  repo that was not read would make "0 violations" a false pass.
- **Cross-repo suspects are reported, labelled *current reach only · not pinned*.** Whether a
  cross-repo dependant was edited is unknown until pins exist.
- **Requirements:** REQ-QMT-17 (the check, with suspects) and REQ-QMT-18 (the walks), both
  under CR-001 in `qmstrace-ledger`, which the developer accepts. Design element DSN-QMT-14.
- **Acceptance:** on the new test bed `<workspace>/_tests/beacon-split/`, cloned from
  `beacon-engine` and never pushed back. The measures are fixed in
  [beacon-split](../tests/beacon-split.md) before the run.

**Checklist:**
- [x] CR-001 drafted as `evaluated` in `qmstrace-ledger`
- [x] CR-001 accepted by the developer — `qmstrace-ledger` `bff7b99`
- [x] **M10·0**, [#27](https://github.com/Lightbridge-KS/qmstrace/pull/27) · `e39856a`:
  - the fixture `tests/fixtures/split/`, in the ADR layout, with a colliding derived ID;
  - `ledger copy-schema` skips `"."`, and says how to undo a copy an older run wrote there.
- [x] **M10a**, [#28](https://github.com/Lightbridge-KS/qmstrace/pull/28) · `fa75a33`:
  - `ledger check [--strict] [--quiet]`: the union, coverage across repos, per-repo violations,
    refusals and cross-repo suspects;
  - the fix text;
  - REQ-QMT-17 and DSN-QMT-14;
  - the docs the ADR lists;
  - the manual: the `ledger check` reference, `how-to/check-the-project.md`, and *Around the
    repo* rewritten.
- [x] **M10b**, [#29](https://github.com/Lightbridge-KS/qmstrace/pull/29) · `b6ad49d`:
  `ledger thread` and `ledger impact` across repos, and REQ-QMT-18.
- [x] Acceptance on beacon-split, M10a: A1–A9 and A11–A13 pass, run 2026-09-28 — [results](../tests/beacon-split.md#results)
- [x] Acceptance A10 on the M10b engine — [results](../tests/beacon-split.md#results)
- [x] **Decided 2026-09-29** (ask record *Two loose ends from M10*):
  - a gap's next move keeps naming the repos that declare the type, in the older layout too;
  - `init` in a ledger is fixed now, as M10c, before M11.
- [x] CR-002 drafted, then accepted by the developer — `qmstrace-ledger` `4af8f28`
- [x] **M10c**, [#31](https://github.com/Lightbridge-KS/qmstrace/pull/31) · `d9b86d0`, closing [#30](https://github.com/Lightbridge-KS/qmstrace/issues/30):
  - `init` in a ledger: its own `qmstrace.toml` when it has none, and a stanza naming the
    ledger's verbs;
  - REQ-QMT-19; DSN-QMT-11 amended.
- [x] **Guidance fix**, `94fd827`: the packaged stanza and skill require mutation checks in
  a disposable copy, never the working checkout; parity is pinned by a meta-test.

## After — M11 · mentions

Every token with a configured prefix in a scanned file (prose, table or Mermaid) must exist; a
dangling one is a violation, like V03. Only configured prefixes count, since `SHA-256`, `UTF-8`
and `ADR-0001` all fit the bare ID shape.

## Cancelled — E6 · dogfooding

E6 would have measured PRD success criteria 5 and 6 by having fresh agents work in qmstrace
traced by its own ledger. It was **cancelled on 2026-09-28 after run A**, in favour of
real-world use.
- Run A's work is kept (#24 and the baseline, below).
- Run B (STOPs 8–10) and Phase 9 (results, findings, merge) are cancelled.
- Run A's results were never written up. The protocol, the measures and the E6 tracker stay on
  the unmerged branch `experiment/e6-measures`; the driver's notes are in
  `<workspace>/_tests/qmstrace-e6/`. Its findings are under [Open](#open-from-landed-work).
- The branch stays unmerged, as the record; it is not deleted. Its remote ref was verified
  on 2026-10-13 at `9f97490`; there is no local branch in this checkout.

## Landed

| Milestones | Delivered | Merged |
|---|---|---|
| M0–M4 | Design and blueprint; scaffold and dry gate; configuration, scanning, `status`, manual, `thread`, `check`, `rules`, `impact`, JUnit results | #1–#3, #5–#10 |
| M5a–M5b | Historical baselines, request citations, withdrawal, suspects | #11–#12 |
| M6–M8 | Engine-native test bed, offline browser, Diátaxis pages, slice closure; hover and UAT fixes | #13–#15 |
| M9, M9b | Rich Markdown; `ledger copy-schema` | #17, #18 |
| Self-trace | Product repo of project `QMT` with ledger `qmstrace-ledger` (`a3faeab`); constraint now *no other project's data* | #19 · `63b5c7f` |
| M9c | Skill at `.agents/skills/qmstrace/`; create-only `.claude/skills/` link | #23 · `02caed1` |
| Gate green | E6 run A: 16 requirements ([SRS](../req/qmstrace-srs.md)), 13 design elements ([blueprint § 11](../structure/codebase-blueprint.md#11-design-elements--what-the-code-is-traced-to)), 26 modules, 83 tests | #24 · `9dbe29f` |
| Baseline | `baseline/requirements/1` on `9dbe29f`: 16 frozen; `check --strict` exits 0 | tag |
| M10 | The project-wide check: `ledger check`, `thread`, `impact` across repos; `copy-schema` skips the ledger; `init` in a ledger. REQ-QMT-17…19 under CR-001 and CR-002 | #27, #28, #29, #31 · `d9b86d0` |

**Decided at the baseline:** CI does not run `check --strict` yet. Tags keep the form
`baseline/requirements/<n>` until qmstrace cuts releases.

Each milestone's merge SHA, decisions and evidence are archived:
[M5a–M9c](../archive/progress/landed-m5a-m9c.md), [slice 1 through
M5a](../archive/progress/slice-1-product-repo-half.md), and the
[exploration](../archive/progress/overview-qmstrace.md). E1, E3 and E4 are complete; their
methods are in the [experiment record](../tests/beacon-authoring-experiment.md).

## Open from landed work

- **Not verified:** the M9 how-to page as deployed; the local browser opened from a file; the
  manual's production deployment since M5a; `init` without symbolic links; whether Claude Code
  and Codex load `AGENTS.md` and skills from a folder added to a session (ADR-0001).
- **Filed:**
  - #16 `init` should replace an unedited earlier skill copy. The issue's text still names the
    skill's old home.
  - #20 files `init` creates are `0600`.
  - #21 rollback leaves folders behind.
  - #22 `ux`: no symbolic links.
  - #25 an `id_pattern` with alternatives lets a slip in its second family pass silently.
  - #26 `ux`: an ID without its subject key passes until the first baseline, then stops
    every run.
  - [agent-stuff#71](https://github.com/Lightbridge-KS/agent-stuff/issues/71).
- **Not filed, from run A:**
  - `check` repeats G06's fix once per module.
  - `results` prints about 42 KB and names no report location.
- **Not filed, engine:**
  - Recognise the same repo by its Git common dir.
  - Stale comments in the beacon test bed's configurations.
- **Ledger side:**
  - `change-requests/README.md` omits "to a controlled scope".
  - REQ-QMT-06, 08 and 16 cite only AGR-1; they were frozen that way knowingly. REQ-08 needs
    a change-control clause, which now takes a change request.

## Slice-1 acceptance

Met, except the local browser opened from a file
([evidence](../archive/progress/landed-m5a-m9c.md#slice-1-acceptance--the-checks-and-their-evidence)).
Still binding: every command has a golden, every finding code an emitting fixture, and none of
the stand-in's defects returns ([scenario catalogue](../tests/scenario-catalogue.md)).

## Deferred

- **Slice 2, the ledger.**
  - Design: event shape, states for non-document work products, the signature loop, the
    recorded inspection basis, cross-repo questions.
  - Persistence: the AST digest format, derived-ID renames, an accepted-request index. See the
    [PRD open questions](../req/qmstrace-prd.md#open-questions) and D7/D9.
- **After M10:**
  - pins: `ledger import NAME@PIN`, the trace lock, and the edit state of cross-repo
    dependants;
  - `ledger status`, `ledger results` and `ledger graph`;
  - a product repo's CI checking out the ledger beside it;
  - moving documents that are already baselined from one repo to another;
  - the remaining "judged at the ledger's import" phrases;
  - moving qmstrace's own SRS into `qmstrace-ledger` (open in ADR-0001).
- **E5:** an audit demo, once the engine has a ledger.
- **Later:**
  - Output: machine-readable output; a conformance view.
  - Suspects and evidence: clearing a suspect by recorded review; collectors.
  - Browser: a project-wide browser at pins; the
    [browser extensions](../design/trace-browser.md#evidence-and-scope).
  - Other: a second profile; E2 option C; validating the commit references in this tracker.
- **`VISION.md`:** waits until use supports durable invariants.

## Landed — developer commit hooks

Added 2026-10-13: local commit hooks run Ruff lint with safe fixes, Ruff formatting,
whitespace and final-newline fixes, YAML/TOML syntax checks, merge-conflict checks and a
redacted Gitleaks scan of staged changes. Python hook tools use the locked development
dependencies; Gitleaks is an external prerequisite. Fixtures and golden output are protected
from whitespace fixes. Types, tests, wheel checks and the manual build stay in the dry gate.

Verification: the configuration validates and the hooks pass on the staged tooling files.
In a disposable copy containing only the tooling changes, `just dry` passes: 794 Python
tests, four browser tests, types, wheel validation and the manual build. A staged synthetic
secret is rejected with redacted output; Ruff preserves an intentionally invalid fixture.
A repository-wide run in a disposable copy found pre-existing extra final newlines in
`docs/tests/scenario-catalogue.md`, `docs/structure/codebase-blueprint.md`,
`docs/req/qmstrace-srs.md` and `contents/reference/commands/init.md`; those files were not
changed by this tooling work.

## Standing design

For contracts, read the design docs, not this tracker:
- [glossary](../../CONTEXT.md)
- [PRD](../req/qmstrace-prd.md)
- [data](../design/data-architecture.md)
- [surface](../design/surface-architecture.md)
- [system](../design/system-architecture.md)
- [blueprint](../structure/codebase-blueprint.md)
- [trace browser](../design/trace-browser.md)
- [scenario catalogue](../tests/scenario-catalogue.md)
