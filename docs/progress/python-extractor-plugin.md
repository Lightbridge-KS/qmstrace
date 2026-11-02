---
summary: Python plugin migration implemented under accepted CR-008. Full dry gate passes 1565 tests; macOS/Linux independent wheels and both strict trace gates pass. Native Windows candidate evidence and historical released combinations remain unverified.
read_when:
  - implementing or reviewing the Python extractor plugin migration
  - checking change-control, compatibility evidence or remaining work
---

# Python extractor plugin — implementation

Parent: [overview](overview-qmstrace.md). Predecessor:
[C# plugin](csharp-extractor-plugin.md). Existing mechanism:
[extensibility architecture](../design/extensibility-architecture.md).
Change request: [draft CR-008](python-plugin-change-request.md).

## Now

CR-008 was accepted and recorded in the ledger on 2026-11-02. The Python workspace
package, provider-aware setup and release preparation are implemented. Nothing is committed
or published. The full local dry gate and macOS/Linux installed-wheel checks pass.
Native Windows acceptance for this candidate remains pending.

The project manager explicitly accepted the duplicate-declaration compatibility correction:
API v1 preserves duplicate item IDs and locations for host V01 validation. This is a validation
relaxation, not an API-field change. Other DTO and link validation remains unchanged.


## Confirmed choices

One `qmstrace-lang-python` workspace member contains `python-module` and `pytest`.
Both remain explicitly installed, like C#. Include migration in unpublished host 0.4.0;
prepare Python plugin 0.1.0 without bumping C# 0.1.0. Reuse API v1 and remove legacy Python
extractor import paths, documenting that break. No fallback implementation, automatic
installation, new setup hooks or new API major. Pytest is not a runtime dependency.

Markdown, report parsing, graph judgments, starter assets, pytest marker registration and
transactional setup stay host-owned. Preserve default Python starter selection; missing
providers refuse before any writes. The development group installs both workspace plugins.

## Phase 1 — change control and reference

- [x] Inspect status, rules, both requirement threads, impact and baseline/request evidence.
- [x] Draft concrete requirement changes under provisional CR-008.
- [x] Run unchanged Python reference tests and capture pre-migration outputs.
- [x] Reconcile C# evidence with merged PR 77 and passing platform CI.
- [x] Obtain explicit acceptance, recheck numbering and register the accepted request in the ledger.

## Phase 2 — public API adaptation

- [x] Route bundled Python through ExtractRequest/Extraction and the existing adapter first.
- [x] Preserve IDs, locations, levels, class-inherited links, runs_as and AST digests.
- [x] Move Python diagnostic wording, stray guidance and private field parsing behind API v1.
- [x] Recognize configured markers; ordinary pytest decorators must not produce invalid plugin output.
- [x] Preserve wrong-carrier findings in the host; never import scanned code or pytest.
- [x] Surface the duplicate-declaration conflict for an explicit contract decision.
- [x] Resolve duplicate-declaration compatibility and pass both affected reference tests.

Exit: unchanged reference facts and findings pass through the adapter.

## Phase 3 — independent workspace member

- [x] Scaffold with `uv init --lib`, own README/changelog/license/typing marker and manifest.
- [x] Start at 0.1.0.dev0; declare qmstrace>=0.4.0 with development-only workspace overrides.
- [x] Register both extractors as API 1, derived IDs, named links; use stdlib parsing only.
- [x] Remove built-in Python registration/descriptors, old implementation and compatibility wrappers.
- [x] Extend typing, test discovery, import guards, trace scanning and each package's 90% coverage floor.
- [x] Verify provider availability transactionally for both starters, preserving marker registration.

Exit: Python configurations work with explicit installation; host-only document assessment
and plugin inspection work; missing Python refuses without writes or reduced evidence.

## Phase 4 — compatibility and independent packages

- [x] Build all three distributions with --no-sources and install outside the checkout from a prepared wheelhouse.
- [x] Verify host only, Python only, C# only and both-provider environments; no runtime pytest or checkout paths.
- [x] Exercise no-import admission, malformed manifests/results, faults, empty extraction and marker-form round trips.
- [x] Preserve docstrings, strays, parse errors, IDs, async/class tests, inherited markers, levels and exact digests.
- [x] Verify parameterized JUnit identities/verdicts and current/sibling/tagged scans with one catalog.
- [x] Verify missing historical capability refuses instead of reducing evidence.
- [x] Replace Python alone against an identical host wheel; replace a compatible host with both plugins unchanged.
- [ ] Run Linux/macOS/Windows installed-wheel matrix and retain native Windows distinct-drive acceptance.
- [x] Record runtime/dependency versions and artifact hashes; Python 3.13 is the baseline, not a cross-minor digest promise.
- [x] Run complete dry gate, browser/manual checks, both strict trace gates, report matching and disposable mutations.

Exit: candidate matrix passes. Unavailable historical released API-v1 combinations remain
unverified; fixture successors are mechanism evidence, not released compatibility evidence.

## Phase 5 — release preparation and documentation

- [x] Prepare host 0.4.0, Python 0.1.0 and unchanged C# 0.1.0 manifests/changelogs.
- [x] Add explicit package/tag mapping for qmstrace-lang-python-vX.Y.Z and tag/changelog tests.
- [x] Keep annotated-tag validation, selected-package build and CI-created draft releases only.
- [x] Document and test explicit Python/C#/combined uv tool --with installation and pinned upgrade/rollback in temporary environments.
- [x] Add the design amendment ADR; reconcile architecture, blueprint, manual and tracker evidence.

Exit: automation and guidance verified. Tagging, publication and consumer upgrades remain
separate operations; no release execution is implied by preparation.

## Reference evidence — 2026-11-02

On unchanged `de02a3a`, CPython 3.13.2, the following selection passed **100 tests**:

```sh
uv run pytest -q --no-cov tests/unit/test_extract_python.py tests/unit/test_forms.py \
  tests/unit/test_junit.py tests/integration/test_results_pytest.py tests/cli/test_results.py
```

Existing assertions and CLI goldens remain the independent expected behavior. The
[reference snapshot](python-plugin-reference.json) records exact input text and complete
outputs from that unchanged implementation for representative module, pytest, invalid-ID,
parse-error and unread-marker cases, including literal digests and corrective guidance.
It is a frozen pre-migration observation, not an expected-output file to regenerate from
the new plugin. Configuration paths and reference revision are included in the snapshot.
Existing test cases cover the broader behavior set beyond these representative records.

Local strict trace check exited 0: 920 items, 634 links, zero violations, zero gaps and
37 suspects. The requirement impact reaches two design elements, 15 components and 38 tests.
These are preparation results, not Python-plugin acceptance. Suspects require review;
remote-tag completeness and historical external/sibling citations remain unverified.

## Migration verification — 2026-11-02

The duplicate-declaration conflict initially caused two reference failures. After explicit
acceptance, the adapter preserves declarations for host V01 judgment; both original tests
pass unchanged, and a direct adapter-to-graph regression verifies locations and digests.

From the repository root, with the dependency wheelhouse prepared:

```sh
PYTEST_ADDOPTS=--junitxml=dist/python-plugin-tests.xml just dry
uv run qmstrace results dist/python-plugin-tests.xml --json
uv run qmstrace check --strict --json
uv run qmstrace -C ../qmstrace-ledger ledger check --strict --json
```

The ledger command uses this workspace's configured sibling ledger; another checkout must
supply its configured ledger path. Wheelhouse preparation is `just prepare-wheelhouse` and
requires network access; installed-wheel checks then install offline from those artifacts.

| Check | Result |
|---|---|
| Complete dry gate | Pass: 1,565 Python tests, formatting/lint, strict typing, wheel checks and manual build |
| Production coverage | Host 98.14%; C# 99.00%; Python 100.00% — each above 90% |
| Browser tests | Four passed |
| JUnit trace matching | All 1,565 runs matched all 796 scanned tests; zero unmatched or duplicate runs |
| Both strict trace gates | Exit 0; 922 items, 644 links, zero violations and gaps, 35 suspects |
| macOS and Linux isolated wheels | Both language checks passed, including plugin-only and compatible host updates |
| Runtime dependency audit | No known vulnerabilities reported for the locked runtime dependency export |
| Native Windows candidate checks | Not run; no online Windows peer was available; CI matrix and distinct-drive gate retained |

The public API selection verifies all five frozen cases, exact digests and rendered guidance,
ordinary pytest decorators and missing-provider setup. Existing JSON golden content is unchanged
except for toolchain provenance; empty-provider inspection lists only Markdown.

Installed-wheel checks cover host-only document operation, each language alone, both providers,
no-import discovery, fixture-provider installation, unchanged host during each plugin update,
unchanged plugin packages during a compatible host update, and temporary tool installation,
upgrade and rollback. The other language's output is compared during updates. Exact environments
and hashes are generated under `dist/compatibility-*-python.json`,
`dist/compatibility-*-csharp.json` and `dist/python-linux-evidence/`. CI uploads equivalent
platform evidence. These generated local artifacts are not committed release evidence.

Four mutations in disposable copies were detected: duplicate declarations rejected as a plugin
fault (one failing regression), dropped Python links (two), changed module digests (two), and
lost pytest report identity (two). Working source was never mutated. Generated results are in
`dist/python-plugin-mutations.json`.

## Remaining acceptance and evidence limits

- Native Windows installed-wheel and distinct-drive checks must pass for this candidate;
  C# PR 77's earlier result does not establish this migration's acceptance.
- Historical released API-v1 combinations remain unavailable. Fixture successors prove the
  mechanism only. Runtime versions are recorded; cross-minor digest equality is not claimed.
- The 35 suspects require review. Counts changed with source-path moves and removed legacy
  tests; no review or clearance is inferred. Reachable local tags and working-tree evidence
  do not verify remote-tag completeness, historical external citations or report freshness.
- Automated browser tests and manual compilation do not establish human manual acceptance.
- Release workflow execution, commits, publication and consumer upgrades remain separate.
