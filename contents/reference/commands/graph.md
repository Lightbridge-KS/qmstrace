# qmstrace graph

!!! abstract "TL;DR"

    Export a self-contained HTML browser of the current assessment. Open the file locally;
    no server or network is needed. Findings remain informational and visible in the file.

## Usage

``` text
--8<-- "cli/golden/help-graph.txt"
```

`ID` optionally selects the initial thread. Every item visible to the run is included in
both cases; an initial selection is not an export or privacy filter. An unseen ID exits 2
without writing a file. The output path is required, resolves from the effective working
directory (`-C` on either side), and must not already exist. Its parent must exist.

## Example

From the miniature service repo:

``` sh
qmstrace graph REQ-SVC-01 --out trace.html
```

``` text
--8<-- "cli/golden/graph-service.txt"
```

## Controls

| Control | Behavior |
|---|---|
| Search | Finds IDs and titles across all included items, including filtered ones |
| Item list | Keyboard-accessible selection; reveals the selected item's type and thread |
| Scope | All items, or the selected thread |
| Direction / depth | Limits displayed upstream/downstream reach using the engine's traversal |
| Item / link filters | Hide display elements; labelled counts show what is hidden |
| Inspector | Ownership, source location, metadata, badges, links and finding next moves |
| Findings | All violations, gaps and suspects, independent of graph filters |
| Fit / reset | Fit visible nodes, or restore the full view and filters |

Pan, zoom and drag nodes on the graph. Positions start in configured type columns; physics
is disabled. Arrows retain authored direction (test → requirement), including links that
skip columns or form cycles. Dashed dependency links count toward no coverage. Selecting
an item highlights its reach; it does not reverse arrows. Backward traversal stops at
`Assumes` unless an ordinary path also reaches the item.

## Evidence and exits

A usable assessment exits 0 even with findings. Usage/output/assessment failures exit 2;
internal faults exit 3. The graph uses current validated links, so refused links appear as
findings rather than connections. The findings list retains deleted-item diagnostics and
historical-only suspects. Each S01 includes all roots, tags, graph versions and distances.

The file contains item titles, metadata, source paths and findings. Review its contents
before sharing it. It embeds no source archive. It is a working-tree snapshot; its commit
has not been verified. Source and baseline limits remain visible under filtering. Siblings
are not pinned and traversal stops at the local repo's edge. No test report is loaded.

Generation neither edits source nor records review. Existing files are never replaced;
choose another output name or explicitly remove an obsolete artifact before regenerating.
