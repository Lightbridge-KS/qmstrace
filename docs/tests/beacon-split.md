---
summary: The beacon-split test bed and M10's acceptance measures — beacon's gateway and agent reshaped into the ADR-0001 layout (the ledger holds the SRS and design; the product repos hold code and tests), where `qmstrace ledger check|thread|impact` is judged. Measures A1–A13 fixed before the run; results below.
read_when:
  - running, repeating or extending M10's acceptance of the project-wide check
  - changing how `ledger check`, `ledger thread` or `ledger impact` judge a project across repos
  - rebuilding the beacon-split test bed
---

# beacon-split — acceptance of the project-wide check

**Status: measures fixed on 2026-09-28, not run yet.** Plan: M10 in the
[tracker](../progress/overview-qmstrace.md). Layout: [ADR-0001](../adr/0001-the-ledger-holds-the-documents.md).

## What is tested

Whether `qmstrace ledger check` (M10a), and `ledger thread` and `ledger impact` (M10b), judge a
real small project in the ADR-0001 layout as one whole. That means:

- coverage rules are met across repos;
- each repo's own violations are still found;
- a changed frozen requirement reaches the tests downstream of it, in another repo;
- walks cross the repo edge.

Each of these goes wrong in the ADR's probe today. The run also checks that the verbs refuse
rather than pass when a repo is missing or holds other rules.

## Why a new test bed

`beacon-engine` holds the slice-1 evidence: the gateway's `m5b/requirements/*` and
`baseline/requirements/*` tags freeze requirements in the gateway's own tree. Moving the SRS out
would disturb that record. `beacon-split` is cloned from it and never pushed back. qmstrace is
never its own subject here.

It keeps what makes beacon a fair test:

- two subjects, `gateway` (BCN) and `agent` (BAG);
- a cross-repo `Assumes`;
- the agreement AGR-1…9 with change requests;
- a real derived-ID collision: both product repos have `tests/unit/test_config.py`.

## How it is built

In `<workspace>/_tests/beacon-split/`, from `beacon-engine`'s `engine-main` branches:

1. **Clone** `beacon-ledger`, `beacon-gateway` and `beacon-agent` with `--branch engine-main`,
   then run `git remote remove origin` in each.
2. **M0: record the old layout's baseline, before any reshaping.** Run local `status` and
   `check --strict` in each product repo, and record the item, link, violation and gap
   counts, and each gap's item and code.
3. **Ledger:**
   - move both subjects' SRS, PRD and design documents in, under `docs/req/` and
     `docs/design/`;
   - add a `qmstrace.toml` with:
     - `ledger = "."` and `[schema] path = "qmstrace.schema.toml"`;
     - subjects `gateway`/BCN and `agent`/BAG;
     - patterns `^REQ-(BCN|BAG)-\d{2}$` and `^DSN-(BCN|BAG)-\d{2}$`;
   - in the schema:
     - `[repos]` gains `ledger = "."`;
     - a baseline scope with tag `^split/requirements/(?P<n>\d+)$`, so the old tags never
       match;
   - remove the stand-in's `qmstrace.project.toml` and `trace.lock`.
4. **Product repos:**
   - remove `docs/req/` and `docs/design/`;
   - drop `[subjects]` and the document item types from `qmstrace.toml`;
   - remove the legacy `.qmstrace/`.

   `docs/progress/` stays. It is not traced.
5. Run `qmstrace ledger copy-schema` in the ledger, then `qmstrace init` in all three repos.
   Commit each as `reshape: ADR-0001 layout`.
6. Tag the ledger: `git tag -a split/requirements/1`.
7. Build the engine from the milestone's branch (`just wheel`) and install it into
   `beacon-split/.engine-venv`.

## Measures

Fixed before the run. A measure passes only as written; a partial result is recorded as
partial, with what was seen.

| # | Step | Passes when |
|---|---|---|
| A1 | `ledger check` | exit 0; items = M0 gateway + M0 agent; links = their sum; violations = the union of M0's |
| A2 | `ledger check --strict` | the gaps equal the union of M0's, at their new locations; no G02–G04 gap that M0 had met |
| A3 | the same run | `gateway:tests/unit/test_config.py::…` and `agent:tests/unit/test_config.py::…` are distinct items; no V01 |
| A4 | local `check --strict` in the ledger, then in each product repo | the ledger fails on G02–G04 only, and each fix names `qmstrace ledger check`; each product repo exits 0 |
| A5 | `ledger copy-schema` | prints a `skipped: ledger` line; the sha256 of the ledger's `qmstrace.toml` is unchanged |
| A6 | change a gateway test to `verifies("REQ-BCN-99")` | exit 1, with V03 located at `../beacon-gateway/…`; then revert |
| A7 | edit a rule's text in the schema, without copying it | exit 2 naming gateway, agent and `ledger copy-schema`; after the copy, A1 holds again |
| A8 | rename `../beacon-agent` | exit 2 naming agent; then restore |
| A9 | reword REQ-BCN-05 after the tag, with no change request | V10 on REQ-BCN-05; S01 on the ledger's design elements downstream of it, and on gateway components and tests labelled `current reach only … not pinned` |
| A10 | `ledger thread REQ-BCN-05`; `ledger impact REQ-BCN-05 DSN-BAG-02` (M10b) | forward reaches the qualified gateway tests; backward reaches REQ-BCN-05's origin clause; the candidate `Impacts:` lists requirements only |
| A11 | every command above, run twice | identical bytes; no absolute home path in any output |
| A12 | the wall time of `ledger check` | recorded; informational |
| A13 | `beacon-engine`, before and after | `HEAD`, `tag -l` and `status --porcelain` unchanged in all three repos |

## Results

Not run yet.
