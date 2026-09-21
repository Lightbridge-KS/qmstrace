# Findings

!!! abstract "TL;DR"

    A finding is one thing wrong or unfinished in a repo, on one line: a code, where it is, what
    is wrong, and what to do next. A code's first letter is its kind. This version reports
    violations — `V` codes — and every one of them is in the table below.

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
| `G` | gap | only the gate — a coverage rule not met yet; its codes come from the project's trace schema | not built yet |
| `S` | suspect | never — downstream of something that changed since a baseline | not built yet |

## The catalogue

--8<-- "manual/findings.md"

`V10` to `V13` are held for the baseline checks, which are not built yet.

`qmstrace status` counts violations by code on its last line. Listing each one, with its place
and next move, is the job of `qmstrace check`, which is not built yet either.
