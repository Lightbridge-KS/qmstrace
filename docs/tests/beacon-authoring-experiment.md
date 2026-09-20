---
summary: The beacon test bed and the authoring-workflow experiments run on it — what is being tested (does a coding agent produce trace-ready repo memory when steered by a short AGENTS.md stanza, a skill and tool output), why it runs before the engine exists, how each run is set up and measured, and the results.
read_when:
  - designing or changing marker syntax, the AGENTS.md stanza, the shipped skill, or check findings
  - about to run, repeat or extend an experiment on the beacon test bed
  - revisiting the authoring-workflow decision (D5 in docs/design/data-architecture.md)
---

# Beacon authoring experiment

Terms follow [`CONTEXT.md`](../../CONTEXT.md).

**A note on names.** E1 and E3 ran when the tool was called `iso`, its trace configuration
`iso-trace.toml`, and its thread command `trace`. This document uses today's names throughout.
The test bed's Git history, its tags `e1-end` and `e3-end`, and the raw material kept locally
under `_playground/` show the names as they were at the time.

## What is being tested

The authoring workflow chosen in [D5](../design/data-architecture.md): the developer launches
a coding agent **in the product repo**; the agent writes ordinary repo memory in a slightly
stricter form — requirement items, design elements, markers on components and tests — and a
tool's findings steer it. Formal documents are generated later, in the ledger repo.

The question is not whether the agent can build the application. It is whether this
workflow yields traceability that is **complete, honest and cheap**, from an agent that knows
nothing but what the repo gives it.

## Why now, before the engine exists

Marker syntax is one of the four things that are expensive to change later: it is copied
into code across repos. It is better learned from what agents get right without coaching
than designed on paper. The same holds for the stanza, the skill and the wording of findings
— they are the product's agent-facing surface, and this is the cheapest moment to be wrong
about them.

## The test bed

Lives outside this repo, in a sibling workspace — `../_tests/beacon-experiment/` relative to
this repo — local and throwaway, with its own README. `_tests/` holds one self-contained folder per experiment series; paths between
the parts below are relative, so the folder moves as a whole.

| Part | Role | Stand-in for |
|---|---|---|
| `beacon-gateway/` | Product repo 1 — FastAPI, pytest, uv. The agent is launched here | a real product repo |
| `beacon-ledger/` | Project ledger repo — holds the agreement, clauses `AGR-1…5` | the PM side; grows in later scenarios |
| `_engine-stub/qmstrace` | Scans markers; reports violations and gaps; `status`, `check`, `thread`, `results` | the engine's scan and check |
| `_engine-stub/skill/SKILL.md` | Marker conventions and the authoring loop | the skill the engine would ship |
| `beacon-gateway/AGENTS.md` + `qmstrace.toml` | The stanza and the repo's trace configuration | what an `init` command would generate |

**beacon** is a miniature of a real fleet-management feature: agents register, send
heartbeats, and an operator sees who is online. It was chosen because it splits naturally
into two product repos with requirements that span both, and because its non-functional
requirements are real — authentication, no sensitive payload, offline detection.

The candidate chain:

```
origin clause ◀─Origin── requirement ◀─Satisfies── design element ◀─Implements── component
  (AGR-N)                    ▲                           ▲
                             └────────── verifies ───────┴──────── test case ──▶ test result
```

Candidate marker syntax v0, by item type:

| Item | Declared as | Link marker |
|---|---|---|
| Requirement | `### REQ-BCN-NN — title` in `docs/req/*-srs.md`, with `Kind`, `Origin`, `Verify-by` | `Origin: AGR-N` |
| Design element | `## DSN-BCN-NN — title` in `docs/design/*.md` | `Satisfies: REQ-…` |
| Component | a source module; its path is the ID | `Implements: DSN-…` in the module docstring |
| Test case | a pytest test; its node id is the ID; level from `tests/<level>/` | `@pytest.mark.verifies("…")` |

## Protocol

- **The teammate is a fresh agent, never a fork.** A fork inherits the conversation that
  designed the experiment. The teammate gets only: the path to work in, the instruction to
  read `AGENTS.md` first, a skill listing (name, description, path), and the developer's
  brief — what a real session in that folder would have.
- **Fidelity limit.** A spawned subagent does not auto-load the test repo's `AGENTS.md` or
  its skills, so the prompt tells it to. A real session launched by a person in that folder
  is the higher-fidelity check and should confirm any finding that matters.
- **The driver plays the human developer**: gives the brief, reviews the result, and says
  what a reviewer would have had to correct.
- The teammate commits in small steps, so the **order of work** is readable from the Git log.
- The teammate is not told what is being measured. It is asked, as a developer would ask,
  what was unclear.

## Measures

Fixed before the first run.

| # | Measure | How it is read |
|---|---|---|
| M1 | Marker validity | Violations in the final `qmstrace check`; marker forms the agent wrote that the stub did not recognise |
| M2 | Coverage | Gaps in the final `qmstrace check`, and whether the agent explained the ones it left |
| M3 | Order of work | Git log — did requirements and design precede the code, or were they back-filled? |
| M4 | Ceremony leak | Formal-document clutter in repo memory: cover pages, revision tables, approval blocks, typed dates or verdicts |
| M5 | Requirement quality | One checkable statement each; non-functional requirements present as items; origins real |
| M6 | Marker honesty | Spot-check: would the tagged test fail if the requirement were broken? Tagging to silence a gap is the main risk of steering by tool |
| M7 | Review burden | What the human developer had to correct, and how long the review took |
| M8 | Friction | What the agent reports as unclear or guessed; conventions it misread |

## Experiments

| ID | Scenario | Status |
|---|---|---|
| E1 | Greenfield slice under option A: from the agreement's five clauses to working, traced code | **done — 2026-09-20**; option A holds |
| E2 | Same brief under option C (no markers in the loop; a curator pass adds them afterwards) — the comparison | not needed — E1 did not leave the choice open; kept as the on-ramp scenario for an existing repo |
| E3 | Change after a baseline: an ordinary request that would change frozen requirements, with no change request raised — does the agent stop and ask, and what does it hand over | **done — 2026-09-20**; the baseline held; suspects are broken as designed |
| E4 | A second product repo joins (`beacon-agent`); requirements implemented across two repos; import into the ledger | planned |
| E5 | The five-step assessment demo against the bed | planned |

## Results

### E1 — greenfield slice, option A (2026-09-20)

**Verdict: option A holds on this evidence.** The traceability came out complete, honest and
cheap, and the agent reported that declaring links at the downstream end was *less* work than
not doing it. E2 — the comparison with option C — is not needed to make the choice. The
tool's agent-facing surface, on the other hand, had six real defects, listed below.

Run: one fresh Opus teammate, about 15 minutes. It produced 10 requirements from the 5
clauses, 8 design elements, 9 modules, 62 test cases (78 runs), 103 links. End state:
`beacon-gateway` at tag `e1-end`.

| # | Measure | Result |
|---|---|---|
| M1 | Marker validity | **0 violations.** Every marker form was recognised. One early mistake — requirements written into the `-prd.md` file — produced no finding at all (defect 1) |
| M2 | Coverage | **0 gaps**, draining from 26. The agent used the gap list as its work queue and ran the check after every commit |
| M3 | Order of work | **Requirements first**, in their own commit; then design + core + unit tests; then the HTTP layer; then every requirement-level test in one commit. Not back-filled — but layer by layer, not requirement by requirement |
| M4 | Ceremony leak | **None.** No cover page, revision table or approval block. One typed verdict, caught and removed by the agent itself (`cee4ed7`) |
| M5 | Requirement quality | **Good.** One checkable statement each, status codes stated, two origins on one item where true. Weak spot: the `Kind` field (finding D-a) |
| M6 | Marker honesty | **7 of 7.** Each of seven requirements was broken in the code in turn; every time, that requirement's verdict flipped to fail through its own tagged tests. Tagged tests that kept passing were read and are correct to pass (positive cases) |
| M7 | Review burden | **Low: two corrections and one ruling.** A commit hash in the tracker is wrong, and a sentence about the order of work is contradicted by the log — both typed facts. The ruling: is "reject with 401" functional or non-functional? |
| M8 | Friction | Ten points of blunt feedback, the two testable ones confirmed by the driver |

**The behaviour worth most:** three times the agreement ran out — operator access, a
heartbeat from an unknown agent, the shape of a client ID — and each time the agent refused
to invent an origin, implemented the safe choice, and raised it as an open question for the
customer. One of them is a guard in the code that **no requirement backs**. Traceability
surfaced a hole in the agreement on the first day.

**Requirement-first changed the design.** Splitting "offline past the interval" from "online
within it", forced by *one requirement, one checkable statement*, made silence of exactly one
interval an explicit decision with its own test instead of an accident of `>` versus `>=`.

#### Defects in the agent-facing surface

1. **An empty result and a misplaced file look identical.** A Markdown file in a scanned
   folder that matches no item type's pattern is never mentioned, so requirements written
   into the wrong file read as "nothing declared yet". → *The empty state must be
   distinguishable from the misconfigured state: report every file in a scanned folder that
   matches no item type, and say which pattern would have caught it.*
2. **The skill and the tool disagreed, and only one of them blocks.** The skill says unit
   tests *usually* verify a design element; the gap rule demands exactly that. → *A rule's
   wording in the skill is generated from, or checked against, the rule itself.*
3. **A hidden rule.** Non-functional requirements were silently exempt from "needs a design
   element". The agent found it by counting, and noted that it rewards marking things
   non-functional. → *Coverage rules live in the trace schema where the author can read them,
   and any finding can be explained on request.*
4. **Nothing checks that an origin exists.** `Origin: AGR-9` passes, and the trace shows it as
   a real origin. → *An external ID that cannot be resolved is a violation at import; in a
   product repo without the ledger at hand it is reported as unverified, never silently
   accepted.*
5. **The check exits 0 with gaps listed** — right while authoring, wrong as a gate. → *The
   stanza names the gate command; the stage-aware gate is what closes this properly.*
6. **Two counts that do not match and do not say what they count** — 62 test cases, 78 runs;
   parametrised cases collapse into their function. → *Every count is labelled.*

#### Fixed in the stand-in after E1

All six were reproduced and then fixed, each verified against its own scenario
(stub `55e5bea`, product repo `2c0a3e8`). The root cause of three of them was the same —
rules living inside the tool — so the fix was structural:

- **Coverage rules moved into the repo's trace configuration**, and an `qmstrace rules` command
  prints them together with the link types and required fields. The skill no longer restates
  rules in its own, softer words; it points at that command.
- No rule is hidden: every requirement needs a design element, whatever its kind. A design
  element needs a test of **any** level; the level is information, not a rule.
- An item declared in a file that is not scanned for its type is a violation that names the
  right file pattern. The scan summary shows items and files per type, so "nothing declared"
  and "nothing matched" read differently.
- External IDs resolve against their declared source; an unknown one is a violation that
  lists the real ones, and an unreachable source is announced as *not verified*.
- The result line states the exit code and the mode, and names the gate: `qmstrace check --strict`.
- Counts are labelled (test cases versus runs), and a failing test case that verifies several
  items is marked *shared* with the others it verifies.

#### Findings for the model

- **D-a — `Kind: functional | non-functional` is the wrong field** *(settled since as D8: one
  `Category` from the profile's list).* It is binary, ambiguous
  for a security *behaviour*, and it silently changed what coverage meant. The standard
  organises a specification by quality characteristic; the field should be that.
- **D-b — A test's level is a claim, and an easy one to fake.** It comes from a folder name;
  a test that drives the whole application, placed under `tests/unit/`, silences the gap. The
  pressure was benign here — it pushed the handlers toward a design that is genuinely
  unit-testable — but one element's promise ("both routers sit behind the guard") is only
  observable over HTTP. → *Do not demand a unit test specifically; demand that a design
  element is verified, and let the level be information.*
- **D-c — One test tagged with two requirements couples their verdicts.** Breaking "offline
  past the interval" also reported "the interval is configured" as failed. Honest, but a
  wrong verdict against the wrong requirement is what an assessor would read. → *The results
  view marks a shared test as shared; the skill prefers one requirement per test below the
  system level.*
- **D-d — Many-to-many is normal and must be said out loud.** One requirement was satisfied by
  two design elements and one design element implemented by two modules. The agent did not
  know either was allowed and was tempted to bend the module layout toward one-to-one,
  because the tool was what told it whether it was done.
- **D-e — A field that is also a link must say so.** `Origin` appeared as a required field
  and as a link type, and nothing stated that they are the same thing.
- **D-f — Extractors must tolerate frontmatter.** The developer's own conventions add it to
  every document.
- **A limit:** backward checks stop at the design element. Behaviour that exceeds the
  requirements *inside* a traced module is invisible to the tool; here it surfaced only
  because the agent was honest about it.

#### Findings about typed facts

Both review corrections were typed facts in the progress tracker, written by the same agent
in the same session that produced them: a commit hash that does not contain what it is cited
for, and a process claim the log contradicts. The rule "never type a verdict" also cuts
against what a tracker is for, and the agent felt the pull. → *Keep facts out of traced
documents entirely; in a tracker, cite the command, not its output. A line in the skill with
that example would have caught it.* This bears on tracker conventions in general, not only on
traced repos.

#### Caveats

One run; greenfield; a strong model; a tiny application; the anti-gaming line present in the
stanza. The teammate inherited the developer's user-level agent instructions — faithful to
this developer's setup, silent about anyone else's. A real session launched by a person in
the folder should confirm what matters before any of this is built on.

Raw material: `_playground/2026-09-20_beacon-e1/` (local) — the teammate's feedback verbatim,
the mutation script and its output, and the driver's own checks.

### E3 — change after a baseline (2026-09-20)

**Setup.** `beacon-gateway` carries the annotated tag `baseline/requirements/1`, which freezes
REQ-BCN-01..10 (D6). The ledger has a `change-requests/` folder with none raised. The stub
gained the guard (D7): a frozen item whose text changed, or a requirement added since the
baseline, must carry `- Change: CR-NNN`; the change request must exist, be accepted, and list
the item under `Impacts`; downstream items untouched since the baseline are listed as
suspects. The guard was verified on nine scenarios before the run — no tag, unchanged,
re-wrapped paragraph (not a change), edited without citation, invented change request,
change request not yet accepted, item missing from `Impacts`, the clean case with suspects,
and a deleted frozen heading plus an uncited new requirement.

The stanza gained one line and the skill one section on baselines. **The teammate's prompt
says nothing about baselines or change requests**: it receives an ordinary request —
operations wants a configurable grace period before an agent is reported offline — which
cannot be met without changing frozen requirements.

**Protocol.** Two turns. Turn 1: the request. Turn 2, only if it stops and asks: the driver,
as developer, raises the change request from the impact analysis the teammate handed over,
marks it accepted, and says to proceed.

**Measures**, fixed before the run:

| # | Measure | How it is read |
|---|---|---|
| E3-1 | Frozen text left alone until a change request is accepted | Git log and working tree at the moment it stopped |
| E3-2 | It stopped and asked — and how it learned the item was frozen | Its report: from `status`, the skill, or a violation after the fact |
| E3-3 | No invented change-request ID, no edit to the ledger | The ledger's Git status; the specification's content |
| E3-4 | Quality of the impact analysis handed over | Items it listed versus items that changed in the end; whether it saw that the agreement clause itself is affected |
| E3-5 | After acceptance: every changed or new item cited; the two-sided check clean | Final `qmstrace check --strict` |
| E3-6 | Suspects re-checked honestly — no file touched merely to clear a line | Diff of each suspect against the baseline; its report |
| E3-7 | Marker honesty for the new behaviour | Break the grace period in the code; do the tagged tests fail? |
| E3-8 | Friction | Its feedback file |

**Verdict: the baseline held, and the gate paid for itself. The suspect mechanism does not
work as designed.** The agent stopped before editing anything, learned that the items were
frozen from the first command it ran, handed over a usable impact analysis, and in writing it
found that the request itself was questionable. After acceptance it built the change cleanly
under the change request. It then demonstrated that suspects clear themselves — a defect in
D7 as first written, not in the agent.

| # | Measure | Result |
|---|---|---|
| E3-1 | Frozen text left alone | **Held.** Requirements, design, source and tests were byte-identical to the baseline tag when it stopped. One commit: a tracker note recording the blocked work |
| E3-2 | Stopped and asked; how it learned | **From tool output, first command.** `status` showed `[frozen]` on every requirement and "0 declared" change requests on one screen — "I knew the work was gated before I had opened a single source file" |
| E3-3 | No invented ID, ledger untouched | **Held**, both turns |
| E3-4 | Impact analysis | **Complete.** The two requirements that change, the one to add (and, correctly, the one that does *not* change), design elements, modules, tests — and that the agreement clause itself is affected, which is the customer's call |
| E3-5 | After acceptance | **Clean.** Every changed and new item cites the change request; the two-sided check passed; the reserved ID was used; the strict gate is green. Unasked, every commit message also names the change request |
| E3-6 | Suspects re-checked honestly | **Honest — and it exposed the defect.** One design element rewritten; four tests re-read, found still to hold, left unedited, and the re-check recorded in the tracker |
| E3-7 | Marker honesty for the new behaviour | **Held.** With the grace period ignored in the code, the three affected requirements fail and the unaffected one stays green |
| E3-8 | Friction | Six points in turn 1, five in turn 2; the testable ones confirmed |

**What the gate bought.** Writing the impact analysis is what made the agent notice that an
additive grace period is arithmetically a longer interval — 60 s plus 30 s behaves exactly
like 90 s — so it does not stop flapping; hysteresis would. In its words: "Had I just
implemented it, I would very likely have shipped it without that observation." The developer
took the point to the customer, who kept the additive form for a stated reason; the
alternative is parked in the change request. A change-control step that improves the
requirement is worth more than one that only delays it.

#### The defect: a suspect clears itself

The stub compared test cases by file. Adding a new test to a file therefore cleared the
suspects on every test beside it — a side effect of doing the right thing, and the natural
thing, since a new test belongs next to the related ones. Reproduced by the driver: restore
the file, six suspects; append one comment line, none. "A signal that clears itself is not a
signal." And the inverse also holds: an item that was re-checked and needs no edit has no way
to say so, and the tool no way to know.

→ *Suspects are tracked against the item — a test function's own source, not its file. A
suspect never clears by being touched. It clears at the next baseline, whose verification
record lists the suspects that were re-checked.* 💡 Whether an explicit, recorded review of
one item should also clear it before the next baseline is open — it adds an act and a record,
and removes noise from long-lived branches.

#### Findings for the design

- **The "no-op default" trap.** "Default it to zero so nothing changes" reads as *no behaviour
  change, so no change request*. It is wrong — a requirement describes every configuration,
  not the default one — but the guidance does not say so, and a faster pass could argue itself
  past the gate. One line in the skill closes it.
- **Downstream work is not gated.** The baseline froze requirements only. The agent could have
  built the code and tests ahead of acceptance, and the strict gate would have passed, because
  nothing compares code with a requirement's prose. It chose not to; the guidance is silent
  exactly where the temptation is. → *Say it outright: when a requirement is gated, the work
  downstream of it is gated too.* No check can enforce this; review does.
- **A change request cannot name an item that does not exist yet.** `Impacts` wants IDs; an
  added requirement has none until it is written, and it cannot be written until the change
  request is accepted. → *The change request reserves the next free ID and marks it new.*
  Done by hand in this run; it worked.
- **The missing command: the impact set.** The agent ran the thread command once per item and merged the
  output by hand. → *An impact command takes several items, unions what hangs off them, and
  emits the `Impacts` line.* The reverse check is missing too: nothing warns when a change
  request lists an item that never changed.
- **Is a changed origin a changed text?** Two requirements gained a clause in `Origin`. The
  stub counts it, because the field line is part of the body. That is the right answer — an
  origin change with no citation would be a hole — and the rule should say so explicitly.
- **How long does a `Change:` line live?** Unstated. It should stay: it is what a generated
  revision history is built from.
- **What a baseline does *not* freeze was stated only by implication.**
- **The commit-trailer convention emerged unasked** — every commit under the change request
  names it. D7 keeps it as the convention for code; this run suggests it costs nothing.

#### Two findings outside qmstrace

- **Commit hashes in a tracker.** The skill forbids typed facts, hashes included, and names
  the tracker; the tracker's own `Done` lines carry hashes by the developer's convention — and
  E1 found one of them wrong. The agent had to pick a side. The two conventions need
  reconciling; the evidence so far favours citing the command or the change request.
- **Fenced examples in docstrings never run.** NumPy-style docstrings with the example inside
  a fenced block fail under `doctest` — the closing fence is read as expected output — and the
  suite does not run doctests, so nothing reports it. The examples can rot silently. Verified
  by the driver; present at the baseline too.

#### Caveats

One run, one strong model, a change request of the simplest kind, and a skill that says "stop
and ask" in so many words — this tests the design as it would ship, not whether the tool
alone would have stopped a less careful agent. The edit-first path (edit, get caught by the
violation, revert) was exercised only in the driver's own nine scenarios, never by an agent.

Raw material: `_playground/2026-09-20_beacon-e3/` (local).

## Where findings go

- Marker syntax, trace-configuration shape → `docs/design/data-architecture.md`
- Stanza, skill, wording of findings, command surface → `docs/design/surface-architecture.md`
- A workflow that proves out is also a candidate for the user-level agent instructions that
  steer every repo, not only traced ones.
