---
summary: Data architecture of qmstrace. Settled — decisions D1–D10 with their rejected alternatives; the product-repo half of the model (the item chain, marker syntax v0, the trace configuration with rules as data, citation across repos, item text, baselines, change-request citation, the kinds of finding); and the ledger's import at a pin with the trace lock, v0. Not yet written — work-product states, events, evidence pointers, the ledger layout, the profile's format.
read_when:
  - deciding how trace data, work-product state or evidence is stored or moves
  - about to reopen one of the settled decisions below
  - writing the core model sections of this document
---

# Data architecture

**Status:** half written (2026-09-21). The decisions and the **product-repo half** are settled
— the latter by two experiments on a test bed, so it is marked *v0*: proven once, on one small
application. The **ledger half**, under *Not yet written*, waits for the next experiment and
for the open questions in the [PRD](../req/qmstrace-prd.md). Terms follow
[`CONTEXT.md`](../../CONTEXT.md).

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

### D5 — Author where the work happens; formalise in the ledger repo

The developer launches the coding agent in the **product repo**, and the agent writes repo
memory in a slightly stricter form. The ledger repo imports it at a pin and generates the
formal documents. Content is authored; ceremony — cover, DocID, revision history, bilingual
headings, signature blocks, information-item order — is rendered.

| Repo memory | What being traced adds |
|---|---|
| `docs/req/<subject>-prd.md` | nothing — stays casual, carries no IDs |
| `docs/req/<subject>-srs.md` | the requirement items: ID heading, one checkable statement, category, origin, verification method |
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

- **A — Author where the work happens; formalise in the ledger repo.** *Chosen.*
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

**Validated on the beacon test bed** — a greenfield slice (E1) and a change after a baseline
(E3): [`docs/tests/beacon-authoring-experiment.md`](../tests/beacon-authoring-experiment.md).
Both were one run with a strong model on a small application; revisit if wider use shows
markers that are wrong, dishonest, or costly to review. The ledger half of this decision —
import at a pin, generated formal documents — is not yet tested (E4).

### D6 — A baseline is a tag the project already cuts; the trace configuration says which tags are baselines and what each freezes

**The standard lets a project name its own baselines** in its version-control strategy, and a
project usually has: a release tag is already the product baseline, and a plan may already
name a requirements and a design baseline. So the engine *recognises* baselines by a
configured tag pattern and never imposes a name of its own — above all, it never asks for a
second tag beside a release.

```toml
[baselines.requirements]                       # default pattern; a plan's own name works as well,
tag    = '^baseline/(?P<subject>[a-z0-9-]+)/requirements/(?P<n>\d+)$'   # e.g. '^(?P<subject>[a-z]+)-req-v…$'
covers = ["requirement"]

[baselines.product]                            # the release tag IS the product baseline
tag     = '^v\d+\.\d+\.\d+$'                    # pre-release tags are a different scope, or none
subject = "*"
covers  = ["requirement", "design_element", "component", "test_case"]
```

- **A scope is a subject together with item types — never the whole repo.** A *subject* is
  the `<subject>` of `docs/req/<subject>-srs.md` and the key inside its item IDs. A product
  repo carries several subjects at once, each claimed by a different project; freezing one
  must not freeze another.
- **"An added item needs a change request" is judged against that subject's own requirements
  baseline.** A subject begun after a product baseline is a new project under its own
  agreement, not a string of change requests against the last release.
- **The applicable baselines are the ones reachable from `HEAD`.** A maintenance line sees its
  own last release; a hotfix branch cut from the release branch sees only what was released.
  A feature branch older than a tag does not see it — the pull-request gate runs on the merge
  result, where the tag is reachable, so the change is still caught before it lands.
- **The tag is annotated.** Tagger and date are then collected facts. A lightweight baseline
  tag carries neither and is reported as weaker evidence; old ones are not rewritten.
- **After a product baseline, a code change carries its change request by pull-request or
  commit convention (D7), not by item text** — a fix rarely rewords a requirement.
- **Two events, linked by the pin:** the baseline of items is a tag in the product repo; the
  issue of a controlled document rendered from them is an event in the ledger repo.
- The agent learns that an item is frozen from tool output, never from a field in the document.

How the standard's baselines fall onto a release-branch workflow, none of it new work:

| The standard's baseline | What the project already cuts |
|---|---|
| Requirements | an annotated tag on the integration branch once the specification is validated |
| Design | an annotated tag on the integration branch once the design is approved |
| Construction | the point where the release branch is cut |
| Software | a pre-release tag on the release branch |
| Product | the annotated release tag on the main branch, with the published release |

A project declares the ones it uses; the standard does not require all five by name.

- **Rejected — one tag name imposed by the engine** (the first form of this decision,
  `baseline/<scope>/<n>` for the whole repo). It ignored release tags that already are
  baselines, names a signed plan may already declare, and the fact that one repo carries
  several subjects. Checking it against a real repository with a release-branch workflow, a
  maintenance line and fourteen release tags is what exposed all three. *Kept as the default
  pattern.*
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
  baseline, whose verification record lists the suspects that were re-checked.
  **Decided since: an explicit, recorded review may also clear one suspect earlier** — to be
  added after the first slices. It writes *reviewed against this text, by whom* into the trace
  lock, so the lock's diff is the evidence; an agent may propose it, and the pull request's
  approval is what makes it count — otherwise it is a rubber stamp. Without it, the list on a
  long-lived branch becomes noise that is ignored.
- **Refinements from E3:** a change to a link field such as `Origin` counts as a change to
  the item's text; a `Change:` line is permanent, since a generated revision history is built
  from it; a change request reserves the ID of any item it adds; and when a requirement is
  gated, the work downstream of it is gated too — a rule for the skill and for review, because
  no check can compare code with a requirement's prose.

### D8 — A requirement carries one `Category`, from the profile's list; the functional / non-functional split is derived

```markdown
### REQ-XYZ-10 — A call carries an API key
The gateway shall reject, with status 401, a request that does not carry a valid API key.
- Category: security
- Origin: AGR-5
- Verify-by: test
```

The standard's requirements specification lists ten categories for the requirements
description, and *functional* is only one of them: functional suitability · performance
efficiency · compatibility · usability · reliability · maintainability · portability ·
security · design and construction constraints · legal and regulative. A requirement names
the **one** it is there to secure.

- **It dissolves the ambiguity the first experiment hit.** "Is rejecting with 401 functional?"
  has no good answer; "which category is this requirement there to secure?" does — security.
  A requirement that seems to need two categories is usually two requirements, the same rule
  as *one checkable statement*.
- **The split is derived, never authored.** Functional suitability is *functional*; the other
  nine are *non-functional*. The reverse mapping is impossible, so the finer field is strictly
  more informative. The first adopter's controlled template groups requirements under
  Functional / Non-functional headings; that layout is rendered from the category. A legacy ID
  scheme that encodes the split stays a matter of the trace schema's ID pattern.
- **The allowed values belong to the profile**, not to the engine — the standard is data. A
  trace schema may add to them; medical-device work would add `safety`, which newer quality
  models carry and this standard's text does not.
- **No coverage rule depends on it.** How a requirement is verified stays with `Verify-by`.
  The one use beyond rendering is informational: `status` lists the categories under which a
  subject has no requirement — a prompt, never a gap, because the standard says a
  specification *may* have them.
- The generated specification groups requirements by category in the standard's order, so an
  assessor maps it one to one.

- **Rejected — `Kind: functional | non-functional`**, the first form. Binary, ambiguous for a
  security *behaviour*, and in the first stand-in it silently changed what coverage meant. It
  was the one field the agent that wrote the first specification was not confident about.
- **Rejected — several categories per requirement.** Truer for a few items, but every
  requirement would then appear in several sections, and "which one do I put first" is the
  same judgement without the discipline.
- **Rejected — no field.** The generated specification could not be grouped, and nothing
  would prompt the author to consider the qualities at all.
- **Rejected — the name `Quality`.** Two of the ten values — the constraints and the legal
  ones — are not quality characteristics.

### D9 — The project's trace schema is authored in the ledger; each product repo carries a generated, verified copy

Two product repos of one project must agree on link types, coverage rules, required fields
and their values, where the agreement and the change requests are, and which repos belong to
the project. That is one file, authored in the ledger repo. **Each product repo carries a
generated copy of it**, between markers in its own trace configuration, beside what is local:
the item types it declares, their ID patterns, the files to scan, its baselines. The copy
carries a digest; the ledger's import refuses a repo whose copy does not match the schema at
the pin. `rules` prints what is in force and says which part is the project's and which is
the repo's.

- **Why a copy and not a path:** the pull-request gate runs in the product repo's own
  pipeline, where the ledger is not checked out — and a product repo cloned on its own could
  otherwise not be checked at all. It is the pattern already used for vendored skills: a copy
  that is generated, never edited, and audited for skew.
- **Cost accepted:** a generated block to keep current, and a window in which a repo runs on
  an older schema until it is synchronised — visible, because the import names the mismatch.
- **Rejected — a path from the product repo to the ledger's file.** One source and no
  machinery, and it is what the fourth experiment ran on, with no friction — but only because
  both repos sat side by side. *Kept for a test bed.*
- **Rejected — the full schema written by hand in each product repo.** Two hand-kept copies
  of the rules drift, and nothing says which is right.
- **Not yet tried.** The experiment exercised the path form.

### D10 — `Assumes`: a dependency link that counts toward no coverage rule

```markdown
## DSN-BAG-02 — Gateway client
Satisfies: REQ-BAG-04, REQ-BAG-05
Assumes: DSN-BCN-06
```

An item **assumes** something another item provides — usually in another repo: that
re-registering is harmless, that an unknown agent gets a 404, that the other side owns a
pattern this side declines to check. In the fourth experiment the agent had a sibling's ID in
mind three times and wrote a comment, because no marker fitted.

- **It counts toward no coverage rule.** Its whole job is to carry **suspicion and the impact
  set across a boundary** that they otherwise stop at: a change request against the assumed
  item makes the assuming item suspect, and lists it in the impact set. Without it a change
  request's "downstream" section is written by hand — a hand-kept matrix by another name.
- **It points at a requirement or a design element**, in this repo or a sibling; from a design
  element or a requirement.
- **Across repos it is judged at the ledger's import, against the pin** — never against a
  colleague's uncommitted working tree.
- **Rejected — the name `Depends-on`.** It would attract every import and every call. `Assumes`
  limits itself: it is written only when a change *there* could break something *here*.
- **Rejected — leaving it in prose.** The knowledge exists at the moment the code is written
  and is lost to every later change request.
- **Not yet tried.**

## The product-repo half (v0)

What a product repo carries and how it is read. Everything here was exercised by an agent
working from nothing but the repo's own guide, a skill and tool output — see
[`docs/tests/`](../tests/beacon-authoring-experiment.md).

### The chain

```
origin clause ◀─Origin── requirement ◀─Satisfies── design element ◀─Implements── component
 (declared in                ▲                           ▲
  the ledger)                └────────── verifies ───────┴──────── test case ──▶ test result
```

Every arrow is authored at its downstream end and points upstream (D1); the forward view is
derived. **Every link type is many-to-many, and the tooling must say so**: an agent that did
not know was tempted to bend the module layout toward one-to-one, because the tool was what
told it whether it was done.

### Marker syntax v0

| Item | Declared as | Its ID | Link marker |
|---|---|---|---|
| Requirement | a heading `### <ID> — <title>` in the subject's specification file, followed by one checkable statement and its fields | authored, from the trace schema's pattern | `- Origin: <clause>[, <clause>]` |
| Design element | a heading `## <ID> — <title>` in a design document | authored | `Satisfies: <requirement>[, …]` |
| Component | a source module | derived — the module's path | `Implements: <design element>` in the module docstring |
| Test case | a test function | derived — the test runner's own identifier for it | the test framework's own tagging, e.g. `@pytest.mark.verifies("<ID>")`, on the function or its class |

- **A field whose name is a link marker *is* the link.** `Origin` is at once a required field
  of a requirement and its link to the clause; nothing else declares it.
- Fields are `- Key: value` lines under the heading; bold keys are accepted. Several targets
  are comma-separated.
- A heading inside a code fence is not a declaration. Frontmatter is tolerated and ignored.
- **The file an item is declared in matters**, because each item type is read from the file
  patterns its trace schema names. An item declared elsewhere is invisible — and must be
  reported, not silently skipped.
- A test's level — unit, integration, system — comes from where it sits and is **information,
  not a rule**. It is a claim that is easy to fake, and some design elements can only be
  verified from outside.
- A test case is a *test function*. A parametrised function is one test case that runs several
  times; results are aggregated per test case, worst verdict first, and every count says
  which of the two it is counting.

**Known limit.** Derived IDs are not immutable: renaming a module or a test function changes
its ID, which the glossary forbids for an item. No experiment has renamed anything. Open. In
the ledger a derived ID is also **qualified by its repo**, because two repos of one project
can both have `tests/unit/test_config.py` — and in the fourth experiment they did.

### The trace configuration

One file at the product repo's root declares everything the tool enforces there. **Nothing is
hidden in the tool**, and the skill shipped with it never restates a rule — it points at the
command that prints them. Three of the six defects found in the first experiment were one
defect: a rule that lived in code, or in prose that disagreed with the code.

```toml
[items.requirement]            # one block per item type
id_pattern = '^REQ-<KEY>-\d{2}$'
files      = ["docs/req/*-srs.md"]
required   = ["Category", "Origin", "Verify-by"]
fields     = { "Verify-by" = ["test", "inspection", "analysis"] }   # Category's values come from the profile (D8)

[links]                        # marker = who may carry it, what it may point at
Satisfies = { from = ["design_element"], to = ["requirement"] }

[[rules]]                      # coverage rules are data; an unmet rule is a gap
code  = "G02"
item  = "requirement"
where = { "Verify-by" = "test" }          # optional: narrows the rule by a field's value
needs = "incoming:verifies"
text  = "no test verifies it yet."

[external.agreement]           # IDs declared outside this repo: cited here, never declared here
prefix = "AGR-"
source = "<where they are declared>"

[baselines.<scope>]            # D6
[change_requests]              # D7
```

- **External IDs resolve or are announced as unverified.** A cited ID its source does not
  declare is a violation that lists the real ones. An unreachable source is stated in the
  output — never silently accepted. An invented origin threaded through a trace is the most
  expensive error this system can let through, and the cheapest to catch.
- A requirement's classification is one `Category` from the profile's list (D8).
- **Where it lives across repos:** the shared part is authored in the ledger and copied here,
  generated and verified; the local part is written here (D9).

### Across repos (v0)

Exercised once, with two product repos — see the fourth experiment.

- **A requirement has one home.** It is declared in the repo that owns it, under that repo's
  subject; another repo cites it by ID exactly like a local item, and a sibling's requirement
  re-declared locally is a violation that says whose it is.
- **Locally, a sibling is read from its working tree and the output says so** — "not pinned".
  Only the ledger's import reads at a pin.
- **The thread between two repos runs through the origin.** Requirements are product-scoped —
  "The gateway shall…" — so a client's design element cannot satisfy a gateway requirement,
  and did not try to. What joins the two sides is the agreement clause both derive from: in
  the test bed three clauses have requirements in both repos. A project-wide view should be
  organised by origin clause; none is yet.
- **A true marker is not sufficient: the verdict has to land on whoever can act on it.** A
  client test that really does fail when the gateway's guard breaks would, tagged with the
  gateway's requirement, redden a requirement in a repo whose code is fine — or, tagged only
  with the client's, redden the client's for a gateway fault. `verifies` across repos is
  allowed; it is not the natural cross-repo link.
- **The link agents reach for across repos is a dependency — now `Assumes` (D10).** A client design element *assumes* something of the gateway: that re-registering is
  harmless, that an unknown agent gets a 404, that the gateway owns the client-ID pattern — the
  last "a negative delegation, which `Satisfies` gets backwards". Three times the agent had a
  sibling's ID in mind and wrote a comment because no marker fitted. Such a link would count
  toward **no coverage rule**; its job is to carry suspicion and the impact set across the
  repo boundary, which today stop at the repo's edge.

### Item text

An item's **text** is its title and its body up to the next heading, link fields included,
with every run of whitespace — line breaks too — collapsed to one space, and with the
`Change:` line left out.

- Re-wrapping a paragraph is not a change. It is the most common harmless edit an agent makes,
  and the first implementation got it wrong.
- Rewording is a change. So is a changed link field: an origin that gains a clause changes what
  the requirement derives from.
- Citing a change request is not a change, which is why that one line is excluded.
- **A field-only change is still a change, and it is noisy**: moving eleven requirements from
  one classification field to another made 24 downstream items suspect though no behaviour
  changed. The next baseline cleared them, as D7 says; in between, the list was all noise.

### Kinds of finding

| Kind | Meaning | Fails |
|---|---|---|
| **Violation** | Wrong at any stage: an unknown or malformed ID, a marker pointing at the wrong type of item, a missing required field, an item declared where it is not read, an external ID its source does not declare, a frozen item changed or added without an accepted change request that lists it, a frozen heading deleted | always |
| **Gap** | A coverage rule not yet met. Expected in the middle of the work; the agent uses the list as its work queue | the gate only — and, in the engine, only from the rule's stage on |
| **Suspect** | Downstream of an item that changed since the last baseline. Needs a fresh look, not necessarily an edit | never — it clears at the next baseline (D7) |

Two coverage rules are known to pull the wrong way, and are open:

- **`Verify-by: inspection` or `analysis` is a free pass.** "Needs a test" applies only to
  `Verify-by: test`, so the cheapest way to close that gap is to change one word. An
  inspection or an analysis needs a recorded basis — it is a verification record, which
  belongs to the ledger half — and until then such items are listed apart, so the shortcut
  shows.
- **"Every design element needs a test" can push a decorative tag** onto an element whose
  honest tests are all requirement tests.

**The check cannot tell a true marker from a decorative one.** It verifies that a marker
exists and points at the right kind of item; only breaking the code shows whether the tagged
test would notice. In the fourth experiment the agent did exactly that to its own work and
found a marker that could not fail. That procedure is the author's, not only the reviewer's.

## The ledger's import (v0)

Run in the ledger repo, by the project side, once per baseline or whenever the project is to
be judged as a whole. Exercised in the fourth experiment by the driver, not by an agent.

- `import NAME@PIN …` reads each named product repo **at the pin** — never its working tree —
  with the project's schema, and takes the union: authored IDs must be unique across the
  project, derived IDs are qualified by repo, links are validated and coverage rules applied
  across the union. Whether a requirement is covered *across all repos* is answered here and
  nowhere else.
- It writes the **trace lock** (D1): a header of pins — name, pin, commit — then one sorted
  line per item (ID, type, repo, file, text digest) and per link. Generated, committed, never
  edited. **A second run at the same pins is byte-identical** and leaves the working tree
  clean; moving one pin back a commit changed thirteen lines and brought a gap back.
- **A pin that carries no trace configuration is an error**, not an empty project. The first
  form silently imported nothing from a pin older than the repo's configuration file.

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

The ledger half, and what joins it to the half above:

- Work products, their states and transitions — including evidence forms that are not
  documents.
- Events and evidence pointers: the smallest shape that answers what, when, where and how.
- How a transition that happens outside any repository — a signature on a Word copy — becomes
  an event without anyone typing a fact.
- A project-wide view organised by origin clause; the dependency link across repos.
- Item-level suspects, and with them the trace lock's use as the record of what was reviewed.
- The ledger repo's file layout; the profile's format.
- Flow end to end: markers → extract → import at a pin → in-memory build → rules → emitted
  tables.
- Extension points: rules, collectors, extractors.

Four things are expensive to change later and get designed in full before the first engine
slice. Two are now drafted above as v0 — **marker syntax** (copied into code across repos) and
**ID conventions** (cited in signed documents). Two are not — the **event and
evidence-pointer shape** (append-only) and the **ledger layout**.
