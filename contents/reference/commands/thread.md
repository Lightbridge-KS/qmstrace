# qmstrace thread

!!! abstract "TL;DR"

    `qmstrace thread <ID>` walks one item backward to what it derives from, and forward to what
    hangs off it — for a requirement, its design elements, code and tests; for a clause, every
    item here that derives from it. Each item appears once, nearest first. It stops at this
    repo's edge.

## Synopsis

``` text
--8<-- "cli/golden/help-thread.txt"
```

Any ID the run can see works: a requirement or a design element, a module's path, a test's ID
(`file::function`, as pytest names it), a clause the agreement declares, or an item of a
sibling repo. `-C` goes on either side of the command, as with `status`.

## Output

A requirement — backward to its clause, forward to its design, code and tests:

``` text
--8<-- "cli/golden/thread-requirement.txt"
```

An automated test, walked back to the clauses it serves:

``` text
--8<-- "cli/golden/thread-backward.txt"
```

A clause, and everything here that derives from it:

``` text
--8<-- "cli/golden/thread-origin.txt"
```

A sibling's item — this repo's side of it only:

``` text
--8<-- "cli/golden/thread-sibling.txt"
```

The same item in a pipeline, where the sibling and the ledger are not checked out:

``` text
--8<-- "cli/golden/thread-in-a-pipeline.txt"
```

When an assumption and an ordinary ancestry path reach the same item backward, the ordinary
path is used so its origins remain visible; the assumption is retained as `also`. To combine
several starting items into a change-request candidate, use [impact](impact.md).

## Reading a line

| Part | Example | What it says |
|---|---|---|
| the marker | `Satisfies` | the link that reaches this item first; each step of indentation is one more link from the item you asked about |
| the item | `DSN-SVC-01 — Key check · design element · docs/design/…:8` | its ID, title, type and where it is written; a sibling's item carries the sibling's path, and *not pinned* |
| `also …` | `also Satisfies from DSN-SVC-02` | another link between this item and one already shown — the item is not repeated |
| `assumes it — counts toward no coverage` | | an `Assumes` link, followed forward: what the assuming item relies on changing can break it |
| `assumed — what it derives from is not followed` | | walking backward, an assumption ends the walk |
| the last line | `forward: 2 design elements, … — this repo only` | counts by type, in both directions |

When the run could not read something — an external source, a sibling — or refused links as
violations, the lines under the heading say so. An empty direction says *nothing here hangs off
it*. Why each item appears once, and where the walk stops: [The chain](../../explanation/the-chain.md).

## Exit code

`0` — or `2` for an ID nothing here can see, with the closest IDs it can. In a pipeline, where a
sibling could not be read, it says so instead of calling the ID missing. See
[Exit codes](../exit-codes.md).
