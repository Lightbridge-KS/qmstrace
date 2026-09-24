# Findings

!!! abstract "TL;DR"

    A finding is one thing wrong or unfinished in a repo, on one line: a code, where it is, what
    is wrong, and what to do next. A code's first letter is its kind. This version reports
    violations — the `V` codes below, which are qmstrace's own — and gaps, whose `G` codes are
    the project's, printed by `qmstrace rules`. S01 lists a downstream item needing review.

## The shape of a finding

Every finding carries the same four parts, and the last one is never left out:

| Part | Example | What it is |
|---|---|---|
| code | `V09` | stable, classed by its first letter |
| where | `docs/req/service-srs.md:14` | the file and line to open |
| what is wrong | `the agreement declares no AGR-9` | the fact, with the IDs involved |
| next move | `Fix: cite a real one, or tell the developer that nothing covers this — never invent one.` | what to do, and, where a wrong move is tempting, which one not to make |

## Kinds

| Letter | Kind | What it fails | In this version |
|---|---|---|---|
| `V` | violation | always — the trace data is wrong at any stage | reported |
| `G` | gap | only the gate — a coverage rule not met yet; its codes come from the project's trace schema | reported |
| `S` | suspect | never — downstream of changed or deleted frozen text | reported |

## The catalogue

--8<-- "manual/findings.md"

`V10` to `V13` are emitted by the [baseline guard](baselines.md).
`V16` is the one violation found in a baseline tag's tree that does not stop the tag being
read: it declares nothing. How to avoid it: [write traced docs](../how-to/write-traced-docs.md).
`S01` is a [suspect](suspects.md); its next move starts with `Review:` and does not claim
that review or approval has happened.

`qmstrace status` counts violations and gaps by code on its last line;
[`qmstrace check`](commands/check.md) lists each one, with its place and next move. A gap's code
and words come from the project's rule — see [`qmstrace rules`](commands/rules.md) — and its next
move from qmstrace: the form of the marker to write, or the violation to fix first.
