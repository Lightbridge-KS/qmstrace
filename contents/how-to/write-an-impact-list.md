# Write an impact list

!!! abstract "TL;DR"

    Before editing several traced items, run `qmstrace impact ID…` with their IDs. Review the
    downstream work, origins and source limitations, then use the candidate line to prepare
    the change request. Keep proposed new items explicit; a graph walk cannot invent them.

1. Identify the existing items the request would change. In the miniature service, for example:

    ``` sh
    qmstrace -C service impact REQ-SVC-01 REQ-SVC-02
    ```

2. Read the source notices before using the list. If a starting ID is unseen, correct it or
   make its source available and rerun. The whole request stops until every start is visible.
   A readable accepted request can confirm a reservation; the command still needs a declared
   item before it can traverse its links or include it in a candidate line.

3. Review the combined output:

    ``` text
    --8<-- "cli/golden/impact-multiple.txt"
    ```

4. Inspect the downstream designs, components and tests to decide which need edits and which
   need review only. Inspect the listed origins to decide whether the proposed change also
   requires a change to the agreement. The command's boundary is this repo. For a change that
   spans repos, run [`qmstrace ledger impact`](../reference/commands/ledger.md#qmstrace-ledger-impact)
   with the same IDs in the ledger: it walks every repo of the project.

5. Use the candidate `Impacts:` line as the starting point for the change request's list.
   Review it against the proposed edits; record review-only work in the impact analysis.
   Explicitly name proposed new items and any new agreement clause. The traversal cannot
   infer future content, and printing this line does not approve the change request.

6. Follow the project's change-request acceptance process before editing frozen work. After
   the accepted edits, run [check](../reference/commands/check.md) and review the changed
   trace links.

For the filtering rules and exit codes, see [impact](../reference/commands/impact.md).
