# Check the whole project

!!! abstract "TL;DR"

    In the ledger repo, run `qmstrace ledger check`. It reads every repo the schema lists
    under `[repos]` — from tracked defaults or a selected workspace map — and judges them as one project.
    `qmstrace ledger check --strict` is the ledger's gate. A repo it cannot read stops it,
    with exit `2`.

## Steps

1. **List every repo of the project** under `[repos]` in the ledger's `qmstrace.schema.toml`,
   each as a name and a path from the ledger. If the ledger holds the requirements and the
   design, list it too, as `ledger = "."`, and give it a `qmstrace.toml` of its own — see
   [configuration](../reference/configuration.md#a-ledger-that-holds-the-documents).

2. **Locate every repo.** Use the ledger-relative defaults in `[repos]`, or
   [select a workspace map](use-a-workspace-map.md) for a different layout. In a pipeline,
   check out each repo at the selected location. Inspect it with `qmstrace paths`; a repo
   that is not there stops the check rather than passing unread.

3. **Give every product repo the ledger's rules**, in the ledger:

    ``` sh
    qmstrace ledger copy-schema
    ```

    A repo holding other rules than the ledger's schema — an older copy, say — is refused by
    the check, and named. See [share the project's schema](share-the-schema.md).

4. **Run the check, in the ledger:**

    ``` sh
    qmstrace ledger check
    ```

    ``` text
    --8<-- "cli/golden/ledger-check-split.txt"
    ```

    The header lists every repo read. If the command stops with exit `2`, deal with each repo it
    names, then run it again.

5. **Work through the findings.** A violation's location names the repo it is in
   (`../client/…`); fix it there. A gap's next move names the repos where the missing link can
   be written. A suspect in another repo than the changed item is reached by today's links only
   — review it as any suspect: [review downstream suspects](review-suspects.md). To see what
   hangs off an item across every repo, `qmstrace ledger thread ID`.

6. **Gate the ledger** on the strict form, in its pipeline:

    ``` sh
    qmstrace ledger check --strict
    ```

    Each product repo keeps its own gate, `qmstrace check --strict`, in its own pipeline.

What each part of the output means, and every refusal: the
[ledger reference](../reference/commands/ledger.md#qmstrace-ledger-check). Why the check reads
working trees and what is left to the pinned import: [Around the repo](../explanation/around-the-repo.md).
