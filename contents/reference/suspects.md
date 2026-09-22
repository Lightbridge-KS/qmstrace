# Downstream suspects

!!! abstract "TL;DR"

    `status` summarizes existing local items downstream of changed or deleted frozen text.
    `check` lists every `S01` review obligation. Suspects never fail the gate, and editing an
    item or passing its tests does not clear them.

## What creates a suspect

Each changed or removed frozen document item starts two independent walks: its governing
baseline graph and today's graph. Ordinary links and `Assumes` are followed transitively.
The combined reach includes removed dependencies, but never a path assembled from old and
new links. Only dependants that existed in that upstream snapshot and still exist locally
today are listed. New intermediate items can carry the walk without becoming suspects.

The comparison belongs to the **upstream** item. A newer baseline covering only a downstream
design does not clear a requirement's chain. Once the applicable upstream baseline includes
the change, that chain disappears. An explicit recorded-review clearance is not implemented.

## Status summary

``` text
--8<-- "cli/golden/status-suspects-summary.txt"
```

Distance is the shortest number of links from any contributing root, in either graph
version. Status lists distance-one items and counts farther items by distance. Every item
counts once even when several roots reach it.

## Complete findings

``` text
--8<-- "cli/golden/check-suspects-strict.txt"
```

Each S01 gives the current file/line, upstream roots and governing tags. Each reason retains
its baseline/current distances and says `historical-only`, `current-only` or `both versions`.
Its own digest determines `unchanged` or `edited — still needs review`; these can differ
between roots with different snapshots. Findings are sorted by minimum distance then ID.

The same complete findings and evidence limits survive quiet output:

``` text
--8<-- "cli/golden/check-suspects-quiet.txt"
```

## Boundaries and exits

- Withdrawn items keep their labels and review obligations. Their coverage exemption is separate.
- A deleted frozen root retains its surviving dependants alongside V13. A missing dependant
  is not listed as an item to review today.
- Traversal stops at this repo's edge. Historical sibling/external citations are **NOT
  VERIFIED**; today's sibling files cannot supply historical evidence.
- Invalid historical local graphs prevent judgment with exit `2`, naming the tag and finding.
  Current graph violations remain visible, including the limits imposed by refused links.
- Suspects never affect exit codes, including `check --strict`. No review state is persisted;
  a successful check is not approval of the change.

See [baselines](baselines.md) for offline Git and schema requirements, and
[review downstream suspects](../how-to/review-suspects.md) for the workflow.
