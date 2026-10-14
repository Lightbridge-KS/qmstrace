---
summary: Ubiquitous language for qmstrace — the standard's vocabulary, the trace graph, evidence, and the repositories and documents involved.
read_when:
  - introducing, renaming, or disambiguating a domain term
  - naming a type, module, command, file, or column after a domain concept
  - a word from ISO/IEC 29110, the organisation's document control, and the engine seem to mean different things
---

# qmstrace

Keeps the state, traceability and audit evidence of a software project's work products, so
that an auditor's questions are answered by query instead of by assembly. Three vocabularies
meet here — the standard's, the organisation's document control, and the engine's own — and
this glossary says which word wins.

## Language

### The standard

**Profile**:
A named catalogue taken from a standard: its work products, their applicable states, and the
conformance requirements an audit checks. ISO/IEC 29110 Basic is the first.
_Avoid_: standard (the document, not the catalogue), template
**Work Product**:
A kind of output the profile requires of a project, defined by required content and
applicable states — never by file format.
_Avoid_: deliverable, document, artifact

**Evidence Form**:
The medium a project chooses for one work product: a controlled document, a section of one,
a repository, a tracker feature, a release.
_Avoid_: format, file type

**Versioned Work Product**:
A work product that is baselined and afterwards changed only through a change request —
plan, requirements specification, design, test cases, traceability record.
_Avoid_: living document

**Dated Record**:
A work product created once per real event and never re-versioned — meeting record, change
request, verification record, validation record, progress status record. It exists only
because the event happened.
_Avoid_: log, form instance

**State**:
A lifecycle position the profile defines for a work product: initiated, verified, validated,
approved, baselined, and the rest.
_Avoid_: status (belongs to items), stage (belongs to the project)

**Transition**:
A work product's move from one state to another. The transition, not the file, is what an
auditor asks to see evidence of.
_Avoid_: update, promotion

**Verification** (ทวนสอบ):
The internal check that a work product was built right, done by someone other than its
author and evidenced by a verification record.
_Avoid_: review, QA, V&V

**Validation** (ตรวจสอบและอนุมัติ):
The customer's confirmation that the right thing was built, evidenced by a validation record
signed by project manager and customer.
_Avoid_: approval, acceptance, V&V

**Baseline**:
An approved set of work-product revisions frozen as the team's single reference, changed only
through a change request. A project names its own baselines; a release is one of them — the
product baseline — and each freezes a subject, not a repository.
_Avoid_: release (a release is one baseline, not the concept), snapshot, freeze

**Stage**:
The project's position in the profile's activity sequence, from requirements through
assembly. It decides how complete the traceability is expected to be.
_Avoid_: phase, sprint, state

**Configuration Item**:
A work product or component placed under version control and baselining.
_Avoid_: CI (collides with continuous integration)

**Change Request**:
A proposed change to a baselined work product, carrying its impact analysis. It names every
item it touches and reserves the ID of any item it adds.
_Avoid_: feature request, ticket

**Correction**:
A corrective action for a deviation from the *plan* — schedule, effort, a problem raised in
review. Not a product change and not a code fault.
_Avoid_: issue, bug

**Defect**:
A fault in the software found by a test or a review, owned until resolved and re-tested.
_Avoid_: issue, correction

**Role**:
The hat the profile assigns to an act — project manager, analyst, designer, programmer,
customer. One person may wear several; an act is recorded against a role, not only a name.
_Avoid_: title, position

**Auditor**:
The party who examines a project's evidence against a standard — in an *internal audit*, the
organisation's own quality check, or in a *certification audit*, by an external body. Under
ISO/IEC 29110's scheme the certification auditor is formally an *assessor* (ผู้ประเมิน)
conducting an assessment; the standard's own text uses both words.
_Avoid_: assessor (except when quoting that scheme), inspector, reviewer

### The trace graph

**Item**:
A uniquely identified unit of engineering content that can be traced: an origin clause, a use
case, a requirement, a design element, a component, a test case, an automated test.
_Avoid_: node, entity, artifact, need

**Subject**:
A named body of requirements within a product — the name of its specification and the key
inside its item IDs. A project claims one or more subjects, and a baseline freezes a subject.
_Avoid_: module, feature, project, component

**Item ID**:
An item's identifier: immutable once committed and never reused. Retiring an item changes
its status, not its ID.
_Avoid_: key, number

**Qualified ID**:
A derived item ID — a module's path, an automated test's ID — prefixed by its repo's name in
`[repos]` wherever the whole project is judged: `service:tests/unit/test_api.py::test_x`. Two
repos may hold the same path; an authored ID is never qualified.
_Avoid_: full ID, global ID, `../service/…` (that is a location, not an identity)

**Item Text**:
An item's title and its section — everything down to the next heading at the same or a higher
level, sub-sections, tables and diagrams included — its link fields included, with layout
ignored. It is what a baseline freezes and what a change is measured against: re-wrapping a
paragraph or renumbering a heading is not a change, rewording is, and so is a changed origin.
_Avoid_: content, body, hash

**Frozen**:
Said of an item whose text is fixed by a baseline reachable from the current commit.
_Avoid_: locked, read-only, baselined (that describes a work product, not an item)

**Status**:
Whether an item is active, withdrawn, or superseded.
_Avoid_: state

**Link**:
A typed, directed relationship from one item to another — verifies, satisfies, implements,
assumes. It is declared at the downstream end: the test names the requirement it verifies.
_Avoid_: edge, relation, reference, trace (as a noun)

**Assumes**:
The link saying that an item relies on something another item provides, often in another
repo. It counts toward no coverage rule; it carries suspicion and the impact set across the
boundary.
_Avoid_: depends-on, uses, requires

**Marker**:
An item or link declaration written in the place where the item itself is authored — a
heading that starts with the item's ID, a line in the item's section, a tag on an automated
test, the start of its `DisplayName`.
_Avoid_: annotation, tag (collides with a Git tag), comment

**Stray**:
A marker written in a form the tool does not read — an `Implements:` in a comment instead of
the module docstring, a `Satisfies:` line outside every item's section, a `Satisfies` table
row. It links nothing; the gap it leaves names it.
_Avoid_: orphan, dangling marker

**Mention**:
An ID written where it declares nothing — later in a heading, in a table, in prose or in a
diagram. It links nothing and counts toward no coverage rule. A mention of this repo's kind
that nothing declares, written where a declaration was likely meant, is reported.
_Avoid_: reference, citation (that is a link to another repo's item)

**Origin**:
The customer-side source a requirement traces back to: an agreement clause or a
terms-of-reference clause.
_Avoid_: source, parent

**Category**:
The one concern a requirement is there to secure, taken from the profile's list — functional
suitability, security, reliability and the rest. The functional / non-functional split is
derived from it, never authored.
_Avoid_: kind, type, quality, non-functional (as a category of its own)

**Trace Schema**:
One project's declaration: the profile it follows, its product repos, its link types and
coverage rules, and where its agreement and change requests live. Authored once, in the
ledger repo, by the project side.
_Avoid_: profile (that is the standard's catalogue), config, metamodel

**Trace Configuration**:
One product repo's own file: a generated, verified copy of the project's trace schema, plus
what is local to the repo — the item types it declares, their ID patterns, the files to scan,
its baselines.
_Avoid_: trace schema (that is the project's), settings

**Schema Copy**:
The project's trace schema written into a product repo's trace configuration, between
`# qmstrace:begin` and `# qmstrace:end`, with a digest that is checked on every run. Generated
in the ledger by `qmstrace ledger copy-schema`, never edited by hand; what lets a product repo
be judged without its ledger beside it.
_Avoid_: embedded schema, vendored schema, schema cache

**Coverage Rule**:
A statement of which links an item type must have, and from which stage onward.
_Avoid_: check, constraint

**Finding**:
What a run reports as wrong or unfinished in the user's repo — a violation, a gap or a suspect
— as one line: a code, where, what is wrong, and the next move. Always data, never a crash; a
run that cannot judge at all says so instead, and judges nothing.
_Avoid_: error, issue, warning

**Notice**:
What a run could not verify or did not pin — an external source out of reach, a sibling read
from its working tree, a citation judged only at the ledger's import. It fails nothing, and no
form of output may hide it.
_Avoid_: warning, info, log line

**Gap**:
A coverage rule not yet satisfied. Before the rule's stage it is a progress signal; from that
stage on it is a finding.
_Avoid_: error, violation, hole

**Violation**:
Trace data that is wrong at any stage: an unknown ID, a link of a type the trace schema does
not allow, a malformed ID.
_Avoid_: gap, warning

**Suspect**:
Something downstream of content that changed after it was last reviewed — an item, a
translation, a rendered document. It needs a fresh look, not necessarily a change, and it
never stops being suspect merely by being touched.
_Avoid_: stale, dirty, outdated, broken

**Impact Set**:
Everything downstream of the items a change would touch — what a change request's impact
analysis has to name.
_Avoid_: blast radius, dependencies, affected files

**Forward Trace / Backward Trace**:
Walking from any item toward what hangs off it — as far as the test results — or back from it
to what it derives from, as far as the origin. Backward links are authored; the forward trace
is derived from them.
_Avoid_: upstream/downstream trace

**Thread**:
One item followed both ways — backward to what it derives from, forward to what hangs off it —
each item shown once, nearest first. What `qmstrace thread` prints; *follow a thread from claim
to evidence*.
_Avoid_: trace (as a noun), path, lineage

**Test Case**:
The planned, baselined description of a test and what it verifies — an entry in a Test
Specification, run by one or more automated tests, and passing only when all of them pass.
`TC-BAG-03.4 — The wait stops growing at the ceiling`, run by two xUnit methods. Where a
project has no Test Specification, its automated tests verify directly (ADR-0003).
_Avoid_: test (unqualified), test function

**Test Specification**:
The document that holds a subject's test cases — the evidence form of the test-cases work
product, as the requirements specification is of the requirements. A Markdown file in the
ledger, `docs/test/<subject>-test-cases.md`, one heading per test case.
_Avoid_: test-case register (a Register is generated), test plan

**Automated Test**:
The code that runs a test case, or verifies an item directly: a pytest function, an xUnit
`[Fact]` or `[Theory]` method. Its ID is derived from where it is; a parametrised function or
a Theory is one automated test that runs several times.
_Avoid_: test case (for the code), test method, unit test (a level, not a kind)

**Test Result**:
The verdict of one automated test in one run. Appended, never edited, never typed by hand. A
test case's verdict is the worst of its automated tests' results.
_Avoid_: test status, outcome

**Gate**:
The check that work must pass to be accepted: no violations, and no gaps the current stage
forbids. Distinct from the check run while authoring, which lists gaps without failing.
_Avoid_: CI, build, lint

### Evidence

**Evidence**:
The thing, in its home system, that proves a transition or a result happened — a merged pull
request, a signed document revision, a test run, a tracker item. qmstrace never holds
evidence, only pointers to it.
_Avoid_: proof, attachment, record (unqualified)

**Home System**:
The system of record where a piece of evidence lives and is logged: the Git host, the
tracker, the document store, the test runner.
_Avoid_: source, backend, integration

**Evidence Pointer**:
A reference to evidence: its home system, its locator, and its pin.
_Avoid_: link (reserved for items), URL, attachment

**Pin**:
The coordinate that fixes a pointer to one immutable version — a commit, a Git tag, a
document revision.
_Avoid_: version, snapshot

**Admissible**:
Evidence an auditor will accept: it carries the content the profile lists, lives in a
system with a log, is versioned and baselined if it is a configuration item, and sits behind
access control.
_Avoid_: valid, compliant

**Event**:
An append-only record that something happened to a subject: what changed, who acted in which
role, when the home system says it occurred, and the evidence pointer.
_Avoid_: log entry, history, audit trail (the trail is the sum of events)

**Collector**:
A deterministic program that harvests facts — dates, commits, verdicts, actors, states — from
a home system's own log. Facts are collected, never typed.
_Avoid_: scraper, sync, importer

### Repositories and documents

**Project**:
In the standard's sense: one agreement, one plan, one delivery. A project may span several
product repos and is never itself a repository.
_Avoid_: repo, product

**Product Repo**:
A repository holding a software product's code, tests and repo memory. It outlives many
projects and carries markers, nothing more.
_Avoid_: project repo, source repo

**Sibling**:
Another repo of the same project, seen from one of them: listed in the trace schema, and read
from its working tree — not pinned — so that its items can be cited by ID. Usually another
product repo; where the ledger holds the documents (ADR-0001), the ledger is a sibling too.
Only the ledger's import reads it at a pin.
_Avoid_: dependency, neighbour, peer

**Ledger's Check**:
`qmstrace ledger check`, run in the ledger repo: every repo of the project read from its
working tree and judged as one — coverage met across repos, each repo's own violations,
suspects across repos. Not pinned; the import is the pinned half.
_Avoid_: project check (ambiguous with a product repo's own `check`), import, sync

**Repo Memory**:
A product repo's casual, agent-first `docs/` tree — requirements, design, decisions,
trackers. The upstream that formal documents are derived from.
_Avoid_: documentation, wiki

**Ledger**:
The committed text record of one project: its items, links, work-product register, events
and evidence pointers.
_Avoid_: database, store, registry

**Ledger Repo**:
A repository holding project ledgers together with the sources of their controlled documents.
_Avoid_: QMS repo, docs repo

**Engine**:
qmstrace itself — the tool. It holds no other project's data: the one trace in its repo is its own.
_Avoid_: platform, system

**User Manual**:
qmstrace's own documentation for the people who use it — tutorials, how-to guides, reference and
explanation — written in `contents/` and published. Not repo memory, which is internal, and not a
controlled document.
_Avoid_: docs (that is repo memory), documentation site, help

**Stanza**:
The short generated block in a product repo's agent guide saying that the repo is traced and
what that asks of an agent working there.
_Avoid_: prompt, instructions, system prompt

**Skill**:
The authoring guide shipped with the engine — the chain, the markers, the loop, how to read
findings — installed by `init` into a product repo at `.agents/skills/qmstrace/`, where a
coding agent's harness lists it. It never restates a rule; it points at `qmstrace rules`.
_Avoid_: playbook, prompt

**Import**:
Reading a product repo's markers into a ledger at a pin.
_Avoid_: sync, fetch, collect (collectors harvest facts, imports read markers)

**Trace Lock**:
The generated, committed listing of every item and link in a ledger at one commit. Its diff
is what a reviewer reads when traceability changes.
_Avoid_: matrix, export, cache

**Register**:
A generated listing of the ledger for one audience: work-product register,
configuration-item register, baselines table. Never maintained by hand.
_Avoid_: checklist, index, spreadsheet

**Controlled Document**:
A document under the organisation's document-control procedure, identified by a DocID and
released as numbered revisions.
_Avoid_: QMS doc, official doc

**Draft**:
A rendered output of a ledger repo. Always marked as a draft and never authoritative.
_Avoid_: version, copy

**Issued Revision**:
A revision assigned, signed and released under document control. From that moment the
production copy is the master and the ledger repo's copy is not.
_Avoid_: final, approved version, release

**Reconcile**:
Folding prose edits made on a Word copy back into the source. Generated tables are never
reconciled; they are corrected in the ledger and rendered again.
_Avoid_: merge, sync, round-trip

**Drift**:
A difference between an issued or staged document and the ledger at the pin it was rendered
from — someone edited downstream what should have changed upstream.
_Avoid_: suspect (that is upstream change awaiting review), mismatch
