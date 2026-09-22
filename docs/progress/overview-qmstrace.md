---
summary: Repo-level progress tracker for qmstrace — what has landed, what is in flight, what comes next, what is deferred, the open questions attached to scheduled work, and the learnings that now bind the design. Pointers only; the content lives in the docs it links to.
read_when:
  - starting a session in this repo — read this first
  - deciding what to work on next, or whether something is already settled
  - finishing a piece of work — update this file in the same change
---

# qmstrace — progress

**Phase: engine slice 1 is being built.** The design is settled and recorded; the authoring
workflow was proven first on a test bed with a throwaway stand-in, whose scenarios now seed
the engine's tests. This tracker points; it does not restate. Terms follow
[`CONTEXT.md`](../../CONTEXT.md).

Design work is cited by document and by test-bed tag. Engine milestones may cite a commit
hash — as a pointer, never as evidence (see *Done*).

## Done

- [x] Exploration of the three predecessors and the standard; the framing as a compiler —
      sources → strict intermediate data → formal targets — [PRD](../req/qmstrace-prd.md) § As-is story
- [x] Glossary, 52 terms across four clusters — [`CONTEXT.md`](../../CONTEXT.md)
- [x] PRD draft v0.1 — [`docs/req/qmstrace-prd.md`](../req/qmstrace-prd.md)
- [x] Decisions D1–D10 with the alternatives that lost —
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
- [x] **D8 — a requirement carries one `Category`** from the profile's list; the functional /
      non-functional split is derived, so a template with those two headings still renders
- [x] **E4 — a second product repo joins.** One home per requirement held; the shared schema
      in the ledger caused no friction (**D9, provisional**); the import of two repos at a pin is
      clean, deterministic and sensitive to the pin. The agent wrote no marker across the repo
      boundary — rightly: the links available were false, or true and misplaced. The link it
      wanted is a dependency, which the model lacks. Its own mutation pass found a marker that
      could not fail. Test-bed tag `e4-end`; findings in both design docs
- [x] **Nine open decisions put to the developer; seven settled** — `Assumes` adopted as a
      dependency link that counts toward no coverage rule (**D10**); each product repo carries a
      generated, verified copy of the project's trace schema (**D9**, decided); an explicit,
      recorded review may clear a suspect before the next baseline, added later (D7); the slice
      order stands, with the ledger half worked through in parallel; the ledger's verbs sit
      under a group of their own; machine-readable output comes later, findings structured
      from the start; **a tracker may cite commit hashes** — as pointers, never as evidence —
      and the skill's ban on typed facts covers traced documents and test results only
- [x] **Two namings settled.** *Profile* is the standard's catalogue, *trace schema* the
      project's declaration, *trace configuration* a product repo's own file — three levels,
      three owners. *Auditor* replaces *assessor*: it covers internal and certification audits
      alike, matches the team's usage, and sits with *audit evidence*; the 29110 scheme's own
      word is kept as a note

## Now

- [ ] **Engine slice 1 — the product-repo half.** Planned, reviewed and approved; milestones,
      decisions and acceptance checks in [`slice-1-product-repo-half.md`](slice-1-product-repo-half.md).
      The fixtures come from [`docs/tests/scenario-catalogue.md`](../tests/scenario-catalogue.md).
      M0, M1 (scaffold and dry gate), M2a (the configuration), M2 (`status`, end to end), M2c
      (the user manual, live at <https://qmstrace.netlify.app/>), M2b (`thread`, the parity
      script), M3 (`check`, `rules`, coverage gaps; pull request 8, `ba2e0ca`) and M3b
      (`impact`; pull request 9, `23c80a5`) have landed. **M4 — `results` — is built and locally verified**,
      on `codex/m4-results`, awaiting PR review. Its 419-test dry gate, manual build,
      E1 counts and seven mutations pass; verification detail is in the slice tracker.
      M5a (baselines and change) follows M4 review.
      The four M3 manual pages were verified to return HTTP 200 on 2026-09-21.
      Both M3b manual pages were also verified in production, including their expected output
      examples, on 2026-09-21.

## Next

- [ ] **Grilling session** on the ledger half: the event shape, work-product states for
      non-document evidence forms, how a signature on a Word copy becomes an event — and, new
      from E4, the recorded basis of an inspection, which is a verification record
- [ ] **E5 — the five-step audit demo** against the bed, once the engine has a ledger
- [ ] A real session launched by a person in a test-bed repo, to confirm what the spawned
      teammates showed

## Deferred

- **E2 — option C as a comparison.** Not needed to choose; kept as the on-ramp scenario for an
  existing repo with no markers.
- **The real pilot.** The documentation repo for the live certification audit stays as its plan
  declares; nothing changes there mid-audit.
- **Collectors, the conformance view, the trace browser, a second profile** — PRD P1/P2.
- **`VISION.md`.** Not earned yet. Candidate invariants are accumulating under *Confirmed
  contracts*; propose it once they have survived an engine slice.

## Open questions

Attached to scheduled work; standalone ones live in the PRD. `rg 💡` lists every marker.

- **A lint that every commit hash cited in a tracker exists** — agreed; a repo-hygiene check
  rather than an engine feature. One wrong hash was typed by an agent in E1.
- **`Verify-by: inspection` is a free pass** until an inspection has a recorded basis.
- **"Every design element needs a test" can push a decorative tag.**
- **Derived IDs are not immutable** — a module's path, a test function's name. Not exercised.
- **A cross-repo open question has no home**: whether an agent re-registers after the gateway
  forgets it sits in two trackers as two half-questions. It belongs to the project.

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
- **The thread between two repos runs through the origin clause**, not through a direct link.
- **A true marker is not sufficient: the verdict has to land on whoever can act on it.**
- **The check cannot tell a true marker from a decorative one** — breaking the code can, and
  the author does it, not only the reviewer.
- **A pin with no trace configuration is an error, not an empty project.**
- **Every command has a fixture.** The stand-in's one regression was the one command not
  re-run after a rewrite.
- **The applicable baselines are the ones reachable from `HEAD`.** Maintenance lines and
  hotfix branches see their own; the pull-request gate runs on the merge result.

## Related

- Requirements: [`docs/req/qmstrace-prd.md`](../req/qmstrace-prd.md)
- Design: [`data-architecture.md`](../design/data-architecture.md) ·
  [`surface-architecture.md`](../design/surface-architecture.md)
- Experiments: [`docs/tests/beacon-authoring-experiment.md`](../tests/beacon-authoring-experiment.md)
