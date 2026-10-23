---
summary: ADR-0008 — a document ID pattern must have a provable literal start shared by every branch, and a baseline-covered document item must identify exactly one configured subject while it is authored; bad tagged evidence remains an exit-2 refusal with a successor-baseline recovery path.
read_when:
  - changing id_pattern or id_prefix validation, especially grouped or alternate regex forms
  - changing subject-key ownership, V17, or baseline snapshot refusal diagnostics
  - investigating an ID that disappears from check or a tag that cannot be judged
---

# ADR-0008 — Prove ID starts and subject ownership before baselines

- **Status:** accepted, 2026-10-23
- **Amends:** [data architecture](../design/data-architecture.md) marker syntax and D6;
  [surface architecture](../design/surface-architecture.md) findings contract
- **Decided by:** the developer, 2026-10-23, for issues #25 and #26

## Context

`id_prefix` is the beginning every ID of a Markdown item type must share. A pattern such as
`^(REQ|NFR)-SVC-\d{2}$` with `id_prefix = "REQ-"` was accepted although it also matches
`NFR-SVC-01`. A malformed `NFR-SVC-3` then disappeared from the graph without V02; a check
could report no violations after silently losing an item.

A second defect appeared when `REQ-03` was allowed by a requirement pattern with an optional
subject segment. Before the first baseline, it passed. Once tagged, ownership could not be
decided; editing the current heading did not repair the tagged copy.

## Decision

- **Prove a common start before scanning.** Configuration derives the literal prefix guaranteed
  by every branch of `id_pattern`. An explicit `id_prefix` must itself be a prefix of that
  proved start. Grouped alternatives remain valid when they share a provable start:
  `^(REQ|RQ)-…` has `R`; `^REQ-(SVC|CLT)-…` has `REQ-`. Distinct `REQ-` and `NFR-` families
  have no common start and are refused, even when an explicit prefix names one family.
  Unsupported regex syntax that defeats the proof is refused conservatively; rewrite the
  pattern to put its common literal start first or separate the item types. Escaped literals
  participate in the proof, including dotted IDs.
- **Report bad subject ownership before a tag.** V17 names a locally declared Markdown item
  of a type in any configured baseline `covers` list when its ID does not contain exactly one
  matching subject-key occurrence as a complete internal segment. Duplicate configured keys
  also prevent unique ownership. `status` counts it; `check` and
  `ledger check` fail with exit 1. An unscoped type is unaffected.
- **Do not guess under a baseline.** If a selected baseline could govern a current item with
  unknown ownership, the run exits 2 because applicability is unjudgeable. An invalid item
  or configuration in the selected tagged tree also exits 2, naming the tag. A current edit
  cannot repair the old snapshot; the project corrects its current tree and establishes an
  approved successor baseline. The old tag is never rewritten.

No new configuration key, dependency or command is added. The existing frozen requirements
remain unchanged; this closes defects in their implementation and diagnostics.

## Rejected alternatives

- **Accept a prefix after sampling a few matching IDs.** Arbitrary regex branches can evade
  examples; a sample is not proof that the prefix covers every match.
- **Allow several unrelated ID families under one item type with a single `id_prefix`.** A
  malformed ID in a different family remains invisible. Separate item types can express
  distinct families without a new prefix-list policy.
- **Infer subject from the file path or rewrite an old tag.** Files can move, and changing
  a tagged snapshot would replace the evidence being judged.
- **Report V17 with exit 1 under an applicable baseline.** The tool cannot know whether the
  item was controlled without its subject, so exit 2 is the honest result there.
