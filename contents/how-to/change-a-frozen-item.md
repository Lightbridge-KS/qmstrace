# Change a frozen item

!!! abstract "TL;DR"

    Start with `qmstrace status`. Before changing frozen text, obtain an accepted change
    request that lists the item. Add its fresh ID to `Change`, make the approved edit, then
    run `qmstrace check --strict`. Review the evidence notices as well as the exit code.

1. Run `qmstrace status` and identify the governing tag. Resolve any inability to read its
   historical configuration before editing. See [baseline evidence](../reference/baselines.md)
   for schema snapshots and complete Git checkouts.

2. Run `qmstrace impact` with the existing items' IDs and [review the candidate impact
   list](write-an-impact-list.md). Ask the project side to reserve any new IDs explicitly.
   A verified reservation is reported for an unseen start, but cannot supply a graph walk.

3. Follow the project's acceptance process. Confirm the request file has the configured
   accepted `State` and lists every item being changed under `Impacts`. Do not alter the
   register merely to silence a finding.

4. Add the accepted request ID to the item's comma-separated `Change` field, preserving
   earlier citations, and make the approved edit. To retire the item, retain its heading and
   set `Status: withdrawn`. An old citation already present at the baseline cannot authorize
   another change.

   Without a fresh citation, the guard reports:

    ``` text
    --8<-- "cli/golden/check-baseline-unauthorized.txt"
    ```

   With the accepted request listing the changed item:

    ``` text
    --8<-- "cli/golden/check-baseline-authorized.txt"
    ```

5. Run `qmstrace check --strict`. Address violations and coverage gaps. An unavailable ledger
   leaves request acceptance unverified even if the command succeeds; arrange verification
   against the register through the project workflow.

6. Review affected designs, code and tests, and run relevant tests. M5a's guard does not yet
   list downstream suspects. A successful gate is not evidence that those reviews occurred.

For finding definitions and exact comparison rules, see [Baselines and change
control](../reference/baselines.md).
