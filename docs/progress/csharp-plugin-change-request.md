---
summary: Historical proposal for CR-007, accepted and recorded in the ledger on 2026-11-02. Specifies edits to requirements 12, 15 and 21 and additions 24–26.
read_when:
  - reviewing the required change request before implementing the extractor plugin contract
---

# C# plugin — change-request draft

**Status:** accepted by the project manager on 2026-11-02 and recorded in the ledger as
`change-requests/CR-007.md` with explicit authorization. That ledger record is authoritative.
The proposal below is retained as the impact-analysis history; it is not a second register.

The [approved architecture](../design/extensibility-architecture.md) supplies the design.
This draft supplies the concrete requirement changes needed to implement it. At proposal time, the
register contained accepted CR-001–CR-006; none covered independent plugins.

## Proposed request

Allow trusted language maintainers to release extraction updates independently of qmstrace,
while preserving trace judgments and making the exact extraction environment identifiable.
C# is the first explicit additional package. Operators must be told when the required
capability is absent, and an incomplete assessment must never appear successful.

Proposed request header for the project side:

```text
CR-007 — Independently versioned language extraction
Requested-by: project manager
Impacts: REQ-QMT-12, REQ-QMT-15, REQ-QMT-21, REQ-QMT-24, REQ-QMT-25, REQ-QMT-26
```

The proposed header omitted state; the project manager subsequently supplied acceptance.

## Proposed changes to existing requirements

| Item | Exact addition or replacement |
|---|---|
| REQ-QMT-12 | Add: “Before writing a starter that requires an external extractor, init verifies that a compatible provider is installed. If unavailable, it refuses without writing files and explains the required installation.” |
| REQ-QMT-15 | Replace the first sentence with: “Two runs of a command on the same source tree, with the same external inputs and resolved host, plugin, runtime and parser-dependency versions, print identical bytes, with no path of the machine it ran on.” |
| REQ-QMT-21 | Add: “C# extraction is supplied by an explicitly installed compatible language package; its existing marker, identity, digest and test-report matching behavior is preserved.” |

Existing origins/categories/verification methods remain. Each changed item will cite the
fresh accepted request without erasing prior change provenance.

## Proposed requirement additions

These IDs are candidates, not declarations or reservations.

| Candidate | Proposed statement | Category | Origin | Verification |
|---|---|---|---|---|
| REQ-QMT-24 | A compatible independently versioned language package adds named source/test extractors without a host source change. The host validates declarations before handler import and uses one provider per extractor and one catalog across current, sibling and historical scans. Missing, incompatible or ambiguous required providers refuse assessment; plugin faults never yield successful empty extraction. | compatibility | AGR-2, AGR-5 | test |
| REQ-QMT-25 | The plugins command lists installed providers, declared capabilities, API compatibility and discovery problems in text or JSON, without requiring trace configuration or importing handlers. | usability | AGR-5 | test |
| REQ-QMT-26 | Assessment and table JSON identify the executing host, Python runtime, used plugin distributions, API versions and parser dependency versions as deterministic additive metadata, preserving source notices and avoiding machine-specific paths. | reliability | AGR-9, AGR-15 | test |

## Impact analysis

Initial command analysis of requirements 01, 02, 04, 05, 12, 15 and 21 found six design
elements, 44 components and 131 automated tests downstream. That broad candidate analysis
is not the list of requirement text edits: the six proposed Impacts above are the intended
changes/additions. A second analysis starting at requirements 12, 15 and 21 found
three design elements, 24 components and 61 automated tests downstream. Proposed new
IDs 24–26 have no graph items yet. Recheck the set before submission if the tree changes.

Design owners include DSN-QMT-02, 03, 04, 11, 12 and 15. Source reading, schema validation,
setup, rendering, C# extraction, packaging and CI require changes. Tests must cover
manifest admission, no-import inspection, result validation, historical scans, unchanged
C# behavior and independently installed wheels. New design IDs, if needed, are assigned
without renumbering existing items.

No trace-schema or agreement change is proposed. Existing origins support the additions;
the project side must confirm that interpretation. Requirements 01, 02, 04, 05, 14, 22 and
23 retain their current text. Moving source/test paths changes derived identities and
requires explicit trace review, not fabricated continuity.

The governing local baseline is `baseline/requirements/1` at `9dbe29f98a64`.
Remote-tag completeness and historical external/sibling citations remain NOT VERIFIED.
New tests or passing gates do not clear existing suspects or record human review.

## Boundary

Acceptance authorizes the listed requirement changes and additions for the approved
implementation. It does not publish releases, upgrade consumers, approve clinical use,
or establish cross-platform acceptance. The accepted CR-007 record was added to the
ledger on 2026-11-02; no other change-request record was changed.
