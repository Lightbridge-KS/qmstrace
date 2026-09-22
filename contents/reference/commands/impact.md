# qmstrace impact

!!! abstract "TL;DR"

    `qmstrace impact ID…` combines the downstream work affected by several starting items and
    shows their upstream origins. It prints a candidate `Impacts:` line for a change request.
    The analysis stops at this repo's edge. An unseen starting ID rejects the whole request.

## Synopsis

``` text
--8<-- "cli/golden/help-impact.txt"
```

Supply one or more IDs visible to the run: requirements, design elements, module paths, test
node IDs, external clauses or sibling items. Repeated IDs and argument order do not change
the output. `-C` works before or after the command.

## Output

Two requirements in the miniature service share downstream work. Each downstream item appears
once, grouped by its configured type. Origins are those of the starting items, not of every
item reached downstream:

``` text
--8<-- "cli/golden/impact-multiple.txt"
```

`Assumes` carries impact forward through further items. Backward, it does not establish
ancestry: an assumed item's origins appear only if an ordinary path also reaches them.

The candidate line contains starting and downstream items whose types are covered by a
configured baseline. It is sorted and deduplicated. Upstream origins are context, not added
to this line. A starting origin can qualify only if its type is itself covered.

The line proposes items to review; it does not claim they all need edits or are frozen.
The shared assessment reads baseline evidence and change requests, but candidate membership
still depends on configured types, not frozen state. An accepted request's reservation is
reported for an unseen start; it does not establish that item's type or links. When no known
item type qualifies, the command explains why it emits no candidate line.

## Repository boundary

A sibling's item is read from its working tree, not pinned. Only links authored in the
current repo are traversed; the sibling's own ancestry and downstream work are not scanned:

``` text
--8<-- "cli/golden/impact-sibling.txt"
```

In a pipeline a cited sibling ID can remain visible even when its source is unavailable.
Its type is unknown and it is omitted from the candidate line, explicitly:

``` text
--8<-- "cli/golden/impact-in-a-pipeline.txt"
```

Unread sources, unverified citations and violations that exclude links remain visible.
This is a working-tree analysis within one repo, not a project-wide analysis at pins.

## Exit codes

`0` means the requested walk was produced, including its limitations; gaps and violations
do not turn this informational command into a gate. Use [check](check.md) to judge the repo.

`2` means usage, configuration or unseen starting IDs prevented the request. If even one
starting ID is unseen, the entire request is refused: no partial listing and no `Impacts:`
line. The diagnostic lists every unseen ID, nearby matches and source limitations. An unseen
ID is never presumed reserved by a change request.

`3` means an internal error. See [Exit codes](../exit-codes.md).

For the authoring steps, see [Write an impact list](../../how-to/write-an-impact-list.md).
