---
summary: ADR-0013 — accepted direction for manifest-first registered language plugins in a uv workspace; C# is the first separately versioned package. Implemented under CR-007; release publication and consumer installation remain separate.
read_when:
  - changing extractor ownership, public plugin compatibility or package release boundaries
---

# ADR-0013 — Independently versioned language extractors

- **Status:** accepted 2026-11-01; implemented under CR-007, accepted 2026-11-02
- **Decided by:** developer-manager, through the accepted implementation plan
- **Amends:** the blueprint's internal-only registry and no-plugin decision; ADR-0004's
  ownership of C# parser dependencies; ADR-0011's JSON projection with additive provenance
- **Change control:** CR-007 is accepted and recorded in the ledger for requirements 12, 15, 21 and 24–26

## Context

A language parser update currently requires a host release. Extractors already accept
source text, but configuration, findings and renderers also contain language knowledge.
Moving parser files alone cannot provide independent releases.

## Decision

Follow the [extensibility design](../design/extensibility-architecture.md): a stable public
Python API, manifest admission before handler import, one provider per extractor and one
catalog per invocation. C# ships as an explicit additional wheel in the same uv workspace.
The host retains source access, graph validity, coverage, baselines and verdict propagation.

Package versions evolve independently. Exact resolved tool environments and provider
provenance support evidence reproduction. Independent wheels are tested outside the
workspace. The existing C# syntax, identities and report matching remain compatible.

## Consequences

The host must remove embedded language assumptions and validate plugin results. The C#
package owns its parser dependencies and behavioral tests. Operators install the package
into the host's environment. API maintenance and cross-version tests become continuing
obligations. Trusted in-process plugins have no security or failure-containment boundary.

## Rejected alternatives

- **Internal registry only:** cannot deliver a parser correction independently.
- **Priority/fallback dispatch:** a failed extractor could hide absent trace evidence.
- **Separate plugin repository immediately:** unnecessary coordination during seam development.
- **Worker/RPC host:** no independent runtime or containment requirement in the agreed scope.
- **Separate SDK distribution immediately:** the versioned host-owned API provides the needed
  boundary without another release dependency.

## Evidence and remaining work

The [tracker](../progress/csharp-extractor-plugin.md) records checks actually run and the
accepted requirement request. Design acceptance does not establish implementation,
cross-platform acceptance, release publication or a consumer upgrade.
