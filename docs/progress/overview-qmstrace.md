---
summary: Repo-level progress tracker for qmstrace — what has landed, what is in flight, what comes next, what is deferred, the open questions attached to scheduled work, and the learnings that now bind the design. Pointers only; the content lives in the docs it links to.
read_when:
  - starting a session in this repo — read this first
  - deciding what to work on next, or whether something is already settled
  - finishing a piece of work — update this file in the same change
---

# qmstrace — progress

**Phase: design, before any engine code.** The authoring workflow is being proven on a test
bed with a throwaway stand-in for the engine; findings graduate into the design docs. This
tracker points; it does not restate. Terms follow [`CONTEXT.md`](../../CONTEXT.md).

Landed work is cited by document and by test-bed tag, not by commit hash — nothing in this
repo is committed yet, and a typed hash is a fact nobody checks (see *Confirmed contracts*).

## Done

- [x] Exploration of the three predecessors and the standard; the framing as a compiler —
      sources → strict intermediate data → formal targets — [PRD](../req/qmstrace-prd.md) § As-is story
- [x] Glossary, 52 terms across four clusters — [`CONTEXT.md`](../../CONTEXT.md)
- [x] PRD draft v0.1 — [`docs/req/qmstrace-prd.md`](../req/qmstrace-prd.md)
- [x] Decisions D1–D7 with the alternatives that lost —
      [`data-architecture.md`](../design/data-architecture.md) § Settled decisions
- [x] Spike: composite foreign keys can police link rules in the in-memory database —
      [`data-architecture.md`](../design/data-architecture.md) § Verified notes
- [x] Test bed scaffolded: product repo, ledger repo, engine stand-in, skill stand-in —
      [`beacon-authoring-experiment.md`](../tests/beacon-authoring-experiment.md) § The test bed
- [x] **E1 — greenfield slice under option A.** Option A holds: complete, honest (7 of 7
      mutations caught), cheap. Six defects found in the agent-facing surface, all fixed in
      the stand-in. Test-bed tag `e1-end`
- [x] **E3 — change after a baseline.** The baseline held: the agent stopped before editing,
      handed over a complete impact analysis, and built cleanly under the accepted change
      request. The suspect mechanism was shown to clear itself; D7 revised. Tag `e3-end`
- [x] **Decided: the stand-in dies.** It stays throwaway; its findings graduate into the design
      docs and its scenarios seed the engine's fixtures. The engine's first slice is planned
      from the docs, not grown from the stand-in
- [x] Baselines checked against a real repository with a release-branch workflow, a
      maintenance line and tagged releases — **D6 amended**: the tag pattern is configuration
      and a release tag is the product baseline; a scope is a subject with item types; an added
      item is judged against its subject's own requirements baseline
- [x] **What the test bed settled has graduated into the design docs**: D5 marked validated;
      six terms added to [`CONTEXT.md`](../../CONTEXT.md) and two revised; the product-repo
      half written in [`data-architecture.md`](../design/data-architecture.md) — the chain,
      marker syntax v0, the trace configuration with rules as data, item text, kinds of
      finding; [`surface-architecture.md`](../design/surface-architecture.md) written; PRD v0.2

- [x] **Renamed to `qmstrace`** — repository, command, trace configuration, skill, stanza
      markers; the thread command is `thread`, since the name already carries *trace*. Reasons
      and the names that lost: [`surface-architecture.md`](../design/surface-architecture.md) §6

## Now

Nothing in flight. The design docs now hold everything the two experiments settled.

## Next

- [ ] **Stand-in, second fix round** — item-level suspects that never clear by being touched;
      an impact command that unions several items and emits the `Impacts` line; a warning when
      a change request lists an item that never changed; configurable baseline tag patterns
      and subject scope; the skill lines E3 asked for
- [ ] **E4 — a second product repo joins.** Requirements implemented across two repos; import
      into the ledger at a pin. Tests D2 and decides where the trace schema lives
- [ ] **E5 — the five-step assessment demo** against the bed
- [ ] **Grilling session** on the ledger half: the event shape, work-product states for
      non-document evidence forms, and how a signature on a Word copy becomes an event
- [ ] `system-architecture.md` (C1–C2) — when the first engine slice is planned
- [ ] Plan the first engine slice; `docs/structure/` just before building

## Deferred

- **E2 — option C as a comparison.** Not needed to choose; kept as the on-ramp scenario for an
  existing repo with no markers.
- **The real pilot.** The documentation repo for the live assessment stays as its plan
  declares; nothing changes there mid-assessment.
- **Collectors, the conformance view, the trace browser, a second profile** — PRD P1/P2.
- **`VISION.md`.** Not earned yet. Candidate invariants are accumulating under *Confirmed
  contracts*; propose it once they have survived an engine slice.

## Open questions

Attached to scheduled work; standalone ones live in the PRD.

- 💡 **Where does the trace schema live?** The test bed put item types, link types and coverage
  rules in the *product repo*, because a local check needs them; the glossary defines the
  trace schema per *project*. With two product repos the two must agree. E4 decides.
- 💡 **May an explicit, recorded review clear a suspect before the next baseline?** (D7)
- **`Kind: functional | non-functional`** should become a quality characteristic (E1, D-a) —
  deferred once to keep E3 to one variable; schedule with the second fix round or E4.
- **Derived IDs are not immutable** — a module's path, a test function's name. Not exercised yet.
- The 💡 markers still open: `CONTEXT.md` (two), the PRD (one), `data-architecture.md` (two),
  `surface-architecture.md` (two). `rg 💡` lists them.

## Confirmed contracts

Learnings that bind the design. All of these have landed in the design docs named under
*Done*; they are kept here as the short list to read first.

- **Steer by tool output first, prose second.** In both experiments the agent learned what
  mattered from the first command it ran, not from the guide.
- **An empty result must not look like a misconfiguration.** Report what was scanned, and any
  item declared where it is not scanned.
- **No rule is hidden, and the skill never restates one.** Rules are declared in the trace
  configuration and printed on request; the skill points at the command.
- **Every count is labelled; a failing test case that verifies several items says so.**
- **A signal must not clear itself.** A suspect that disappears when a file is touched is
  worse than none.
- **Facts are collected, never typed.** Both corrections in E1's review were typed facts — a
  commit hash and a claim about the order of work — written by the agent that produced them.
- **A requirement describes every configuration, not the default one.** A new setting with a
  no-op default still changes the text.
- **When a requirement is gated, the work downstream of it is gated too** — a rule for the
  skill and for review; no check can enforce it.
- **A change request reserves the ID of any item it adds.**
- **Re-wrapping a paragraph is not a change; rewording is; a changed link field is.**
- **The standard lets a project name its own baselines.** The engine recognises the tags a
  project already cuts — a release tag is the product baseline — rather than imposing its own.
- **The applicable baselines are the ones reachable from `HEAD`.** Maintenance lines and
  hotfix branches see their own; the pull-request gate runs on the merge result.

## Related

- Requirements: [`docs/req/qmstrace-prd.md`](../req/qmstrace-prd.md)
- Design: [`data-architecture.md`](../design/data-architecture.md) ·
  [`surface-architecture.md`](../design/surface-architecture.md)
- Experiments: [`docs/tests/beacon-authoring-experiment.md`](../tests/beacon-authoring-experiment.md)
