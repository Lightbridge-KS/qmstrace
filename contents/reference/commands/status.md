# qmstrace status

!!! abstract "TL;DR"

    `qmstrace status` answers *where am I*: what was read, what lies around the repo and whether
    it could be verified, then one line per requirement. Run it first in any traced repo. It is
    not a check — it exits `0` whatever it counts.

## Synopsis

``` text
--8<-- "cli/golden/help-status.txt"
```

Run it anywhere inside a product repo: qmstrace walks up to the nearest `qmstrace.toml`. To run
it on another repo, give `-C` — before the command, as with `git -C`, or after it:

``` sh
qmstrace -C ../client status
qmstrace status -C ../client
```

## Output

With the ledger and the project's other repos checked out beside this one:

``` text
--8<-- "cli/golden/status-service.txt"
```

In a pipeline, where only this repo is checked out:

``` text
--8<-- "cli/golden/status-client-in-a-pipeline.txt"
```

| Block | What it says |
|---|---|
| `schema:` | where the rules in force come from — the project's trace schema by path, a verified copy of it, or the repo's own |
| `scanned (…)` | per item type: items and files read, the file patterns, and files ignored; a type the project knows and this repo does not scan says so. The parenthesis says what was read — the working tree, never a pinned commit |
| `links:` | links that entered the graph — every one allowed by the trace schema |
| `external …` | whether IDs cited from outside any product repo, such as agreement clauses, were checked, and against which file |
| `sibling …` | each of the project's other repos: read from its working tree (*not pinned*), or not reachable |
| `not verified here:` | citations of another repo's items that this run could not check; they are judged when the ledger imports the project |
| `baseline …` / `baselines:` | governing local tags, annotation evidence and limits; see [Baselines](../baselines.md) |
| `controlled document items:` | frozen, changed, new, removed and withdrawn counts; changed/removed are subsets of frozen |
| `change requests:` | the register's availability, readable requests and malformed files |
| `suspects:` | unique local items needing review; distance-one items listed, farther items counted by distance; [check](check.md) lists all reasons |
| one line per requirement | its category, what it points back at, what hangs off it — design elements, the test cases of a Test Specification, automated tests by level — and its title |
| `verified by …` | requirements verified by inspection or analysis, listed apart: nothing records their basis yet |
| last line | violations and gaps, each counted by code — see [Findings](../findings.md). [`qmstrace check`](check.md) lists every one, with its next move |

## Exit code

Frozen requirements carry their governing tag and comparison state; withdrawn requirements
are labelled explicitly. [Change a frozen item](../../how-to/change-a-frozen-item.md) describes
the authoring workflow.

`0`, whatever it counts — or `2` when it cannot judge at all, such as in a folder with no
`qmstrace.toml` above it. V17, a controlled document ID with no unique subject key, is
counted before a tag; it does not change this informational exit code. See
[Exit codes](../exit-codes.md).
