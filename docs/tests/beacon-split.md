---
summary: The beacon-split test bed and M10's acceptance measures — beacon's gateway and agent reshaped into the ADR-0001 layout (the ledger holds the SRS and design; the product repos hold code and tests), where `qmstrace ledger check|thread|impact` is judged. Measures A1–A13 fixed before the run; results below.
read_when:
  - running, repeating or extending M10's acceptance of the project-wide check
  - changing how `ledger check`, `ledger thread` or `ledger impact` judge a project across repos
  - rebuilding the beacon-split test bed
---

# beacon-split — acceptance of the project-wide check

**Status: M10a run on 2026-09-28 — A1–A9 and A11–A13 pass; A10 waits for M10b.** Plan: M10 in the
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

### M10a — run 2026-09-28

**Engine:** the wheel built from `feat/m10a-ledger-check` at `738e392`, sha256 `ed73a6a0…`,
installed in `beacon-split/.engine-venv`. **Bed:** cloned from `beacon-engine`'s `engine-main`
branches, reshaped, and committed as the ledger `a48bba6`, the gateway `61a02e4` and the agent
`c9619e5`. The ledger is tagged `split/requirements/1`, annotated. Raw outputs are in the
local playground, `_playground/2026-09-28_beacon-split/out/`.

**M0, the old layout before the reshape:**

| Repo | Items | Links | Violations | Gaps |
|---|---|---|---|---|
| gateway | 104 | 124 | 0 | 0 |
| agent | 73 | 84 | 0 | 0 |

The 208 links are E4's trace-lock count.

| # | Seen | Verdict |
|---|---|---|
| A1 | exit 0; 177 items (104 + 73) across 3 repos, 208 links, 0 violations | pass |
| A2 | `--strict`: exit 0, 0 gaps (M0 had none) | pass |
| A3 | 18 `test_config.py` test cases, qualified `agent:` and `gateway:`; no V01 | pass |
| A4 | the ledger's own `check --strict`: exit 1 on 47 gaps, all G02 (21), G03 (13) and G04 (13), every fix naming `qmstrace ledger check`, no violation. Gateway (85 items) and agent (58) exit 0 | pass |
| A5 | `skipped: ledger — the ledger itself; its qmstrace.toml reads qmstrace.schema.toml by path`; the ledger's `qmstrace.toml` sha256 unchanged | pass |
| A6 | exit 1: V03 at `../beacon-gateway/tests/integration/test_agent_endpoints.py:9`, *no such item in any repo of the project*. G07 on that test and G02 on REQ-BCN-01, which lost its only test, follow from it. Reverted | pass |
| A7 | exit 2, naming agent and gateway, each with `run qmstrace ledger copy-schema <repo>`; after the copy, exit 0 on 177 items | pass |
| A8 | exit 2: `agent: there is no ../beacon-agent/qmstrace.toml`; restored | pass |
| A9 | V10 on REQ-BCN-05; 16 S01: DSN-BCN-02 in the ledger (both versions), and 15 gateway tests and components, each *current reach only … gateway is read from its working tree, not at that baseline — not pinned* | pass |
| A10 | M10b | — |
| A11 | 8 commands, each run twice: `ledger check`, plain, `--strict` and `--quiet`; `ledger copy-schema`; each repo's `check --strict`; gateway `status`. Identical bytes; no home path in any output | pass |
| A12 | 0.38 s for `ledger check`, 177 items | informational |
| A13 | `beacon-engine`: HEAD, branches, tags and `status --porcelain` identical before and after, in all three repos | pass |

**Seen on the way:**

- `init` in the traced ledger works: it installs the stanza and the skill, and no pytest
  settings. But its stanza names `qmstrace check --strict` as the gate, where the ledger's
  gate is `ledger check --strict`. This is the deferred *`init` in a ledger directory* item.
- The ledger's `id_pattern` needs alternatives (`^REQ-(BCN|BAG)-\d{2}$`) to hold two subjects.
  Its derived prefix `REQ-` covers both families, so #25 does not bite here.
