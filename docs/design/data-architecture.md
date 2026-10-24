---
summary: Data architecture of qmstrace. Settled — decisions D1–D10 with their rejected alternatives; the product-repo half of the model (the item chain, marker syntax v0, the trace configuration with rules as data, citation across repos and the ledger's check of the whole project over working trees (M10a, ADR-0001), item text, baselines, change-request citation, the kinds of finding); and the ledger's import at a pin with the trace lock, v0. Not yet written — work-product states, events, evidence pointers, the ledger layout, the profile's format.
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
- **Consequence:** three kinds of repository — the engine (tool, no other project's data), ledger
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
- **Amended while planning the first engine slice: the database arrives with the ledger, not
  before.** A product repo's graph is a few hundred items; three experiments validated
  coverage rules as *data* judged in plain Python, and `check` runs fifteen times a session.
  The same guarantee is kept another way — the graph is built so that **an illegal link never
  enters it** — and the database earns its place where the union of several repos is queried
  and tables are emitted. Until a profile has a file of its own, a requirement's `Category`
  values are read from the trace schema, and the schema does not name its profile: the key was
  read and carried unused, and was dropped in M2 — adding it back with the profile's file breaks
  no configuration, keeping a key with no meaning would have been a promise nobody keeps.

### D5 — Author where the work happens; formalise in the ledger repo

*Amended 2026-09-28 by [ADR-0001](../adr/0001-the-ledger-holds-the-documents.md): the target layout for real-world use is option B's — the ledger repo holds the SRS and design, product repos hold code, tests and markers. Option A stays supported. The text below is D5 as first settled.*

The developer launches the coding agent in the **product repo**, and the agent writes repo
memory in a slightly stricter form. The ledger repo imports it at a pin and generates the
formal documents. Content is authored; ceremony — cover, DocID, revision history, bilingual
headings, signature blocks, information-item order — is rendered.

| Repo memory | What being traced adds |
|---|---|
| `docs/req/<subject>-prd.md` | nothing — stays casual, carries no IDs |
| `docs/req/<subject>-srs.md` | the requirement items: ID heading, one checkable statement, category, origin, verification method |
| `docs/design/*.md` | a section that is a design element gets an ID and a `Satisfies:` line |
| source modules, tests | `Implements:` in the module docstring; a `verifies` tag on the automated test, naming its test case or what it verifies directly |
| `docs/test/<subject>-test-cases.md` (in the ledger) | the test cases, where the project keeps a Test Specification: ID heading, a `verifies:` line (ADR-0003) |
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
  created late, where auditors expect it updated at each stage; it abandons D1. **Kept as the
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
covers  = ["requirement", "design_element", "component", "automated_test"]
```

- **A scope is a subject together with item types — never the whole repo.** A *subject* is
  the `<subject>` of `docs/req/<subject>-srs.md` and the key inside its item IDs. A product
  repo carries several subjects at once, each claimed by a different project; freezing one
  must not freeze another.
- **"An added item needs a change request" is judged within an already controlled subject
  and item type.** A subject begun after a product baseline is a new project under its own
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

Made precise while planning the engine — each of these was a hole in the first
implementation:

- **The latest baseline of a scope is the topologically latest reachable tag that matches**,
  never the one with the newest date. A pattern need not carry a number: a release tag has
  none.
- **One governing baseline per item.** Where two scopes cover the same item — a requirements
  baseline and a later release — the later reachable one governs, and a finding is reported
  once.
- **The guard judges document-declared items.** After a product baseline a code change
  carries its change request by convention (D7), so "frozen text changed" is asked of
  requirements and design elements, not of modules and tests.
- **A tree at a tag is read with the configuration at that tag** — file patterns move.
  **M5a clarification (2026-09-22):** its schema must also be recoverable from the tagged Git
  tree, embedded or through a same-tree file path. An external historical schema path is
  *could not judge*. Today's ledger is not evidence of yesterday's schema. **Rejected:**
  reading the current external schema with a notice — it could change which frozen items
  are even found. Future baselines include the schema; existing tags are not rewritten.
- **A release cut before the repo was traced freezes nothing**: a subject that did not exist
  at a baseline is not judged against it. Without this rule, adopting the tool in a repo with
  old release tags would make every item "new since" and demand a change request for each.
- **Local evidence is labelled honestly.** With baselines configured, shallow history,
  explicit tag-exclusion settings, a non-repository or unavailable required objects are
  *could not judge*. Otherwise the guard judges reachable local tags and reports when none
  match. **Remote-tag completeness is always unverified.** An offline clone has no universal
  proof that all remote tags were fetched; M5a corrects the earlier promise to detect that
  condition. **Rejected:** requiring remote queries — the product-repo check remains offline
  and never fetches. Checkout preparation owns obtaining the intended history and tags.
- **Ancestry can be ambiguous.** Incomparable governing commits after a merge are *could not
  judge*, naming all competing tags; establish an approved baseline after the merge. Tags
  on the same commit are equivalent, with their annotation evidence retained. **Rejected:**
  dates, numeric ordering or first-parent preference; none establishes approval precedence.
- **Scope identity survives configuration edits.** Historical covered type names and item
  identities remain eligible after a type or scope rename. Subject keys are exact ID segments;
  unknown or ambiguous ownership is *could not judge*. A new subject absent from a historical
  configuration is not frozen by that snapshot's wildcard release.
- **Authoring catches unowned controlled IDs before a tag** (ADR-0008). A locally declared
  Markdown item of a baseline-covered type without exactly one subject-key occurrence and
  one configured owner is
  V17 while no applicable baseline is selected. Once a baseline may govern it, ownership is
  required to judge scope: the run exits 2. A bad selected tagged tree names its tag and needs
  a valid, approved successor baseline; the current file cannot repair the old snapshot.
  An existing frozen item's ID must also remain owned under the current subject configuration;
  changing today's subject keys cannot silently leave it frozen under only the old key.

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

- **Only a fresh citation counts.** An item that already cites a change request and is
  edited again needs a *new* citation: what licenses a change is a citation that was not there
  at the governing baseline. A permanent `Change:` line does not license later edits.
  M5a checks every fresh citation offered for a changed or added controlled document item.
  The register is read from its current working tree, not a verified ledger pin. Request IDs
  come from filenames; `State` and `Impacts` are metadata before prose sections. Fenced
  examples cannot authorize changes. Malformed or duplicate metadata fails, never becoming
  the permissive unavailable-register case. Accepted values are case-sensitive.
- **Withdrawal retains identity.** `Status: withdrawn` is read on document items whether or
  not the schema requires the field. Withdrawal and reactivation change item text. Withdrawn
  items raise no coverage gaps, and links with a withdrawn endpoint cannot satisfy active
  items' coverage. Validation, graph traversal and test-result evidence remain visible.
  **Rejected:** exempting only the withdrawn item's own gaps — a retired design would still
  make an active requirement appear covered. Other status values receive no implicit exemption.
- **Where the register cannot be reached** — a pipeline with no ledger beside it — a fresh
  citation passes *with a notice that survives the quiet form*, and is verified for real at
  the ledger's import. Failing instead would force every product repo's pipeline to check out
  the ledger, which is what D9 exists to avoid. For later: the generated copy of the schema
  could carry an index of accepted change requests and agreement clauses.
- **Rejected as the checked mechanism — a commit trailer** (`Change-Request: CR-001`).
  Git-native and it covers code, but it is easy to forget, a squash merge can drop it, and it
  attributes by file rather than by item. *Kept as the convention for code changes.*
- **Deferred — the pull-request or issue link** read by a Git-host collector. Not checkable
  offline, and it needs the host.
- **The suspect rule, in full.** Downstream of a changed or removed frozen item, **transitively** —
  *suspect* means downstream of changed content, and the impact set must reach as far — and
  grouped by distance: status lists the first hop and counts the rest; check lists every
  suspect. An item that existed at the
  baseline and is unchanged is suspect; one that existed and was edited is *still listed*,
  worded as edited, because an edit is not a review; one that is new since the baseline is
  not a suspect. `impact` and suspects are two renderers of one traversal.
- **Suspects need no syntax of their own — but they must not clear themselves.** An item is
  suspect when it sits downstream of an item that changed since the last baseline. The first
  form of this rule also let a suspect clear when it was *touched*, and the first
  implementation compared test cases by file; experiment E3 showed that adding one test to a
  file silently cleared the suspects on every test beside it. **Revised:** a suspect is
  tracked against the item itself, never clears by being touched, and clears at the next
  applicable upstream baseline. The project's verification record lists the suspects that
  were re-checked; the engine does not verify that review occurred.
  **Decided since: an explicit, recorded review may also clear one suspect earlier** — to be
  added after the first slices. It writes *reviewed against this text, by whom* into the trace
  lock, so the lock's diff is the evidence; an agent may propose it, and the pull request's
  approval is what makes it count — otherwise it is a rubber stamp. Without it, the list on a
  long-lived branch becomes noise that is ignored.
- **M5b — two graph versions, one upstream reference.** Each changed or removed frozen
  document item starts a chain, independently of citation validity. Walk its governing
  snapshot's graph and the current graph separately, including dependencies, then union the
  reached local identities. Never splice edges from different versions into a path.
  **Rejected:** current links only — deleting a link would erase a historical review
  obligation; mixed-version paths — they can assert a dependency that never existed.
- **Eligibility and evidence are per root.** A dependant must exist in that root's snapshot
  and locally today. New intermediate items are traversed but not labelled; absent
  dependants are omitted. Keep every root, tag, per-version shortest distance and whether
  the dependant's own digest changed. Deduplicate the item count, not its reasons. A cycle
  alone does not make its own root suspect; another changed root can make it suspect.
  **Rejected:** clearing a chain at a newer downstream-only baseline — it does not replace
  the upstream item's governing snapshot. Removed roots retain surviving dependants beside
  V13; withdrawn items retain review obligations and labels despite their coverage exemption.
- **Historical graphs stop at the repository edge.** Validate local links using the tagged
  schema; malformed local graph evidence prevents judgment. Historical sibling/external
  citations are unverified boundary nodes, never filled from today's filesystem. This is
  local change analysis, not project-wide traversal at pins.
- **M10a — a dependant in another repo, in the ledger's check.** A root's governing snapshot
  is one repo's tagged tree, so no version of another repo at that baseline is read. There a
  dependant is reported **by today's reach only**: its reason names its repo, has no
  historical distance, and leaves *edited* unknown rather than guessed; the output says *not
  pinned*. Both rules above still hold on the root's side: nothing is spliced, and the
  historical walk stops at the root's repo. A dependant in the root's own repo keeps the M5b
  rule unchanged. **Rejected:** leaving product-repo tests silent until pins — in the layout of
  [ADR-0001](../adr/0001-the-ledger-holds-the-documents.md), every test is in another repo than
  the requirement it verifies, so a changed requirement would never reach one.
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
  auditor maps it one to one.

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
the project. That is the project's **trace schema** — one file, `qmstrace.schema.toml`, authored in the ledger repo. **Each product repo carries a
generated copy of it**, between markers in its own **trace configuration** (`qmstrace.toml`), beside what is local:
the item types it declares, their ID patterns, the files to scan, its baselines. The copy
carries a digest; the ledger's import refuses a repo whose copy does not match the schema at
the pin, and the ledger's check (M10a) refuses one whose rules differ from the ledger's working
tree. `rules` prints what is in force and says which part is the project's and which is
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
- **Generated by `qmstrace ledger copy-schema`** (M9b), run in the ledger. For each repo the
  schema names in `[repos]` — or those named on the command line — it writes the copy into
  that repo's `qmstrace.toml` and keeps every other byte. The copy sits between two comment
  lines, `# qmstrace:begin — …` and `# qmstrace:end`; inside them, `[schema]` carries the
  digest, then the ledger file's own lines — comments kept — with each header moved under
  `schema` (`[links]` → `[schema.links]`, `[[rules]]` → `[[schema.rules]]`).
  - **First adoption** replaces the run of consecutive `[schema…]` tables — a path form or an
    unmarked copy — wherever it sits; later runs replace what lies between the markers. A line
    is a header or a marker only when everything above it is complete TOML, so a `[` inside a
    multi-line array or string is never one.
  - **Verified before anything is written:** the new text parses, its digest equals the ledger
    file's, every key outside `schema` is unchanged, and the whole configuration still loads.
  - **All or nothing:** every repo is planned first; any refusal names every problem and
    writes nothing. A second run changes nothing.
  - **Refused:** a repo not named in `[repos]`, one holding its own schema (overwriting would
    discard rules only it holds), a path to another schema, a copy of another project,
    conflicting markers, schema tables split around other tables.
  - **A marker means a copy.** When the begin marker is present, `[schema]` must carry a
    digest: deleting the digest line cannot quietly turn a generated copy into the repo's own
    schema. An unmarked copy — generated before M9b — stays valid.
  - *Rejected — names:* `sync` (suggests two ways, and collides with `uv sync`), `schema`
    (reads as "show"), `export` (the emit verb's job), `push`/`publish` (suggest Git).
    *Rejected — a path argument:* it would let a repo check against the project's rules
    while the project does not know it. *Rejected — writing repo by repo:* a failure halfway
    would leave the project on two digests without saying so. *Rejected — a TOML-editing
    library:* a runtime dependency for one command, and it reformats the file.
  - **Copy before the first baseline.** At a baseline tag the engine reads the configuration
    from the tagged tree, where a path to the ledger leads nowhere: a repo that cut a baseline
    while reading its schema by path can never be judged at that tag.

#### Current checkout locations — ADR-0010

**0.3.0 amendment ([ADR-0012](../adr/0012-names-only-configuration.md)):**
[names-only v2 configuration](names-only-workspaces.md) separates membership/identity from
native checkout locations. V2 requires `repo`/`workspace_profile`, uses exact named-user-file
selection after overrides, and emits portable evidence. The v1 input contract below retains
its original discovery/default/digest interpretation; its old relative-output limit is
superseded by logical source labels and CLI/table `/2`. Native Windows acceptance is recorded
separately from the representation's implementation.

The schema's `[repos]` continues to declare project membership and ledger-relative default
locations. The local `ledger` pointer remains a default locator relative to its repo's
trace root. A **workspace map** can
replace those current checkout locations for one invocation, so the same `MINI` project can
be checked in a different directory layout without editing or re-copying its schema.
[ADR-0010](../adr/0010-local-workspace-maps.md) amends location resolution only; it does not
remove paths from the existing schema format.

```toml
# .qmstrace/workspace.toml in a folder containing these checkouts
version = 1
project = 'MINI'
ledger_repo = 'ledger'

[repos]
ledger = '../ledger'
service = '../service'
client = '../client'
```

Relative repo paths in a map resolve from its canonical containing directory, including
when selected through a symlink; native absolute input paths are also accepted. Environment
variables inside TOML paths are not interpolated. Here the file is in
`.qmstrace/`, so `../service` reaches the containing folder's `service` checkout. The
`ledger_repo` value names an entry in the map; its directory is the ledger trace root, even
when that root is nested inside a Git repository. The ledger role is required even in the
older layout where the ledger itself is not a traced member of the schema's `[repos]`.

- **Select one whole map.** Explicit `--workspace FILE`, then `QMSTRACE_WORKSPACE`, then the
  nearest ancestor `.qmstrace/workspace.toml` searched from the discovered trace root, then
  `~/.qmstrace/workspaces/*.toml`. User-level matching requires both the schema's `project`
  and a mapped checkout canonically equal to the current trace root. A malformed candidate
  encountered in that user-level stage causes exit 2 even when another file matches;
  unrelated valid maps are ignored, and multiple matches cause exit 2. An earlier selection
  does not inspect later stages. Full selection/refusal policy is in the
  [surface contract](surface-architecture.md#workspace-map-selection-and-paths).
- **No entry-by-entry fallback.** A missing or unreadable mapped member stays unavailable;
  a member omitted from a selected map is unavailable too, even when its default path
  exists. Local commands retain visible source notices; whole-project commands refuse an
  unread member. The map must identify the current root and the ledger role. It cannot
  invent schema members, grant coverage or hide schema skew. Distinct names cannot alias
  one canonical checkout. Preserve the schema's ledger self-member when one exists. A
  reachable mapped ledger without `qmstrace.schema.toml`, or belonging to another project,
  is refused with guidance to select the ledger's trace root rather than its Git root.
- **One resolution for current reads and writes.** Sibling discovery, external declarations,
  change-request registers, project assessment and schema-copy destinations use the selected
  locations. External and request paths remain ledger-relative. Ledger verbs remain rooted
  in the ledger; selecting a map from a product repo does not switch command scope.
- **Historical and digest boundaries stay intact.** `[schema] path` still resolves from the
  repo's trace root; a map does not repair a missing path-form schema. At a tag, only the
  tagged configuration and its existing same-tree schema rules apply. Maps are excluded
  from schema digests and item text and never rewrite a copied `[schema]`, tracked defaults,
  scan paths, report paths or output destinations.
- **Portable evidence (ADR-0012).** Mapped/project checkout labels use repo identities;
  sources carry a path within their owning root, never a filesystem relpath across drives.
  Selection provenance names the source and map filename. Native roots stay operational.
  Legacy input defaults remain relative as authored; no map changes a historical schema.

**Rejected:** editing schema `[repos]` for each machine (changes the shared digest), merging
partial maps with defaults (can mix unrelated checkouts), taking the first user match
(directory order would select evidence), and letting current maps replace historical paths
(would judge a tagged item against today's rules). Removing defaults from v1 remains unsupported; the separate v2 migration in ADR-0012
removes them without reinterpreting old evidence.

The shape — settled by writing the examples first and the parser second, because it lands in
every product repo and is expensive to change. **The annotated reference is the engine's own
fixture project**: `tests/fixtures/mini/` holds a ledger's trace schema, two product repos'
trace configurations and a repo on its own, and the tests parse all of them.

```toml
# a product repo's trace configuration — qmstrace.toml
version = 1                                   # an unknown key anywhere is a configuration error:
ledger  = "../the-ledger"                     # a mistyped `requird` would be a hidden rule
                                              # `ledger` is optional — without it, external sources
[subjects.gateway]                            # are reported as not verified
key = "BCN"                                   # the subject, named where an agent can see it

[schema]                                      # the project's trace schema, in one of three forms:
path = "../the-ledger/qmstrace.schema.toml"   #  1. by path — repos side by side, a test bed
# digest = "sha256:…" + the schema's content  #  2. a generated, verified copy — checked here
# the schema's content, with no digest        #  3. the repo's own — a repo with no ledger

[items.requirement]
extractor  = "markdown"                       # named here — never inferred from the type's name
id_pattern = '^REQ-BCN-\d{2}$'                # the ID's literal start is derived from it
files      = ["docs/req/*-srs.md"]
```

```toml
# the project's trace schema — qmstrace.schema.toml, in the ledger
[item_types.requirement]                      # what the project requires of a type…
required = ["Category", "Origin", "Verify-by"]
[links]
Assumes = { from = […], to = […], coverage = false }   # …a link says whether it counts toward coverage
[externals.agreement]                         # items declared outside any product repo
item_type = "origin_clause"
[baselines.product]
tag = '^v\d+\.\d+\.\d+$'   subject = "*"      # a scope names its subject: in the tag, or "*"
```

- **Three forms, not two.** The third — the schema's content under `[schema]` with no digest —
  is a repo that has no ledger: what adopting the tool in one existing repo looks like. A path
  together with a digest or content is an error. *Rejected — a path with a digest as a pin on
  the ledger's file:* a fourth form, for a job the ledger's import already does at a pin.
- **A copy edited by hand is refused**, by a self-check that needs no ledger: the digest is
  taken over the schema's *content*, independent of key order, comments and layout, so the
  same function serves the ledger's file and a repo's copy of it.
- **Whether a link counts toward coverage is the link's own property** (`coverage = false`),
  not a name the engine knows: a rule that needs such a link is a configuration error (D10).
- An item type the project knows and a repo does not declare is *known, not scanned there* — a
  client with no design documents declares no design elements.
- The copy lives under **its own namespace** — both files declare `[items.requirement]`, and a
  TOML parser rejects a table declared twice. Verified.
- A copy makes the ledger-relative paths to the agreement and the change requests
  unresolvable, hence the local **`ledger`** pointer, or the ledger role in a selected
  workspace map for current reads.
- A coverage rule may not need `Assumes` (D10) — a configuration error.
- One glob matcher serves every tree; the stand-in's two disagreed about `src/**/*.py`.
  Verified. It needs Python 3.13.

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
  colleague's uncommitted working tree. *Amended by M10a:* the ledger's check carries it
  across repos over working trees first — suspicion and reach, labelled *not pinned* — and the
  import at pins still decides it for good.
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
  the ledger)                └──────── verifies ─────────┤
                                                     test case
                                                         ▲ verifies
                                                   automated test ──▶ test result
```

*Amended 2026-10-14 ([ADR-0003](../adr/0003-test-cases-and-automated-tests.md)):* a test case is
an entry in a Test Specification, run by automated tests. A project that keeps no Test
Specification lets its automated tests verify requirements and design elements directly — the
arrow from *test case* is then theirs.

Every arrow is authored at its downstream end and points upstream (D1); the forward view is
derived. **Every link type is many-to-many, and the tooling must say so**: an agent that did
not know was tempted to bend the module layout toward one-to-one, because the tool was what
told it whether it was done.

### Marker syntax v0

*Amended 2026-09-24 (M9): sections, heading forms, near-misses — below the table. Amended
2026-10-14 ([ADR-0002](../adr/0002-dotted-ids.md)): the ID shape, dotted numbers; and
([ADR-0003](../adr/0003-test-cases-and-automated-tests.md)): test cases and automated tests; and
([ADR-0004](../adr/0004-reading-csharp.md)): C# components and xUnit tests. Amended 2026-10-21
([ADR-0007](../adr/0007-a-file-with-no-type-to-document.md)): a file with no type to document —
a Razor page, a file of top-level statements.*

| Item | Declared as | Its ID | Link marker |
|---|---|---|---|
| Requirement | a heading `### <ID> — <title>` in the subject's specification file, followed by one checkable statement and its fields | authored, from the trace schema's pattern | `- Origin: <clause>[, <clause>]` |
| Design element | a heading `## <ID> — <title>` in a design document | authored | `Satisfies: <requirement>[, …]` |
| Component | a source module | derived — the module's path | `Implements: <design element>` in the module docstring |
| Test case | a heading `### <ID> — <title>` in a Test Specification | authored | `verifies: <requirement or design element>[, …]` |
| Component, in C# | a `.cs` file | derived — the file's path | `Implements: <design element>` in the first type's leading `///` doc comment |
| Component, in a Razor page | a `.razor` file | derived — the file's path | `@* Implements: <design element> *@` in the page's head — its leading blank lines, Razor comments and directives, above the first markup or code block |
| Component, in a file with no type | a `.cs` file declaring no type, e.g. top-level statements | derived — the file's path | `Implements: <design element>` in the `//` or `///` comment block the file opens with |
| Automated test, in C# | an xUnit `[Fact]` or `[Theory]` method | derived — `path::Class::Method` | the ID at the start of its `DisplayName`, a string literal: the one link its type carries |
| Automated test | a test function | derived — the test runner's own identifier for it | the test framework's own tagging, e.g. `@pytest.mark.verifies("<ID>")`, on the function or its class — naming the test case it runs, or what it verifies directly |

- **One ID shape for every project**: capital letters and digits in hyphen-joined segments,
  ending in a number that may carry dotted parts — `REQ-SVC-01`, `TC-SVC-04.1-01`. An ID is
  read whole wherever it is written, or not at all; it is never cut short. A heading that
  starts with a malformed ID of this repo's kind is a lead, reported as V02 (ADR-0002).
- **A field whose name is a link marker *is* the link.** `Origin` is at once a required field
  of a requirement and its link to the clause; nothing else declares it.
- Fields are `- Key: value` lines in the item's section; bold keys are accepted. Several
  targets are comma-separated.
- **An item is a section** — its heading and everything under it down to the next heading at
  the same or a higher level. A deeper heading belongs to the item: its sub-sections,
  diagrams and tables are item text, and fields and links count anywhere in it.
  *Rejected — an item ends at the next heading of any level* (the rule until M9): an edit
  under `#### Acceptance criteria` in a frozen requirement escaped change control, and a
  `#### Traceability` sub-section written by an architecture skill was dropped (user
  acceptance, 2026-09-24). *Rejected — fields only before the first sub-heading:* the
  section would be the item's text but not its fields, two rules for one block.
- **Only this repo's IDs end an item.** A heading ends the open item when its first word
  matches one of this repo's item-ID patterns or shares their prefix; any other heading is a
  sub-heading if deeper, a boundary if not. `#### IEC-62304 software safety class` stays
  inside a requirement although its first word has an ID's shape. Items never nest.
- **The shared prefix is proved, not asserted** (ADR-0008). Configuration derives a literal
  beginning common to every `id_pattern` branch; `id_prefix` may shorten that start but may
  not name only one branch. A grouped pattern with a provable start still works. If the proof
  cannot establish an ID-shaped start, configuration is refused before anything is scanned.
- **Heading forms.** The ID comes first, after an optional section number (`4.2`, `4.2.1.`),
  and may be wrapped in emphasis or backticks; a trailing Pandoc attribute (`{#…}`, `{.…}`,
  `{-}`) is not part of the title. Decoration is layout: renumbering or restyling a heading
  is not a change. An ID later in a heading declares nothing.
- **Tables, prose and diagrams declare nothing.** An ID there is a mention. An undeclared ID
  of this repo's kind later in a heading, or as a table row's first cell, is a near-miss and
  a violation (V16). A link marker this item type carries, written as a table row or outside
  every item's section, is a stray: it links nothing, and the gap it leaves names it.
- A heading inside a code fence is not a declaration. A fence closes only on a line of the
  same character, at least as long as its opener, with nothing after it — so a fenced
  example can hold a fence of its own. Frontmatter is tolerated and ignored.
- **The file an item is declared in matters**, because each item type is read from the file
  patterns its trace schema names. An item declared elsewhere is invisible — and must be
  reported, not silently skipped.
- A test's level — unit, integration, system — comes from where it sits and is **information,
  not a rule**. It is a claim that is easy to fake, and some design elements can only be
  verified from outside.
- An automated test is a *test function*. A parametrised function is one automated test that
  runs several times; results are aggregated per automated test, worst verdict first, and
  every count says which of the two it is counting. A test case passes only when every
  automated test that runs it passes (ADR-0003).

**Known limit.** Derived IDs are not immutable: renaming a module or a test function changes
its ID, which the glossary forbids for an item. No experiment has renamed anything. Open. In
the ledger a derived ID is also **qualified by its repo**, because two repos of one project
can both have `tests/unit/test_config.py` — and in the fourth experiment they did.

### The trace configuration

One file at the product repo's root declares everything the tool enforces there. **Nothing is
hidden in the tool**, and the skill shipped with it never restates a rule — it points at the
command that prints them. Three of the six defects found in the first experiment were one
defect: a rule that lived in code, or in prose that disagreed with the code.

The shape is settled in D9, and its annotated reference is the fixture project
`tests/fixtures/mini/`. In outline — the project's part, then the repo's:

```toml
# the trace schema (the project's)
[item_types.requirement]                 # what the project requires of a type
required = ["Category", "Origin", "Verify-by"]
[item_types.requirement.values]
"Verify-by" = ["test", "inspection", "analysis"]   # a value is spelled exactly, case included

[links]                                  # marker = who may carry it, what it may point at
Satisfies = { from = ["design_element"], to = ["requirement"] }

[[rules]]                                # coverage rules are data; an unmet rule is a gap
code  = "G02"
item  = "requirement"
where = { "Verify-by" = "test" }         # optional: narrows the rule by a field's value
needs = "incoming:verifies"
text  = "no test verifies it yet."

[externals.agreement]                    # IDs declared outside any product repo
item_type   = "origin_clause"
prefix      = "AGR-"
source      = "agreement.md"             # relative to the ledger
declared_as = '^\s*[-*]\s+\*\*(AGR-\d+)\*\*'

# the trace configuration (the repo's)
[items.requirement]                      # one block per item type this repo declares
extractor  = "markdown"                  # markdown needs an ID pattern; python-module and
id_pattern = '^REQ-SVC-\d{2}$'           #   pytest derive their IDs and refuse one
files      = ["docs/req/*-srs.md"]
```

- **External IDs resolve or are announced as unverified.** A cited ID its source does not
  declare is a violation that lists the real ones. An unreachable source is stated in the
  output — never silently accepted. An invented origin threaded through a trace is the most
  expensive error this system can let through, and the cheapest to catch.
- A requirement's classification is one `Category` from the profile's list (D8).
- **Where it lives across repos:** the shared part is authored in the ledger and copied here,
  generated and verified; the local part is written here (D9).
- **What the ledger's tables carry** beyond the chain: `[tables.matrix] fields`, the requirement
  fields the traceability matrix shows. The tables' columns are otherwise derived from the
  item and link types above, so a project whose chain differs needs no engine change
  ([ADR-0005](../adr/0005-tables-as-data-and-several-reports.md)).

### Across repos (v1 — the ledger's check, M10a)

First exercised with two product repos in the fourth experiment; since
[ADR-0001](../adr/0001-the-ledger-holds-the-documents.md) the target layout keeps the
documents in the ledger, which is traced itself and lists itself in `[repos]` as `"."`.

- **An item has one home: the repo that declares it.** In the target layout that is the
  ledger for requirements and design elements, and a product repo for modules and tests;
  in the older layout, the product repo that owns the feature. Another repo cites it by ID,
  exactly like a local item, and one declared again elsewhere is a violation that says whose
  it is.
- **In one repo, a sibling is read from its working tree and the output says so** — "not
  pinned". **Where a sibling cannot be read** — in a pipeline only one repo is checked out — a
  citation of an ID that is not this repo's own enters the graph as *not verified here* and is
  named in the header. An ID matching this repo's own pattern gets no such benefit: this repo
  was read, so it is known not to exist (decided while planning M2).
- **In the ledger, `qmstrace ledger check` judges every repo together** — each read from its
  working tree, said *not pinned*. Each repo is scanned with its own configuration and built
  against the others' items, so what depends on one repo's patterns and files — V01, V02, V07,
  V16, V04, V05 — stays that repo's, exactly as its own check reports it with every sibling
  read. The repos' graphs are then joined, and on the union a coverage rule is met by a link in
  any repo, walks cross repo edges, and a change makes what hangs off it suspect in every repo
  (D7, M10a). Nothing in it is *not verified*: every repo was read, so an unknown ID is V03.
- **A derived ID carries its repo there** — `service:tests/unit/test_api.py::test_x` — because
  two repos can hold the same path, as the fourth experiment found. An authored ID is never
  qualified: it is the project's already. Every location is written from the ledger
  (`../service/…`).
- **A repo not read makes a clean result false**, so the check refuses rather than reports:
  a listed repo that is missing or unreadable, one whose schema differs from the ledger's
  (D9), two names for one folder, or a traced ledger missing from `[repos]` — every problem
  named at once, exit 2.
- **The pinned half is still the ledger's import.** The check reads working trees; the import
  reads each repo at a pin, writes the trace lock and decides every citation for good.
- **The thread between two product repos runs through the origin.** Requirements are
  product-scoped — "The gateway shall…" — so a client's design element cannot satisfy a gateway
  requirement, and did not try to. What joins the two sides is the agreement clause both
  derive from. A project-wide view organised by origin clause is not built yet.
- **A true marker is not sufficient: the verdict has to land on whoever can act on it.** A
  client test that really does fail when the gateway's guard breaks would, tagged with the
  gateway's requirement, redden a requirement in a repo whose code is fine — or, tagged only
  with the client's, redden the client's for a gateway fault. `verifies` across repos is
  allowed; it is not the natural cross-repo link between two product repos.
- **The link agents reach for across repos is a dependency — `Assumes` (D10).** A client design
  element *assumes* something of the gateway: that re-registering is harmless, that an unknown
  agent gets a 404, that the gateway owns the client-ID pattern — the last "a negative
  delegation, which `Satisfies` gets backwards". It counts toward **no coverage rule**; it
  carries suspicion and the impact set across the repo boundary — in one repo up to its edge,
  in the ledger's check across it.

### Item text

An item's **text** is its title and its section — every line down to the next heading at the
same or a higher level, sub-headings included — link fields included, with every run of
whitespace — line breaks too — collapsed to one space, and with the `Change:` line left out.
A sub-heading enters as its words: without its `#` marks and trailing attribute, and without
a section number that continues the item's own (item `4.2`, sub-heading `4.2.1`). Any other
number, as in `#### 404 when unknown`, is text.

- Re-wrapping a paragraph is not a change. It is the most common harmless edit an agent makes,
  and the first implementation got it wrong.
- Rewording is a change. So is a changed link field: an origin that gains a clause changes what
  the requirement derives from.
- Citing a change request is not a change, which is why that one line is excluded.
- Renumbering the document is not a change: a heading's number and attribute are layout.
- **A stricter reading can make an old tag unreadable.** Both sides of a baseline comparison
  are read by today's extractor, so a rule that reads more — fields in a sub-section, a
  decorated heading — can turn a tagged tree into one with violations, and the run then
  cannot judge. The way out is a new baseline, never a rewritten tag. V16 alone never
  blocks a snapshot: it declares nothing.
- Text is read as UTF-8 and normalised (NFC) before digesting; a digest carries its algorithm
  — `sha256:…` — because it becomes a format the day the ledger writes it into the lock.
- **A field-only change is still a change, and it is noisy**: moving eleven requirements from
  one classification field to another produced 24 stand-in findings though no behaviour
  changed. M5b's mapped replay finds 79 unique existing dependants: 8 designs, 9 components
  and 62 tests. The reproduced stand-in count is 20 unique items across 24 direct-link
  findings; it omits transitive reach and edited items. The next applicable baseline clears
  the engine's chains too. These are review obligations, not assertions of changed behavior.

### Kinds of finding

| Kind | Meaning | Fails |
|---|---|---|
| **Violation** | Wrong at any stage: an unknown or malformed ID, a marker pointing at the wrong type of item, a missing required field, an item declared where it is not read, an ID of this repo's kind written where it declares nothing, an external ID its source does not declare, a frozen item changed or added without an accepted change request that lists it, a frozen heading deleted | always |
| **Gap** | A coverage rule not yet met. Expected in the middle of the work; the agent uses the list as its work queue | the gate only — and, in the engine, only from the rule's stage on. *Slice 1: every gap fails the gate; stages come with the ledger* |
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
