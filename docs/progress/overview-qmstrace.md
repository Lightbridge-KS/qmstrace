---
summary: The single active qmstrace tracker — terminal and JSON output merged as PR 71. The v0.2.0 release-refresh candidate is prepared and verified; maintainer merge and authorized rebuilding remain before publication. The unpublished tag/draft still predate this feature. External-source issue 60 and M11 remain later.
read_when:
  - starting a session in this repo — read this first
  - planning or finishing a milestone, or checking whether slice 1 is done
  - deciding what is next or which verification remains
---

# qmstrace — progress

**Updated 2026-10-24 · Release 0.1.1, the V14 fix, published. Slice 1, the product-repo half: landed. M10, the project-wide check:
landed. [Package refactors](#landed--package-refactors) and [M12 · the C#
capability](#landed--m12--the-c-capability): landed.** Now: [real-world use](#now--real-world-use)
on a C# repo, in the layout of ADR-0001. [#49 · tables as data](#landed--49--tables-as-data)
landed; the authoring-integrity fix for #25 and #26 merged as PR #67. Issue #57 merged as PR #68 (`03d0719`). Workspace maps merged as PR #69 (`8223d32`).
PR #70 merged (`48e5ba1`); `v0.2.0` is tagged and its release draft awaits maintainer review
and publication. Terminal/JSON output merged as PR #71 (`5453de2`); the existing draft
predates that feature and must be rebuilt before publication. M11 · mentions remains later. Commit hashes locate work. Verification claims refer to checks
that were actually run.

## Landed — terminal and JSON output

**Merged as [PR #71](https://github.com/Lightbridge-KS/qmstrace/pull/71)
(`5453de2`, 2026-10-24; implementation `09029ec`, skill clarification `f65b293`).**
Two sequential slices on `codex/cli-output`: semantic terminal styling with plain-byte
parity, then explicit `qmstrace.cli/1` results and agent guidance.
[ADR-0011](../adr/0011-cli-presentation-and-json.md) records the presentation and machine
contract. Existing release reconciliation is retained; the `v0.2.0` tag and draft release
are unchanged. The current draft predates this feature; rebuilding it requires updated
release notes, candidate verification and separate release authorization.

- [x] Ship and verify terminal styling, conditional Rich help and the output-mode reference.
- [x] Ship command JSON, parser/domain/internal errors, schema and command goldens.
- [x] Update the bundled and installed skill, Diátaxis pages, design and scenarios.
- [x] Inspect built pages/package assets; pass dry and local/ledger strict checks.

Slice 1 verified all **227 existing CLI tests** with unchanged plain behavior goldens;
**17 terminal tests** then verified ANSI-stripped parity, selection policy, repeated help
calls, literal brackets/Unicode and a real PTY before slice 2 began. The output-mode manual
page built successfully and was inspected. Final terminal coverage adds long titles,
report verdict colors, narrow help and actual forced-color redirected stdout/stderr.
An installed-console probe caught Typer stripping forced ANSI; explicit stream color
selection fixed it and subprocess regressions pin that behavior.

Slice 2 retains existing judgment and exits, including failed tests under informational
exit zero, full quiet findings and whole-request rejection of unseen impact starts.
JSON goldens cover every supported local/project command, all error categories and baseline
withdrawal/suspect evidence. The packaged/published schema validates all of them; existing
behavior-output and table JSON goldens are unchanged. Only **15 existing help goldens**
add the flag, including explicit refusal guidance for writing commands. An option-aware
prepass respects values and `--`; a regression prevents positional parameter names from
being mistaken for options. Tests exercise the bundled agent commands, maps, sibling TRX
case paths, verification methods, unavailable sources, projection failures and one assessment
per invocation. The installed skill is synchronized with its packaged source; init's
existing refusal policy remains unchanged.

Review follow-up: both skill copies explain the example requirement IDs (`REQ-SVC-01`
and `REQ-SVC-02`), their prefix/subject/item parts and substitution with declared project IDs.

**Final verification, 2026-10-24:** `just dry` passed **1,470 Python tests, 4 browser tests,
98.45% coverage**, formatting, lint, strict mypy, wheel checks and the strict manual build.
Wheel verification exercises **37 import orders**, packaged skill/schema assets and
installed behavior outside the source checkout, including JSON and a fresh console process.
Local and ledger strict checks both exit zero: **869 items, 0 violations, 0 gaps and 32
informational suspects**; **16 frozen, 3 changed, 7 new, 0 removed**. Remote-tag completeness
remains unverified. Frozen SRS and trace configuration bytes are unchanged.

The built JSON reference and agent how-to were inspected in a browser. The two rendered JSON
snippets equal their goldens, the schema download returns HTTP 200 and matches the package,
and four rendered shell blocks preserve their source. The CI gate example runs unchanged
under `bash -eu` on a disposable MINI project and preserves exit one with complete JSON.
Six installed-console assessment commands also complete there; report interpretation uses
the existing synthetic JUnit fixture, not a newly executed consumer test suite.

Two disposable-copy mutations prove detection: disabling semantic styles fails **7** tagged
parity cases; disabling JSON selection fails **10** command cases. Imported paths were checked
inside each copy, which was then deleted. Local playground notes retain logs and manual
inspection evidence. No consumer repository was modified. Local implementation and verification are complete;
PR review and merge are complete. The [PR dry gate](https://github.com/Lightbridge-KS/qmstrace/actions/runs/40064762632)
and deploy preview passed. Reconciled 2026-10-24: local `main` and `origin/main` point to
`5453de2`, which contains both feature commits; the local milestone branch and stale remote
reference were pruned. [Merge CI](https://github.com/Lightbridge-KS/qmstrace/actions/runs/40064927564)
passed. Release rebuilding and publication remain separate gates.

## Landed — workspace maps

**Merged as [PR #69](https://github.com/Lightbridge-KS/qmstrace/pull/69)
(`8223d32`, 2026-10-24; implementation `3ac0437`).** Per-machine checkout maps preserve
schema formats, digests and historical reads. Consumer rollout remains separate.

- [x] Add strict map parsing and shared location resolution, preserving tracked-path fallback.
- [x] Wire explicit/environment/ancestor/user discovery into reads and transactional copies.
- [x] Add the paths diagnostic, CLI options, provenance and focused regression coverage.
- [x] Ship ADR-0010, design/ownership/scenario updates and Diátaxis manual pages.
- [x] Inspect goldens and rendered manual; run dry and both strict trace gates.

Accepted discovery: CLI, environment, nearest ancestor map, then a unique user-level match
by project and canonical current checkout. Malformed user candidates fail discovery; maps
never merge or replace tagged configuration. Relative locations remain the output contract;
cross-drive layouts are refused. Implementation and PR review are complete; release and
consumer rollout remain separate gates.

Verified during development: **142 focused workspace-map tests** passed, followed by **107
setup, CLI-map and workspace-dispatch tests** after adding init provenance coverage.
Acceptance includes a Unicode Git worktree, two relocated layouts with equal logical
graphs and schema/configuration bytes, report matching, transactional schema copies,
historical-schema isolation and deterministic output. Disabling discovery in a disposable
copy made the nested relocated-ledger test fail on the obsolete tracked defaults; the copy
was removed. The local playground session retains that mutation evidence.

Final local and ledger `check --strict --quiet` both exit 0: **829 items, 0 violations,
0 gaps and 32 informational suspects**, with 16 frozen, 3 changed, 7 new and 0 removed.
Remote-tag completeness remains unverified. Consumer rollout and the actual user profile
remain separate; this change does not migrate consumer repositories. The frozen SRS,
dependency manifest/lockfile and trace configuration are unchanged. Existing behavior-output
goldens are unchanged; the 14 existing help goldens add the workspace option and command.

Verification recorded for PR #69: `just dry` passed **1,385 Python tests, 4 browser tests, 98.46% coverage**,
formatting, lint, strict mypy, isolated wheel/package checks and the manual build. The
built paths reference, map reference and developer/CI how-to were inspected: four included
goldens match exactly, all 16 rendered code blocks are intact, and CI heredoc boundaries
and cleanup survive rendering. The final review found no remaining concrete defects.
Accepted limits remain: no cross-drive layout support, schema-format migration, tracked
member-identity field, or consumer rollout in this increment.

Reconciled 2026-10-24: GitHub confirms the merge; the PR dry gate and deploy preview
passed. [CI on the merge commit](https://github.com/Lightbridge-KS/qmstrace/actions/runs/40049553446)
also passed. Local `main` and `origin/main` point to `8223d32`; the merged implementation
commit is an ancestor. The local milestone branch was deleted. Release 0.1.1 remains the
latest published release; merge is not publication or consumer installation.

## Landed — #57 · verification-method grouping

**Merged as PR #68 (`03d0719`, 2026-10-23).** [ADR-0009](../adr/0009-group-verification-by-applicable-rules.md)
records the accepted display contract. `status` and `results` classify a requirement as
test-backed only when a valid declared method meets an applicable incoming-`verifies` coverage
rule; linked outcomes remain test evidence for all methods. The versioned `ledger table`
format, gap judgment, verdict aggregation and exits remain unchanged.

- [x] Share rule applicability with coverage and classify local and sibling requirements.
- [x] Add demonstration, missing/invalid method, test-case path and configurable-rule tests.
- [x] Review all affected goldens and built manual pages.
- [x] Run the full dry gate and local/ledger strict checks; record measured outcomes.

Verification recorded for PR #68: 74 focused CLI/judgment/architecture/table tests passed before
the final CLI assertions; the final `just dry` passed **1,233 Python tests, 4 browser tests,
98.51% coverage**, formatting, lint, mypy, wheel/package checks and strict manual build.
The generated status and results code blocks show the demonstration requirement apart with
its declared method and passing linked test labelled as evidence. Local and ledger
`check --strict --quiet` both exited 0 with **757 items, 0 violations, 0 gaps and 32
informational suspects**; 16 frozen, 3 changed, 7 new and 0 removed. Remote-tag completeness
remains unverified.

## Landed — #25 and #26 · ID authoring integrity

**Merged as PR #67 (`a5947a0`, 2026-10-23).** The existing tracker
reconciliation was carried from `main`. [ADR-0008](../adr/0008-prove-id-starts-and-subject-ownership-before-baselines.md)
records the accepted contract: an `id_prefix` must fit a provable shared start across every
pattern branch; V17 reports controlled document IDs without one subject while authoring.
Under an applicable baseline, ownership uncertainty still stops judgment (exit 2), with
tag-specific recovery when the selected snapshot is at fault.

- [x] Prove common starts for grouped alternatives and escaped literals; reject a mismatched
  explicit prefix before scanning. Keep the existing V02 path for malformed headings.
- [x] Add pure ownership judgment for local and ledger assessments, V17 in the catalogue,
  and tag-aware refusals for current and historical evidence.
- [x] Add focused regressions, CLI goldens, ADR, design/scenario updates and Diátaxis manual
  updates; inspect the rendered V17 snippets.
- [x] Complete the full dry gate and both strict trace checks; record the measured results.

Verification on this branch: 192 focused configuration, ownership, baseline, CLI and catalogue
tests passed. Both newly tagged behavioral tests failed when their respective guard was
disabled in a disposable copy; the copy was removed and the evidence is in the local
`_playground/2026-10-23_id-authoring-integrity/` session. The first `just dry` run reached
1,222 passing Python tests and 98.50% coverage but identified two architecture-test inventories
that needed the new `_prefix` owner and judge export; both were updated. The final `just dry`
passed: **1,224 Python tests, 4 browser tests, 98.53% coverage**, formatting, lint, mypy,
wheel/package checks and strict manual build. The built V17 code blocks were inspected.
Final review also covered a subject-key change in today's configuration for an existing
frozen item (exit 2) and a repeated key segment in one ID (V17); 51 focused tests passed.
Local and ledger `check --strict --quiet` both exit 0: **752 items, 0 violations, 0 gaps,
32 informational suspects**, with 16 frozen, 3 changed, 7 new and 0 removed. Remote-tag
completeness remains unverified, as before. These measurements were made on the PR branch.

## Landed — package refactors

The accumulated refactors on `codex/config-package` merged as #32 (`75ba627`, 2026-10-13).
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

## Now — real-world use

qmstrace is applied to real development in the developer's own workflow, and reshaped by what
that use finds. Findings become issues, and changes to settled design go through the design docs.
The first real project is a C# repo, chosen 2026-10-15.

**Release 0.1.0** — the engine the project installs, pinned by a tag
([releasing](../dev/releasing.md)):
- [x] CHANGELOG section, install pages in the README and the manual, the release workflow and
  its runbook — #44 (`80eef1d`).
- [x] The MIT License — #45 (`b88e79a`). The first `v0.1.0` tag, on `80eef1d`, was never
  published; it was re-cut after #45 and #46 merged, so the first release carries the license
  and #46's article fix.
- [x] `v0.1.0`, annotated, on `0ff740e`; the workflow drafted the release with the wheel, and it
  was published 2026-10-15. Installed here from the tag as a uv tool, both trace gates pass
  with the installed binary: 657 items, 0 violations, 0 gaps.
- [x] `main` moves on to `0.2.0.dev0`, with `uv lock`.

**Release 0.1.1** — #48's V14 fix, for the first C# adopter, cut from `main` as the runbook's
patch path says. Nothing else on `main` since `v0.1.0` changes what ships. The packaged skill
and setup are unchanged since `v0.1.0` (`git diff --stat v0.1.0..HEAD -- src/qmstrace/assets
src/qmstrace/core/setup` is empty), so `init` after the upgrade changes nothing:
- [x] Version `0.1.1`, its CHANGELOG section, the install pins in the README and the manual,
  and the runbook's patch path — #51 (`91f7b37`).
- [x] `v0.1.1`, annotated, on `91f7b37`; the workflow drafted the release with the wheel, and it
  was published 2026-10-15. Installed here from the tag as a uv tool, both trace gates pass
  with the installed binary: 657 items, 0 violations, 0 gaps. `init` with it in this repo
  reports every file unchanged.
- [x] `main` moves back to `0.2.0.dev0`, with `uv lock`.

### Next — release 0.2.0 (refresh verified; maintainer merge pending)

**Initial readiness checked 2026-10-24 on `8223d32`.** At that snapshot the manifest and
lockfile named `0.2.0.dev0`; GitHub listed only published 0.1.0 and 0.1.1, with no draft
release, and `v0.2.0` did not exist locally or on GitHub. The merge CI was green. The
[release workflow](../../.github/workflows/release.yml) still gates a pushed version tag,
checks it against the manifest, extracts CHANGELOG notes and drafts a GitHub release with
the wheel. The [release runbook](../dev/releasing.md) keeps publication with a maintainer;
no package-index publication is configured.

**Accepted version and scope: 0.2.0, shipping the merged work since 0.1.1.** This includes
schema-driven ledger tables and report verdicts, several reports per results view,
language-aware starters, C# markers for files without a type, ID-authoring integrity,
verification-method grouping and workspace maps. The stricter configuration refusals and
new V17 finding need explicit upgrade notes. The initial release-prep scope is complete.
Terminal/JSON output is now merged as PR #71 and must be included in a rebuilt draft before
publication; its entries are now in the existing 0.2.0 changelog section on the refresh branch.
The manifest and lockfile already name `0.2.0`; another version bump is unnecessary for this
unpublished candidate.

- [x] Prepare release changes on `codex/release-0.2.0`; include the tracker reconciliation.
- [x] Audit `v0.1.1..main` against the CHANGELOG. Consolidate its duplicate `Added`
  headings; add the missing #67, #68 and #69 entries and workspace-preserving skill
  migration guidance. State schema/history, no-map and cross-drive boundaries.
- [x] Set `pyproject.toml` to `0.2.0`, run `uv lock`, date the release section when it is
  prepared, retain an empty `Unreleased` section and update comparison links. Update the
  current install pins in `README.md` and `contents/how-to/set-up-a-repo.md`, without
  rewriting historical release records.
- [x] Run `just dry`, local and ledger strict trace gates, and inspect the built manual.
  Smoke-test the built wheel outside the source checkout: version/help, paths with and
  without a map, relocated local/ledger reads and setup preserving a local map. Use
  disposable fixtures; record evidence limits and informational suspects.
- [x] Review and merge the release PR; require successful CI on its merge commit.
- [x] With release authorization, create and push an annotated `v0.2.0` tag on that exact
  merge commit. A release tag is not a requirements baseline; do not create or move one.
- [x] Let CI gate the tag and draft the GitHub release; verify tag/manifest/wheel metadata,
  release notes and a clean tag installation.
- [x] Review and merge the terminal/JSON feature as PR #71; verify its PR dry gate and preview.
- [x] Prepare release-refresh changes on `codex/release-0.2.0-refresh`: carry this tracker
  reconciliation, move terminal/JSON notes into the existing 0.2.0 `Added` section,
  leave `Unreleased` empty and audit the full
  candidate scope. Keep manifest/lock at `0.2.0` and existing install pins; retain upgrade
  guidance for ID checks and workspace maps and describe the new agent/output contracts.
- [x] Verify the refreshed candidate with `just dry`, local/ledger strict checks, manual
  inspection and an isolated wheel installation. Exercise plain/forced-color/JSON output,
  nonzero JSON errors, unchanged table JSON and packaged skill/schema assets.
- [ ] Review/merge the release-refresh PR; require successful CI on that exact merge commit.
- [ ] With explicit rebuild authorization, recheck that v0.2.0 is still unpublished, remove
  the obsolete draft and local/remote release tag, and create/push an annotated `v0.2.0`
  at the verified refresh merge commit. Never move a published release tag or a baseline.
  The existing workflow creates a draft rather than replacing one, so the old draft must
  be removed before the tag push triggers it.
- [ ] Let release CI gate the new tag and create the replacement draft. Verify its commit,
  manifest/wheel version, CHANGELOG notes and asset checksum; smoke-test the downloaded CI
  wheel and a clean tag installation, including JSON and bundled skill/schema assets.
- [ ] Maintainer review and publication of the rebuilt draft release.
- [ ] After publication, move `main` to `0.3.0.dev0` with `uv lock` in a follow-up PR;
  reconcile this checklist with the actual release/tag and verification results.
- [ ] Plan consumer upgrades and workspace-profile rollout separately. Preserve existing
  configurations, inspect stricter ID checks and skill migration before adopting maps.

**Candidate verification, 2026-10-24:** `just dry` passes **1,385 Python tests, 4 browser
tests and 98.46% coverage**, formatting, lint, strict mypy, isolated wheel checks and the
manual build. Local and ledger `check --strict --quiet` both exit 0 with **829 items,
0 violations, 0 gaps and 32 informational suspects**; remote-tag completeness remains
unverified. The dependency set is unchanged; only the project's version changed in the
lockfile. The release workflow's notes extraction yields one nonempty 0.2.0 section with
unique Added/Changed/Fixed headings; published changelog history is unchanged.

An isolated temporary environment installed the wheel with hashed runtime dependencies
from the lockfile. All 30 recorded commands completed with their expected exits, covering
import origin, version/help, tracked/default paths, relocated local and ledger strict
checks, table JSON, report matching, schema-copy byte preservation, setup preserving a
local map, idempotent setup, C# starter assets and partial-map refusal without writes.
The synthetic report checks matching, not execution of consumer tests. The sandbox was
removed; local evidence remains in the ignored release playground session. The final
candidate wheel is byte-identical to the smoke-tested one. The built installation example pins
0.2.0, and four workspace-map golden code blocks match their rendered pages.

**Tag and draft verified, 2026-10-24:** [PR #70](https://github.com/Lightbridge-KS/qmstrace/pull/70)
merged at `48e5ba1` (candidate `c20bbe5`). [Merge CI](https://github.com/Lightbridge-KS/qmstrace/actions/runs/40053553159)
passed before the annotated `v0.2.0` tag was pushed at that exact commit. The local release
branch and its stale remote reference were pruned. [Release CI](https://github.com/Lightbridge-KS/qmstrace/actions/runs/40053692403)
passed both the dry gate and draft job. The
[GitHub draft](https://github.com/Lightbridge-KS/qmstrace/releases/tag/untagged-baa345e531ea67637793)
is unpublished; its notes match the 0.2.0 CHANGELOG section and its attached wheel declares
version 0.2.0. The downloaded asset checksum matches GitHub's recorded SHA-256; all 95
package files match the candidate wheel. Build-tool metadata differs between local and CI
archives. The actual downloaded CI wheel also passes all 30 smoke commands in an isolated
temporary environment. A separate clean Git-tag installation resolves `v0.2.0` to
`48e5ba1` and reports `qmstrace 0.2.0`. Both temporary environments were removed.

**Reconciled after PR #71, 2026-10-24:** GitHub still reports v0.2.0 as an unpublished draft.
Both local and remote annotated tags resolve to `48e5ba1`, preceding `5453de2`; the draft's
wheel remains the earlier candidate. Its existing asset checksum is
`5527f5911d0b9dbb4288103985d9d25eda1e4eb7aaeb53ceeba189f118d5c8a0`.
Neither tag nor draft was changed during this reconciliation. Earlier installation and
asset verification above applies to that old candidate, not the merged terminal/JSON feature.

**Release refresh verified, 2026-10-24:** on `codex/release-0.2.0-refresh`, terminal/JSON
entries are included under 0.2.0, `Unreleased` is empty and the release workflow's exact
notes extraction includes them. Published changelog history, manifest/lock version 0.2.0,
install pins, runtime code, trace configuration, frozen SRS and release workflow are unchanged.
The runbook no longer describes the now-public repository as private and documents the
unpublished-candidate refresh sequence.

`just dry` passed **1,470 Python tests, 4 browser tests and 98.45% coverage**, formatting,
lint, strict mypy, isolated wheel checks across 37 import orders and the strict manual build.
Both local and ledger strict checks exit 0: **869 items, 0 violations, 0 gaps and 32
informational suspects**; **16 frozen, 3 changed, 7 new, 0 removed, 0 withdrawn**. Remote-tag
completeness remains unverified; these checks do not record suspect review.

An isolated installation of the refreshed wheel passed **56 recorded subprocess commands**
outside the source checkout, using hashed locked runtime dependencies, a fresh home and
disposable split/MINI repositories. Checks include relocated workspace maps, transactional
schema copies and init preservation, plain/forced-color parity, schema-valid assessment JSON,
usage/unseen-ID exit 2, failed-check exit 1, complete quiet JSON, unchanged table bytes and
packaged skill/schema parity. The temporary environment and fixture roots were removed.
Synthetic reports establish matching behavior, not newly executed consumer tests.

Built JSON and agent/CI pages were inspected in the browser. Two rendered JSON goldens and
four rendered shell blocks match their sources; the schema download returns HTTP 200 and
matches the packaged bytes, and the install example still pins v0.2.0. Local logs and
summaries remain in the ignored release-refresh playground. The existing tag/draft is
untouched. Candidate preparation stops for maintainer review and merge at release step 3;
hosted checks for the refresh PR and its eventual merge remain distinct from local checks.

**Pending:** maintainer merge of the release-refresh PR, separately authorized tag/draft
rebuilding, maintainer publication, the post-publication development-version PR and consumer
rollout. Nothing was published by this step; `main` remains at version 0.2.0.
The release workflow is unchanged. Issue #60, M11, cross-drive traversal and the
schema/member-identity migration remain outside this release-preparation scope.

**Target layout — [ADR-0001](../adr/0001-the-ledger-holds-the-documents.md), 2026-09-28:**
- **The ledger repo holds the documents:** the SRS and the design documents, beside the
  agreement, the change requests and the schema. It is traced itself, and lists itself in
  `[repos]` as `"."`.
- **Product repos hold code and tests.** Their markers cite the ledger's IDs.

M10 supports this layout through `ledger check`, `ledger thread` and `ledger impact` over
working trees. The ADR's failed checks describe the pre-M10 probe, not the current engine.
Pinned imports and historical cross-repo edit comparisons remain deferred.

**Next onboarding steps:**

1. Choose a project — a C# repo — its ledger and product repos, and one small feature to
   trace end to end.
2. Install the latest release as a uv tool, as the README says; confirm `qmstrace --version` and
   that `ledger --help` lists `check`, `thread` and `impact` before onboarding with it.
3. Settle subjects and ID patterns before authoring and before the first baseline. The
   guards for #25 and #26 merged in #67 and are included in the prepared 0.2.0 release;
   published 0.1.1 does not yet include them. Audit older IDs and tagged evidence before
   adopting the stricter checks; historical invalid ownership still needs a valid successor
   baseline rather than rewriting a tag.
4. Set up the ledger and code/test repos, then trace the feature and run the project gate.
   Product `init` still generates a repo-owned starter; joining an existing ledger needs
   configuration edits followed by `ledger copy-schema`. See the
   [project how-to](../../contents/how-to/check-the-project.md). In a C# repo, `init` writes the
   C# starter and no `pytest.ini` (#38, ADR-0006): it recognises a .NET repo by its solution or
   project file and says which starter it chose. See
   [*Trace a C# repo*](../../contents/how-to/trace-a-csharp-repo.md).
5. Record observed friction as issues; choose fixes from that evidence before expanding to
   M11. Baseline only after the IDs, trace and review are ready.

**Fixed from use:**
- [x] 2026-10-21, seen in the first C# project's design register (#64): a component's marker was
  read only from the leading `///` doc comment of a `.cs` file's first type, and a Blazor
  `.razor` page has no such type — one design element named only an Admin Razor page and stayed
  uncovered permanently, three more named a Razor component or a `Program.cs` of top-level
  statements beside C# classes and closed through the classes while the register's other named
  components dropped out with nothing said. Probing the engine first showed the two shapes are
  different problems: on a top-level `.cs` the marker was already read and then discarded as a
  stray, while in a `.razor` it was invisible — and routing such a file through the C# parse is
  unsafe, since a `///` field line inside an error span makes the whole file V08, so where the
  markup sits decides whether the file is read. A file with no type is now marked in its own
  leading comment: a Razor page in the first `@* … *@` of its head, read by line and never by
  the parser; a file of top-level statements in the block it opens with. A file that has a type
  is untouched, so nothing that linked links differently. No new requirement and no
  configuration change — REQ-QMT-21 amended under CR-006, DSN-QMT-15 retitled, decided in
  ADR-0007.
- [x] 2026-10-21, the deferral ADR-0004 filed and CR-003 excluded, now paid for by the first C#
  project (#38): `init` in a repo with no configuration wrote the Python starter, so a C# repo
  read as traced while declaring nothing, and the manual's C# how-to had to tell readers to
  rewrite `[items]` and delete a `pytest.ini`. The starter now declares the item types of the
  language the repo's build files name — a .NET solution or project file at or just below the
  root means C#, `pyproject.toml` or nothing means Python — and the run's first line names the
  starter and the file that chose it. A repo holding both is refused until `--language` says
  which. One asset: `starter.toml` plus an `items-<language>.toml` tail, so the schema is not
  duplicated. No new requirement — REQ-QMT-12 amended under CR-005, decided in ADR-0006. The
  pytest marker needed no rule: it was already registered only where an item type reads pytest
  tests.
- [x] 2026-10-16, seen while a project was designed with one agreement per engagement (#55,
  #56): two `[externals.*]` tables with the prefix `AC-` routed every `AC-` citation to the first
  table's file, so a clause declared in the second drew a `V09` naming the wrong file — whose
  next move invited a duplicate clause; and a `source` of `*/agreement.md` read as a file not
  checked out here, leaving the family *not verified* without a word. Both are now refused when
  the schema is read: overlapping prefixes (equal, or one starting the other) and a `source`
  holding `*`, `?` or `[`. #56's second item — a `source` naming several files, their IDs
  pooled — is #60. Removing either refusal in a disposable copy fails its four tests.
- [x] 2026-10-15, seen in the first C# adopter's tests (#50): a `DisplayName` whose ID is
  followed directly by a suffix — `TC-…-01/O03`, an observation number — was `V14` and linked
  nothing, because the first whole word had to be an ID. The leading ID now ends at the
  boundary prose uses (`ID_IN_TEXT`), so prose and `DisplayName` read the same words alike;
  a commented-out test follows the same rule. The packaged skill is unchanged, so `init`
  after an upgrade still changes nothing (#16). A parametrised test pins the issue's table;
  restoring the whole-word rule in a disposable copy fails its five suffix rows and the stray.
- [x] 2026-10-15, seen while the first C# adopter's ledger was designed: `V14` on an xUnit
  `DisplayName` or a pytest marker named a field line neither has — *the 'verifies' line holds
  IDs only, comma-separated*. A C# agent goes looking for that line, and in pytest, two IDs in
  one argument is the very slip that raises `V14`. Each extractor now gives its own next move;
  Markdown's is unchanged. A test per extractor, each failing when its fix is reverted.
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

## Landed — #49 · tables as data

The PRD's P0 *emit tables as data for the existing render machine* is implemented. Issue #49
closed 2026-10-23 after #58 (the three JSON tables), #62 (report-backed verdict columns) and
#63 (review follow-ups) merged; #59 delivered its #40 prerequisite, several reports in one run.
The first C# adopter's original record was a hand-typed matrix whose result columns were empty.
**Not yet verified:** a render layer consuming the JSON or a pilot traceability record rendered
with zero hand-typed IDs (PRD success criterion 2).

**Decided 2026-10-15** by the developer, every recommendation taken (the design prep, a probe
of today's model on the `cases` fixture and the record of the answers are in a local
playground session, `2026-10-15_issue-49-design`):

| # | Decision | Chosen |
|---|---|---|
| 1 | Command | One ledger verb, the table named: `qmstrace ledger table matrix \| requirements \| coverage` |
| 2 | Format | Versioned JSON, `qmstrace.table/1`: metadata, columns, rows |
| 3 | Columns | Derived from the schema's chain, plus the requirement fields `[tables.matrix] fields` names |
| 4 | Verdicts | Reports on the command line (`--report REPO=FILE`), one column per level, each cell pointing at its report; needs #40 |
| 5 | Read from | Working trees; each repo's commit and cleanliness recorded; not pinned |
| 6 | Committed? | No — an output a render layer consumes; the issued document is the record |
| 7 | Change control | One CR-004 for #40 and #49: amends REQ-QMT-10, adds REQ-QMT-23 |

Also settled: an automated test that verifies directly, with no test case between, gets its own
row; no timestamps (REQ-QMT-15).

**Phases, agreed with the Orchestrator 2026-10-16:**

- [x] **A · design** — #54 (`51612c5`) — CR-004 drafted `evaluated` in `qmstrace-ledger`;
  [ADR-0005](../adr/0005-tables-as-data-and-several-reports.md), the surface architecture
  following it; CONTEXT.md's *Traceability Matrix* and *Coverage Summary*.
- [x] **CR-004 accepted** — by the developer, 2026-10-16 (qmstrace-ledger `3928b27`).
- [x] **B · #40** — #59 merged; several reports in core, to ADR-0005; amends REQ-QMT-10
  under CR-004. `results REPORT...`: a run in two reports is one run with its worst verdict,
  each run keeps its reports' labels and sha256, a report may name its repo, and one report
  prints the view it always did. Order-independence and the cross-file duplicate rule each
  fail their tests when broken in a disposable copy.
- [x] **#49a** — #58 merged; `ledger table` without verdict columns adds REQ-QMT-23
  and DSN-QMT-16. It includes schema-derived tables (`core/tables.py`),
  `[tables.matrix] fields`, `model.id_order`, each
  repo's checkout (`infra/git.checkout`), the JSON document (`render/tables.py`), the command,
  goldens and the manual; REQ-QMT-23 (`Change: CR-004`) and DSN-QMT-16, with their markers.
  Mutation checks in disposable copies: without the direct-test row rule, 5 tests fail; with
  cleanliness always true, 5 fail.
- [x] **#49b** — #62 merged, with #63's review follow-ups; `--report REPO=FILE`, per-level
  verdict columns, each cell's evidence pointer; additive, so the format stays
  `qmstrace.table/1`. Built on #40's core combination:
  `Workspace.project_results` reads each `--report` as the repo it names; one column per
  level, then an overall `verdict`, each cell naming its reports. Decided by the developer: a
  test's own level wins over its test case's (`[tables.matrix] level`); reports matching
  nothing are refused. REQ-QMT-23 gains its verdict clause under CR-004; DSN-QMT-16 follows.

## Landed — M12 · the C# capability

Merged 2026-10-15: M12a #35 (`6e8dbe5`), M12b #36 (`d39aa68`), M12c #37 (`058fe71`), M12d #39
(`688f1db`), M12e #41 (`64f99b3`), with the gap wording of #42 (`977e82d`) merged into M12e's
branch. `main` then failed one test, which used `csharp-file` as an extractor qmstrace did not
have; #43 (`b6c8b87`) gave it a misspelt name instead.

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

- [x] **M12-0** — decisions and vocabulary, [#34](https://github.com/Lightbridge-KS/qmstrace/pull/34) · `5f8a1d1`; CR-003 accepted (ledger `7d75978`):
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
- [x] **M12a** — dotted IDs, engine-wide, [#35](https://github.com/Lightbridge-KS/qmstrace/pull/35), merged `6e8dbe5`. REQ-QMT-20.
  - [x] `ID_TOKEN` widened; `id_tokens` reads running text whole or not at all, in every
    reader (headings, fields, tables, mentions, strays, pytest markers, change requests).
  - [x] A heading that starts with a malformed ID (`REQ-SVC-04.1a`, `REQ-SVC-03b`) is a lead:
    V02 names the whole word.
  - [x] A dotted `id_prefix` accepted; listings sort dotted numbers as numbers; the refusal
    at an unreadable baseline tag counts by code past three problems.
  - [x] Verified: the 959 existing tests and every golden unchanged; on every fixture and
    golden, undotted text reads exactly as before; four mutations in a disposable copy each
    fail a REQ-QMT-20 test.
- [x] **M12b** — test cases in the trace, [#36](https://github.com/Lightbridge-KS/qmstrace/pull/36), merged `d39aa68` (stacked on M12a), with
  `qmstrace-ledger` branch `m12b-automated-test` merged just before it. REQ-QMT-02.
  - [x] `test_case` → `automated_test` in qmstrace's own schema (the ledger) and in the starter;
    both trace gates still 0 violations, 0 gaps, 0 suspects after the rename.
  - [x] A gap's next move names every way the link can be made (`judge.Way`, one per type and
    extractor, with its repos); a single way keeps today's text byte for byte; an item's own
    gap is written the way its own repo reads it; a test case is never told to verify a test
    case. The ledger check's last-repo-wins forms bug is gone.
  - [x] Fixture `tests/fixtures/cases` (a Test Specification, dotted IDs, one planned test case
    no test runs); SKILL.md teaches the Test Specification; `status` says *one automated test*.
  - [x] REQ-QMT-02 edited under CR-003; 14 suspects downstream of it (informational, behaviour
    unchanged).
- [x] **M12c** — verdicts through test cases, [#37](https://github.com/Lightbridge-KS/qmstrace/pull/37), merged `058fe71` (stacked on M12b).
  REQ-QMT-10.
  - [x] A verdict follows `verifies` links from the automated tests a report ran — directly or
    through test cases (`core/results.py`); a requirement names the cases on the way; test
    cases that reach no requirement are listed apart; a test case nothing runs adds nothing.
  - [x] Run identities move to the item (`Item.runs_as`, set by the pytest extractor); the
    JUnit reader decides the matched name; a sibling's own links ride on its node
    (`Node.declares`), read by `results` only.
  - [x] Verified on real pytest output (`cases`), with a differential test: where no test case
    stands between, every verdict equals the direct-link one. The output says *automated
    tests* where it counted test functions.
- [x] **M12d** — C# source, [#39](https://github.com/Lightbridge-KS/qmstrace/pull/39), merged `688f1db` (stacked on M12c). REQ-QMT-21,
  REQ-QMT-12.
  - [x] `extract/csharp/`: `_syntax.py` (the only tree-sitter importer), `component.py`
    (`csharp-file`), `xunit.py` (`xunit`); DSN-QMT-15. Runtime dependencies tree-sitter 0.26
    and tree-sitter-c-sharp 0.23.5, confined by an architecture test.
  - [x] Every probe shape from the bed reads as measure C9 expects; nothing dropped silently.
  - [x] Fixture `tests/fixtures/cases/agent` — a real .NET project (built and run: 3 results,
    probes 18); the ledger's check across three repos names pytest and xUnit ways together.
  - [x] SKILL.md's C# examples; the manual's *Trace a C# repo*; issue
    [#38](https://github.com/Lightbridge-KS/qmstrace/issues/38) for a C# starter — closed
    2026-10-21, see *Fixed from use*.
  - [x] Fixed after the bed run found it (`e6e5133`): a test's gap cited the first unread-marker
    finding or stray in its file; each now names its own method.
- [x] **M12e** — the TRX reader and report dispatch, [#41](https://github.com/Lightbridge-KS/qmstrace/pull/41), merged `64f99b3` (stacked on M12d).
  REQ-QMT-22.
  - [x] `extract/reports.py` parses once with defusedxml (now its only importer, pinned) and
    the root picks `junit.py` or the new `trx.py`; anything else is refused naming both.
  - [x] A TRX run is matched by class and method, named by `testName`; `Passed` pass,
    `NotExecuted` skip, any other outcome fail with the outcome kept; the first line of the
    message only. Entries that share a name but not a method are two runs.
  - [x] Fixtures: four real captures of the `cases` agent (full, a skip and a failing row,
    filtered, the probes), sanitised; a sentinel TRX proves no path, name, output or trace
    reaches the report or the output. Every probe run matches its extractor's identity.
  - [x] Messages and the manual name the format given; REQ-QMT-22, DSN-QMT-09 amended.
  - [x] Found: one TRX per test project, and a solution run with a fixed `LogFileName` keeps
    only the last project's results — issue
    [#40](https://github.com/Lightbridge-KS/qmstrace/issues/40); the manual warns of both.
- [x] **M12-R** — run C1–C13 on beacon-dotnet and record the results: **13 of 13 pass**
  ([record](../tests/beacon-dotnet.md#results--run-2026-10-14), `979d69d` on `main`), on a wheel
  from `a7a3807`; bed end state tagged `m12r-end`. The first pass found the gap-citation defect
  fixed in M12d; the rerun gave the same output for C1, C2, C7 and C8.
- [x] **After M12-R** — a gap whose link has nothing to point at in this repo names the sibling
  that declares its targets (`fix/gap-wording-sibling-targets`, stacked on M12e): the run's C#
  agent was told to *write the design here*, wording from M3 that predates ADR-0001. Where no
  sibling declares one, the text is unchanged; no golden moved.
- [x] **After M12-R** — the example fixtures follow ADR-0003 (`fix/mini-automated-test`, [#46](https://github.com/Lightbridge-KS/qmstrace/pull/46)): `mini`
  and `split` call their pytest functions `automated_test`, so the manual's first look, the
  configuration, `status` and `thread` pages no longer teach *test case* for a test function.
  Every golden moved by wording only, with the schema digests and fixture commit IDs that
  follow from it. A schema that keeps `test_case` is pinned by one test (reads the same tests,
  links and gaps). Found by the rename: a next move read *declares a automated test*; it now
  takes its article.

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
| Refactors | Configuration, judge, graph, setup, Markdown, Python extractor, text renderer, workspace and CLI packages, public interfaces preserved | #32 · `75ba627` |
| M12 | The C# capability: dotted IDs, test cases and automated tests, verdicts through test cases, `csharp-file` and `xunit`, TRX. REQ-QMT-20…22 under CR-003; beacon-dotnet 13 of 13 | #35–#43 · `b6c8b87` |

**Decided at the baseline:** CI does not run `check --strict` yet. Tags keep the form
`baseline/requirements/<n>` until qmstrace cuts releases.
**Decided at 0.1.0 (2026-10-15):** release tags `vX.Y.Z` are not baselines and keep their own
form; a release freezes no requirement ([releasing](../dev/releasing.md)).

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
  - #60 an external source cannot yet pool IDs across several agreement files.
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

- **A public repository.** The code is MIT-licensed (`LICENSE`); the repository stays private
  until a review clears its history and content:
  - the full Git history scanned for secrets, home paths, machine names and other projects'
    data, not only the staged changes the commit hook scans;
  - third-party text: `docs/references/` (an ISO/IEC 29110 cheat sheet, paraphrased) and
    any quoted standard text in `docs/`;
  - ownership of the code confirmed before it is published;
  - then: the manual's `repo_url` in `zensical.toml`, the *private* wording in the README,
    *Set up a repo*, *A first look* and the release notes, and whether to publish to PyPI.
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
