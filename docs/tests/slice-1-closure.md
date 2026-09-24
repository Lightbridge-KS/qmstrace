---
summary: M6–M8 acceptance record — engine-native product test bed, mapped baselines, command and browser parity, real pytest mutation checks, package/manual verification and explicit remaining limits.
read_when:
  - verifying slice-1 closure or reproducing the engine migration
  - checking browser adoption evidence and local-view performance limits
---

# Slice-1 closure verification

**Run: 2026-09-24.** Implementation is under review on `codex/m6-m8-slice-closure`.
M5b was already merged in PR #12; its behavior is retained and replayed here.

## Method and migration

Fresh disposable clones replay E1 and E3 against their documented source pins. The retained
engine-native test workspace is `../_tests/beacon-engine/`; the original
`../_tests/beacon-experiment/` remains the historical reproduction bed. Source repositories,
tags and traced `src/`, `tests/` and `docs/` bytes are preserved. Its workspace README now
points to the successor. The stand-in is retained at the successor's `_archive/engine-stub/`.
Legacy ledger import must use the old-shape historical workspace; real import awaits slice 2.

The engine is installed from a built wheel in an isolated Python 3.13 environment. Product
pytest environments stay separate. Both product repos use embedded engine schemas and the
new managed guide/packaged skill; their repeated `init` output is byte-identical. All three
migrated repos retain an `engine-main` branch. Gateway and agent migration commits are
`2840b8e3d7bc16c699388c72f9a0feaf1ccca3a3` and
`84f1153131050f31a61810fa7048f148f55f2cba` respectively.

Historical external-schema configurations are not retroactively treated as valid engine
snapshots. An explicit overlay history maps original content into commits with recoverable
embedded schemas. Original tags remain; only `m5b/requirements/` mapped tags are selected.
The prefix retains the already-tested M5b replay convention, not a production naming rule.

| Source pin | Original commit | Engine overlay commit |
|---|---|---|
| baseline/requirements/1 | `ee4eeb4a7a63438b476a6a450d02c5b03616f7be` | `7946e96c93c51e071375c3c0e596246e07aa573f` |
| e3-end | `23aab77245c17fefc4d2b31132ae9cd5edd66a09` | `93edfd7c2ec62013b2f4638d7de13ee502b9fd11` |
| baseline/requirements/2 | `4d2e6b7d367bd7e6d3439ba1bdcb0573b20c657d` | `64032e8d0981acb2b4cf84775238cf8d612941fb` |

The agent uses `e4-end` (`b723b7e0b83c0431ef44a3f76ad4925f712ff0b0`); the migrated ledger
starts at `bbf2a63c82eb3657a4b288968be3ac8f42ff34a0`. E1 uses gateway
`cee4ed7658a81ad9a291544d8c4aec84b860dd02` and ledger
`cc19a6be18b2af322f48c2b8faeb5931b0e52c2d`, with the corresponding Kind-era schema overlay.

## Verified outcomes

- **E1:** 62 cases / 78 runs, 10 passing requirement verdicts, no violations/gaps/unmatched
  entries. Each of seven documented source mutations flips its targeted requirement to
  fail. Source is restored from the pin before each mutation and at completion.
- **E3:** 10 frozen · 2 changed · 1 new · 0 removed. No-tag, unchanged, rewrap, uncited,
  missing/unaccepted request, missing Impacts, accepted change and removal cases pass;
  controlled addition is also exercised. Restoring the system-test file, adding a comment
  and adding an unrelated test retain the same 11 suspects.
- **Second baseline:** the preceding field-only change produces 79 unique suspects,
  including 8 edited dependants; applying the governing baseline leaves 11 unchanged frozen
  items and zero suspects. The stand-in comparison remains as recorded in the M5b tracker:
  its 24 findings / 20 unique items omit transitive and edited dependants.
- **E4/migration:** 104 gateway + 73 agent local items, 124 + 84 links; total 177 / 208.
  Graph/gap parity with the trace lock passes, including reach from 43 starts per repo.
  `status`, `check --strict`, `check --quiet`, `rules`, `thread`, `impact`, `results` and
  `init` execute in both migrated products with equal output under both `-C` placements.
  Real pytest reports are regenerated for both products. The wheel-installed `graph`
  command also produces identical files and output under both `-C` placements.
- **Boundaries:** available siblings remain labelled not pinned; duplicate ownership emits
  V01; a missing sibling is unreachable; a missing ledger preserves NOT VERIFIED in quiet
  output. An explicit added client `Assumes` mutation propagates reach without adding a
  coverage rule. It is a test mutation, not content present at the E4 pin.
- **Impact:** the two CR-001 changed IDs reach 18 downstream items; REQ-BCN-11 enters the
  candidate only when already declared and explicitly supplied. CR-002 remains the
  classification-only change replayed before the second baseline.

## Browser checks and limits

All projected forward/backward closures equal the shared core in miniature fixtures and
both migrated repos (128 and 101 visible-to-run nodes, respectively, including boundaries).
Tests cover deterministic bytes, effective-directory output, refused overwrites, hostile
text, configured external types, simultaneous badges and historical-only S01 provenance.
Node built-in tests exercise search, selection, direction, filters, reset and findings
without a package-manager dependency. Existing shared-core tests cover cycles and
converging dependency/ordinary paths.

Browser inspection through a loopback-served document verifies canvas rendering, keyboard
selection, depth/direction controls, full inspector text, explicit zoom and source notices.
A hostile `</script><img …>` title renders literally; no injected image exists. No console
warnings/errors were observed. The 1,000-node / 999-link dependency-chain view loads and
supports keyboard search/selection; depth 1 shows three nodes around the middle item.
Generation took under one second and produced approximately 5.9 MB locally. This is a
bounded measurement, not a latency guarantee. Precomputed all-pairs reach may grow
quadratically; larger/project-wide graphs are outside this slice's claim.

The standalone file embeds its assets, preserves the browser-library license and denies
connections through CSP. Direct `file://` opening was blocked by the verification browser's
URL policy and remains unverified. No workaround was used. The browser is read-only and
contains no historical/current edge overlay, report overlay, live refresh or review storage.

## Reproduction records

Raw local scripts, mappings and output are retained under
`_playground/2026-09-24_slice-closure/`: `baselines/`, `results/`, `acceptance/`,
`boundaries.json`, `scale.json` and dry-gate logs. They are scratch records; this document
contains only inspected outcomes. Source fixture paths are relative so the workflow can be
recreated from equivalent checkouts. The formal verification record is the reviewed PR;
these local measurements do not assert release publication or ledger-side audit acceptance.


## Final local gate and manual

`just dry` passed: 571 Python tests, 99.09% coverage, three Node control tests, formatting,
lint, strict types, complete wheel-asset verification and a strict clean manual build.
The setup and graph help/command goldens were inspected. Their included output equals
complete built code blocks; setup was visually inspected and the graph reference inspected
in the browser. The new how-to/explanation pages and updated tutorial build successfully.
CI and deployed-preview outcomes are recorded on the combined PR. Release publication
and production deployment are outside this verification record.
