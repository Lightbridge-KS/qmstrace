# qmstrace ledger

!!! abstract "TL;DR"

    The project side's verbs, run in the ledger repo — where `qmstrace.schema.toml` is. Today
    there is one: `copy-schema` writes the project's trace schema into each product repo as a
    generated, verified copy, so that a product repo can be judged on its own — in its
    pipeline, or at a baseline tag. All repos or none; a second run changes nothing.

## The group

``` text
--8<-- "cli/golden/help-ledger.txt"
```

The ledger's verbs are kept apart from the product-repo loop: an agent reading the help in a
product repo does not see verbs it must not use. Run one in a product repo and it names the
ledger; run a product verb in the ledger and it names the product repos.

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
