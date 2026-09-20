---
summary: Product requirements for iso-trace — the problem, users, as-is story, goals and non-goals, prioritised capabilities, slices, constraints, success criteria and open questions. DRAFT v0.1.
read_when:
  - deciding whether something is in scope, or which priority it has
  - planning a slice or writing a design doc that must serve a stated capability
  - a requirement turns out to be wrong — edit it here, in place
---

# iso-trace — Product Requirements

**Status:** draft v0.1 (2026-09-20). Evolves in place: a wrong requirement is edited, not
superseded. Capability IDs are assigned when a design doc, milestone or test first cites one.
Terms follow [`CONTEXT.md`](../../CONTEXT.md).

## Problem

A very small team running ISO/IEC 29110 with coding agents already produces the facts an
assessor asks for. They are scattered across five places: the repo memory of product repos,
test code and test runs, the Git host's issues, pull requests and tags, the tracker, and
signed Word documents in the document store. Three things that should connect them do not
exist as data:

- **State** — which work product is in which state, and what evidenced each transition.
- **Traceability** — origin ↔ requirement ↔ design ↔ code ↔ test ↔ result, many-to-many, in
  both directions.
- **Evidence location** — for any claim: what, when, where, and how.

Today all three are prose and hand-typed tables, and hand-typed tables desynchronise at the
first change. The legacy product's signed reports show it: the traceability matrix has a
column headed "Unit Test ID" that lists design elements; no non-functional requirement is
traced anywhere; there is no design hop, no link to a test result, and no origin.

The standard cares about transitions, not files. A complete file set with no evidence of
state transitions still fails.

## Users

| User | Works in | Needs |
|---|---|---|
| **Developer-manager** with a coding agent (primary) | product repos, the ledger repo, a terminal | Author traceability once, where the knowledge arises; see what is missing; never retype a matrix |
| **The coding agent** (first-class) | the same, through a command line | A self-describing surface, compact output, findings that say what to do next, stable exit codes |
| **Reviewers and approvers** — analyst, quality representative, consultant, internal customer | Word and the document store only | Read, edit and sign documents without installing or learning anything |
| **Assessor** (read-only) | whatever is put on the screen | Follow a thread from claim to evidence in minutes |
| *Later:* the wider development team | their own product repos | The same, without the first user's help |

## As-is story

A developer-manager builds a fleet-management feature with a coding agent. Requirements,
design and a progress tracker live in the product repo's repo memory — casual, English,
written for the agent. Separately, in a documentation repo, the same requirements are
rewritten as a formal bilingual specification with stable IDs, and a traceability matrix is
typed by hand with a dash in every cell that is not yet known. The tests in the product repo
carry no requirement IDs, so the code-to-requirement link exists only in memory and in that
matrix.

A consultant edits the project plan in Word in the document store; the edits are retyped
into the source by hand. A document is issued and signed; nothing in the repository knows,
and the next render can overwrite the staged copy with something that looks newer.

When an assessor asks to trace one requirement forward to a passed test, the answer is
assembled by hand across three repositories and a drive.

Three earlier efforts each solved one part:

| Predecessor | What it proved | What it lacks |
|---|---|---|
| A documentation repo rendering Quarto to the institutional Word template, drafts only, issues recorded as Git tags | The render targets and the drafts-only invariant | Any data behind the tables; all mappings are prose |
| A retrofit tool: fetch → normalise → agent curates → gate → render, from Git-host history | The split between agent and deterministic code; evidence harvesting | Anything beyond three change-record forms |
| An unbuilt design spec for a traceability data layer | The entity/link shape and three-tier validation | Work products, states, evidence; it hard-codes one project's ID scheme |

iso-trace is the shared kernel under all three.

## Goals

1. **One ledger per project answers the assessor's questions by query.** The acceptance test
   is the five-step assessment demo under *Success criteria*.
2. **Traceability is authored once, where the knowledge arises, and never retyped.**
3. **Every transition and every test result is an event** with collected facts and a pinned
   evidence pointer.
4. **Formal documents are projections of the ledger** — generated tables, reconciled prose.
5. **The agent is a first-class user of a deterministic core.** Agents propose meaning;
   collectors record facts; humans approve.
6. **The standard is data.** A second profile, or a project with a different ID scheme, needs
   no engine change.

## Non-goals

- A document editor, or a replacement for the organisation's document-control procedure.
  Revisions are assigned and signed there; the engine never assigns one.
- A system of record for tasks, issues, code or signatures. The engine holds pointers.
- A platform — web application, database server, multi-tenant service — until a team need is
  demonstrated. A static, generated read-only view is in scope; a service is not.
- Retro-documentation. No back-dating, and no dated record created before its event.
- Passing the current pilot assessment. A flat table passes it. The engine pays off at the
  first change request and the second project.
- Anything that touches patient data.

## Capabilities

### P0 — without these it is not the product

| Capability | Notes |
|---|---|
| Load a profile and a trace schema | ISO/IEC 29110 Basic; the pilot project's ID scheme |
| Extract markers from Markdown/Quarto sources and from test code | First test framework: the pilot's |
| Import product repos at a pin | Several repos into one ledger |
| Build the ledger and write the trace lock | The lock's diff is what a reviewer reads |
| Check — violations always fail; gaps fail from their stage on | Every finding in one pass, each naming file and line; stable exit codes |
| Trace one item forward and backward | The assessor's fourth question |
| Record test results from a test-run report | Appended per run, tied to a commit; never typed |
| Emit tables as data for the existing render machine | Replaces the hand-typed traceability matrix; the engine knows nothing about Word |
| Work-product register — work product → evidence form → state | Replaces the prose checklist |
| Record an event with a pinned evidence pointer | Including a document's issue; generalises today's per-document Git tag |
| Status — one compact view of states, coverage, gaps and suspects | The agent's and the human's entry point |

💡 Work-product state and events are listed as P0 but scheduled as the second slice. If the
first slice should stay purely traceability, they still belong here — state tracking is one
of the three reasons the project exists — but the call on ordering is open.

### P1 — makes it hold up under change

| Capability | Notes |
|---|---|
| Suspect detection by content hash | Links, and rendered documents against their source |
| Impact of a change request | Which requirements, design elements, tests and documents are touched |
| The five-step assessment demo, one command per step | See *Success criteria* |
| Collector for the Git host | Pull requests, reviews, tags, releases, issues — with the host's own timestamps |
| Drift check on a Word document | IDs and generated tables compared with the ledger at the document's pin |
| Reconcile helper | Word copy → comparable text → a diff the agent can turn into a patch |
| Conformance view | Each normative requirement of the profile → the evidence that answers it |
| Static read-only trace browser | Generated; for the person driving the screen during an assessment |
| A second trace schema | The legacy product's ID families, to prove nothing is hard-coded |

### P2 — later

Collectors for the tracker and the document store · a second profile (medical-device
software lifecycle) · stored, reviewable translations that become suspect when their source
changes · checks running in product-repo pull requests · a team-facing interface.

## Slices

Incremental, each end to end, each leaving something in use.

1. **Generated traceability record for the pilot project.** Trace schema, markers, import,
   ledger, trace lock, check, emitted table rendered into the existing Word template. Done
   when that document contains no hand-typed ID.
2. **Work-product register and events.** The prose checklist and the per-document issue tags
   become ledger data; the register is generated.
3. **Test results.** Results collected from test-run reports fill the last columns of the
   traceability record.

Then P1, ordered by what the pilot's first real change request needs.

💡 Slice 1 runs against a pilot that is under live assessment. The alternative is to prove it
on a copy of the pilot's data first and switch the real document over only once the generated
table matches the hand-typed one cell for cell.

## Constraints

- **Text in Git is the ledger.** The database is built in memory on each run and never
  committed; the pull-request diff stays the verification evidence.
- **Pointers, not copies.** Evidence stays in its home system.
- **Facts are collected, never typed.** Dates, commits, verdicts, actors and states come from
  a home system's own log. An agent may propose links, prose and translations — not facts.
- **A named human approves.** Agent-drafted content is marked as such and carries its
  reviewer.
- **IDs are immutable and never reused.**
- **Reviewers install nothing.**
- **Drafts only.** Nothing the engine emits can be mistaken for an issued revision.
- **The engine repo holds no project data.** Fixtures are anonymised; no patient data, no
  site network facts, no signatures.
- **Deterministic core.** Same inputs at the same pins give the same ledger, findings and
  tables.

## Success criteria

1. **The five-step assessment demo runs on the pilot, one command per step:**
   list every work product with its version history · point to the baselined requirements,
   design, test cases and code · follow one change request end to end · trace one requirement
   forward to a passed test · show a verification or validation record for every work product
   the plan marks for one.
2. The pilot's traceability record renders with **zero hand-typed IDs**.
3. A deliberately broken fixture — an unknown ID, a link in the wrong direction, a coverage
   gap past its stage — fails the check with **all** findings listed, each naming file and
   line.
4. A second trace schema with different ID families runs with **no engine code change**.
5. An agent given only the built-in help and the status view **finds a gap and proposes the
   fix as a pull request** with no other instruction.

## Open questions

- **Where is a requirement's text canonical?** *Answered provisionally* — in the product
  repo's repo memory, with the formal bilingual specification a projection of it; see D5 in
  [`data-architecture.md`](../design/data-architecture.md), which also keeps the two options
  that lost. Under test in [`docs/tests/`](../tests/beacon-authoring-experiment.md). What
  stays open: how a stored translation is reviewed and when it becomes suspect.
- What is the smallest event shape that answers what, when, where and how for every evidence
  form — including forms with no document, such as a repository or a tracker feature?
- How does a transition that happens outside any repository — a signature on a Word copy —
  become an event without anyone typing a fact?
- Which states does a work product with a non-document evidence form actually pass through?
- Marker syntax for each source type, and the ID conventions a trace schema may declare.

## Related

- Settled design decisions and their rejected alternatives:
  [`docs/design/data-architecture.md`](../design/data-architecture.md)
- The standard's work products in brief:
  [`docs/references/iso29110-work-product-cheatsheet.md`](../references/iso29110-work-product-cheatsheet.md)
- Legacy traceability example: `_examples/` at the repo root — real signed documents, kept
  locally and never tracked.
