---
summary: ADR-0002 — an ID's number may carry dotted parts (DES-XYZ-04.1, TC-XYZ-04.1-01), read whole wherever it is written or reported, never cut short; one global ID shape still. Amends marker syntax v0 and the manual's ID-shape explanation; fixes IDs cut short at the first dot.
read_when:
  - changing the ID shape (`core/model.py` ID_TOKEN) or any reader that finds IDs in text
  - an adopter's IDs carry dots, or an ID is read differently in a heading, a table or prose
  - writing or changing `id_pattern` / `id_prefix` guidance
---

# ADR-0002 — Dotted IDs

- **Status:** accepted, 2026-10-14
- **Amends:** [data architecture](../design/data-architecture.md) *Marker syntax v0* (which
  relied on an ID shape it never stated), and the manual's
  [IDs and file patterns](../../contents/explanation/ids-and-file-patterns.md), which says dotted
  numbers are "no"
- **Decided by:** the developer, 2026-10-14, from the beacon-dotnet test bed's findings

## Context

The first C# adopter numbers its items hierarchically: `DES-XYZ-04.1` is element 1 of
requirement 04, and `TC-XYZ-04.1-01` is test 01 of that element. Its rule is that IDs are never
renumbered; its documents, its tests' `DisplayName`s and its filed CI evidence all carry them.

qmstrace has one ID shape, `[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+` — capital letters and digits in
hyphen-joined segments, ending in a number. A dotted ID does not fit, and the readers disagree
about it:

| Where the ID is written | Read today |
|---|---|
| a link field, a pytest marker | reported: not an ID |
| a Markdown heading | an item with the ID cut short (`TC-XYZ-04`) and the rest in its title |
| a table cell, a stray, a mention | cut short, silently: two test cases become one ID |

On the [beacon-dotnet](../tests/beacon-dotnet.md) bed this is end to end: the ledger's own
check reports 49 V02, one per dotted test case, each naming a cut-short ID, and reads no test
case at all. In an undotted copy the same ledger reads all 49 with 0 violations.

## Decision

- **An ID's number may carry dotted parts.** An ID is capital letters and digits in
  hyphen-joined segments, ending in a number; any numeric part may be followed by `.` and more
  digits (`04.1`, `03.1`, `1.2.3`). A dot counts only between digits.
- **An ID is read whole wherever it is written, or reported — never cut short.** In running
  text the shape is bounded on both sides: `TC-BAG-03.1a` is not an ID, and is not read as
  `TC-BAG-03`; a sentence-final full stop is not part of the ID before it.
- **One global shape, still.** Every reader — headings, fields, tables, mentions, strays,
  markers in code, change requests, citations — uses the one shape, so a marker means the same
  in every repo of a ledger.
- **A heading that starts with a malformed ID of this repo's kind is reported** (V02), never
  read as prose.
- **IDs stay opaque.** `04.1` is not read as a link to requirement 04; the item still states
  its links.

The shape, for the record:

```text
[A-Z][A-Z0-9]*(?:-[A-Z0-9]+(?:\.\d+)*)*-\d+(?:\.\d+)*
```

## Evidence

- Checked 2026-10-14: in running text the new shape finds exactly the old pattern's IDs in 288
  of qmstrace's 291 text files: docs, manual, tests, source, glossary and its ledger. The 3
  that differ are the docs that write dotted IDs, where the old pattern cut them short. In
  *See REQ-BAG-09. Then TC-FLT-04.1-01, TC-FLT-04.1-02 and DES-FLT-04.1.* it finds exactly those
  four IDs.
- beacon-dotnet M0 (engine `75ba627`): 49 V02 on the dotted test cases; 0 in an undotted copy.

## Consequences

- One pattern changes in `core/model.py`; every reader picks it up. `id_pattern` and
  `id_prefix` may contain dotted parts.
- beacon-split, read by the new engine, must match the `75ba627` oracle exactly (measure C13):
  widening the shape changes nothing that had no dot.
- A new requirement, REQ-QMT-20, under CR-003.
- The refusal at a baseline tag whose snapshot cannot be read (M0: 49 V02 in one 6.7 KB line)
  is summarised by code, with the first few, and says how to see the rest.
- **Docs to follow, in M12a:** *Marker syntax v0* states the ID shape; the manual's
  *IDs and file patterns* page; the scenario catalogue's *Dotted IDs* section.

## Rejected alternatives

- **Keep the shape and report every dotted ID.** The adopter would renumber 243 mentions in its
  docs, 75 `DisplayName`s and its test-case document, against its own never-renumber rule, and
  its filed evidence would no longer join the trace without a mapping.
- **Let each project's schema set its ID shape.** A marker's meaning would depend on the repo,
  and two repos of one ledger could read the same line differently. Kept open only until a
  project needs a shape this one cannot cover.

## Open

- Issue #25 (an ID pattern with alternatives lets a slip in its second family pass) is
  adjacent: M12a's malformed-lead reporting covers the first family's case, not #25.
