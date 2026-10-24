---
summary: ADR-0012 — names-only v2 membership, explicit repo identity and required workspace_profile, native cross-drive locations and versioned 0.3.0 output; v1 historical evidence remains readable.
read_when:
  - reviewing the 0.3.0 names-only configuration implementation plan
  - deciding v2 compatibility, profile discovery or cross-drive evidence representation
---

# ADR-0012 — Names-only configuration and local workspace profiles

- **Status:** accepted, 2026-10-24; implementation and native Windows N12 verified; PR #74 merged at `79841ec`; shipped in v0.3.0 at `a276e6e`
- **Accepted direction:** required `workspace_profile` in v2, cross-drive Windows support
  and uniform `qmstrace.cli/2`, chosen by the developer in the design form
- **Amends:** ADR-0010's retained path defaults/cross-drive refusal,
  ADR-0011's shipped JSON projection, ADR-0005's table location contract and D9's
  configuration representation. Existing v1 meanings remain valid for legacy input.

## Context

Workspace maps in 0.2.0 override locations but leave cross-repo paths in the committed
schema and its verified copies. A product can omit its optional local ledger pointer,
but this does not remove copied schema paths or introduce a stable local repo identity.
The names-only goal requires a versioned representation rather than path placeholders.

The developer wants arbitrary checkout layouts on each machine, including different
Windows drives. Existing relative filesystem locations cannot represent that evidence
without changing the output contract.

## Decision

The [feature design](../design/names-only-workspaces.md) defines the examples, full
resolution flow, ownership and implementation sequence:

- Shared schema version 2 declares a ledger-role name and a set of member names. Local
  configuration version 2 declares its own repo name and required default profile stem.
- Workspace maps keep format version 1. Explicit CLI, environment and ancestor sources
  override an exact named user-profile lookup. Select one source and validate identity;
  never merge maps, guess sibling locations or borrow tracked defaults for v2.
- An absent implicit profile permits a local view from a valid copied/same-tree schema,
  with evidence notices. Invalid selections are exit 2; project operations require all
  members. Selecting a map never changes command scope or repairs a schema reference.
- V1 readers, digest calculation, tracked fallback and historical same-tree loading remain.
  V2 schema membership is normalized for a new digest and copies are regenerated explicitly.
- Native paths remain operational; portable repo-relative locations identify evidence.
  The 0.3.0 assessment JSON contract is uniformly `qmstrace.cli/2`, including handled errors.
- Table output advances to `qmstrace.table/2` rather than changing `/1` meanings.
  Existing v1 starter generation is preserved; v2 schema-copy/bootstrap and init refresh
  are documented without introducing an automatic migration command.

The developer accepted table `/2` and the v1 starter/v2 bootstrap scope before implementation.
Native Windows proof is recorded in the
[acceptance results](../tests/names-only-workspaces.md#native-windows-acceptance-2026-10-24);
the required CI job remains a release gate. Design acceptance is separate from platform
verification. Consumer migration and release publication
remain separate actions.

## Consequences

- Moving a checkout changes a local profile rather than project rules or schema copies.
- Local identity checks can reject a valid project's checkout bound under the wrong member
  name, which location-only validation cannot establish in 0.2.0.
- V1 configuration readability is retained; consumers of output `/1` still need an explicit
  migration to the new output version or must remain pinned to the old release.
- Cross-drive evidence uses logical locations, not leaked native roots. A native Windows
  acceptance job is necessary before claiming support.
- The first v2 conversion changes the schema digest and needs coordinated copies. A future
  relocation does not. Historical tags and controlled item identities are not rewritten.
- REQ-QMT-17's self-member wording is representation-neutral. Assessment confirmed it is a
  new controlled item covered by existing accepted CR-001; its citation is retained. No
  request acceptance or baseline is manufactured.

## Rejected alternatives

- **Keep machine paths as dummy defaults.** Does not achieve names-only configuration and
  allows a missing map to accidentally select another layout.
- **Change the existing `[repos]` meaning under version 1.** Obscures which interpretation
  applies to tagged evidence and old tools. New fields alone could be additive, but this
  change replaces the membership representation itself.
- **Select a profile by identity alone in v2.** Leaves the default ambiguous when several
  layouts match. A committed logical profile name is the selected interface; overrides
  still permit different local arrangements.
- **Require a readable profile for every local command.** Prevents useful standalone
  product checks from a valid committed schema copy.
- **Fall back after a malformed default or an explicit missing file.** Hides a configuration
  problem and can mix evidence from an unintended checkout set.
- **Keep cross-drive refusal.** Does not meet the accepted location-flexibility scope.
- **Keep `/1` labels while changing field meanings.** Misleads existing consumers. Uniform
  CLI `/2` also gives parser errors a predictable format before repo discovery.
