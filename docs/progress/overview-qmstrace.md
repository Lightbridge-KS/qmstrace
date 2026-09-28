---
summary: The single active qmstrace tracker — slice 1 landed through M9c, qmstrace traced by its own ledger and its first requirements baseline cut; E6 dogfooding cancelled after run A; now qmstrace applied in real development and shaped as it goes, targeting the layout where the ledger holds the documents (ADR-0001); next M10, the project-wide check, then M11 mentions; what landed work left open; deferred slice-2 work.
read_when:
  - starting a session in this repo — read this first
  - planning or finishing a milestone, or checking whether slice 1 is done
  - deciding what is next or which verification remains
---

# qmstrace — progress

**Updated 2026-09-28 · Slice 1, the product-repo half: landed.** Now: [real-world
use](#now--real-world-use). Next: [M10 · the project-wide check](#next--m10--the-project-wide-check),
then M11 · mentions. Commit hashes locate work. Verification claims refer to checks that were actually run.

## Now — real-world use

qmstrace is applied to real development in the developer's own workflow, and reshaped by what
that use finds. Findings become issues, and changes to settled design go through the design docs.
The first real project is not yet chosen.

**Target layout — [ADR-0001](../adr/0001-the-ledger-holds-the-documents.md), 2026-09-28:**
- **The ledger repo holds the documents:** the SRS and the design documents, beside the
  agreement, the change requests and the schema. It is traced itself, and lists itself in
  `[repos]` as `"."`.
- **Product repos hold code and tests.** Their markers cite the ledger's IDs.

The engine already supports this layout for authoring and for each repo's own check. The
checks that need the whole project fail, and the ADR has the evidence.

## Next — M10 · the project-wide check

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
- [x] **M10a**, a pull request:
  - `ledger check [--strict] [--quiet]`: the union, coverage across repos, per-repo violations,
    refusals and cross-repo suspects;
  - the fix text;
  - REQ-QMT-17 and DSN-QMT-14;
  - the docs the ADR lists;
  - the manual: the `ledger check` reference, `how-to/check-the-project.md`, and *Around the
    repo* rewritten.
- [ ] **M10b**, a pull request: `ledger thread` and `ledger impact` across repos, and
  REQ-QMT-18.
- [x] Acceptance on beacon-split, M10a: A1–A9 and A11–A13 pass, run 2026-09-28 — [results](../tests/beacon-split.md#results)
- [ ] Acceptance A10, after M10b.

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
- The branch stays unmerged, as the record; it is not deleted.

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
  - The stanza says to break behaviour in a "disposable test", but the skill says "disposable
    copy". Agents followed the stanza and broke the live checkout. Aligning them rewrites every
    traced `AGENTS.md`.
  - `check` repeats G06's fix once per module.
  - `results` prints about 42 KB and names no report location.
- **Not filed, engine:**
  - `ledger copy-schema` rewrites the ledger's own `qmstrace.toml` into a copy of its own schema
    when `[repos]` lists `"."`. In M10's scope.
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
  - `init` in a ledger directory, with a stanza that names `ledger check --strict` as the gate;
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
