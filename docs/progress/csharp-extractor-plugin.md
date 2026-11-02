---
summary: C# plugin merged in PR 77 at de02a3a. Linux/macOS/Windows installed-wheel and native Windows distinct-drive CI passed. Historical released combinations and publication remain unverified.
read_when:
  - resuming the C# plugin and uv workspace implementation
  - checking package acceptance, evidence or remaining platform gates
---

# C# extractor plugin — implementation

Parent: [overview](overview-qmstrace.md).
Design: [extensibility architecture](../design/extensibility-architecture.md).
Decision: [ADR-0013](../adr/0013-extractor-plugins.md).

## Now

Merged through [PR 77](https://github.com/Lightbridge-KS/qmstrace/pull/77) at `de02a3a`.
Verified on 2026-11-02: [CI run 41411640695](https://github.com/Lightbridge-KS/qmstrace/actions/runs/41411640695)
passed the dry gate, installed-wheel checks on Linux/macOS/Windows, and native Windows
distinct-drive acceptance for candidate `03defc6`. This supersedes the local Windows
limitation below. Host 0.4.0 and C# 0.1.0 remain unpublished. Successor:
[Python plugin migration](python-extractor-plugin.md).

## Local verification record before PR submission

Implementation and local verification completed on 2026-11-02. Host `0.4.0` and C#
plugin `0.1.0` are prepared in separate uv workspace packages. Changes remain uncommitted;
no release tag, draft release, publication or consumer installation was performed.

CR-007 was accepted by the project manager on 2026-11-02 and recorded, with explicit
authorization, in the configured ledger's `change-requests/CR-007.md`. It covers edits
to requirements 12, 15 and 21 and additions 24–26. The ledger record is authoritative.

## Phase 1 — design and compatibility reference

- [x] Inspect configuration, source, release workflow and wheel checks at `c6b40d9`.
- [x] Record the architecture, nine decisions, lifecycle diagrams and ADR; reconcile standing documents.
- [x] Inspect rules, threads, impact and governing baseline/request evidence.
- [x] Preserve existing literal C# expectations and CLI goldens as the behavioral reference.
- [x] Run 117 unchanged C# extraction, forms, TRX, integration and CLI reference tests.
- [x] Record accepted CR-007 and reconcile controlled requirements before implementation.

## Phase 2 — host seam

- [x] Implement `qmstrace.plugin_api.v1`, immutable values and stable ID/digest helpers.
- [x] Add manifest-first catalog, pure descriptor-driven configuration and lazy handlers.
- [x] Route C# behavior through the adapter; move language descriptions and guidance into the plugin.
- [x] Add metadata-only `plugins` inspection in text/JSON, independent of trace configuration.
- [x] Add deterministic provider/toolchain metadata to assessment/table JSON.
- [x] Test admission, invalid results, provider faults, shared historical/sibling catalogs and new providers.

## Phase 3 — workspace package

- [x] Scaffold `packages/qmstrace-lang-csharp` with `uv init --lib` and independent package records.
- [x] Move C#/xUnit/Razor implementation and parser dependencies, retaining parser ranges.
- [x] Add development workspace sources; keep host runtime independent of C#.
- [x] Extend typing, lint, coverage and trace scanning to member code/tests; retain each package's 90% floor.
- [x] Refuse C# setup without a provider before writes; retain host starter data.
- [x] Verify host-only and paired installed wheels outside the checkout.

## Phase 4 — independent package acceptance

- [x] Build each wheel with `--no-sources`; verify metadata, manifest, typing and licenses.
- [x] Install offline from a prepared dependency wheelhouse; record exact environments and artifact hashes.
- [x] Update the plugin against an identical installed host and API-file hash.
- [x] Retain the plugin across a fixture compatible host update; install an additional fixture provider.
- [x] Execute macOS and Linux installed-wheel checks; configure the Linux/Windows/macOS CI matrix.
- [x] Preserve browser checks and the native Windows distinct-drive gate.
- [x] Run the complete dry gate, both strict trace gates and disposable-copy marker mutation checks.
- [x] Execute native Windows installed-wheel and distinct-drive checks for this candidate (PR 77 CI).
- [ ] Verify released historical API-v1 combinations when those artifacts exist.

**Acceptance limit:** platform CI now passes; historical local-only evidence remains below. Fixture versions
prove the update mechanism; they are not historical release evidence.

## Phase 5 — release preparation

- [x] Prepare host `0.4.0` and plugin `0.1.0`, each with its own manifest and changelog.
- [x] Retain host `vX.Y.Z` tags; add plugin `qmstrace-lang-csharp-vX.Y.Z` tags and CI draft releases.
- [x] Validate tag/manifest agreement and package-specific changelog extraction.
- [x] Document paired-wheel installation, upgrade and rollback using `uv tool install --with`.
- [x] Exercise the documented tool installation/update/rollback in temporary tool environments.
- [ ] Run the release workflow on authorized annotated tags after the remaining gates and human review.

Publication and consumer installation are separate operations. The release workflow only
drafts private GitHub releases; it does not publish to a package index.

## Verification — 2026-11-02

From the repository root, after preparing the dependency wheelhouse:

```sh
just prepare-wheelhouse
PYTEST_ADDOPTS=--junitxml=dist/plugin-tests.xml just dry
uv run qmstrace results dist/plugin-tests.xml --json
uv run qmstrace check --strict --json
uv run qmstrace -C ../qmstrace-ledger ledger check --strict --json
```

The last command uses the configured sibling ledger checkout. A different workspace must
supply its ledger path. Wheelhouse preparation downloads dependencies; installed-wheel
checks use that prepared wheelhouse offline. See the [installation guide](../../contents/how-to/install.md)
for distribution installation and retained dependency constraints.

| Check | Observed result |
|---|---|
| Format, lint, strict typing | Pass |
| Python suite | 1,570 passed |
| Coverage | Host 98.23%; C# package 99.00%; aggregate 98.28% |
| Browser suite | 4 passed |
| Isolated host imports/assets | 36 import orders; package data, CLI behavior and license verified |
| Strict manual build | Pass |
| Runtime dependency audit | No known vulnerabilities reported by pip-audit for the locked runtime dependency export |
| JUnit trace matching | All 1,570 runs matched all 794 scanned tests; zero unmatched or duplicate runs |
| Local and ledger strict checks | Both exit 0; 920 items, 634 links, zero violations, zero gaps, 37 suspects |
| macOS installed wheels | Pass on Python 3.13.2 |
| Linux installed wheels | Pass on Python 3.13.11 in an isolated container |
| Native Windows | Not run; CI gates configured, no available native runner during this verification |

Installed-wheel checks cover host-only refusal, explicit C# installation, no-import
inspection, an independently installed fixture extractor, plugin-only update, compatible
host update, and tool installation/upgrade/rollback. Exact environments and wheel hashes
are recorded in generated `dist/compatibility-darwin.json` and
`dist/linux-evidence/compatibility-linux.json`. CI uploads equivalent platform evidence
and candidate wheels. These local artifacts are not committed release evidence.

Four mutations in disposable copies were detected by the relevant tests: unsupported API
admission (2 failures), provider fault converted to empty success (4), lost provider
provenance (2), and dropped C# links (10). The working checkout was not mutated.
Generated `dist/plugin-mutations.json` records those results.

The runtime audit used `uv export --all-packages --no-dev --no-hashes
--no-emit-workspace --format requirements-txt` and `pip-audit 2.10.1` with `--no-deps --disable-pip`
on that complete pinned export. This is advisory-database evidence at the run date, not
a guarantee about undiscovered vulnerabilities.

The original reference cases retain their expected IDs, links, digests, strays, diagnostic
text and TRX identities. Existing assessment text goldens are unchanged; JSON goldens add
only toolchain metadata. New command help and plugin-inspection goldens describe the new surface.

## Remaining evidence and review

- Native Windows candidate checks passed in PR 77 CI, superseding the local run limitation.
- Oldest supported released host with candidate plugin, and candidate host with a previously
  released plugin, are unavailable at this first API-v1 release. Fixture successors remain
  explicitly separate from those combinations.
- The 37 suspects require review. Passing gates and edits do not record review or approval.
- Remote-tag completeness and historical external/sibling citations remain NOT VERIFIED.
  Trace checks read reachable local tags and current working trees; report commit/freshness
  is not verified by report matching.
- Manual build and automated browser checks do not establish human browser/manual acceptance.
- Release workflow execution, publication and consumer installation remain unperformed.

## Deferred

Python package extraction, report-reader plugins, another language, executable setup hooks,
hot reload and process isolation are outside this implementation.

Pre-PR verification repeated the dry and strict trace gates after normalizing invalid API
metadata for JSON inspection. The added TOML-date regression passes; reproducibility
review findings also corrected stale acceptance text in the design.
