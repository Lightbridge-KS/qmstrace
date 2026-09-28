---
summary: The E6 dogfooding tracker — the phases and STOP points of the run that measures PRD success criteria 5 and 6 on qmstrace traced by its own ledger; what is done, what the developer decided, what is next. Kept on the unmerged branch experiment/e6-measures, beside the experiment doc, so the agent under test cannot read it.
read_when:
  - resuming E6 — which STOP is next and what was decided at the earlier ones
  - preparing, launching or verifying run A or run B
---

# E6 · dogfooding — progress

**Parent:** [qmstrace progress](overview-qmstrace.md) · **Protocol, brief and measures:**
[the experiment doc](../tests/dogfooding-experiment.md) · **Branch:** `experiment/e6-measures`,
unmerged until the runs end. The tracker on `main` stays neutral — it says only that
qmstrace is traced by its own ledger and that the gate is not green yet — because agent A
reads it.

**Updated 2026-09-28. Now: STOP 4** — the developer approves the measures, the brief and the
seed, and answers the experiment doc's 💡 points.

A STOP is where the developer acts or approves; the driver does not pass it alone.

## Phases and STOPs

| Step | What | Status | Pointer |
|---|---|---|---|
| **STOP 1** | M9b, the schema copy, merged; the engine pinned from the merge | ✔ | #18 · `f4e770b`; the first pin, since superseded |
| **Phase 2 · STOP 2** | The ledger repo drafted; its agreement and schema approved; pushed, private | ✔ | `qmstrace-ledger` · `a3faeab` |
| **Phase 3 · STOP 3** | The setup pull request: meta-tests moved, the constraint amended, the trace configuration and schema copy, `init` | ✔ | #19 · `63b5c7f` |
| M9c, before run A | The skill moved where a harness lists it; the engine re-pinned from the merge | ✔ | #23 · `02caed1`; wheel `d4e1dab1…2365` |
| **Phase 4** | The experiment doc: test bed, verbatim brief and skill listing, measures E6-A-1…14, seeded sample, caveats | ✔ | this branch · `68dc0fd`, `ced08a4` |
| **STOP 4** | Approve the measures, the brief and the seed; answer the doc's 💡 points | **now** | the experiment doc |
| **STOP 5** | Pre-launch, from a fresh driver session on `main`: the checklist in the experiment doc | next | |
| Phase 6 | Run A — a fresh teammate `qmstrace-dev-e6a` gets the brief | | |
| Phase 7 · STOP 6 | The driver verifies A against E6-A-1…14; A's branch pushed and a draft pull request opened with A's text; the developer's review is itself a measure | | |
| **STOP 7** | The developer approves the SRS and cuts `baseline/requirements/1`; the CI gate policy is decided | | |
| Phase 8 · STOP 8–10 | Run B: the developer picks the request (STOP 8) and its measures E6-B-… are committed here first; B stops and hands over; CR-001 accepted in the ledger (STOP 9); B's pull request (STOP 10) | | |
| Phase 9 | Results into the experiment doc; findings into the design docs; this branch merged; this tracker closed | | |

## Decided so far

- **Dogfooding decision form, 2026-09-27:** the engine repo's constraint becomes *no other
  project's data*; the ledger repo `qmstrace-ledger`, private; key `QMT`, giving `REQ-QMT-nn`
  and `DSN-QMT-nn`; origins are agreement clauses; the first SRS covers slice 1 as built; the
  full chain, rules G01–G06; two fresh agents.
- **Planning, 2026-09-27:** the schema-copy command first (M9b); the meta-tests move to
  `tests/meta/` with level `meta`; the measures on this unmerged branch; teammates launched
  in-process, as in E1–E4.
- **2026-09-28:**
  - design elements may be declared in `docs/structure/*.md` as well;
  - the skill moves to `.agents/skills/qmstrace/`, with a link from `.claude/skills/` when the
    repo has `.claude/`, before run A (M9c);
  - this tracker lives here, not on `main`.

## Open

- **At STOP 4:** the experiment doc's four 💡 points — `qmstrace` listed as a bare name in the
  brief; the brief names the gate; seed `29110` with six requirements and five modules; a
  negative fetch refspec for the run.
- **At STOP 5:**
  - the launch commit — `main` has moved past `02caed1` with docs-only commits, so the pin
    built there stays valid;
  - the memory index the teammate inherits: it names the test bed, the fresh-agent rule, and
    now the background fetch and this branch;
  - `<workspace>/pr-drafts/` created empty.
- **Seen on the way:** a background fetch stored `origin/experiment/e6-measures` in the
  working copy twice on 2026-09-28, each time removed by hand. The experiment doc
  carries it as a pre-launch check, a caveat and a 💡.
