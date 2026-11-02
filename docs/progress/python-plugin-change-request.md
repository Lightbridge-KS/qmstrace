---
summary: Historical CR-008 proposal; accepted by the project manager and recorded in the ledger on 2026-11-02. The ledger record is authoritative.
read_when:
  - reviewing or recording the Python plugin change request
---

# CR-008 — Independently installed Python extraction

- State: accepted (authoritative record in the ledger)
- Requested-by: project manager
- Impacts: REQ-QMT-02, REQ-QMT-12

Accepted by the project manager on 2026-11-02 with explicit authorization to record the
request in the ledger and proceed. `change-requests/CR-008.md` in the configured ledger
is authoritative; this product-side proposal is retained as impact-analysis history.

## Request

Allow Python module and pytest extraction to be released independently of qmstrace through
an explicitly installed compatible language package. Preserve existing trace configurations,
markers, identities, digests, findings, guidance and JUnit report matching. Include this
migration in the unpublished host 0.4.0 release, with Python plugin 0.1.0.

## Proposed requirement changes

Append to REQ-QMT-02:

> Python module and pytest extraction are supplied by an explicitly installed compatible
> language package; existing marker, identity, digest and test-report matching behavior is
> preserved.

Append to REQ-QMT-12:

> The Python starter, including default Python selection, requires its extraction provider
> before any files are written. When unavailable, setup explains explicit installation;
> it does not install a provider or fall back to a reduced configuration.

Retain existing categories, origins, verification methods and prior Change citations;
append the fresh accepted request citation only after acceptance is recorded.

## Impact analysis

On `de02a3a`, `qmstrace impact REQ-QMT-02 REQ-QMT-12` reaches two design elements
(DSN-QMT-04 and DSN-QMT-11), 15 components and 38 automated tests. This graph reach is not
the complete implementation file list: plugin infrastructure, package metadata, CI, wheel
checks and documentation also need updates. Existing API, inspection and provenance
requirements 24–26 remain applicable without text changes. No new requirement IDs,
agreement changes or trace-schema rule changes are proposed.

Move Python extraction and language guidance into a workspace package. Keep Markdown,
report readers, graph judgments, starter assets and transactional setup in the host.
Remove legacy internal Python extractor import paths, documenting the import-path break;
retain CLI extractor names and configured behavior. Source moves change derived component
identities and require trace review, not invented identity continuity.

The governing local baseline is `baseline/requirements/1` at `9dbe29f98a64`.
Remote-tag completeness and historical external/sibling citations remain NOT VERIFIED.
The register currently has seven readable requests and no malformed records. Accepted
CR-007 is present in its working tree; that does not imply it is committed.

## Acceptance boundary

Acceptance and authorized ledger registration are complete. No publication or consumer
installation is implied.

This draft does not authorize release publication or consumer installation. Passing tests
and edits do not record review or clear suspects. The [tracker](python-extractor-plugin.md)
owns execution state and verification results.
