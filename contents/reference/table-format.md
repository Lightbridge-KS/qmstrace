# The table format

!!! abstract "TL;DR"

    `qmstrace ledger table` writes one JSON document per table, format `qmstrace.table/1`:
    what was read, then the columns, then the rows. Columns are named after the project's own
    item types and found by name; a new key or column keeps `/1`, so a reader ignores what it
    does not know. Identical inputs give identical bytes.

## The document

| Key | Holds |
|---|---|
| `format` | `qmstrace.table/1` |
| `table` | `matrix`, `requirements` or `coverage` |
| `project` | the project's name, from its trace schema |
| `draft` | a reminder that the table is generated, never an issued revision |
| `schema` | the trace schema's digest — the rules the table was read under |
| `ledger` | the ledger's `commit` and whether its working tree was `clean`; `null` outside Git |
| `read` | each repo read: its name, its `location` from the ledger, its `commit` and `clean` |
| `pinned` | `false`: every repo was read from its working tree, not at a pin |
| `violations`, `gaps` | the counts `ledger check` would report |
| `notices` | everything that could not be verified or was not pinned, and what the table leaves out |
| `columns` | the columns, in order |
| `rows` | one object per row, keyed by column name |

There is no timestamp and no path of the machine: the commits say what was read. A repo with
uncommitted work is marked `"clean": false` — the table shows its working tree, which no
commit holds.

## Columns

Each column names itself, the kind of value its cells hold — `id`, `ids` (a list, sorted with
numbers read as numbers), `text` or `count` — the item `type` those values are, and the link
`via` which they hang off the row.

Columns follow the project's [trace schema](configuration.md). Two names are fixed: the
`requirement` type every table starts from, and the `verifies` link. An item type that is both a
source and a target of `verifies` is a test case; one that is only a source, an automated test.
The other links that count toward coverage, walked from the requirement, give the rest:

- what the requirement points at — its origin clauses;
- what points at the requirement — its design elements, the first level of the matrix's rows;
- what points at those — the components that implement a design element;
- the requirement fields the schema names under `[tables.matrix] fields`.

A link that counts toward no coverage — `Assumes` — is in no table.

## The matrix

One row per requirement, design element and test case, requirement-major:

- a test case's row lists the automated tests that run it, through another test case too;
- an automated test that verifies directly, with no test case between, has a row of its own;
- a test case nothing runs still has its row, with no automated test;
- a test case that verifies the requirement itself repeats on each of its design rows;
- a requirement with nothing below it still has one row;
- withdrawn items are in no row, and a notice counts them, as it counts items that reach no
  requirement.

The `cases` fixture project's matrix:

``` json
--8<-- "cli/golden/ledger-table-matrix-cases.json"
```

## The requirements register and the coverage summary

The register has one row per requirement, withdrawn ones included: its title, its origins, the
fields its type declares, its `Change` and `Status`, its repo, and where it is declared.

The coverage summary has one row per tier that reaches a requirement — its design, its test
cases, its automated tests. Each row names the rules that ask for the tier, how many
requirements those rules select (`of` — a rule's `where` narrows it), how many are covered,
and which are not. An automated test reaches a requirement directly or through test cases,
never through a design element. Coverage counts links, not passing tests.

## Versioning

A new key, column, table or notice keeps `qmstrace.table/1`: find columns by name, and ignore
what you do not know. Removing or renaming anything, changing a cell's JSON type, the row grain
or the order, or what `clean`, `pinned` or `draft` mean, makes `qmstrace.table/2`.

The document is UTF-8. On a console that cannot print UTF-8, write it with `--out` instead.
