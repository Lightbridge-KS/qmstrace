---
summary: ADR-0010 — select one local workspace map for current checkout locations while preserving trace-schema defaults, digests, historical reads and ledger command scope.
read_when:
  - implementing or reviewing workspace-map parsing, discovery or current location resolution
  - changing how sibling, ledger or schema-copy destinations are located
  - documenting qmstrace paths or distinguishing local locations from project rules
---

# ADR-0010 — Local workspace maps

- **Status:** accepted, 2026-10-24
- **Amends:** [data architecture](../design/data-architecture.md) D9's current location
  resolution, [surface architecture](../design/surface-architecture.md#workspace-map-selection-and-paths)
  selection and diagnostics, and [architecture ownership](../structure/codebase-blueprint.md#workspace-map-ownership--adr-0010)
- **Decided by:** the developer, for the workspace-map slice

## Context

The `MINI` project's schema can name `service = "../service"`, while another developer or
pipeline keeps that checkout elsewhere. Editing schema paths to suit each machine changes
the shared schema digest and requires new copies even though no project rule changed.
The local `ledger` pointer alone cannot express an alternative layout for every member.

The existing schema has already shipped. Its ledger-relative paths, generated copies and
tagged configuration remain valid; this slice adds current location resolution alongside
them. A later schema migration is a separate decision.

## Decision

A workspace map is a local TOML file with exactly this shape:

```toml
version = 1
project = 'MINI'
ledger_repo = 'ledger'

[repos]
ledger = '../ledger'
service = '../service'
client = '../client'
```

Paths resolve from the map's canonical directory, including when selected through a symlink;
TOML path values do not interpolate environment variables. `ledger_repo` names its ledger entry. Stable repo
names keep the schema's membership and qualified-ID meaning. The ledger role can exist
without being a traced schema member in the older layout. A selected map must identify the
current canonical trace root and ledger role. Unknown keys/versions, invalid types, unknown
member names other than that role, or aliases for one canonical checkout are refused.

An existing schema ledger self-member keeps its role and trace-root binding. A reachable
mapped ledger without `qmstrace.schema.toml`, or belonging to another project, is refused
with guidance to select the correct ledger trace root, which may be nested inside a Git repo.

Select one whole source: root/leaf `--workspace FILE`, then `QMSTRACE_WORKSPACE`, then the
nearest ancestor `.qmstrace/workspace.toml` from the discovered trace root, then a unique
match in `~/.qmstrace/workspaces/*.toml`. Relative CLI/environment selector paths use the
effective invocation directory after `-C`. Any duplicate selector causes exit 2, including
two at root, two at leaf, or one at each, even when the files are identical.
Explicit, environment and nearest-ancestor files must be usable and applicable or cause
exit 2, without fallback. User-level maps match the project and canonical current root;
unrelated valid maps are ignored. At that stage, every candidate is validated: a malformed or
unreadable candidate causes exit 2, and multiple matching maps cause exit 2. Earlier
selection does not inspect later stages. With no matching map, use existing tracked defaults.

Never merge entries or fall back per member. A missing map entry or unreadable mapped
directory stays unavailable. Local commands preserve source notices; whole-project commands
refuse unread members, and schema copy retains transactional all-or-nothing behavior.
Current external/request reads, sibling reads, project membership locations and copy
destinations share the selected resolution. Ledger commands still require invocation in the
ledger trace root; the map does not turn a product command into a project-wide one.

`qmstrace paths` diagnoses configuration and location selection from either root. It shows
source provenance, current root, ledger role and effective member locations/availability;
it scans no items, assesses no baselines, reads no reports, invokes no Git/network operation
and writes nothing. Missing siblings can be diagnosed with exit 0; unusable selection or
configuration is exit 2. Availability is not evidence verification.

Diagnostic checkout locations are relative to the active trace root; selection provenance
names the source kind and map filename.
Cross-drive layouts that cannot be represented relatively cause exit 2. The tracked
`ledger` pointer stays repo-relative; schema repo defaults stay ledger-relative, and
`[schema] path` keeps its trace-root-relative meaning. Maps
never replace historical configuration or schema, change digests or item text, rewrite
tracked configuration, or relocate report/output arguments. Mapped command provenance and
existing evidence limits survive quiet output; commands without a map retain their output.
The emitted table's JSON contract remains `qmstrace.table/1`.

## Consequences

- Developers and pipelines can choose different checkout layouts without copying a new schema.
- Workspace maps are local operational input; no consumer configuration is migrated or
  rolled out by this change.
- A partial map visibly loses access to omitted members; it cannot borrow a default checkout
  and accidentally mix evidence from two layouts.
- Strict user-candidate validation makes a broken file visible before an unrelated map can
  be used. The error identifies the candidate with a relative location and a next move.
- The pure parser, filesystem discovery and diagnostic rendering have separate
  [source owners](../structure/codebase-blueprint.md#workspace-map-ownership--adr-0010);
  existing workspace owners coordinate their use.
- The [scenario catalogue](../tests/scenario-catalogue.md#workspace-maps--adr-0010) defines
  verification obligations. This ADR records the accepted decision, not a test result.

## Rejected alternatives

- **Edit schema paths per machine.** Changes shared digests and copied rules for a local fact.
- **Remove schema locations immediately.** Requires a versioned migration and changes the
  meaning of existing copies and historical reads.
- **Merge maps or fill omitted entries from defaults.** Can silently combine different layouts.
- **Select the first user match.** Directory iteration would decide which checkout is read.
- **Ignore malformed user candidates.** Hides configuration failures and can select the wrong
  layout when a broken candidate was intended to match.
- **Apply current maps inside historical configuration loading.** Substitutes today's location
  knowledge for evidence that must come from the tagged tree.
- **Follow the map into the ledger for a ledger command.** Changes command scope according to
  local configuration; explicit ledger invocation remains the boundary.
- **Print absolute locations when relative output is impossible.** Leaks machine-specific
  paths and changes the relative-location contract; cross-drive layouts are refused instead.
