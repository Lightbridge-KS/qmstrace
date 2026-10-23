# Baselines and change control

!!! abstract "TL;DR"

    `status` identifies frozen document items; `check` guards changes to them. A baseline is
    a configured tag reachable from `HEAD`. Changing or retiring a frozen item needs a fresh
    accepted change request listing its ID. Git and request evidence limits remain visible.

## Selecting a baseline

The configured tag pattern, subject and `covers` types define a scope. The latest reachable
commit governs, by ancestry rather than tag number or date. Overlapping scopes produce one
comparison per item. Tags at the same commit are equivalent; their names and annotation
metadata are retained. Incomparable governing commits cause exit `2`: establish an approved
baseline after the merge. A feature branch cannot see a tag outside its ancestry.

Annotated tags supply a tagger and date. Lightweight tags still govern but are labelled weaker
evidence. Detached `HEAD`, linked worktrees and trace roots inside a larger repository work.

``` text
--8<-- "cli/golden/status-baseline-frozen.txt"
```

Counts concern controlled document items. **Changed and removed are subsets of frozen**;
new items are outside that frozen population. Withdrawn counts current items with that status.
Path-derived modules and tests are scanned but the document guard does not require item-level
change citations on them; code changes follow the project's commit or pull-request convention.

A document type named in any baseline `covers` list needs an ID with exactly one configured
subject key, even before a tag is cut. V17 reports missing or ambiguous ownership while
authoring. Once a relevant baseline exists, uncertainty prevents judgment (exit `2`). If the
bad ID or configuration is in the selected tagged tree, the refusal names that tag; correcting
today's files requires a valid, approved successor baseline rather than rewriting the old one.

## Historical configuration

Each tagged tree supplies its own `qmstrace.toml`, extraction patterns and schema. A tag from
before trace configuration freezes nothing. An existing malformed configuration cannot be
treated as pre-trace history. Historical identities survive later pattern and type changes.

The schema must be embedded or stored in the **same tagged Git tree**. A historical path such
as `../ledger/qmstrace.schema.toml` cannot be resolved from today's ledger: that would substitute
unverified rules for historical evidence. Such a baseline causes exit `2`.

For future baselines, give the product repo the project's schema before the tag is cut: run
`qmstrace ledger copy-schema` in the ledger and commit the copy — see
[share the project's schema](../how-to/share-the-schema.md). Existing tags are not rewritten automatically. A project adopting
this arrangement establishes its next approved baseline under its normal review process;
the tool does not retroactively certify older changes.

## Offline evidence

No command fetches tags or missing objects. Shallow history, unavailable required objects and
explicit tag-exclusion settings prevent judgment when baselines are configured. An ordinary
full local repository is judged against its reachable local tags. **Remote-tag completeness
is not verified**, even when some local baselines are present. The project's checkout process
must obtain the intended history and tags before running the gate.

``` text
--8<-- "cli/golden/status-baseline-shallow.txt"
```

## Citations and request metadata

`Change: CR-001, CR-002` is a comma-separated list. A citation is fresh only when absent from
the governing snapshot. Adding a citation alone does not change the item's digest. Rewording,
changing a link or changing status does; whitespace-only rewrapping does not.

Request files live in the configured directory, with the ID as filename (`CR-001.md`). Their
metadata preamble carries `State` and `Impacts`; the accepted value is matched exactly.
`Impacts` is a comma-separated list of authored or path-derived IDs. Fenced examples and fields
inside prose sections grant no approval. Duplicate or malformed metadata is a violation.

| Situation | Finding |
|---|---|
| Controlled item changed or added without a fresh citation | V10 |
| Fresh citation names a missing, malformed or unaccepted request | V11 |
| Accepted request does not list the item in `Impacts` | V12 |
| Frozen heading disappears | V13 |

Every fresh citation offered for a change is checked. A missing request in a readable register
fails; an unavailable register permits fresh citations with a **NOT VERIFIED** notice, retained
in quiet output and the result line. Malformed files never receive that permissive fallback.
Request files are read from the current working tree, not a verified ledger pin.

``` text
--8<-- "cli/golden/check-baseline-unavailable.txt"
```

## Withdrawal

Retain the heading and write `Status: withdrawn`, with a fresh accepted citation when frozen.
Withdrawal and reactivation are text changes. A withdrawn item raises no coverage gaps of its
own, and links with a withdrawn endpoint cannot satisfy active items' coverage rules. Its
identity, links, validation findings, traversal and test-result evidence remain visible.
Withdrawal does not turn a test result into approval. No special coverage exemption is inferred
from another status value.

See [Downstream suspects](suspects.md) for the review list. A passing change guard establishes neither
that downstream work was reviewed nor that an unverified request was accepted.
