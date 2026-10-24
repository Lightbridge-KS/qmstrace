# qmstrace paths

!!! abstract "TL;DR"

    Show the current trace root, selected map or tracked defaults, ledger role and effective
    repo locations. This is a configuration-only diagnosis, available from a product or
    ledger root. It scans no items and judges no trace evidence.

For machine consumption, add `--json` before the command or after its arguments.
See [CLI output modes](../output.md) and [the JSON contract](../cli-json.md).

## Invocation

``` text
--8<-- "cli/golden/help-paths.txt"
```

Run from a traced directory, a nested directory or a ledger root; `-C` selects the effective
invocation directory. `--workspace FILE` is accepted before the command or after `paths`,
once only. See [workspace maps](../workspace-maps.md) for selection order and path bases.

## With a workspace map

The `SPLIT` fixture project's locations and selection provenance. These generated examples
are separate from the generic `MINI` map input in the
[workspace-map reference](../workspace-maps.md#format):

``` text
--8<-- "cli/golden/paths-map.txt"
```

Mapped checkout locations are logical labels such as `service:.`; provenance names the source
kind and map filename. A missing member is labelled unavailable, never filled from the
tracked default location.

## With tracked defaults

For v1 input without a matching map, existing tracked locations are used and labelled:

``` text
--8<-- "cli/golden/paths-default.txt"
```

## Version 2 without a profile file

A missing implicit named profile permits a local-only view. `paths` shows the required
profile stem, known local identity and unavailable members. A malformed or explicitly missing
profile is an error. See [names-only configuration](../names-only-configuration.md).

## Scope and exits

The command reads configuration, resolves the selected layout and checks filesystem
locations. It performs no marker extraction, graph or baseline assessment, report reading,
Git/network operation or write. An available directory does not prove its trace content
can be judged, its schema is current or its evidence is verified.

Exit `0` means the layout was diagnosed; siblings may still be unavailable. Exit `2` means
configuration or map selection failed, including ambiguous v1 matches or a wrongly bound
v2 profile. Exit `3` means an internal fault. Use [`check`](check.md) or
[`ledger check`](ledger.md#qmstrace-ledger-check) for trace judgment.
