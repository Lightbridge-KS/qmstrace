---
summary: Tracker for engine slice 1 — the product-repo half of qmstrace as a real, tested package that replaces the throwaway stand-in. Milestones M0–M8, the decisions taken while planning, what a second-opinion review changed, the acceptance checks for "the test bed runs on the engine", and what is parked.
read_when:
  - working on any milestone of slice 1, or deciding what comes next in it
  - about to write engine code — read the decisions and the module shape first
  - checking whether the slice is done
---

# Slice 1 — the product-repo half as an engine

**Parent:** [`overview-qmstrace.md`](overview-qmstrace.md) · **Scope:** [PRD § Slices](../req/qmstrace-prd.md) ·
**Design:** [`data-architecture.md`](../design/data-architecture.md) ·
[`surface-architecture.md`](../design/surface-architecture.md) ·
**Fixtures:** [`scenario-catalogue.md`](../tests/scenario-catalogue.md) ·
**Structure:** [`codebase-blueprint.md`](../structure/codebase-blueprint.md)

**Done when** the test bed runs on the engine instead of the stand-in, with the stand-in's
verified scenarios as fixtures — at least one test per command. The stand-in's only
regression was the one command not re-run after a rewrite; an agent found it in minutes.

## Decisions taken while planning

| Decision | Choice |
|---|---|
| Architecture tier | **Modular** — `core / extract / infra / render`, `cli.py`, `assets/`. Interfaces only at seams that really vary |
| Value objects | **Dataclasses**, `frozen=True, slots=True`, validated in `__post_init__`. No pydantic |
| DuckDB | **Slice 2**, with the ledger. Slice 1 judges rules-as-data in Python — what three experiments validated. Amends D4 |
| Git flow | **GitHub Flow**: a branch and a draft pull request per milestone, a dry gate in CI. Docs-only changes may still go to `main` |
| Exit codes | **`0`** no failing findings in this mode · **`1`** the check failed — violations, or gaps under `--strict`; the result line says which · **`2`** could not judge — usage, configuration, wrong kind of repo, unknown ID, unreadable report · **`3`** internal error. Click already owns 1 and 2; this never fights it |
| Unverifiable citation | In a pipeline without the ledger, a fresh change-request citation or an origin **passes with a notice that survives `--quiet`**; it is verified for real at the ledger's import |
| Suspects | **Transitive, grouped by distance** — the first hop listed, the rest counted. `impact` and suspects are two renderers of one traversal |
| Python | **3.13+** — one glob matcher from the standard library for every tree. The tool runs in its own environment; product repos are not constrained |
| Layout, types | `src/` layout from `uv init --package`; **mypy**, strict on `core/` |

## Module shape

Revised by the review — the first draft would have re-grown the stand-in's `Repo.__init__`.

```
src/qmstrace/
  core/       pure, no IO
    model        Item, Link, Finding, ItemText (digest with an algorithm tag) — frozen dataclasses
    config       TraceConfig.parse(local_text, schema_text | None) — validates, merges, and
                 records where each key came from (the project's or the repo's)
    graph        TraceGraph.build(...) -> (graph, findings): an illegal link never enters it.
                 node(id) knows its home: local, sibling, external. downstream/upstream return a
                 Closure that keeps the edge that reached each node
    judge        pure functions: coverage · resolve_baselines · guard · suspects
    findings     the catalogue — each code once: what is wrong, the next move
  extract/    IExtractor.extract(path, text, spec) — takes TEXT; chosen by configuration, never
              by an item type's name. markdown · python_module · pytest (with the JUnit reader:
              they share one test-ID convention)
  infra/      ISourceTree — WorkingTree | GitTree(rev): files(), read(), label ("working tree,
              not pinned" | a tag). IGit, domain-shaped: state() · tags_reachable_from_head() ·
              is_ancestor() · list_files(rev) · read_files(rev, paths). externals
  render/     functions returning str; no renderer interface until a second form exists
  workspace   Workspace.open(root).assessment() -> Assessment (violations, gaps, suspects,
              notices, frozen state, what was scanned). A command is: open → render → exit
  cli         typer wiring only; a handler returns an int and an @outcome decorator maps it —
              and CouldNotJudge, and anything unexpected — to an exit code. Never imports click:
              this Typer vendors it privately (verified)
  assets/     skill · stanza · init templates — shipped as package data
```

**One scan function over different trees.** The stand-in had three scanners and two fence
parsers. The real seam is the *source tree*, not Git: the same extractors read the working
tree, a tree at a baseline tag, and a sibling.

## Milestones

Each is a branch and a draft pull request, except M0.

- [x] **M0 · docs** — this tracker · the [scenario catalogue](../tests/scenario-catalogue.md) ·
      design docs amended for the decisions above and for what the review found ·
      [`system-architecture.md`](../design/system-architecture.md) (C1–C2, a first C3) ·
      the [codebase blueprint](../structure/codebase-blueprint.md), whose framework check found
      that this Typer no longer installs click · the agent guide's Git rule
- [x] **M1 · scaffold and gate** *(merged — pull request 1)* — `uv init --package`; typer; ruff, mypy, pytest with
      coverage; `justfile`; CI with named steps; `--version` from package metadata; **a wheel
      is built in CI and a placeholder asset read back from it** — data files missing from a
      wheel is a classic late surprise
- [ ] **M2a · the configuration, by example** — both test-bed configurations rewritten in the
      new shape and parsed in full, including the parts unused until M5. A later change of
      shape would churn every fixture
- [ ] **M2 · see the repo** — trees (working, at a revision, with a contract test), the three
      extractors, item digests including a test function's own source, the graph; `status`,
      `thread`. A local parity script — stand-in versus engine on the test bed's tags, with a
      list of expected differences — runs from here on
- [ ] **M3 · judge it** — link validation, required fields, coverage rules, the findings
      catalogue, the text renderer; `check`, `--strict`, `--quiet`, `rules`; **`impact` and
      `Assumes`** — pure graph features, no Git needed
- [ ] **M4 · results** — the JUnit reader on defusedxml; `results`
- [ ] **M5a · baselines and change** — Git, baseline resolution, the guard, change requests
- [ ] **M5b · suspects** — item-level, transitive, never cleared by a touch
- [ ] **M6 · setting up a repo** — `init` (trace configuration, stanza between markers, the
      test framework's marker registered, idempotent); the skill as package data with the
      loop's "break it" step; the parity test between skill and code
- [ ] **M7 · the test bed runs on the engine** — acceptance checks below
- [ ] **M8 · close the slice** — README, CHANGELOG, what the slice taught into the design
      docs, trackers reconciled; the stand-in archived in the test bed, not deleted

## Acceptance — "the test bed runs on the engine"

Parity with the stand-in is a trap where the stand-in was wrong. The engine must **not**
reproduce: suspects tracked by file, or cleared when an item is edited, or one hop deep · a
hard-coded tag pattern · no check that a baseline tag is annotated · duplicate findings
across overlapping scopes · the silent passes listed in the scenario catalogue · an
eight-line header before every finding.

1. At the first experiment's end state: 0 violations, 0 gaps, 10 requirements, 62 test cases
   and 78 runs, both counts labelled.
2. The seven gateway mutations flip the same verdicts through `results`.
3. At the third experiment's end state: `10 frozen · 2 changed · 1 new · 0 removed`; with the
   system-test file restored from the tag, the suspects appear — and appending a comment to
   that file, or adding a test to it, clears none of them.
4. Each of the nine guard scenarios gives its expected code.
5. At the second requirements baseline nothing is suspect; one commit before it, the
   field-only change's suspects are listed.
6. In the client repo: a sibling's items are labelled *not pinned*; a re-declared gateway
   requirement names its owner; with the sibling moved away, *not reachable*; with the ledger
   moved away, *not verified* — and that survives `--quiet`.
7. New behaviour: a lightweight baseline tag is reported as weaker evidence; a feature branch
   forked before a tag does not see it; a shallow clone is never reported as "nothing frozen".
8. `impact` on the two changed requirements reproduces the change request's `Impacts` set plus
   the agreement clause; one `Assumes` added in the client repo is traversed and raises no gap.
9. Every command is run in both product repos; `init` in a scratch copy reproduces the
   committed stanza byte for byte; two consecutive runs of anything give identical bytes.

Two meta-tests guard the regression structurally: every registered command has a golden
output, and every catalogue code has a fixture that emits it.

## Parked

- **The ledger's import stays on the stand-in** until slice 2, and the stand-in cannot read
  the new configuration shape. The ledger's `trace.lock` at the fourth experiment's end state
  is frozen as slice 2's golden file; the ledger is parked until then.
- The agent-facing checks (PRD success criteria 5 and 6) — one fresh teammate run on the
  engine, replaying the third experiment's request — follow the slice.
- For slice 2: the generated copy of the schema could also carry an **index of accepted change
  requests and agreement clauses**, so a product repo's pipeline can verify a citation offline.

## Open questions

- `Status: withdrawn` needs semantics: a withdrawn item should stop raising coverage gaps.
- `id_prefix` in a configuration — keep it, or derive it from the ID pattern.
- A test function's digest uses `ast`; its dump format changed in Python 3.13. Harmless while
  both sides are computed at run time — a format question once slice 2 writes the lock.
