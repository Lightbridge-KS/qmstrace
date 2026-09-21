# Configuration

!!! abstract "TL;DR"

    Two files decide everything qmstrace enforces: the project's **trace schema**
    (`qmstrace.schema.toml`, in the ledger repo) and each product repo's **trace configuration**
    (`qmstrace.toml`, at the repo's root). No rule hides in the tool, and an unknown key anywhere
    is an error — a mistyped key would be a rule nobody can see.

## Three levels, three owners

| Level | File | Owner | Says |
|---|---|---|---|
| profile | not a file yet | the standard | the work products and their states — ISO/IEC 29110 first |
| trace schema | `qmstrace.schema.toml` | the project, in its ledger repo | item types and their required fields, link types, coverage rules, where the agreement and the change requests are, which tags are baselines, the project's product repos |
| trace configuration | `qmstrace.toml` | one product repo | where the schema is, the repo's subjects, which item types it declares, their ID patterns and the files to read |

A product repo holds the project's trace schema in one of three forms:

- **by path** — `[schema] path = "…"`, when the ledger repo sits beside it;
- **a verified copy** — the schema's content under `[schema]`, with a digest that is checked, so
  a copy edited by hand is refused;
- **its own** — the schema's content with no digest, for a repo with no ledger.

The files below are the annotated examples qmstrace's own tests read; each says, in its
comments, what belongs in it and what does not.

## A product repo's trace configuration

``` toml
--8<-- "fixtures/mini/service/qmstrace.toml"
```

## The project's trace schema

``` toml
--8<-- "fixtures/mini/ledger/qmstrace.schema.toml"
```

## A repo on its own

``` toml
--8<-- "fixtures/mini/solo/qmstrace.toml"
```

!!! note "Not built yet"

    The comments point at `qmstrace rules`, which will print the rules in force and say which
    part is the project's and which the repo's. It is not built yet.
