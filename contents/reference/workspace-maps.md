# Workspace maps

!!! abstract "TL;DR"

    A local workspace map locates current checkouts without changing project rules.
    Select one with `--workspace FILE`, `QMSTRACE_WORKSPACE`, ancestor discovery or a unique
    user-level match. Maps never merge. `qmstrace paths` shows the selected locations;
    omitted members stay unavailable.

## Format

For a map at `.qmstrace/workspace.toml` in a folder containing `ledger`, `service` and
`client` checkouts, the hand-authored `MINI` input is below. Generated output on this page
and the [paths reference](commands/paths.md) uses the separate `SPLIT` fixture project.

``` toml
version = 1
project = 'MINI'
ledger_repo = 'ledger'

[repos]
ledger = '../ledger'
service = '../service'
client = '../client'
```

| Field | Meaning |
|---|---|
| `version` | Integer `1` |
| `project` | The project's name, matching the trace schema |
| `ledger_repo` | A key in this map's `[repos]` identifying the ledger trace root |
| `[repos]` | Stable repo names mapped to native absolute or relative checkout paths; relative paths start at the map's directory |

The ledger role is required even when the ledger does not declare traced items. The current
trace root must be one of the mapped canonical locations. Unknown fields, invalid types,
empty names/paths, unknown members other than the ledger role, and two names for the same
canonical checkout are refused with exit `2`. Symlinks are compared canonically. A trace
root is the directory holding `qmstrace.toml`, or the ledger's `qmstrace.schema.toml`; it may
be inside a larger Git repository.

Relative entries start at the selected map's **canonical containing directory**. Selecting
a symlink uses the target file's directory, rather than the symlink's directory. TOML path
values are literal: environment variables and `~` are not expanded inside them.

A ledger self-member declared in the schema keeps its identity and trace-root binding.
A reachable mapped ledger without `qmstrace.schema.toml`, or belonging to another project,
is refused with guidance to select the ledger trace root rather than its containing Git root.

## Selection order

| Order | Source | Rule |
|---|---|---|
| 1 | `--workspace FILE` | Before the command or on a leaf command; any duplicate is exit `2`, including twice at root, twice at leaf, or across positions |
| 2 | `QMSTRACE_WORKSPACE` | Used only without a CLI selector |
| 3 | Nearest ancestor `.qmstrace/workspace.toml` | Search starts at the discovered trace root, upward; a nested invocation does not change it |
| 4 | `~/.qmstrace/workspaces/*.toml` | Unique match on project **and** a mapped canonical location equal to the current trace root |
| 5 | Tracked defaults | Repo-relative local `ledger` pointer and ledger-relative schema `[repos]`, when no map matches |

A relative CLI/environment selector path starts at the effective invocation directory after
`-C`. Entries within the selected map start at that file's directory. The first selected
map ends discovery; lower stages are not inspected. An empty `QMSTRACE_WORKSPACE` value
counts as unset. Help and version requests do not read maps.

An explicit or environment file that is absent, unreadable, malformed or inapplicable
causes exit `2` without fallback. An unusable or inapplicable nearest ancestor file also
causes exit `2`; only the absence of that candidate reaches the user stage. During that stage,
every candidate is validated: a malformed or unreadable file causes exit `2`, even when
another file matches. Unrelated valid maps are ignored; several matches are ambiguous and
cause exit `2`. Another checkout of the same project does not match the current root.

## Effective locations

A selected map replaces the whole current layout. An omitted member or a missing/unreadable
mapped checkout stays unavailable, even when a usable checkout exists at its tracked default.
Local commands retain *not verified here* notices; ledger commands refuse a project with
unread members. In the `SPLIT` fixture, map provenance and evidence limits survive quiet
output:

``` text
--8<-- "cli/golden/workspace-check-quiet.txt"
```

Current sibling reads, agreement and change-request reads, ledger assessment and
`ledger copy-schema` destinations share these locations. Agreement/request source paths
still start at the ledger root. Schema copy retains all-or-nothing writes. A map changes
neither membership nor qualified IDs and cannot make differing schema copies acceptable.

Ledger commands still run in the ledger trace root; use `-C` to select that directory.
Selecting a map in a product repo does not switch command scope.

## Boundaries

- Existing schema `[repos]` paths stay ledger-relative defaults. Relative map paths start
  at the map file; printed checkout locations are relative to the active trace root.
  Provenance names the selection source kind and map filename.
  The trace configuration's tracked `ledger` pointer remains relative to that repo's trace root.
  Cross-drive layouts that cannot be expressed relatively are refused with exit `2`.
- `[schema] path` keeps its existing base at the repo's trace root. A map cannot repair an
  unavailable schema file or supply today's rules to a tagged read.
- Schema digests, generated schema copies, item text and historical configuration are
  unchanged. No map is copied into the trace schema or written into a repo's configuration.
- Report and output arguments keep their existing invocation-directory rules.
- The ledger's emitted tables retain the `qmstrace.table/1` JSON format.

Use [qmstrace paths](commands/paths.md) for a configuration-only diagnosis, or follow
[use a workspace map](../how-to/use-a-workspace-map.md) to configure a layout.
