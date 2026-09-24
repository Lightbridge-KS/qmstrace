# Explore a trace interactively

!!! abstract "TL;DR"

    Generate `qmstrace graph --out trace.html`, open it, then search for the item being
    reviewed. Use its thread and finding inspector to locate source and review obligations.

1. From the product repo, generate a new snapshot:

    ``` sh
    qmstrace graph --out trace.html
    ```

2. Open `trace.html` in a browser. Read **Evidence and limits** before interpreting the graph.
   An unavailable source remains unavailable when a node is visible.
3. Search by ID or title and select an item from the list. Keyboard users can Tab to the
   matching button and press Enter. The inspector gives the full ID and source location;
   long labels may be shortened on the canvas.
4. Set **Direction** to downstream to see what hangs off the item, or upstream to see its
   ancestry. Start with depth 1, then widen it. **All items** restores surrounding context.
5. Select an authored link in the inspector to read its marker and declaration location.
   Hidden links still contribute to the precomputed reach: filters change the picture, not
   the assessment. Check the hidden counts when interpreting an apparently isolated item.
6. In **Findings**, choose suspects to review S01. Read every root and governing tag, including
   historical-only reach. A missing current edge does not clear historical review work.
   Follow [Review downstream suspects](review-suspects.md) for the review itself.
7. After editing source, generate a new filename and reopen it. The old file is unchanged.
   Run `qmstrace check --strict` separately when a gate is needed.

The browser cannot record completion or approve a change. For a copyable change-request
candidate use [Write an impact list](write-an-impact-list.md); for explicit test verdicts
use [Read test results](read-test-results.md).
