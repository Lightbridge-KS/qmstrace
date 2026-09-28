---
summary: The single active qmstrace tracker — slice 1 landed through M9c (a table of merges, detail archived); now qmstrace is traced by its own ledger and its gate is not green yet; next M10 mentions; what landed work left open; deferred slice-2 work.
read_when:
  - starting a session in this repo — read this first
  - planning or finishing a milestone, or checking whether slice 1 is done
  - deciding what is next or which verification remains
---

# qmstrace — progress

**Updated 2026-09-28 · Slice 1: the product-repo half.** Every milestone through M9c has
landed — see [Landed](#landed). **Now: [qmstrace, traced by its own
ledger](#now--qmstrace-traced-by-its-own-ledger)**; next, [M10 · mentions](#next--m10--mentions).

This tracker holds what is being done, what is next, and what landed work left open. Each
landed milestone's decisions, checklists and evidence are archived — the links are under
[Landed](#landed). Commit hashes locate work; verification claims refer to checks actually run.

## Now — qmstrace, traced by its own ledger

qmstrace is a product repo of its own project, `QMT`. The ledger repo `qmstrace-ledger` sits
beside it, private on GitHub, and holds the trace schema, the agreement and the change-request
register. This repo carries the verified copy of the schema, the stanza and the skill. The
engine repo's constraint now reads *no other project's data*; the decision and the option that
lost are in the [system architecture](../design/system-architecture.md).

- [x] The ledger repo, at `a3faeab`: the schema — rules G01–G06, test levels `unit`,
  `integration`, `cli` and `meta`, requirement baselines — agreement clauses AGR-1…15 and the
  change-request register.
- [x] This repo traced, in [#19](https://github.com/Lightbridge-KS/qmstrace/pull/19): the
  meta-tests in a level folder of their own, the constraint amended, the trace configuration
  with the schema copy, and the installed guidance held to the package by meta-tests.
- [x] The skill installed where a harness lists it — `.agents/skills/qmstrace/`, linked from
  `.claude/skills/qmstrace` — in [#23](https://github.com/Lightbridge-KS/qmstrace/pull/23) (M9c).
- [ ] The gate is not green yet: `qmstrace check` reports 26 gaps — no module implements a
  design element, and no requirement or design element is declared.

## Next — M10 · mentions

Every token with a configured prefix in a scanned file — prose, table or Mermaid — must exist;
a dangling one is a violation, like V03. Configured prefixes only: `SHA-256`, `UTF-8` and
`ADR-0001` all fit the bare ID shape.

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
| UAT round 1 | `thread` help summary; refusal of an ID pattern no ID can match | #15 · `58fc525` |
| M9 | Rich Markdown: sections, heading forms, strays, V16, fence closing; lens-style fixture and how-to | #17 · `e7d38b6` |
| M9b | `ledger copy-schema`: the verified schema copy, written across repos with one rollback | #18 · `f4e770b` |
| M9c | The skill at `.agents/skills/qmstrace/`; a create-only `.claude/skills/qmstrace` link | #23 · `02caed1` |

Each milestone's decisions, checklist and verification evidence are archived: M5a–M9c in
[landed work, M5a–M9c](../archive/progress/landed-m5a-m9c.md), earlier ones in
[slice 1 through M5a](../archive/progress/slice-1-product-repo-half.md), and the exploration
before it in the [earlier overview](../archive/progress/overview-qmstrace.md). The exploration,
E1/E3/E4 experiments and naming decisions are complete; their settled outcomes live in the
design docs, and the [experiment record](../tests/beacon-authoring-experiment.md) keeps
methods and findings.

## Open from landed work

- **Not verified:** the M9 how-to page as deployed; the local browser opened directly from a
  file (the one open slice-1 acceptance check); the manual's production deployment since M5a;
  `init` where symbolic links are unavailable (#22).
- **Filed:** #16 (`init` should replace an unedited earlier skill copy — its text still names
  the skill's old home), #20 (files `init` creates are `0600`), #21 (rollback leaves the
  folders it created), #22 (`ux`: no symbolic links);
  [agent-stuff#71](https://github.com/Lightbridge-KS/agent-stuff/issues/71) (a traced-repo note
  for the lens skills).
- **Not filed yet:** recognise the same repo by its Git common dir — a clone beside the ledger
  reads the real checkout as its sibling; the `results` report-path display; stale comments
  in the beacon test bed's configurations.

## Slice-1 acceptance

Met: every check in the acceptance table passed in the M7 and M5b replays, except the local
browser opened directly from a file (above). The table and its evidence are archived with
[landed work, M5a–M9c](../archive/progress/landed-m5a-m9c.md#slice-1-acceptance--the-checks-and-their-evidence).

What stays binding: every command has a golden, and every finding code an emitting fixture.
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
