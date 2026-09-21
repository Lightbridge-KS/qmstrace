# Check your work before you commit

!!! abstract "TL;DR"

    Run `qmstrace check` after every change, work through its list — violations first, then
    gaps — and run `qmstrace check --strict` before you commit. When it exits `0`, the repo's
    trace data is right and complete as far as this repo can tell.

## Steps

1. **See where you are.**

    ``` sh
    qmstrace status
    ```

    What was read, and one line per requirement. If an item you wrote is missing, it is in a file
    its type is not read from — `check` will say so.

2. **List what is wrong and what is missing.**

    ``` sh
    qmstrace check
    ```

    Each line ends with `Fix:` — the next move. Work through the **violations** first: a gap
    often exists only because a violation refused the link it needs.

3. **Fix a violation** by correcting the line it names. Never invent an ID to make one go away:
   when nothing real fits — no clause covers a requirement, no change request exists — stop and
   ask whoever owns the decision.

4. **Close a gap** by doing the work it names — write the design element, the test — and then
   the link. A link states a fact: tag a test with a requirement only if the test fails when the
   requirement is broken. To be sure, break the code on purpose and watch the tagged test fail.

5. **Run the gate.**

    ``` sh
    qmstrace check --strict
    ```

    `0` — commit. `1` — the result line says whether violations or gaps remain.

## When a gap cannot be closed here

A rule may ask for an item type this repo does not declare — a repo with no design documents,
say. `qmstrace rules` marks such a rule *cannot be met with the item types this repo scans*.
The gap stands until the repo declares that type, or the item is met in another repo of the
project and judged when the ledger imports it. Under `--strict` it fails, on purpose: the
project's rules say so, and no exemption is hidden.

!!! note "Not built yet"

    Running this gate in a pipeline needs a copy of the project's trace schema inside the repo,
    generated and verified; nothing generates it yet. Until then the gate runs where the ledger
    repo is checked out beside the product repo — on your machine.
