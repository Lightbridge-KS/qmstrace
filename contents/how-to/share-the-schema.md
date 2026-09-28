# Share the project's schema with its repos

!!! abstract "TL;DR"

    In the ledger repo, run `qmstrace ledger copy-schema`; then commit the updated
    `qmstrace.toml` in each product repo. Run it again whenever the project's rules change.
    Do it before a product repo cuts its first baseline tag.

## Steps

1. **List the product repos** under `[repos]` in the ledger's `qmstrace.schema.toml`, each as a
   name and a path from the ledger — `service = "../service"`.

2. **Point each product repo at the schema.** A repo joining the project starts with
   `[schema] path = "../ledger/qmstrace.schema.toml"` in its `qmstrace.toml` — the first form
   in [configuration](../reference/configuration.md). A repo holding a schema of its own is
   refused until its `[schema]` is replaced this way: its own rules are never overwritten.

3. **Copy the schema, in the ledger.**

    ``` sh
    qmstrace ledger copy-schema
    ```

    ``` text
    --8<-- "cli/golden/ledger-copy-schema-first.txt"
    ```

    Name repos to copy into only those. Nothing is written unless every repo can take the copy.

4. **Commit `qmstrace.toml` in each updated repo**, through its own pull request: the diff is
   the schema the repo will be judged by. The repo is now judged on its own — in its pipeline,
   with no ledger beside it, the agreement and change requests are reported as *not verified*.

5. **When the project's rules change**, edit the schema in the ledger and copy again:

    ``` text
    --8<-- "cli/golden/ledger-copy-schema-refresh.txt"
    ```

    A repo that has not taken the new copy keeps being judged by the rules it carries.

## Before the first baseline

At a baseline tag qmstrace reads the configuration from the tagged tree, where a path to the
ledger leads nowhere. A repo that tags a baseline while it reads its schema by path can never
be judged at that tag — copy first, commit, then tag. See [baselines](../reference/baselines.md).

The command's refusals and report lines are in the [ledger reference](../reference/commands/ledger.md).
