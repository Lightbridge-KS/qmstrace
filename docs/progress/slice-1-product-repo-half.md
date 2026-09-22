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
| Unverifiable citation | In a pipeline without the ledger, a fresh change-request citation or an origin **passes with a notice that survives `--quiet`**; it is verified for real at the ledger's import. **The same holds for a sibling's item** when that sibling cannot be read: a link to an ID that is not this repo's own is *not verified here*. `V03` stays for an ID matching this repo's own pattern, and whenever every listed sibling was read (decided while planning M2) |
| Suspects | **Transitive, grouped by distance** — the first hop listed, the rest counted. `impact` and suspects are two renderers of one traversal |
| Python | **3.13+** — one glob matcher from the standard library for every tree. The tool runs in its own environment; product repos are not constrained |
| Layout, types | `src/` layout from `uv init --package`; **mypy**, strict on `core/` |
| Working tree *(M2)* | Inside Git, what a commit could carry — tracked, or untracked and not ignored — so an ignored note is never read, and it is what a tree at a tag will hold. Outside Git, a walk the output labels as such |
| Field values *(M2)* | Matched exactly, case included — the stand-in lower-cased them, a hidden rule |
| Finding codes *(M2)* | A marker carried by the wrong kind of item joins V04; a sibling's item declared again joins V01. New: **V14** a link field that holds something other than IDs, **V15** a marker form the tool does not read |
| `-C` *(M2, widened by #4)* | Before the verb, as with `git -C`, or after it — an agent composing a command line puts it either side. Both at once is a usage error |

## Module shape

Revised by the review — the first draft would have re-grown the stand-in's `Repo.__init__`.

```
src/qmstrace/
  core/       pure, no IO
    model        Item, Link, Lead, Finding, Notice, Extracted — frozen dataclasses; text_digest
                 (the digest carries its algorithm)
    config       TraceConfig.parse(local_text, schema_text | None) — validates, merges, and
                 records where each key came from (the project's or the repo's)
    graph        TraceGraph.build(...) -> (graph, findings): an illegal link never enters it.
                 node(id) knows its home: local, sibling, external, not verified here.
                 forward/backward (M2b) return a Closure that keeps, for each item, the link
                 that reached it first and its distance — thread, impact and suspects render it
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

Each is a branch and a draft pull request, except M0. **From M2c on, each ships its pages of
the user manual** (`contents/`, Diátaxis) — a page that has to warn about a caveat is a design
finding, filed as a `ux` issue unless a milestone already owns the gap.

- [x] **M0 · docs** — this tracker · the [scenario catalogue](../tests/scenario-catalogue.md) ·
      design docs amended for the decisions above and for what the review found ·
      [`system-architecture.md`](../design/system-architecture.md) (C1–C2, a first C3) ·
      the [codebase blueprint](../structure/codebase-blueprint.md), whose framework check found
      that this Typer no longer installs click · the agent guide's Git rule
- [x] **M1 · scaffold and gate** *(merged — pull request 1)* — `uv init --package`; typer; ruff, mypy, pytest with
      coverage; `justfile`; CI with named steps; `--version` from package metadata; **a wheel
      is built in CI and a placeholder asset read back from it** — data files missing from a
      wheel is a classic late surprise
- [x] **M2a · the configuration, by example** *(merged — pull request 2, `eba3e37`)* —
      `core/config.py` and the annotated fixture project `tests/fixtures/mini/` (a ledger's
      trace schema, `service`, `client`, `solo`), parsed in full, including the parts unused
      until M5. The test bed's own configurations are rewritten in M7, when it switches over
- [x] **M2 · see the repo** *(merged — pull request 3, `ce865fa`)* — `status`, end to
      end over the working tree: the glob matcher, `WorkingTree` (honours `.gitignore`), the
      three extractors, item digests including a test function's own source, the agreement and
      a sibling read for citations, the graph with the scanning findings — **link validation
      and required fields land here**, since the graph cannot be built without deciding which
      links are legal — `Workspace` with root discovery and `-C`. Fixtures: the catalogue's
      *Scanning*, *What the stand-in passed silently*, *Across repos* and *Configuration*;
      `tests/fixtures/mini/` filled out. The schema's `profile` key is dropped. **Checked against
      the stand-in** on the test bed at HEAD, with new-shape configurations laid over clones:
      every count and every requirement line the same in both repos (local notes:
      `_playground/2026-09-21_m2-status-vs-standin/`)
- [x] **M2c · the user manual's foundation** *(merged — pull request 5, `e7cbb05`; live at <https://qmstrace.netlify.app/>)* —
      Zensical, source in `contents/`, published on Netlify. Reference is never restated: a page
      frames goldens, help output and fixture files that tests own. Seven pages for what M2
      built. Netlify is imported only after this merges, so that nothing unbuilt is ever
      published. *Waits:* running in a pipeline (slice 2, the schema's copy) · markers (M6,
      beside the skill) · the chain (M2b, shown with `thread`). Frictions found: one `ux` issue
      (#4, `-C` only before the command); the others are owned by M3, M5a and slice 2
- [x] **M2b · follow a thread** *(merged — pull request 7, `9143a6e`)* —
      `thread <ID>`: backward to what an item derives from, forward to what hangs off it; each
      item once, nearest first, under the link that reaches it first. `Assumes` is followed
      forward and not backward. Every ID the run can see can be threaded — uncited sibling items
      and declared clauses too — while `Node.item` stays this repo's own. An unknown ID is *could
      not judge*, with the closest IDs. Manual: the `thread` reference and the chain explained.
      A local parity script — the engine against the stand-in on the test bed, graphs not text —
      runs from here on; the test bed is untouched until M7. **First run: the E4 row matches the
      ledger's `trace.lock` exactly** — 177 items, 208 links, forward reach from 43 starts per
      repo (local: `_playground/2026-09-21_parity/`). The E3 row waits for M5a, where its
      baseline tags test something new
- [x] **M3 · judge it** *(merged — pull request 8, `ba2e0ca`)* — coverage gaps from the
      rules as data, `check` (`--strict`, `--quiet`), `rules`, the wording pass over the findings
      catalogue, the gap that says why a module with a stray `Implements:` is unlinked; `status`
      gains its gap count and its pointer to `check`. **The gate fails on every gap in slice 1**
      — stage-aware gating waits for the ledger, where the project's stages live (decided
      2026-09-21; the surface doc's decision #1). **Parity:** four edits into both the engine's
      copy and the stand-in's give the same gaps on the same items, but for the `Implements:`
      moved into a comment, which only the engine reports — the stand-in was wrong (local:
      `_playground/2026-09-21_parity/`). The pull request's dry gate passed; the four new manual
      pages were verified to return HTTP 200 in production on 2026-09-21
- [x] **M3b · impact** *(merged — pull request 9, `23c80a5`)* — `impact <ID>…`: the forward closure M2b built, `Assumes` included,
      rendered for several IDs, grouped by item type, with the `Impacts` line; an ID a change
      request reserves is judged once change requests are read (M5a). Split from M3 on
      2026-09-21. Assesses once; rejects the whole request if any start is unseen; displays
      starts, the downstream union and upstream origins; generates a candidate `Impacts:`
      line from configured baseline types. CLI/help goldens and reference/how-to pages ship
      together. Converging backward paths exposed an early assumption hiding ordinary
      ancestry: fixed in the shared traversal, with regressions for `thread` and `impact`.
      **Verified:** `just dry` — 375 tests, 99.33% coverage, formatting, lint, types, wheel and
      strict manual build; built pages checked for expanded goldens. Existing E4/gaps parity
      still matches. CR-001's two starts reach 18 downstream IDs matching the frozen lock;
      adding its already-declared new ID explicitly reproduces its candidate line. A client
      assumption propagates impact without changing gaps. Original test-bed repos remain
      clean (local record: `_playground/2026-09-21_m3b-impact/`). GitHub's dry gate and the
      deploy preview passed. Both manual pages were verified in production on 2026-09-21:
      HTTP 200 with the expected impact output examples
- [ ] **M4 · results** *(built — awaiting PR review on `codex/m4-results`)* —
      safe JUnit reader; exact pytest identity matching; pure run deduplication and direct
      `verifies` aggregation. Usable reports exit 0 even with failures or partial matches;
      zero matches exits 2. Missing results, shared tests, sibling ownership and unknown
      targets stay explicit; inspection/analysis methods survive sibling reads. The report
      commit is always unverified. Source/graph notices are preserved. Relative paths use the
      effective invocation directory, including ignored reports and `-C` on either side.
      CLI/help goldens, reference and how-to pages ship together; accepted contract and
      ownership notes are in the surface design, scenario catalogue and blueprint.
      **Verified 2026-09-22:** `just dry` — 419 tests, 99.35% coverage, formatting, lint,
      strict types, wheel and strict manual build. Real pytest reports cover both XML families,
      nested methods, bracketed parameters, xfail/xpass and body-failure/teardown-error duplicates.
      Built pages contain every included golden; existing golden changes are limited to root
      help (new command and clarified informational exit 0). E1 gateway at `e1-end` (`cee4ed7`),
      ledger at `cc19a6b`, using new-format overlays retaining E1's `Kind`: 0 violations,
      0 gaps, 10 passing requirements, **62 cases / 78 runs**. All seven documented mutations
      flip their targeted requirement to `fail`, with pinned source restored between runs.
      Repeated E1 CLI runs are byte-identical. Existing E4 graph/gaps parity still matches
      (177 items, 208 links, 43 starts per repo; the documented stand-in gap defect remains).
      Original repositories are unchanged; clone source is restored. Local evidence:
      `_playground/2026-09-21_m4-results/`.
- [ ] **M5a · baselines and change** — Git, the tree at a revision (`GitTree`, with a contract
      test against `WorkingTree` — moved here from M2, its first consumer), baseline resolution,
      the guard, change requests
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
8. `impact` on CR-001's two changed requirements (`REQ-BCN-05`, `REQ-BCN-06`) shows their
   existing downstream items and upstream agreement clauses at a documented pin. The new
   `REQ-BCN-11` is included when explicitly supplied at a pin where it is declared; before
   declaration, recognizing its reservation belongs to M5a. The walk cannot infer a new
   requirement or agreement clause. One `Assumes` added in the client repo is traversed and
   raises no gap. CR-002 is the later classification change affecting all eleven requirements.
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

- *Settled in M2a:* an ID's literal start is derived from its pattern; `id_prefix` is given only
  when the pattern starts with no literal text.
- *Settled after M2a:* `[schema]` with a path **and** a digest stays an error — three forms, not
  four; pinning the project's schema is the ledger's import's job (D9). The schema's unused
  `profile` key is **dropped** until a profile has a file of its own — adding it back breaks no
  file, removing it later would. Lands in M2, with D4/D8's note.
- *Settled after M2a:* M2 is cut in two vertical steps (`status`, then `thread` with the parity
  script), and `GitTree` moves to M5a.

- `Status: withdrawn` needs semantics: a withdrawn item should stop raising coverage gaps.
  **Moved to M5a** — withdrawing is an act under change control; until then a withdrawn item
  still raises its gaps.
- A test function's digest uses `ast`; its dump format changed in Python 3.13. Harmless while
  both sides are computed at run time — a format question once slice 2 writes the lock.
