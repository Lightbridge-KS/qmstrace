# Around the repo

!!! abstract "TL;DR"

    A product repo is rarely alone. Its items trace back to an agreement kept in the project's
    **ledger repo**, and it may cite items of the project's other repos — its **siblings** — or
    of the ledger itself, when the ledger holds the requirements and the design. qmstrace reads
    them from beside the repo when they are there, and says *not pinned*. When it cannot — as in
    a pipeline, which checks out one repo — it says *not verified here*, and fails nothing for
    it. In the ledger, `qmstrace ledger check` judges every repo together.

## Three kinds of repository

``` mermaid
flowchart LR
  subgraph ledger["ledger repo — the project"]
    docs["agreement · change requests · trace schema<br/>requirements · design"]
  end
  subgraph product["product repos — daily work"]
    svc["service<br/>code · tests"]
    clt["client<br/>code · tests"]
  end
  svc -- "cites by ID" --> docs
  clt -- "cites by ID" --> docs
```

- A **product repo** holds a product's code and tests, with markers in them. It outlives any
  one project.
- The **ledger repo** holds one project: its agreement, its change requests, its trace schema —
  the rules every repo of the project follows — and, in this layout, the project's requirements
  and design, which are reviewed and released together.
- **qmstrace** is installed into them. It holds no project data of its own.

The requirements and the design can also stay in the product repos, beside the code — the
older layout, where the ledger holds only the agreement, the change requests and the schema.
qmstrace judges either way. The ledger lists every repo to read under `[repos]`, and itself as
`"."` when it holds documents.

An item has one home: the repo that declares it. Another repo of the project cites it by ID,
exactly like one of its own items, and never declares it again.

## Not pinned

In a product repo, qmstrace reads the ledger and the siblings from the folders beside it — from
their working trees, as they are right now, with whatever is uncommitted there. That is enough
while you work, and it is said on every run: *read from ../client's working tree, not pinned*.

The project as a whole is judged in the ledger repo. `qmstrace ledger check` reads every repo's
working tree together — coverage met in any repo, suspects across repos — and says *not
pinned*, like everything else here ([check the whole project](../how-to/check-the-project.md)).
Later, the ledger's import will read each repo **at a pin** — one commit, named on purpose — and
decide every citation across repos for good.

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
every sibling, only to judge them against a colleague's uncommitted work. The ledger judges them
all together: `qmstrace ledger check` over working trees now, the import at pins later.

**Why an own ID still fails.** A cited ID that matches this repo's own pattern — `REQ-CLT-07`,
say, in the client — gets no such benefit: this repo *was* read, so the ID is known not to
exist, and the run reports `V03`.

**A pipeline has no ledger to read the schema from**, so a product repo carries a generated,
verified copy of it — written in the ledger by `qmstrace ledger copy-schema` and committed in
the repo. Its digest is checked on every run; only the rules travel, and everything else the
ledger holds stays *not verified* until the ledger's import. See
[share the project's schema](../how-to/share-the-schema.md).
