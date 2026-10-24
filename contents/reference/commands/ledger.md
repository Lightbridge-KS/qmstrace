# qmstrace ledger

!!! abstract "TL;DR"

    The project side's verbs, run in the ledger repo — where `qmstrace.schema.toml` is.
    `check` judges every repo of the project together — coverage met across repos, each repo's
    own violations, suspects across repos — from their working trees; `--strict` is the
    ledger's gate. `thread` and `impact` walk across every repo. `table` emits the traceability
    matrix, the requirements register or the coverage summary as JSON. `copy-schema` writes the
    project's trace schema into each product repo as a generated, verified copy.

`check`, `thread` and `impact` accept `--json` at the root or leaf, with project scope.
`table` retains its existing table JSON; `copy-schema` rejects the flag before writes.
See [CLI output](../output.md) and [the JSON contract](../cli-json.md).

## The group

``` text
--8<-- "cli/golden/help-ledger.txt"
```

The ledger's verbs are kept apart from the product-repo loop: an agent reading the help in a
product repo does not see verbs it must not use. Run one in a product repo and it names the
ledger; run a product verb in the ledger and it names the product repos.

A [workspace map](../workspace-maps.md) may select the current member locations used by
these commands, including schema-copy destinations. Pass `--workspace FILE` before the
command or at a leaf, for example `qmstrace ledger check --workspace FILE`. A map does not
change the invocation root: ledger verbs still run in the ledger trace root, selected with
`-C` when needed. `qmstrace paths` inspects resolution from either kind of root.

## qmstrace ledger check

``` text
--8<-- "cli/golden/help-ledger-check.txt"
```

Every repo the schema lists under `[repos]` is read from its working tree, with its own
`qmstrace.toml`, and the ledger too when it lists itself as `"."` — the layout where the
ledger holds the requirements and the design ([Around the repo](../../explanation/around-the-repo.md)).
Then they are judged as one project:

``` text
--8<-- "cli/golden/ledger-check-split.txt"
```

The header lists each repo read, where it is from the ledger and what it holds. Locations are
written from the ledger (`../client/…`), and a module's or a test's ID carries its repo —
`client:tests/unit/test_api.py::…` — because two repos can hold the same path. Every other
ID is written as it was authored.

Under the gate, with one test in the client losing its marker — the gaps name the repos where
the link can be written:

``` text
--8<-- "cli/golden/ledger-check-strict.txt"
```

After a change to a frozen requirement in the ledger, cited to an accepted change request:
what hangs off it is suspect in every repo. A dependant in another repo than the changed item
is reached by today's links only — the ledger's baseline holds no version of that repo — so its
reason says *current reach only … not pinned; unknown whether edited*:

``` text
--8<-- "cli/golden/ledger-check-suspects.txt"
```

**Refused, exit `2`, every problem named at once** — a clean result with a repo left unread
would be a false one: a listed repo that is missing, has no `qmstrace.toml` or cannot be read;
one holding rules other than the ledger's schema; two names for one folder; a ledger holding a
`qmstrace.toml` that `[repos]` does not list; an empty `[repos]`.

``` text
--8<-- "cli/golden/ledger-check-refused.txt"
```

The older layout — documents in the product repos, the ledger holding only the agreement and
the schema — is judged the same way:

``` text
--8<-- "cli/golden/ledger-check-mini.txt"
```

Exit `0` means no violation — and, under `--strict`, no gap; `1` means one remains; `2` means
the project could not be judged; `3` an internal fault. Suspects never fail. Each repo's own
`qmstrace check` is unchanged: in the ledger, it still fails on gaps only another repo can
meet, and its next move points here.

## qmstrace ledger thread

``` text
--8<-- "cli/golden/help-ledger-thread.txt"
```

The same walk as [`thread`](thread.md) in one repo, over the whole project: forward from a
requirement to the design, the code and the tests of every repo; backward to its origin.
Each judged item says which repo it is in:

``` text
--8<-- "cli/golden/ledger-thread-requirement.txt"
```

A module's or a test's ID carries its repo, and backward from one reaches its origin across
the repo edge:

``` text
--8<-- "cli/golden/ledger-thread-module.txt"
```

A start that no repo declares or cites exits `2`. A module's or a test's ID written without its
repo — `tests/unit/test_api.py::…` — is answered with the qualified IDs it may mean.

## qmstrace ledger impact

``` text
--8<-- "cli/golden/help-ledger-impact.txt"
```

The same as [`impact`](impact.md) in one repo, over the whole project — the downstream items
of several starts, grouped by type, their origins, and a candidate `Impacts:` line limited to
the item types a baseline covers:

``` text
--8<-- "cli/golden/ledger-impact-multiple.txt"
```

The order of the starts, and a start given twice, do not change the output. One unseen start
refuses the whole request, exit `2`.

## qmstrace ledger table

``` text
--8<-- "cli/golden/help-ledger-table.txt"
```

Every repo is read as `ledger check` reads it, and one table is emitted as a JSON document a
render layer turns into a formal document — a traceability record, a requirements
specification's register. Its shape, `qmstrace.table/2`, is in [the table
format](../table-format.md):

- **`matrix`** — one row per requirement, design element and test case, with the origins,
  components and automated tests that hang off them;
- **`requirements`** — one row per requirement: its origins, its fields, its change and its
  status;
- **`coverage`** — requirements covered and not, tier by tier, against the rules that ask
  for each.

The `cases` fixture project's coverage summary — a ledger holding the documents and a Test
Specification, a Python service and a C# agent:

``` json
--8<-- "cli/golden/ledger-table-coverage-cases.json"
```

Every repo's commit, and whether its working tree was clean, are in the document; a repo with
uncommitted work is read as it is and marked `"clean": false`. The tables count links, not
passing tests. A project with violations is still tabled, exit `0`: the violation count and a
notice say the links they refuse are not in it, and `ledger check` lists them.

With `--report REPO=FILE`, repeatable, the matrix also carries verdicts — one column per level
and an overall one, each naming the reports it came from. Name the repo whose tests each report
ran, as `[repos]` names it:

``` sh
qmstrace ledger table matrix --report agent=../agent/TestResults/unit.trx \
  --report service=../service/report.xml
```

The reports are read as one, whatever their order; [the table format](../table-format.md#verdicts)
says how a verdict cell reads.

With `--out`, the document is written to a new file — never over an existing one, exit `2`:

``` text
--8<-- "cli/golden/ledger-table-out.txt"
```

## qmstrace ledger copy-schema

``` text
--8<-- "cli/golden/help-ledger-copy-schema.txt"
```

With no names, every repo the schema lists under `[repos]`, resolved from the ledger. A name
the schema does not list is refused: a repo the project does not know cannot carry its rules.

The first copy into a repo reading the schema by path:

``` text
--8<-- "cli/golden/ledger-copy-schema-first.txt"
```

The repo's `[schema]` becomes the copy, between two comment lines, and every other byte of its
`qmstrace.toml` is kept. Inside, `[schema]` carries the digest, then the ledger file's own
lines — comments too — with each table moved under `schema`. Every run checks the digest
against the content: an edit by hand is caught, and so is a deleted digest line while the
markers stand.

A second run:

``` text
--8<-- "cli/golden/ledger-copy-schema-again.txt"
```

After the project's rules changed, for one repo:

``` text
--8<-- "cli/golden/ledger-copy-schema-refresh.txt"
```

A repo's line says what it held before: *was by path*, *rules changed* with the old digest,
*layout only — rules unchanged*, *replaced a copy edited by hand*, *was an empty [schema]*.

**A ledger that holds the project's documents lists itself** under `[repos]` as `"."`: it is
traced like its product repos, and reads the schema it holds by path. The copy skips it:

``` text
--8<-- "cli/golden/ledger-copy-schema-split.txt"
```

A ledger whose `qmstrace.toml` already holds a copy of its own schema is skipped too, and its
line says to replace that `[schema]` with `path = "qmstrace.schema.toml"`.

**Refused, and nothing written in any repo:** a repo that is missing or has no `qmstrace.toml`;
one holding a schema of its own — replace its `[schema]` with a `path` to the ledger first; one
reading another schema; one carrying another project's copy; conflicting markers, or schema
tables split around other tables. The message names every problem at once.

The copy is written, never committed: commit `qmstrace.toml` in each updated repo, where its
pull request shows the diff. Copy **before the first baseline**: at a baseline tag qmstrace
reads the configuration from the tagged tree, where a path to the ledger leads nowhere.

Exit `0` means every named repo carries this schema; exit `2` means nothing was written, and
why; exit `3` means an internal fault. See [configuration](../configuration.md).
