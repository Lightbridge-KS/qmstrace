---
summary: The single active qmstrace tracker — M0–M8 and node-title hover landed; user acceptance on the beacon-engine test bed under way; slice-1 acceptance and deferred ledger work.
read_when:
  - starting a session in this repo — read this first
  - planning or finishing a milestone, or checking whether slice 1 is done
  - deciding what is next or which verification remains
---

# qmstrace — progress

**Updated 2026-09-24 · Slice 1: the product-repo half.** M0–M8 have landed.
M5b merged in [PR #12](https://github.com/Lightbridge-KS/qmstrace/pull/12) at `8ea7bda`,
including tracker cleanup `0dc5c8c`. M6–M8 merged in
[PR #13](https://github.com/Lightbridge-KS/qmstrace/pull/13) at `6fba9f8`, delivering
setup, test-bed migration, the local browser and slice closure.

**Node-title hover** merged in [PR #14](https://github.com/Lightbridge-KS/qmstrace/pull/14)
at `ea253f0`. Tooltips show literal full titles with a full-ID fallback; list/inspector access
remains available without hover.

**Current: user acceptance on `../_tests/beacon-engine/`.** A user looking for the thread
command reached for `trace`. The verb stays `thread` (the reasoning in the surface doc holds);
the `--help` summary now reads *Trace one item: …* so the word leads to it
(`fix/thread-help-trace`). The test bed's bundled `.engine-venv` predates PR #14; acceptance
runs use a wheel built from `main`.

This is the single active tracker. Detailed milestone history and earlier planning are
[archived](../archive/progress/slice-1-product-repo-half.md); the
[earlier overview](../archive/progress/overview-qmstrace.md) preserves exploration history.
Commit hashes locate work; verification claims below refer to checks actually run.

## Slice closure — landed

Slice 1 requires the product test bed to run on the engine instead of the stand-in,
followed by the accepted M7b local browser and M8 closure.
M6–M8 shipped together in PR #13 with the dry gate and their
[manual pages](../dev/writing-the-manual.md).

- [x] **M6 · set up a repo.** Idempotent `init`: trace configuration, stanza between markers,
  test-framework marker registration; ship the skill as package data, including the
  “break it” loop and a parity test between skill and code.
- [x] **M7 · switch the product test bed to the engine.** Migrate its configurations and
  execute the acceptance checks below. Keep the ledger import on the stand-in until slice 2.
- [x] **M7b · local trace browser.** Generate an offline, read-only HTML view of one
  assessment: item search, thread navigation, findings and evidence limits. Ship manual
  pages and CLI/view parity checks. [Accepted design](../design/trace-browser.md) owns
  scope and rejected alternatives; vis-network 10.1.2 adopted after local evaluation.
- [x] **M8 · close slice 1.** README, CHANGELOG, findings promoted into design,
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
| M5b | Independent historical/current suspect traversal, S01, status/check views and review manual | #12 · `8ea7bda` |
| M6–M8 | Setup, engine-native test-bed migration, offline browser, Diátaxis pages and slice closure | #13 · `6fba9f8` |
| Hover | Node titles on hover in the local browser | #14 · `ea253f0` |

The earlier exploration, E1/E3/E4 experiments and naming decisions are complete.
Their settled outcomes live in the design docs; the
[experiment record](../tests/beacon-authoring-experiment.md) retains methods and findings.

## Latest verified evidence

**User acceptance, 2026-09-24 (`fix/id-pattern-shape`):** on the beacon test bed,
`id_pattern = '^REQ_BCN_\d{2}$'` loaded, then `status` found 0 requirements and `check` gave
57 violations. The configuration now refuses an ID pattern or prefix whose literal start no
ID can have, naming the shape; the agreement and change-request prefixes get the same check.

**M6–M8, 2026-09-24:** `just dry` passed with **571 Python tests, 99.09% coverage**,
three Node browser-control tests, strict types, complete wheel-asset verification and strict
manual build. Setup and graph help/output goldens were inspected; both command pages'
built code blocks match their goldens exactly. Setup was inspected visually and the graph
reference was inspected in the browser. Tutorial, how-to and explanation pages build.

The engine-native test bed now lives at `../_tests/beacon-engine/`; original source repos and
tags are unchanged. E1 mutation, E3 baseline/suspect and E4 graph/gap replays pass again.
Every command runs in both migrated products; repeated setup and both `-C` placements have
identical bytes. The wheel-installed graph command is deterministic in both repos.
The retained stand-in archive serves only historical/ledger reproduction until slice 2.

The browser was exercised on both product projections and a 1,000-node synthetic chain,
including keyboard selection, depth controls, zoom and hostile literal text. Direct local
file-opening was blocked by the verification browser policy and remains unverified;
loopback-served rendering passed. Full methods, mapping commits and remaining limits live
in [slice-1 closure verification](../tests/slice-1-closure.md). CI and deployed-preview evidence belongs to the combined PR; no release or production
deployment is claimed.


**M5b, 2026-09-22:** local `just dry` passed with **528 tests, 99.31% coverage**,
formatting, lint, strict types, wheel contents and strict manual build. Deterministic
status/check/quiet goldens cover S01 reasons, distances, exits and both `-C` placements.
On PR head `393185b`, the [GitHub dry gate](https://github.com/Lightbridge-KS/qmstrace/actions/runs/35710423708)
and Netlify deploy-preview build passed (confirmed 2026-09-24). M5b deployed-page inspection
and production deployment remain unverified.

- **E3 baseline replay:** disposable clones with explicit original-to-overlay commit
  mappings preserve traced source bytes at all three documented pins.
  **10 frozen · 2 changed · 1 new · 0 removed**; all nine guard scenarios pass
  (addition/removal exercised separately); second baseline has 11 unchanged frozen items.
  **11 unique suspects** survive restoring the system-test file, appending a comment and
  adding an unrelated test. The field-only change before the second baseline yields
  **79 unique suspects** (8 designs, 9 components, 62 tests), including 8 edited items.
  Reproduced stand-in output has 24 findings / 20 unique items: it excludes edited items,
  follows direct links only and repeats shared dependants. The applicable second baseline
  clears all chains: **0 suspects**.
- **E4 graph/gap parity:** 177 items, 208 links, reach from 43 starts per repo.
  The engine correctly reports the stray marker that the stand-in silently accepts.
- **E1 results parity:** 62 test cases / 78 runs, 10 passing requirements; all seven
  mutations change their targeted requirement to `fail`. Original test-bed repos
  remain unchanged.
- **Impact parity:** CR-001's two changed starts reach 18 downstream IDs; explicitly
  adding its already-declared new ID reproduces the candidate line.
- **Manual:** nine affected built pages checked; included goldens match complete code
  blocks. Both new M5b pages were visually inspected. M5a's deployed preview previously
  passed inspection; its production deployment has not been verified. M3/M3b production
  pages were checked on 2026-09-21; M4 pages on 2026-09-22.

M5a's GitHub dry gate and Netlify preview passed on final PR head `d814996`.
Its tag-date regression preserves non-UTC offsets and normalizes Git's `Z` / `+00:00`.

Local reproduction records: `_playground/2026-09-22_m5b-suspects/` (mapped baseline and
suspect replay, stand-in comparison, latest parity/gate/manual logs),
`_playground/2026-09-22_m5a-baselines/` (earlier baseline replay),
`_playground/2026-09-21_m4-results/` (results
mutations), `_playground/2026-09-21_m3b-impact/` (impact), and
`_playground/2026-09-21_parity/` (graph/gaps). These are local records, not packaged evidence.

## Slice-1 acceptance

M7 uses the retained engine-native test bed plus disposable replay clones. The historical
workspace retains its old configuration for stand-in/ledger reproduction.

| Check | Current evidence / remaining work |
|---|---|
| E1: 0 violations, 0 gaps, 10 requirements, labelled 62 cases / 78 runs; seven mutations flip the same verdicts | Replayed in fresh E1 clones during M7; all seven targeted verdicts fail |
| E3: 10 frozen · 2 changed · 1 new · 0 removed; all nine guard scenarios | Replayed during M7 with explicit mapped commits; guard checks pass |
| E3: restore the system-test file from the tag; suspects appear and survive an appended comment or an added test | Verified in M5b clones: the same 11 unique items throughout |
| Second requirements baseline: no suspects; preceding commit: field-only change has downstream suspects | Verified in M5b clones: 79 before, 0 at the applicable baseline |
| Client: sibling items say not pinned; duplicate requirement names its owner; missing sibling says not reachable; missing ledger says not verified, including quiet output | Fixtures and migrated two-repo replay pass, including quiet evidence |
| Lightweight tag warns; pre-tag feature branch sees no baseline; shallow history cannot look unfrozen | Verified in M5a fixtures |
| CR-001 impact: changed IDs `REQ-BCN-05`, `REQ-BCN-06` show downstream reach and origins; `REQ-BCN-11` participates only when declared and explicitly supplied | Reach verified in M3b; reserved unseen-ID rejection verified in M5a fixtures |
| Client `Assumes` propagates impact without adding coverage; CR-002 is the later classification change across eleven requirements | M7 dependency mutation and field-only/baseline replay pass |
| Every command in both product repos; `init` in a scratch copy reproduces the stanza; repeated runs produce identical bytes | Wheel-installed commands pass in both products; init and graph deterministic |
| Local browser preserves CLI reach, findings and evidence limits; works offline and by keyboard; handles cycles and safely renders authored text | Shared-core parity, browser/control checks and 1,000-node example pass; direct file-opening smoke check remains unverified |

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
  collectors, conformance view, project-wide trace browser at pins and a second profile.
- **Browser extensions:** separate historical/current comparison views, explicitly supplied
  test-result overlays and live refresh remain outside M7b; see the
  [trace-browser boundaries](../design/trace-browser.md#evidence-and-scope).
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
- [Local trace browser](../design/trace-browser.md): accepted M7b experience and architecture;
  pinned embedded vis-network 10.1.2 adopted after fixture evaluation.
- [System architecture](../design/system-architecture.md) and
  [codebase blueprint](../structure/codebase-blueprint.md): module ownership and source-tree
  seam; Python 3.13+, frozen values, pure core, no DuckDB until slice 2.
- [Scenario catalogue](../tests/scenario-catalogue.md): required behavior and regressions.
