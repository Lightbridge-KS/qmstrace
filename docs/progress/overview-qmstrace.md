---
summary: The single active qmstrace tracker — M0–M5a complete, M5b next; remaining slice-1 milestones, acceptance checks, verified evidence and deferred ledger work.
read_when:
  - starting a session in this repo — read this first
  - planning or finishing a milestone, or checking whether slice 1 is done
  - deciding what is next or which verification remains
---

# qmstrace — progress

**Updated 2026-09-22 · Slice 1: the product-repo half.** M0–M5a have landed.
**Next: plan M5b — downstream suspects.** M5a merged in
[PR #11](https://github.com/Lightbridge-KS/qmstrace/pull/11) at `724ec02`.
No engine implementation is currently in flight.

This is the single active tracker. Detailed milestone history and earlier planning are
[archived](../archive/progress/slice-1-product-repo-half.md); the
[earlier overview](../archive/progress/overview-qmstrace.md) preserves exploration history.
Commit hashes locate work; verification claims below refer to checks actually run.

## Remaining milestones

Slice 1 is done when the product test bed runs on the engine instead of the stand-in.
Each milestone uses a branch and draft PR, passes the dry gate, and ships its
[manual pages](../dev/writing-the-manual.md).

- [ ] **M5b · suspects — next.** Item-level, transitive, grouped by distance: first hop
  listed, the rest counted. An edit does not clear a suspect; an item new since the baseline
  is not a suspect. Reuse the traversal behind `impact` and M5a's historical snapshots.
  Standing contract: [data architecture D7](../design/data-architecture.md).
  Explicit recorded-review clearance remains later work. Plan the command presentation
  and remaining edge cases before implementation.
- [ ] **M6 · set up a repo.** Idempotent `init`: trace configuration, stanza between markers,
  test-framework marker registration; ship the skill as package data, including the
  “break it” loop and a parity test between skill and code.
- [ ] **M7 · switch the product test bed to the engine.** Migrate its configurations and
  execute the acceptance checks below. Keep the ledger import on the stand-in until slice 2.
- [ ] **M8 · close slice 1.** README, CHANGELOG, findings promoted into design,
  trackers reconciled; archive the stand-in rather than delete it.

## Landed

| Milestone | Delivered | Merge pointer |
|---|---|---|
| M0 | Design reconciliation, scenario catalogue, architecture and blueprint | [Design and structure](#standing-design) |
| M1 | Package scaffold, CLI, dry gate and wheel checks | #1 · `776df63` |
| M2a | Validated trace configuration and miniature fixture project | #2 · `eba3e37` |
| M2 | Working-tree scanning, validation, graph and `status` | #3 · `ce865fa` |
| M2c | Golden-backed user manual and Netlify publication | #5 · `e7cbb05` |
| CLI fix | `-C` before or after the command | #6 · `6aea7e4` |
| M2b | `thread`, shared traversal and graph parity | #7 · `9143a6e` |
| M3 | Coverage rules, `check`, `rules`, strict/quiet modes | #8 · `ba2e0ca` |
| M3b | Multi-start `impact` and candidate `Impacts:` list | #9 · `23c80a5` |
| M4 | Pytest JUnit matching and direct requirement verdicts | #10 · `1a4869d` |
| M5a | Historical baselines, fresh request citations, V10–V13 and withdrawal | #11 · `724ec02` |

The earlier exploration, E1/E3/E4 experiments and naming decisions are complete.
Their settled outcomes live in the design docs; the
[experiment record](../tests/beacon-authoring-experiment.md) retains methods and findings.

## Latest verified evidence

**M5a, 2026-09-22:** local `just dry` passed with **492 tests, 99.29% coverage**,
formatting, lint, strict types, wheel contents and strict manual build. GitHub's dry gate and
Netlify deploy preview passed on final PR head `d814996`. Tag dates are normalized across
Git versions (`Z` / `+00:00`); regression tests preserve non-UTC offsets and lightweight tags.

- **E3 baseline replay:** disposable clones with explicit original-to-overlay commit
  mappings preserve traced source bytes at all three documented pins.
  **10 frozen · 2 changed · 1 new · 0 removed**; all nine guard scenarios pass
  (addition/removal exercised separately); second baseline has 11 unchanged frozen items.
  Suspect assertions remain M5b work.
- **E4 graph/gap parity:** 177 items, 208 links, reach from 43 starts per repo.
  The engine correctly reports the stray marker that the stand-in silently accepts.
- **E1 results parity:** 62 test cases / 78 runs, 10 passing requirements; all seven
  mutations change their targeted requirement to `fail`. Original test-bed repos
  remain unchanged.
- **Impact parity:** CR-001's two changed starts reach 18 downstream IDs; explicitly
  adding its already-declared new ID reproduces the candidate line.
- **Manual:** ten built pages checked for expanded goldens; the two new M5a pages were
  visually inspected. Both how-to examples were subsequently verified as complete code
  blocks on the deployed preview. M5a production deployment has **not** been verified.
  M3/M3b production pages were checked on 2026-09-21; M4 pages on 2026-09-22.

Local reproduction records: `_playground/2026-09-22_m5a-baselines/` (mapped baseline
replay and latest parity/gate logs), `_playground/2026-09-21_m4-results/` (results
mutations), `_playground/2026-09-21_m3b-impact/` (impact), and
`_playground/2026-09-21_parity/` (graph/gaps). These are local records, not packaged evidence.

## Slice-1 acceptance

The table distinguishes checks already exercised in clones/fixtures from the final M7
switch-over. It does not claim the test bed already runs on the engine.

| Check | Current evidence / remaining work |
|---|---|
| E1: 0 violations, 0 gaps, 10 requirements, labelled 62 cases / 78 runs; seven mutations flip the same verdicts | Verified in M4 and replayed in M5a; repeat after M7 migration |
| E3: 10 frozen · 2 changed · 1 new · 0 removed; all nine guard scenarios | Verified in mapped M5a clones; repeat after M7 migration |
| E3: restore the system-test file from the tag; suspects appear and survive an appended comment or an added test | **M5b pending** |
| Second requirements baseline: no suspects; preceding commit: field-only change has downstream suspects | Frozen comparison verified in M5a; **suspect checks pending M5b** |
| Client: sibling items say not pinned; duplicate requirement names its owner; missing sibling says not reachable; missing ledger says not verified, including quiet output | Fixtures cover these cases; final two-repo replay remains M7 |
| Lightweight tag warns; pre-tag feature branch sees no baseline; shallow history cannot look unfrozen | Verified in M5a fixtures |
| CR-001 impact: changed IDs `REQ-BCN-05`, `REQ-BCN-06` show downstream reach and origins; `REQ-BCN-11` participates only when declared and explicitly supplied | Reach verified in M3b; reserved unseen-ID rejection verified in M5a fixtures |
| Client `Assumes` propagates impact without adding coverage; CR-002 is the later classification change across eleven requirements | Impact checked in M3b; retain both scenarios in M7 |
| Every command in both product repos; `init` in a scratch copy reproduces the stanza; repeated runs produce identical bytes | Existing command goldens/determinism pass; `init` and final full replay await M6/M7 |

Every command must have a golden, and every finding code an emitting fixture.
Do not reproduce the stand-in's defects: file-level or self-clearing suspects, one-hop-only
reach, hard-coded tag patterns, missing lightweight-tag notices, duplicate findings across
overlapping scopes, or the silent passes in the [scenario catalogue](../tests/scenario-catalogue.md).

## After slice 1 and deferred work

- **Ledger design and slice 2:** settle event shape, non-document work-product states,
  the signature loop, recorded inspection/analysis basis and project-owned cross-repo
  questions. The ledger's `trace.lock` at E4 is frozen as a golden; its stand-in import
  cannot consume the new configuration shape.
- **Persistence decisions for slice 2:** Python AST digest format/versioning before a
  trace lock is written; derived-ID renames; an optional accepted-request/agreement index
  in the generated schema copy for offline citation verification. See
  [PRD open questions](../req/qmstrace-prd.md#open-questions) and data architecture D7/D9.
- **After the engine slice:** a fresh agent run against PRD success criteria 5/6,
  replaying E3, followed by a person-launched test-bed session.
- **E5:** five-step audit demo once the engine has a ledger.
- **Repo hygiene:** validating tracker commit references remains agreed but unscheduled.
- **Later capabilities:** machine-readable output, recorded-review suspect clearance,
  collectors, conformance view, trace browser and a second profile.
- **E2 option C** remains an optional comparison/on-ramp for unmarked repos.
  The real pilot remains under its own plan; the live audit is unchanged.
- **`VISION.md`** remains deferred until slice-1 experience supports durable invariants.

## Standing design

Read these for contracts rather than copying their contents into this tracker:

- [Glossary](../../CONTEXT.md) and [PRD](../req/qmstrace-prd.md): vocabulary, scope, success criteria.
- [Data architecture](../design/data-architecture.md): D1–D10, item digests, baselines,
  change control, withdrawal and suspects. Historical pre-trace tags freeze nothing;
  this differs from a required ledger import pin with no trace configuration.
- [Surface architecture](../design/surface-architecture.md): command/exit contracts,
  findings, evidence limits and authoring loop; decorative markers and unrecorded
  inspection are known limits.
- [System architecture](../design/system-architecture.md) and
  [codebase blueprint](../structure/codebase-blueprint.md): module ownership and source-tree
  seam; Python 3.13+, frozen values, pure core, no DuckDB until slice 2.
- [Scenario catalogue](../tests/scenario-catalogue.md): required behavior and regressions.
