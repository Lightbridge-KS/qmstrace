# Review downstream suspects

!!! abstract "TL;DR"

    Start with `qmstrace status`, then use `qmstrace check` for every suspect and its reasons.
    Review each dependant against the upstream change, run relevant tests, and record that
    review in the project's review process. Do not edit an item merely to remove a finding.

1. Run `qmstrace status` and read the governing baseline and source notices.
   Resolve an inability to judge historical evidence before treating the list as complete.
2. Run `qmstrace check` (or `check --quiet`) for every S01. Inspect each upstream root's
   change against its listed tag. Several reasons can share one dependant.
3. Review unchanged items as well as edited ones. A historical-only reason means a former
   dependency needs attention even though today's graph no longer contains its path.
   Use the tagged source to understand that former relationship.
4. Make justified edits, follow [change control](change-a-frozen-item.md) for frozen text,
   and run relevant tests. [Read test results](read-test-results.md) for test evidence;
   passing tests do not establish that the upstream change was reviewed.
5. Record the review through the project's existing review process. Run `check --strict`
   to catch violations and coverage gaps. S01 remains informational; there is no clearance
   command or approval marker in this version.
6. When the project approves its next applicable upstream baseline, confirm the chain has
   cleared. A downstream-only tag or an unrelated baseline does not clear it.

This example retains a review obligation after a link is removed:

``` text
--8<-- "cli/golden/check-suspects-historical.txt"
```

The [suspect reference](../reference/suspects.md) defines eligibility, distances and evidence
limits. `impact` remains useful for today's candidate impact list; `check` also preserves
historical-only suspect reach.
