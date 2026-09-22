# Kinds of finding

!!! abstract "TL;DR"

    A finding is a **violation** — trace data that is wrong, at any stage — a **gap** — work not
    done yet — or a **suspect** — something downstream of a change, waiting for a fresh look.
    Violations always fail the check; gaps fail only the gate; suspects never fail. Mixing them
    up would either block people mid-work or let wrong data through.

## Three kinds, three verdicts

| Kind | Code | Means | Fails |
|---|---|---|---|
| violation | `V…` | the trace data is wrong: an ID that exists nowhere, a link to the wrong kind of item, a missing field, an item where its type is not read | always |
| gap | `G…` | a coverage rule not met yet: a requirement with no design, a design element with no test | the gate only — `qmstrace check --strict` |
| suspect | `S01` | an existing local item downstream of changed or deleted frozen text: it needs a fresh look, not necessarily an edit | never — an applicable upstream baseline including the change clears its chain |

The [suspect reference](../reference/suspects.md) explains how historical and current
dependencies contribute. Edited and withdrawn items can still need review.

## Why a gap does not fail while you work

In the middle of the work, gaps are expected — they are the list of what is left, in order.
Failing on them would make every intermediate state an error, and the list of gaps is most useful
exactly then: an agent building a slice drained twenty-six of them, one commit at a time.

The **gate** is where they must be gone: `qmstrace check --strict`, run before a commit and on a
pull request. A gap there means work declared done that is not.

A violation is different: nothing about being mid-work makes wrong data right, so it fails in
every mode.

## Stages

The standard lets a rule apply *from a stage on* — "every requirement has a test" matters from
construction, not while the requirements are still being written. In this version no rule has a
stage: under `--strict`, every gap fails. Stages belong to the project's plan, which qmstrace
will read from the ledger; until then the gate is all or nothing.

## Rules are data

Every rule is written in the project's trace schema and printed by
[`qmstrace rules`](../reference/commands/rules.md). None lives in the tool, and none is restated
in a guide or a skill — a rule that lives in two places drifts. A rule with no `where` applies to
every item of its type: there is no exemption the schema does not show.
