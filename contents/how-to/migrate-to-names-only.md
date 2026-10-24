# Migrate to names-only configuration

!!! abstract "TL;DR"

    Upgrade the tool, prepare v2 identity headers and one local map, then let
    `ledger copy-schema` replace the generated blocks transactionally. Review the migration
    on coordinated branches. Existing baseline tags retain their original configurations.

## Convert the project

1. Install a qmstrace build supporting v2. Record each checkout's commit and current local
   and project checks. Use separate migration branches and keep source documents, code and
   tests unchanged while checking configuration parity.
2. Replace the ledger schema's path-valued `[repos]` with `ledger_repo` and `members`, and
   set its version to `2`. Keep existing member names: they qualify path-derived IDs.
   Include the ledger when it holds traced documents. See the
   [v2 reference](../reference/names-only-configuration.md).
3. Give the ledger a v2 `qmstrace.toml` with its `repo`, required `workspace_profile` and
   `[schema] path = "qmstrace.schema.toml"`. Preserve its local subjects and extraction settings.
4. Give each product a v2 identity/profile header and remove its old `ledger` pointer.
   Preserve its local declarations. Keep an existing verified block until the copy replaces
   it, or use an empty `[schema]` as a bootstrap placeholder. This intermediate file is input
   to copy planning; ordinary assessment refuses a mixed-version or incomplete schema.
5. Create the named user map on each developer machine, or select a repo-local/CI map
   explicitly. Bind each member name to its trace root, including a nested ledger solution
   directory. Exclude local maps from Git. No additional workspace repository is required.
6. From the ledger, generate the copies:

    ```sh
    qmstrace ledger copy-schema
    qmstrace ledger check --strict --json
    ```

    Copying validates all selected headers and completed candidates before any write. A bad
    destination stops the whole write. It replaces generated schema blocks and preserves
    everything outside them. A second run is a no-op.
7. In each product, run `paths`, `rules`, `status`, targeted `thread`/`impact`, and its tests
   with reports. Compare logical findings, counts, IDs, verdicts and historical comparisons
   with the recorded v1 results. Check the whole project from the ledger. Keep source notices.
8. Refresh managed guidance using `init`. If the installed skill differs, preserve local
   additions, remove only `.agents/skills/qmstrace/SKILL.md`, and rerun `init`. Preserve
   `.qmstrace/` maps and local edits. Review every diff before merging coordinated changes.

No baseline tag is rewritten and no request acceptance is inferred by migration. Controlled
source changes still follow the project's existing process. Product-only checks can run from
a verified copy without a profile file; that does not establish project-wide coverage.

## Developer layouts and CI

Use the same logical profile stem with different addresses on each machine. To override it:

```sh
qmstrace --workspace /work/local-map.toml paths --json
qmstrace -C /work/records/solution ledger check --strict --workspace /work/local-map.toml --json
```

A relative selector starts at the effective invocation directory after `-C`; relative entries
start at the map file. CI can generate a temporary version-1 map from its checkout locations
and pass `--workspace FILE` or `QMSTRACE_WORKSPACE`. Keep those addresses out of tracked schema
files and shared evidence. See [use a workspace map](use-a-workspace-map.md) for map creation.

## Update output consumers

Check `format` before parsing. Version 0.3.0 emits CLI `/2` and table `/2` even when reading
v1 inputs or reporting a parser error before discovery. Replace location-string assumptions
with `repo`/`path`/`line` records. Table columns and test-verdict semantics remain the same;
its `read[].location` becomes a logical record, and its `where` text uses repo-qualified labels.
There is no legacy output selector. Consumers requiring `/1` remain pinned to 0.2.0.
