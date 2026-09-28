# qmstrace — Agent Guide

An engine that keeps the **state, traceability and audit evidence** of a software project's
work products under ISO/IEC 29110, so an auditor's questions are answered by query instead
of by assembly. **Phase: the first engine slice is being built** — see the slice tracker under `docs/progress/`. (`CLAUDE.md` is a symlink to
this file.)

## Orientation — read in this order

1. [`docs/progress/overview-qmstrace.md`](docs/progress/overview-qmstrace.md) — where the
   work stands, what is next, the learnings that already bind the design
2. [`CONTEXT.md`](CONTEXT.md) — the vocabulary. Three vocabularies collide here (the
   standard's, the organisation's document control, the engine's); this file says which wins
3. [`docs/req/qmstrace-prd.md`](docs/req/qmstrace-prd.md) — what and for whom
4. [`docs/design/data-architecture.md`](docs/design/data-architecture.md) — decisions D1…,
   each with the alternative that lost, and the product-repo half of the model
5. [`docs/design/surface-architecture.md`](docs/design/surface-architecture.md) — the commands,
   the findings contract, the stanza and the skill, as their users meet them
   · [`system-architecture.md`](docs/design/system-architecture.md) — who and what the tool touches
   · [`docs/structure/codebase-blueprint.md`](docs/structure/codebase-blueprint.md) — **before writing
   engine code**: the tree, the import matrix, where a change lands, what is deliberately absent
6. [`docs/tests/`](docs/tests/) — the experiments: what was tested, how, and what was found;
   and the scenario catalogue the engine's tests are built from

## The shape, in one picture

```
product repos  (code, tests, repo memory + markers)     developer hat — daily, agent launched here
      │  import at a pin                                 ↔ the standard's software-implementation process
      ▼
ledger repo    (the project's ledger, controlled-document sources, agreement, records)
      ▲                                                  manager hat — occasional
      │  installed into                                  ↔ the standard's project-management process
qmstrace      (this repo: the tool — it holds no other project's data)
```

## Rules for working here

- **Use the glossary's words.** Before introducing a term, add it to `CONTEXT.md`. When
  putting a decision to the developer, define any coined term on first use and lead with a
  concrete example.
- **Decisions are recorded inline** in the design doc they belong to, with the rejected
  alternative and why. No ADRs yet; they start when a settled doc is amended.
- **A design doc holds what is settled.** Findings from an experiment graduate into
  `docs/design/`; they do not stay stranded in `docs/tests/` results.
- **Update the tracker in the same change** as the work it describes.
- **Verify, don't assert.** A claim in a results section was checked by whoever wrote it — not
  copied from an agent's report. Say what was verified and what was not.
- **No other project's data in this repo**: no real names, signatures, patient data or site
  network facts. The one trace it carries is its own. `_examples/` and `_playground/` are
  local and gitignored — never commit from them.
- **Attention markers.** 💡 marks the few spots that need the developer's judgement;
  `rg 💡` is the review checklist. Budget them.
- **A milestone ships its manual pages.** The user manual (`contents/`, published) grows with
  the code, and a page that must warn about a caveat is a design finding — how, in
  [`docs/dev/writing-the-manual.md`](docs/dev/writing-the-manual.md). What the tool prints is
  included from a golden, never retyped.

## Experiments

The test bed lives **outside this repo**, in a sibling workspace: `../_tests/beacon-experiment/`
— a product repo, a ledger repo, and a throwaway stand-in for the engine (`_engine-stub/qmstrace`)
with a stand-in skill. Its own README describes it; `docs/tests/` says what is tested and why.

- **A teammate agent is always fresh, never a fork** — a fork inherits the conversation that
  designed the experiment. It gets the repo path, "read `AGENTS.md` first", a skill listing,
  and the developer's brief. It is not told what is being measured.
- **Measures are fixed in `docs/tests/` before the run.** The driver plays the human developer
  and verifies the agent's claims independently — mutation checks, Git history, reproduction.
- Raw material → `_playground/YYYY-MM-DD_slug/` with a `NOTES.md`; distilled results →
  `docs/tests/`. End states are tagged in the test-bed repo (`e1-end`, `e3-end`, …).
- **The stand-in is throwaway.** Do not grow it into the engine. Its findings graduate into
  the design docs; its scenarios will seed the engine's fixtures.

## Settled so far, in one line each

Text in Git is the ledger; the database is built in memory and never committed · pointers to
evidence, never copies · agents propose meaning, collectors record facts, humans approve ·
markers at the downstream end, a generated trace lock for the diff · one ledger per project ·
a baseline is a tag the project already cuts. The reasoning is in the design doc — read it
before reopening any of these.

## Git

Conventional Commits. **GitHub Flow from the first engine slice on**: a branch and a draft
pull request per milestone, with the dry gate green — format, lint, types, tests. A reviewed
pull request is what this product calls a verification record. **Docs-only changes to
`docs/` may still go straight to `main`** — never `contents/`: the manual is published, so it
goes through a pull request. Commit only when asked. The remote is a private repository.

<!-- qmstrace:begin — generated; edit qmstrace.toml, not this block -->
This repo is traced for project **QMT**; subjects: qmstrace (QMT).
- Read `.qmstrace/skill/SKILL.md` before changing requirements, design or tests.
- Local items: requirement `^REQ-QMT-\d{2}$` in `docs/req/*-srs.md`; design_element `^DSN-QMT-\d{2}$` in `docs/design/*.md`, `docs/structure/*.md`; component `python-module` in `src/**/*.py`; test_case `pytest` in `tests/**/test_*.py`. IDs are never renumbered or reused.
- Start with `qmstrace status`; `qmstrace rules` prints the actual schema and coverage rules.
- Use `qmstrace thread ID` and `qmstrace impact ID…` before changing connected items.
- Run `qmstrace check` while authoring; `qmstrace check --strict` is the coverage gate.
- Frozen changes and controlled additions need a fresh accepted change request; inspect the governing baseline and request evidence before editing.
- A marker states a fact. Break the behavior in a disposable test and confirm the tagged test fails; restore the source afterwards.
- Suspects need review even after edits or passing tests; `qmstrace check` lists every reason.
- Collect facts with tools; never invent dates, verdicts, test results or approvals. Keep unavailable-source notices visible.
<!-- qmstrace:end -->
