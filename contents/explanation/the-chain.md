# The chain

!!! abstract "TL;DR"

    Everything qmstrace traces is one chain: an agreement clause, the requirements that derive
    from it, the design elements that satisfy them, the code that implements them, and the tests
    that verify them. Each link is written at its downstream end — the later item names the
    earlier one — so nothing is recorded twice. `qmstrace thread` walks the chain either way.

## The chain

``` mermaid
flowchart RL
  req["requirement"] -- Origin --> agr["origin clause<br/>(in the agreement)"]
  dsn["design element"] -- Satisfies --> req
  mod["component<br/>(a module)"] -- Implements --> dsn
  test["test case"] -- verifies --> req
  test -- verifies --> dsn
```

Each arrow is a line in something already written: a field under a requirement's heading, a
line under a design section, a sentence in a module's docstring, a marker on a test.

## Written at the downstream end

A link is declared by the item that comes later in the chain: the test names the requirement it
verifies; the requirement names the clause it comes from. The later item is written with the
earlier one in mind, so that is when the link is known — and there is one place to change it.

A table of links kept beside the documents was the alternative, and it drifts: it is a second
copy of what the test or the design section already says.

So the **backward** trace — from a test to what it serves — is what people write. The
**forward** trace — from a clause to everything that derives from it — is derived by the tool.

## Many to many

A design element may satisfy several requirements, a requirement may need several design
elements, and a test may verify a requirement and its design element at once. Nothing forces
one to one, and the layout of the code should not bend towards it.

A walk therefore meets some items by two paths. `thread` shows each item once, under the link
that reaches it first, and notes the other link on the same line:

``` text
--8<-- "cli/golden/thread-origin.txt"
```

## Assumes: a dependency, not coverage

Sometimes an item relies on something another item provides — often in another repo: that
registering twice is harmless, that the other side checks a pattern. `Assumes:` says so.

- It **counts toward no coverage rule**. Nothing is covered by being assumed.
- It **carries suspicion forward.** When the assumed item changes, the assuming one may break,
  so walking forward crosses an `Assumes` link and goes on past it.
- **Walking backward, it ends the walk.** What the assumed item derives from is not what the
  assuming item derives from. Following it would name clauses that have nothing to do with the
  item you asked about.

## Where the walk stops

At this repo's edge. A sibling's item is shown with its path and *not pinned*, but its own links
— what it derives from, what hangs off it over there — are not read. For the same reason, a
sibling item that assumes something here cannot be seen from here.

In the ledger, [`qmstrace ledger thread`](../reference/commands/ledger.md#qmstrace-ledger-thread)
walks the whole chain in one place, across every repo of the project — from their working
trees, *not pinned*. Reading each repo at a pin is the ledger's import, later. See
[Around the repo](around-the-repo.md).
