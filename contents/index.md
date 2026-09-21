# qmstrace

!!! abstract "TL;DR"

    qmstrace keeps the traceability of a software project — from the agreement, through
    requirements and design, to code and tests — in the repositories where that work is already
    done, so that an auditor's questions are answered by a query instead of by assembly. It is a
    command-line tool. It is early: one command, `qmstrace status`, works today.

## What it does

People and coding agents already write requirements, design notes, code and tests. qmstrace
asks for a little more precision in the same places — an ID in a requirement's heading, a line
under a design section, a marker on a test — and then:

``` mermaid
flowchart LR
  write["markers, where the work is written"] --> read["qmstrace reads them"]
  read --> judge["judges them against the project's rules"]
  judge --> answer["answers: what was read, what is wrong, what is missing"]
```

The rules are data, declared by the project in one file and printed on request — never hidden
in the tool. The standard is data too: ISO/IEC 29110 comes first.

## Where to start

| To… | Read |
|---|---|
| see it work, in five minutes | [A first look](tutorials/first-look.md) |
| look up a command, a finding, an exit code or a configuration key | [Reference](reference/commands/status.md) |
| understand what *not pinned* and *not verified here* mean | [Around the repo](explanation/around-the-repo.md) |

This manual follows [Diátaxis](https://diataxis.fr/): tutorials teach, how-to guides reach a
goal, reference states facts, explanation gives the reasons. Every page opens with a TL;DR.

## Where it stands

Built: `qmstrace status`. The other commands — following one requirement to its tests, checking
a repo, reading test results, guarding baselines, setting a repo up — arrive one at a time, and
this manual grows with them.
