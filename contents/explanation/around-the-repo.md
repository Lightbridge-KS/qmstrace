# Around the repo

!!! abstract "TL;DR"

    A product repo is rarely alone. Its requirements trace back to an agreement kept in the
    project's **ledger repo**, and it may cite items of the project's other product repos — its
    **siblings**. qmstrace reads both from beside the repo when they are there, and says *not
    pinned*, because it read a working tree. When it cannot read them — as in a pipeline, which
    checks out one repo — it says *not verified here*, and fails nothing for it.

## Three kinds of repository

``` mermaid
flowchart LR
  subgraph product["product repos — daily work"]
    svc["service<br/>requirements · design · code · tests"]
    clt["client<br/>requirements · code · tests"]
  end
  ledger["ledger repo — the project<br/>agreement · change requests · trace schema"]
  svc -. "cites by ID (a sibling)" .- clt
  svc -- "read at a pin, later" --> ledger
  clt -- "read at a pin, later" --> ledger
```

- A **product repo** holds a product's code, tests and documents, with markers in them. It
  outlives any one project.
- The **ledger repo** holds one project: its agreement, its change requests, and its trace
  schema — the rules every product repo of the project follows.
- **qmstrace** is installed into them. It holds no project data of its own.

A requirement has one home: the product repo that owns it. Another repo of the project cites it
by ID, exactly like one of its own items, and never declares it again.

## Not pinned

In a product repo, qmstrace reads the ledger and the siblings from the folders beside it — from
their working trees, as they are right now, with whatever is uncommitted there. That is enough
while you work, and it is said on every run: *read from ../client's working tree, not pinned*.

The project as a whole is judged later, in the ledger repo, which reads each product repo **at a
pin** — one commit, named on purpose. That is where a citation across repos is decided for good.

## Not verified here

A pipeline checks out one repo. The ledger and the siblings are not there, so what the repo
cites from them cannot be looked up:

``` text
--8<-- "cli/golden/status-client-in-a-pipeline.txt"
```

| What could not be read | What `status` says | What fails |
|---|---|---|
| the agreement | `external AGR-*: NOT VERIFIED` | nothing — each cited clause is judged at the ledger's import |
| a sibling | `sibling …: NOT REACHABLE` and `not verified here: …` | nothing — unless the ID matches this repo's own pattern |
| the ledger's location (no `ledger` key) | `NOT VERIFIED`, `siblings: NOT LOCATED` | nothing |
| the trace schema, read by path | the run cannot judge — exit `2` | the run — which is why a repo judged alone carries a copy |

**Why not fail?** Failing would force every product repo's pipeline to check out the ledger and
every sibling, only to judge them against a colleague's uncommitted work. The ledger's import
reads them all together, at a pin, and judges every citation for real.

**Why an own ID still fails.** A cited ID that matches this repo's own pattern — `REQ-CLT-07`,
say, in the client — gets no such benefit: this repo *was* read, so the ID is known not to
exist, and the run reports `V03`.

**A pipeline has no ledger to read the schema from**, so a product repo carries a generated,
verified copy of it — written in the ledger by `qmstrace ledger copy-schema` and committed in
the repo. Its digest is checked on every run; only the rules travel, and everything else the
ledger holds stays *not verified* until the ledger's import. See
[share the project's schema](../how-to/share-the-schema.md).
