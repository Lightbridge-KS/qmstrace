# Work Product Evidence CheatSheet — ISO/IEC 29110 Basic Profile

**Scope:** ISO/IEC 29110-5-1-2 (Software Basic Profile for VSEs) — the 23 work products (WP.01–WP.23), what each one is for, and what artefact in a GitHub-centric workflow can serve as its evidence.

**Status:** Working aid. Paraphrased for orientation only — the standard itself is authoritative for exact required content and states.

---

## 1. The Mental Model

Three ideas carry most of the weight:

**Two processes only.** The Basic Profile has Project Management (PM) and Software Implementation (SI). Every WP belongs to one of them (WP.23 belongs to both). Roughly 10 PM / 13 SI.

**States, not existence.** The standard cares that an artefact moved through `initiated → verified/validated → approved → baselined`. Possessing the file proves nothing; evidence of the transition is the deliverable. Closest familiar analogue: a PR's `draft → review requested → approved → merged`, plus annotated tags for "baselined."

**Traceability is the spine.** WP.21 links requirement → design → component → test case → test result, forwards and backwards. Most other WPs are nodes that this record threads together.

```
                    ┌─────────────────────────────────────────────┐
  Customer ────────►│ PM  (governance evidence)                   │
  Agreement WP.02   │                                             │
                    │  PM.01 Plan ──► PM.02 Execute               │
                    │       ▲              │                      │
                    │       └── PM.03 Assess & Control ──┐        │
                    │                                    ▼        │
                    │                              PM.04 Closure  │
                    └───────────────┬─────────────────────────────┘
                                    │ Project plan WP.10
                                    ▼
                    ┌─────────────────────────────────────────────┐
                    │ SI  (engineering evidence)                  │
                    │  SI.01 Init                                 │
                    │  SI.02 Requirements ─► WP.13, WP.18(prelim) │
                    │  SI.03 Design ───────► WP.16, WP.19, WP.21  │
                    │  SI.04 Construction ─► WP.15                │
                    │  SI.05 Integration ──► WP.14, WP.20, WP.08  │
                    │  SI.06 Assembly ─────► WP.06, WP.17         │
                    └─────────────────────────────────────────────┘
```

---

## 2. Quick Reference Table

| # | Work Product | Proc. | One-line purpose | Candidate evidence |
|---|---|---|---|---|
| 01 | Acceptance Record | PM | Customer formally accepts the deliverables | Signed PDF at closure |
| 02 | Agreement | PM | Contracted scope + deliverables list | Signed SOW / internal charter |
| 03 | Change Request | PM | A proposed change, with impact analysis | Issue w/ `change-request` template |
| 04 | Correction Register | PM | Corrective actions for deviations *from plan* | CAPA-style board w/ owner + due date |
| 05 | Implementation Environment | SI | The chosen toolchain | Lockfiles, devcontainer, CONTRIBUTING |
| 06 | Maintenance Documentation | SI | How the next developer picks it up | `docs/architecture.md`, ADRs |
| 07 | Meeting Record | PM | Agreements reached, signed | Minutes (chained to previous) |
| 08 | Product Operation Guideline | SI | How to install, run, operate | Runbook / deployment guide |
| 09 | Progress Status Record | PM | Actual vs planned, with reasons | Status report (tasks/cost/risk) |
| 10 | Project Plan | PM | How the project will be executed | Plan doc + version control strategy |
| 11 | Project Repository | PM | Controlled container for all WPs | The Git repo + Projects |
| 12 | Project Repository Backup | PM | Backup **and proven recovery** | Mirror + documented restore test |
| 13 | Requirements Specification | SI | Uniquely-ID'd, verifiable requirements | SRS / PRD with `Req.#NN` IDs |
| 14 | Software | SI | The integrated, tested build | Tagged release build artefact |
| 15 | Software Components | SI | Unit-tested parts | Modules/packages merged to `main` |
| 16 | Software Design | SI | Architecture + detailed design | C4 (L1–L3) + ADRs + API/schema |
| 17 | Software Product | SI | The consistent delivered bundle | GitHub Release (tag + artefacts + docs) |
| 18 | Software User Documentation | SI | How the end user uses it | User manual / docs site |
| 19 | Test Cases and Test Procedures | SI | Unit, integration, acceptance tests | `tests/` + manual test scripts |
| 20 | Test Report | SI | Test execution + per-defect ownership | CI report + linked `bug` issues |
| 21 | Traceability Record | SI | Req ↔ design ↔ code ↔ test ↔ result | Generated matrix (CSV/YAML), CI-checked |
| 22 | Validation Record | SI* | "Right thing?" — signed by PM + customer | Validation checklist, signed |
| 23 | Verification Record | PM+SI | "Thing right?" — signed by author | PR review w/ checklist + approver |

\* Also produced during PM.01 when the project plan is validated.

---

## 3. Project Management Work Products

### WP.01 — Acceptance Record
Records the customer's formal acceptance: receipt and date, what was delivered, validation against the acceptance criteria, any open issues, signed by customer and project manager. The acceptance criteria themselves live inside this record.
**States:** initiated, signed.
**Evidence:** signed PDF. No good Git-native analogue — the signature is the point.

### WP.02 — Agreement
The description of work: product description, purpose, general customer requirements, in/out of scope, objectives, deliverables list, signed by both parties.
**States:** approved, reviewed, baselined.
**Note:** the only WP whose source is the *customer*. For internal projects, a signed internal charter serves. Sits above the PRD in the hierarchy.

### WP.03 — Change Request
A proposed change to product or documentation, carrying requester contact, impacted product/component, impact on existing operations, impact on associated documentation, criticality and date needed.
**States:** initiated, evaluated, accepted, rejected.
**Evidence:** a GitHub Issue *only if* the template forces the impact-analysis fields. A bare feature request does not qualify.

### WP.04 — Correction Register
**Not a bug tracker.** Corrective actions for deviations from the *plan* — schedule slip, budget overrun, problems raised in review meetings. Fields: initial problem, defined solution, actions taken, responsible person, open date and target closure date, state indicator, follow-up.
**States:** initiated, approved, completed.

Keep the three "something went wrong" WPs distinct:

```
Change Request   = "the product needs to change"     (scope / requirements)
Correction Reg.  = "the project is off-plan, fix it" (process / execution)
Test Report      = "the code has defects"            (product quality)
```

### WP.07 — Meeting Record
Agreements with customer and/or work team: purpose, attendees, date and place, reference to previous minutes, what was accomplished, issues raised, open issues, agreements, next meeting, signed.
**State:** approved.
**Note:** references previous minutes — it forms a chain, not isolated notes.

### WP.09 — Progress Status Record
Status *against the plan*: actual vs planned tasks, results vs objectives, actual vs planned resources, cost vs budget, time vs schedule, current risk vs previously identified risk, and deviations **with the reason why**. Signed by the project manager.
**State:** published.
**Gap warning:** a milestone burndown alone misses cost, risk and reason-for-deviation.

### WP.10 — Project Plan
The largest document. Contains product description, scope, objectives, **selected development cycle** (waterfall / iterative / incremental / evolutionary / agile — you declare it), deliverables, tasks *including verification, validation and review tasks* (may be a WBS), estimated durations, resources incl. training, work team composition, schedule with dependencies, estimated effort and cost, risks, plus two critical sub-sections:

**Version control strategy** — repository tool and location, access mechanisms, version identification and control, **description of the baselines selected** (requirements / design / product), backup and recovery mechanisms, storage-handling-delivery mechanisms.
> This is where you declare that Git + GitHub *is* your mechanism. Writing it properly is what allows normal Git practice to count as evidence elsewhere.

**Delivery instructions** — elements required for release (hardware, software, documentation), delivery requirements, ordered task sequence, applicable releases and media, all delivered components **with version information**, backup and recovery procedures. Signed.
> Effectively a release checklist plus a versioned manifest.

**States:** initiated, validated, approved, updated.

### WP.11 — Project Repository
Electronic container for work products and deliverables: storage and retrieval, browsing, content listing with attributes, sharing between affected groups, **effective access controls**, work product descriptions, recovery of archived versions, status reporting, and **changes traced to change requests**.
**States:** recovered, updated.
**Evidence:** the GitHub repo. The traceability bullet is satisfied by commits/PRs referencing issues (`Fixes #42`). Ordinary GitHub hygiene covers most of this — the work is documenting that it does.

### WP.12 — Project Repository Backup
Repository used to back up and, if needed, recover the project repository.
**State:** recovered.
**The catch:** the process requires *verifying* recovery works. A backup that exists is not evidence; a documented restore test is. Commonly failed.

---

## 4. Software Implementation Work Products

### WP.05 — Implementation Environment
The tools selected for the project — compilers, design tools, construction and test tools.
**State:** established.
**Evidence:** language/SDK versions, lockfiles, `pyproject.toml`, devcontainer or Dockerfile, CI runner image. Executable declarations beat prose here.

### WP.06 — Maintenance Documentation
Describes the software product *and* the development/test environment, so maintenance personnel can take it over. Includes or refers to all product elements developed, and identifies the environment used. **Written for maintainers.**
**States:** validated, baselined.

Distinguish the three documentation WPs by audience:

```
WP.18 Software User Documentation  → end user       "how do I use it"
WP.08 Product Operation Guideline  → operator / IT  "how do I install & run it"
WP.06 Maintenance Documentation    → next developer "how do I change it"
```

### WP.08 — Product Operation Guideline
Information to install and manage the software: criteria for operational use, required operational environment, supporting tools and materials, **possible safety warnings**, start-up preparation and sequence, FAQ, sources of further help, certification and safety approvals, warranty and replacement instructions. Written for operations personnel.
**States:** verified, baselined.

### WP.13 — Requirements Specification
Software requirements — functions, performance, design constraints, attributes — organised around a general introduction and requirement descriptions under quality characteristics (functional completeness, correctness, appropriateness, and further attributes). **Each requirement is uniquely identified (e.g. `Req.#01`), unique, and verifiable or assessable.**
**States:** verified, validated, baselined.
**Delta from a typical PRD:** mandatory stable unique IDs and testability of every line. Those IDs anchor the whole traceability chain — choose the scheme early and never renumber. The quality-characteristic framing means non-functional requirements are not optional.

### WP.14 — Software / WP.15 — Software Components
- **WP.15 Software Components:** a set of related code units. States: unit tested, corrected, baselined.
- **WP.14 Software:** the software item (source and executable) for the customer, formed from integrated components. States: tested, corrected, baselined.

Part vs whole: components pass *unit* tests in SI.04; the integrated software passes *integration* tests in SI.05.

### WP.16 — Software Design
Textual and graphical information on the software structure, in two layers.

*Architectural / high-level:* overall structure, required components, relationships between them, with consideration given to performance characteristics, hardware/software/human interfaces, security characteristics, database design requirements, and error handling and recovery.

*Low-level / detailed:* enough to construct and test each component — prototype, flowchart, ER diagram or pseudo-code — plus input/output data formats, storage needs, data naming conventions, data structure formats, data field definitions and purposes, and the program structure specification.

**States:** verified, approved.
**Evidence:** C4 levels 1–3 plus ADRs for the architectural layer; API specs, schemas and type definitions for the detailed layer. Markdown/Quarto + Mermaid is a legitimate medium.

### WP.17 — Software Product
Not a file — the **defined bundle**, uniquely identified and internally consistent: requirements specification, software design, traceability record, software components, software, test cases and test procedures, test report, product operation guideline, software user documentation, maintenance documentation.
**States:** delivered, accepted.
**Evidence:** a GitHub Release — annotated tag pinning source, attached build artefacts, and the docs set at that same tag. This is the product baseline.

### WP.18 — Software User Documentation
How to use the software from the user-interface perspective: procedures for specified tasks, install and de-install procedures, brief description of intended use (concept of operations), supplied and required resources, needed operational environment, availability of problem reporting and assistance, access and exit procedures, explanation of commands and messages, warnings/cautions/notes appropriate to identified risk, troubleshooting and error correction. **Written for users.**
**States:** preliminary, verified, baselined.
**Note the `preliminary` state:** a draft user doc is required back at the requirements stage, before the code exists. Deliberate — it forces the UX to be described before it is built.

### WP.19 — Test Cases and Test Procedures
Cases and procedures spanning unit, integration and acceptance levels, traceable to requirements and design.
**Two things to internalise:**
1. Authored during **design (SI.03)**, before construction — the standard explicitly permits TDD as a development approach.
2. Verified for consistency across requirements ↔ design ↔ tests, and approved by the Analyst.

### WP.20 — Test Report
Documents test *execution*. Per defect: summary, related test case, who found it, severity, affected functions, date originated, date resolved, who resolved it.
**States:** initiated, [defects] corrected, baselined.
**Evidence:** CI output / JUnit XML **plus** linked bug issues — a raw test log lacks the per-defect ownership and resolution dates.

### WP.21 — Traceability Record
The relationship between requirements, design elements, components, test cases and test procedures, with **forward and backward** mapping through to test results.
**States:** verified, baselined, updated.

```
Req.#01 ──► Design §3.2 ──► src/ingest/dicom_reader.py ──► test_dicom_reader.py ──► PASS
Req.#02 ──► Design §3.4 ──► src/infer/model_runner.py  ──► test_model_runner.py  ──► PASS
   ▲                                                                                  │
   └───────────────────── backward traceability ──────────────────────────────────────┘
```

**No GitHub-native equivalent — the hardest WP to fake.** Practical approach: one CSV/YAML in the repo, regenerated in CI by a script that parses `# Req.#NN` markers in source and tests. It is updated at four separate tasks across SI.02–SI.05, so automation pays for itself quickly.

### WP.22 — Validation Record / WP.23 — Verification Record
Both document an execution and share a field structure: participants, date, place, duration, checklist, passed / failed / pending items, defects identified. They differ in question asked and signatory.

```
Verification (WP.23)  "Did we build the thing RIGHT?"  vs spec  → signed by author
Validation   (WP.22)  "Did we build the RIGHT thing?"  vs need  → signed by PM + customer
```

**States (both):** initiated, approved.
**WP.23 is the highest-frequency artefact in the profile** — produced by nearly every "verify and obtain approval of X" task, in both PM and SI. **A PR review is structurally a verification record:** participants, date, checklist, passed/failed items, defects, identified approver, merge timestamp. Configure PR templates with the verification checklist and require reviews, and WP.23 largely generates itself.

---

## 5. Filling the "Work Products Name (.file)" Column

**Combining is explicitly permitted.** Information items may be combined or subdivided to suit the project and stakeholder needs. One document may carry several WPs, or one WP may span several files — declare the mapping in the Remark column. Do not manufacture 23 separate documents out of obligation.

**Where a GitHub-only answer falls short.** Naming the gaps up front is cheaper than an audit finding.

| Gap | Why | Cheapest fix |
|---|---|---|
| WP.01, WP.02, WP.07 signatures | Git has no signatory concept for people | Signed PDFs, stored in repo |
| WP.09 cost / effort actuals | GitHub tracks tasks, not money | Spreadsheet in repo |
| WP.12 recovery *verification* | Backups exist; proof of restore does not | Periodic restore test, logged |
| WP.21 traceability | No native mechanism | Generated matrix, CI-checked |
| WP.04 correction register | Issues track product bugs, not plan deviations | Separate Project board |

**Suggested repo layout**

```
repo/
├── docs/
│   ├── agreement/           WP.02, WP.01 (signed PDFs)
│   ├── plan/                WP.10  (incl. version control strategy,
│   │                                delivery instructions)
│   ├── requirements/        WP.13
│   ├── design/              WP.16  (C4 + ADRs)
│   ├── user/                WP.18
│   ├── operations/          WP.08
│   ├── maintenance/         WP.06
│   └── records/
│       ├── meetings/        WP.07
│       ├── status/          WP.09
│       ├── corrections/     WP.04
│       └── validation/      WP.22
├── traceability/            WP.21  (generated, CI-verified)
├── src/                     WP.15 → WP.14
├── tests/                   WP.19
├── .github/
│   ├── ISSUE_TEMPLATE/      WP.03  (change request template)
│   └── PULL_REQUEST_TEMPLATE.md   WP.23 (verification checklist)
└── CI artefacts             WP.20
```

Repository itself = WP.11 · Mirror + restore test = WP.12 · Release = WP.17 · Toolchain declarations = WP.05

---

## 6. Five Highest-Risk Items

1. **WP.21 Traceability** — no substitute exists; automate it or it will rot.
2. **WP.12 Backup recovery** — the *verification* is the requirement, not the backup.
3. **WP.13 Requirement IDs** — unstable IDs break every downstream WP.
4. **WP.04 vs WP.03** — conflating plan deviations with product changes is the most common conceptual error.
5. **States over artefacts** — a complete file set with no evidence of state transitions still fails.
