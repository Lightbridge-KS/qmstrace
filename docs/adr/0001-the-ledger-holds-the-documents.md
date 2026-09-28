---
summary: ADR-0001 — the target layout for real-world use: the ledger repo holds the agreement, change requests, trace schema and the SRS and design documents, traced itself; product repos hold code and tests with markers citing the ledger's IDs. Amends D5; the project-wide check moves ahead of M10 mentions.
read_when:
  - deciding where a project's SRS, design documents and change requests live
  - changing D2 or D5 in docs/design/data-architecture.md, or how check, thread, impact or suspects behave across repos
  - setting up qmstrace on a real project
---

# ADR-0001 — The ledger holds the documents

- **Status:** accepted, 2026-09-28
- **Amends:** [data architecture](../design/data-architecture.md) D5 (*author where the work
  happens*), and its section *Across repos (v0)*
- **Decided by:** the developer, from a probe of three layouts on the fixture project

## Context

D5 chose **option A**: requirements and design live in the product repo, beside the code, and
the ledger repo imports them at a pin. It rejected **option B, ledger-canonical**, and kept the
reasoning in full, calling it "the choice most likely to be revisited".

Real-world use is now the direction (see the [tracker](../progress/overview-qmstrace.md)). Its
target is a project run under a QMS, where the SRS and the design are reviewed, released and
changed as one controlled set. D5's four arguments against B, looked at again for that target:

| D5's argument against B | Now |
|---|---|
| The developer must leave the product repo to add a requirement | A requirement change is a controlled event with a change request, done in the manager role, not in the daily coding loop |
| An agent working on the code cannot see requirement text without a second checkout | The developer works with both repos open side by side, and a coding agent's session can take more than one working folder, so the agent sees both |
| It is the predecessor's workflow and keeps its retyping | No longer true: items are text with markers wherever they live, so nothing is retyped |
| Requirements belong to the product and outlive the project | Holds where several projects share one product; that is not the target |

## Decision

The target layout for real-world use is:

- **The ledger repo holds the documents.** It holds the agreement, the change requests and the
  trace schema, and also the SRS and the design documents. It is traced itself:
  - its own `qmstrace.toml` declares requirements and design elements;
  - it reads the schema by path (`[schema] path = "qmstrace.schema.toml"`) and sets
    `ledger = "."`;
  - the schema lists the ledger among the project's repos as `"."`.
- **Product repos hold code and tests.** Their configuration declares components and test
  cases only. Their markers (`Implements:` in a module, `verifies` on a test) cite the ledger's
  IDs.

The engine stays neutral about layout. Documents beside the code (D5's option A) and a separate
documents repo both remain supported. What changes is what gets built next: **a check of the
whole project across its repos**, ahead of M10 · mentions.

## Evidence

Checked with the engine at `fcd68aa`, on scratch copies of `tests/fixtures/mini`, rearranged
into three layouts, each repo a Git repository. The commands were `status`, `check`,
`check --strict`, `thread` and `ledger copy-schema`.

| | Result |
|---|---|
| ✔ the product repo's gate | `check --strict` exits 0. G06 and G07 are met by links to the ledger's items |
| ✔ a mistyped cited ID, with the ledger beside the repo | `verifies("REQ-SVC-10")` is `V03` |
| ✔ baselines in the ledger | work by path, because the schema is in the same tagged tree. A reworded frozen requirement gives `V10` and `S01` on its design elements |
| ✔ change control in one change | an accepted `CR-001.md`, cited with `Change: CR-001` on the item in the same change, clears `V10`. The change request is read, not reported as *not verified* |
| ✔ verdicts across repos | `results` gives a requirement in a sibling its verdict (the fixture's `results-sibling` golden; not re-run in this layout) |
| ✘ the ledger's gate | `check --strict` fails on 6 gaps (G02, G03, G04) that only tests and modules in a product repo can meet |
| ✘ suspects across repos | after a reworded frozen requirement, the design elements in the ledger are suspects, but a test that verifies it gets no signal |
| ✘ `thread` and `impact` | they stop at each repo's edge, so no walk reaches from an origin clause to a test |
| ✘ a product repo's CI | with only that repo checked out, the mistyped ID passes the gate, with exit 0, only listed as *not verified* |
| ✘ `ledger copy-schema` | it rewrote the ledger's own `qmstrace.toml` into a copy of its own schema. After the next schema edit, the ledger would judge itself against old rules |

Every ✘ in the table needs one thing: a view of the whole project.

## Consequences

- **Next milestone:** a project-wide check run in the ledger repo, over the working trees of
  the repos listed in `[repos]`. It judges them together:
  - coverage rules across repos;
  - suspects, `thread` and `impact` across repo boundaries.

  It is the first half of the ledger's import at pins (D2). M10 · mentions follows it.
- **Change control gets stronger.** A change request and the edit it licenses are in one repo,
  so they arrive in one pull request. Documents beside the code could not do this: a product
  repo's pipeline never reaches the change requests.
- **A change that touches both a requirement and code is two pull requests.** The ledger's
  merges first, so the code never cites an ID that does not exist yet.
- **A product repo's CI checks out the ledger beside the repo** until the ledger reads repos
  at pins. Without it, every cited ID is only *not verified here*.
- **Each repo is set up with `init`.** It is not verified whether Claude Code or Codex load
  `AGENTS.md` and skills from a folder added to the session. If one does not, an agent launched
  in a product repo edits the ledger's documents without the ledger's guidance. To be tested.
- **Docs to follow, in the milestone:**
  - D5's consequences, e.g. "A requirement's text is canonical in repo memory, in the repo
    that owns the feature";
  - *Across repos (v0)*, e.g. "A requirement has one home. It is declared in the repo that owns
    it";
  - the manual's *Around the repo* page;
  - the glossary's **Sibling**, because the ledger can now be one.

  D2 already fits: *product repos carry markers only*. So does the glossary's **Ledger Repo**,
  "the sources of their controlled documents".

## Rejected alternatives

- **Keep D5's option A as the target: documents beside the code.** It suits a team without a
  QMS, and the engine keeps supporting it. For this target, though, it spreads the controlled
  set across product repos, and a product repo's pipeline can never verify a change request.
  Checked: in a pipeline, *change requests: NOT VERIFIED*.
- **A separate documents repo beside the ledger.** It works, and the probe ran it. But it adds a
  third repo, and it separates a change request (in the ledger) from the edit it licenses (in
  the documents repo), so one controlled change becomes two pull requests.
- **Let a repo exempt itself from coverage rules**, so that the documents repo passes its gate
  alone. That hides the cross-repo gaps rather than judging them, and it contradicts *rules
  are data, and they are the project's*.

## Open

- Whether qmstrace's own trace moves its SRS and design into `qmstrace-ledger`. For now they
  stay in this repo.
