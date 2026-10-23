# qmstrace check

!!! abstract "TL;DR"

    `qmstrace check` lists every violation and every gap in the repo, one line each, with what to
    do next, followed by every suspect requiring review. Violations always fail it.
    Gaps — the work not done yet — fail only under
    `--strict`, the gate a pull request passes. Run it after every change.

## Synopsis

``` text
--8<-- "cli/golden/help-check.txt"
```

## Output

A repo with nothing wrong and nothing left to do:

``` text
--8<-- "cli/golden/check-clean.txt"
```

The same kind of repo under the gate, with one rule not met yet:

``` text
--8<-- "cli/golden/check-strict.txt"
```

A repo with scanning violations, and the gaps they leave behind:

``` text
--8<-- "cli/golden/check-every-finding.txt"
```

`--quiet`, in a pipeline where the ledger and the sibling repo are not checked out — what could
not be verified still shows, above the findings and again in the result line:

``` text
--8<-- "cli/golden/check-quiet-in-a-pipeline.txt"
```

## Reading it

| Part | What it says |
|---|---|
| `read:` | how many items of each type were read, so an empty result never looks like a clean one |
| the notices | what this run could not verify or judge — an external source, a sibling, baselines. They show in every form, `--quiet` too |
| a finding | code · file:line · what is wrong · `Fix:` — the next move, and where a wrong move is tempting, which one not to make |
| the result line | the counts, the exit code, the mode, and what was not verified. It names the gate, so a reader of the last line alone knows the command a pipeline should run |

`S01` findings carry a `Review:` next move and never fail, even under `--strict`.
All suspects appear under `--quiet` too. See [Downstream suspects](../suspects.md) for
complete tested output and historical/current graph evidence.

Violations come first: a gap often exists only because a violation refused the link it needs,
and its `Fix:` then says to fix that violation first — never to add a second line. The codes:
[Findings](../findings.md). The rules behind the gaps: [`qmstrace rules`](rules.md). Why gaps do
not fail while you work: [Kinds of finding](../../explanation/kinds-of-finding.md).

## Exit code

The [baseline guard](../baselines.md) adds V10–V13 for unauthorized changes and removals.
V17 reports a baseline-covered document ID with no unique subject before a tag is cut.
It can also prevent judgment with exit `2`, including ambiguous baseline ancestry or a
historical schema outside the tagged tree, or an unowned ID under a relevant baseline.
See [Change a frozen
item](../../how-to/change-a-frozen-item.md) for tested output.

| Mode | `0` | `1` |
|---|---|---|
| `qmstrace check` | no violations — gaps may be listed | a violation |
| `qmstrace check --strict` | no violations and no gaps | a violation or a gap |

`2` when it cannot judge at all. See [Exit codes](../exit-codes.md).
