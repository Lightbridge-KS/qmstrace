---
summary: Data architecture of iso-trace — SKELETON. Holds the settled decisions, their rejected alternatives, verified notes, and the lineage from the earlier traceability spec. The model itself (items, links, work products, events, evidence pointers, ledger layout) is not written yet.
read_when:
  - deciding how trace data, work-product state or evidence is stored or moves
  - about to reopen one of the settled decisions below
  - writing the core model sections of this document
---

# Data architecture

**Status:** skeleton (2026-09-20). Decisions and verified notes only. The sections under
*Not yet written* wait for the open questions in the [PRD](../req/iso-trace-prd.md) to be
worked through. Terms follow [`CONTEXT.md`](../../CONTEXT.md).

## Settled decisions

Greenfield decisions are recorded here, with the alternative that lost and why. They become
ADRs only if a later change amends them.

### D1 — Items and links are authored as markers; the trace lock carries the diff

An item is declared where its content is written (a requirement heading, a design section, a
test), and a link is declared at the downstream end — the test names the requirement it
verifies. The engine extracts markers into the ledger and generates a committed **trace
lock**, so a pull request shows traceability changes as a text diff.

- **Rejected — hand-maintained link tables (CSV-first).** One place to look and editable
  without touching code, but it is a second copy of something the test or the design section
  already knows, so it drifts. The reviewable-diff property that motivated it is kept by the
  trace lock.
- **Cost accepted:** markers are scattered, and each source type needs its own extractor.
- A small hand-authored link file remains available for links with no natural home.

### D2 — One ledger per project, in a ledger repo; product repos carry markers only

A project spans several product repos, and work-product states belong to none of them. The
ledger lives in a ledger repo and **imports** each product repo's markers at a **pin**, which
is also what makes a baseline reproducible.

- **Rejected — a ledger inside each product repo.** No single place can answer whether a
  requirement implemented across two repos is covered, and project-level states have no home.
- **Consequence:** three kinds of repository — the engine (tool, no project data), ledger
  repos (data and controlled-document sources), product repos (code, tests, markers).

### D3 — Prose edits on Word copies are reconciled; generated tables never are

Reviewers work in Word. Prose edits made there are **reconciled** into the source through an
agent-proposed patch reviewed as a pull request. Tables generated from the ledger are
read-only downstream: a change to one is **drift**, corrected in the ledger and rendered
again.

- **Rejected — the Word copy as a terminal artifact.** Simpler, but reviewers' edits are
  retyped or lost, which has already happened once by hand.
- **Cost accepted:** comparing a Word document with its source is noisy around tables, Thai
  text and formatting.

### D4 — Generic item and link storage plus a per-project trace schema

Every project shares one storage shape — items and links — and declares its item types, ID
patterns, allowed link types and coverage rules in a **trace schema**. The profile (work
products, states, conformance requirements) is likewise data.

- **Rejected — one table per entity type with ID formats in the schema definition.** The
  database enforces everything natively and queries read plainly, but every project with a
  different ID scheme, and every new item type, needs new schema, load order and checks.
- **Enforcement is recovered by compiling the trace schema** — see the verified note below.
  Because the database is built in memory on every run and never committed, the engine can
  generate a schema as strict as a hand-written one.

### D5 — Author where the work happens; formalise in the ledger repo *(provisional — under test)*

The developer launches the coding agent in the **product repo**, and the agent writes repo
memory in a slightly stricter form. The ledger repo imports it at a pin and generates the
formal documents. Content is authored; ceremony — cover, DocID, revision history, bilingual
headings, signature blocks, information-item order — is rendered.

| Repo memory | What being traced adds |
|---|---|
| `docs/req/<subject>-prd.md` | nothing — stays casual, carries no IDs |
| `docs/req/<subject>-srs.md` | the requirement items: ID heading, one checkable statement, kind, origin, verification method |
| `docs/design/*.md` | a section that is a design element gets an ID and a `Satisfies:` line |
| source modules, tests | `Implements:` in the module docstring; a `verifies` tag on the test |
| `docs/progress/`, `docs/adr/` | untouched — not traced |

Consequences:

- **A requirement's text is canonical in repo memory**, in the repo that owns the feature.
  Requirements belong to the product and outlive the project; a project selects and pins a
  set of them. A requirement implemented across two repos still has one home; the other repo
  cites it by ID. The formal bilingual specification is a projection of those items plus
  framing prose and a stored, reviewable translation.
- **The standard's two processes map onto the two repo kinds.** Software-implementation work
  products live in product repos (developer hat, daily). Project-management work products —
  agreement, plan, records — have no product-repo home and are authored in the ledger repo
  (manager hat, occasional). The ledger joins them.
- **Two launch sites, one per hat.** The daily loop never leaves the product repo.
- **Steering is by tool output first, prose second**: a short generated stanza in the product
  repo's agent guide, a skill shipped with the engine, and findings that say what to do next.
- **Risk accepted:** agents rewrite repo memory freely, while a baselined requirement may
  change only through a change request. The guard is a check, not a rule in prose: an item
  whose content hash differs from the last baseline pin, with no change-request reference,
  is a violation.

The options considered — kept in full because this choice is the one most likely to be
revisited:

- **A — Author where the work happens; formalise in the ledger repo.** *Chosen, provisionally.*
  The agent writes stricter repo memory with markers; the ledger imports and generates.
  For: one place to work, nothing retyped, links authored when the knowledge arises. Against:
  baselined text sits where agents edit freely (guarded as above); every source type needs an
  extractor.
- **B — Ledger-canonical.** Formal documents are authored in the ledger repo; product repos
  only cite IDs. For: project-level ownership is obvious; one home for formal content.
  Against: the developer must leave the product repo to add a requirement; an agent working
  on the code cannot see requirement text without a second checkout; it is the predecessor's
  workflow and keeps its retyping.
- **C — Casual first, curate later.** No markers in the development loop; a curator pass —
  agent plus gate — extracts requirements and links afterwards. For: no ceremony at all while
  building. Against: links are inferred after the fact, and their timestamps show traceability
  created late, where assessors expect it updated at each stage; it abandons D1. **Kept as the
  on-ramp** for an existing repo that has no markers yet.

Under test on the beacon test bed: [`docs/tests/beacon-authoring-experiment.md`](../tests/beacon-authoring-experiment.md).
Revisit if the experiment shows markers that are wrong, dishonest, or costly to review.

### D6 — A baseline is an annotated Git tag; the trace configuration says what it freezes

`baseline/<scope>/<n>` — for example `baseline/requirements/1` — declares a baseline in a
product repo. The repo's trace configuration maps each scope to the item types it freezes.
Tagger and date come from Git, so they are collected, not typed. The agent learns that an
item is frozen from tool output (`status` marks it), never from a field in the document.

- **Rejected — a committed baseline file** listing IDs and content hashes. Diffable, but a
  second record beside Git that an agent can edit; the trace lock at the tagged commit already
  is that snapshot (D1).
- **Rejected — a field on each item** (`- Baseline: 1`). The most visible while editing, but
  it is a typed fact, it is the row-state shape the earlier spec's P7 already rejected, and
  an agent can delete the line.

### D7 — A change to a frozen item cites its change request on the item itself

`- Change: CR-001` under the item, declared at the downstream end like every other link. An
item's text is its title plus its body, whitespace-normalised, **excluding the `Change:`
line** — so citing a change request is not itself a change. The check is two-sided: the
change request must exist, be accepted, and list the item among the items it impacts, which
makes the standard's impact-analysis field verifiable. An item added after a baseline needs
a citation too; a frozen item's heading may not disappear — it is withdrawn, not deleted.

- **Rejected as the checked mechanism — a commit trailer** (`Change-Request: CR-001`).
  Git-native and it covers code, but it is easy to forget, a squash merge can drop it, and it
  attributes by file rather than by item. *Kept as the convention for code changes.*
- **Deferred — the pull-request or issue link** read by a Git-host collector. Not checkable
  offline, and it needs the host.
- **Suspects need no syntax of their own — but they must not clear themselves.** An item is
  suspect when it sits downstream of an item that changed since the last baseline. The first
  form of this rule also let a suspect clear when it was *touched*, and the first
  implementation compared test cases by file; experiment E3 showed that adding one test to a
  file silently cleared the suspects on every test beside it. **Revised:** a suspect is
  tracked against the item itself, never clears by being touched, and clears at the next
  baseline, whose verification record lists the suspects that were re-checked. 💡 Open:
  whether an explicit, recorded review of one item may clear it earlier.
- **Refinements from E3:** a change to a link field such as `Origin` counts as a change to
  the item's text; a `Change:` line is permanent, since a generated revision history is built
  from it; a change request reserves the ID of any item it adds; and when a requirement is
  gated, the work downstream of it is gated too — a rule for the skill and for review, because
  no check can compare code with a requirement's prose.

## Verified notes

### Composite foreign keys can police link rules (spike, 2026-09-20, DuckDB 1.5.5)

Writing the allowed `(link_type, src_type, dst_type)` combinations into a rules table and
pointing a composite foreign key at it rejects links in the wrong direction, links whose
stated type disagrees with the item, and dangling IDs.

- The foreign key **reports only the first violation** and aborts. Findings are therefore
  reported by an anti-join that lists every violation in one pass; the foreign key stays as a
  backstop so no rule query or emitted table can see an illegal link.
- **Not recoverable this way:** ID patterns (a check constraint cannot consult another table —
  generate the per-type check from the trace schema instead) and coverage rules (a key cannot
  require that a child row exists — these stay as rule queries).
- Record: `_playground/2026-09-20_fk-link-rules/` (local, not committed).

## Lineage from the earlier traceability spec

An unbuilt design spec for a traceability data layer preceded this project. Its principles,
and what becomes of each:

| Principle | Here |
|---|---|
| P1 Text is the source of truth; the database is derived and never committed | **Kept.** |
| P2 Entities and relationships in separate tables; never a list of IDs in a cell | **Kept in the ledger's shape; authoring moves to markers (D1).** |
| P3 Plan and results are separate; results are append-only | **Kept** — test case vs test result. |
| P4 One global test registry | **Subsumed** — every item lives in one table (D4). |
| P5 IDs are immutable and never reused | **Kept.** |
| P6 Composite IDs are decomposed and checked against their parts | **Kept as a trace-schema option**, not a fixed rule. |
| P7 Baselines are Git tags, not row state | **Kept**, generalised to pins. |
| P8 Validation is a gate that fails the build | **Amended** — violations always fail; gaps fail only from their stage on. |
| P9 Narrative in documents, relationships in data, neither duplicates the other | **Kept.** |
| P10 Every traceability table in every document is generated | **Kept.** |
| Stack: R | **Replaced** by Python; SQL rule files and the in-memory database stay. |

One open decision of that spec is closed by the legacy reports themselves: in `UT-SRnn-MFnn-nn`,
`SR` is a software sub-module and `MF` a module function — both are design elements, not
software requirements.

## Not yet written

- Core model: item, link, work product, event, evidence pointer, baseline — and how they join.
- Trace schema and profile formats.
- Marker syntax per source type.
- Ledger repo file layout; the trace lock's shape.
- Flow: markers → extract → import at a pin → in-memory build → rules → emitted tables.
- Extension points: rules, collectors, extractors.

Four of these are expensive to change later and get designed in full before the first slice:
**marker syntax** (copied into code across repos), **ID conventions** (cited in signed
documents), **event and evidence-pointer shape** (append-only), **ledger layout**.
