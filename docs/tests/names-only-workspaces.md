---
summary: Acceptance protocol and measured 0.3.0 names-only configuration results: unit/CLI, disposable macOS test-bed checks and native Windows distinct-drive acceptance verified in PR 74.
read_when:
  - creating v2 configuration fixtures or live layout test beds
  - verifying names-only migration and native Windows cross-drive support
  - recording 0.3.0 acceptance results without modifying original test beds or consumers
---

# Names-only workspaces — acceptance protocol

**Status: implementation, macOS acceptance and native Windows N12 verified, 2026-10-24. PR #74 merged at `79841ec`; v0.3.0 published at `a276e6e`.**
Parent: [feature design and implementation plan](../design/names-only-workspaces.md).
Progress belongs in the [existing tracker](../progress/overview-qmstrace.md#landed--030-names-only-configuration).
Tests must distinguish configuration readability, trace judgment, actual test execution,
installation, maintainer review and release publication.

## Test-bed discipline

Use the existing sibling `_tests/` workspace. `beacon-engine/` provides product-owned
documents and historical baselines; `beacon-split/` provides ledger-owned documents;
`beacon-dotnet/` provides C#/TRX coverage. Inspect each test bed's local instructions first.
Clone the needed repositories into a fresh `qmstrace-v2-layouts/<run>/` directory.
Never reshape originals, reset another session's files or edit real consumer checkouts.

Before a run, record original commits/tags, tracked-source hashes, clone locations, the
candidate tool's exact commit/wheel/version and the environment/platform. A v2 migration
is a new commit on the disposable clone; retain its v1 baseline tags at their original
commits. Record any necessary configuration-overlay commit mapping without changing traced
source bytes or claiming that an overlay is original historical evidence.

Keep raw output, subprocess exits and machine paths outside the source repository under
that run's outputs. Distil verified results here and in the tracker. Clone cleanup is
limited to the directories created for that run; preserve a compact reproducible recipe.
No PHI, deployment credentials or site network facts belong in fixtures or records.

## Fixed measures

| ID | Measure | Required evidence |
|---|---|---|
| N01 | Names-only v2 files | Local files contain repo/profile names; shared/copy membership contains names/role only; no committed cross-repo checkout path or legacy ledger pointer |
| N02 | Strict versions | Valid v1/v1 and v2/v2 pairs load; unknown versions, unknown keys and mixed assessment pairs exit 2 with migration guidance |
| N03 | Stable membership | Empty/duplicate/unsafe names and role/member contradictions are refused; reordering members leaves the v2 digest unchanged; names keep qualified IDs |
| N04 | Named default | V2 loads exactly its profile stem; unrelated user files are not read; missing required field is invalid; v1 discovery remains as shipped |
| N05 | Overrides | CLI, environment and nearest ancestor sources override the named default; both option placements and `-C` work; duplicates are usage errors; lower stages remain unread |
| N06 | Missing versus invalid | Absent implicit file permits local-only assessment; explicit absence, malformed/unreadable/stale-bound defaults and dangling links exit 2 without fallback |
| N07 | Exact binding | Wrong project, ledger role, local member identity, duplicate physical roots and swapped same-project member bindings are refused before evidence use |
| N08 | Partial maps | Unmapped/unavailable remote members remain unavailable locally; project check/thread/impact/table refuse incomplete projects; targeted schema copy requires all selected destinations |
| N09 | Separate schema loading | A selected map cannot repair an unreadable schema reference or substitute current rules; copied schemas support product-only checks |
| N10 | Two developer layouts | Migrate once, relocate into two different layouts and change only profiles; item/link IDs, findings, candidates, verdicts, baseline comparisons and logical JSON evidence agree |
| N11 | Path anchors | Native absolute and canonical map-relative paths, symlink-selected maps, nested trace roots, Unicode paths and worktrees resolve correctly; TOML does not expand env/~ |
| N12 | Cross-drive Windows | Run real CLI commands with ledger and products on distinct native drive roots; profiles load, traversal/results/copy work, evidence contains portable locations rather than generated native roots |
| N13 | Historical v1 | Select an original v1 baseline after current v2 migration; frozen/changed/removed/suspect judgments retain their meaning; no current-profile read enters GitTree schema loading |
| N14 | Historical v2 | Cut a synthetic v2 baseline, then change/withdraw/remove items and migrate paths; guards, governing ancestry, fresh citations and suspect provenance behave as specified |
| N15 | Standalone evidence | Remove access to the ledger/products without changing a valid copied schema; local commands keep available judgments and explicit unavailable-source/request notices; no false project approval |
| N16 | Portable outputs | Every supported JSON command and handled exit 1–3 validates as CLI `/2`, including parser errors before discovery; table `/2` preserves columns/verdicts with versioned locations |
| N17 | Presentation and diagnostics | Text labels, ANSI-stripped parity, quiet notices, safe diagnostic locations and authored literal brackets survive; help/version never read profiles |
| N18 | Reports and graph view | Combined JUnit/TRX sources match at resolved operational roots; derived IDs and report digests are stable; generated graph source locations do not depend on native checkout roots |
| N19 | Transactional migration | V2 writer validates every destination/candidate before writing; a bad target causes no writes; only generated blocks change; rerun is byte-identical; empty/older held blocks are handled only by copy planning |
| N20 | Setup and assets | Valid v2 init refresh preserves local edits/maps; existing v1 creation/refusal policy remains; bundled skill, schemas and installed entry points agree with documentation |
| N21 | Controlled-source isolation | No original test-bed/consumer tracked bytes or tags change; no release tag, request acceptance or review clearance is manufactured |
| N22 | Package and manual | Isolated wheel exercises v1/v2, selected and missing profiles, output versions and copy refusals; tested examples appear intact in the built Diátaxis manual |

## Ordered live run

1. Build/install the candidate into a fresh isolated environment outside its source tree.
   Capture v1 baseline outputs before editing any disposable configuration.
2. Convert a ledger-owned fixture and its products to v2 on fresh branches, keeping member
   names and controlled source bytes. Generate copies transactionally and commit the
   disposable migration. Prove N01–N09 and capture its exact pins.
3. Copy/clone that migrated set into layout A and a differently nested layout B. Use
   separate user profiles and a fresh home/environment per layout. Prove N10–N11 with
   canonical logical comparisons, not text deletion that could hide findings or notices.
4. Repeat the important paths in product-owned-document and C#/TRX fixtures. Reuse synthetic
   reports for matching and run real fixture tests when claiming executed verdict evidence.
   Preserve report inputs/digests and distinguish those claims in the record.
5. Execute N12 on native Windows with two genuinely distinct usable drive roots. Do not
   count POSIX parsing of Windows strings as proof. If drive aliases canonicalize onto one
   root, that setup does not satisfy the measure. The selected runner must provide the
   necessary native roots or the cross-drive gate remains unverified; do not silently skip it.
6. Run historical and mutation measures on disposable branches. Restore the pinned clone
   state before each mutation; confirm the targeted test fails and passes after restoration.
   Deliberately swap repo bindings, remove a mapped member and break one copy destination.
7. Inspect goldens, installed output, rendered examples and package assets; run `just dry`
   and local/ledger strict trace gates. Recheck original source hashes and tags before cleanup.
8. Record measure-by-measure outcomes, tool/pin provenance, expected nonzero exits, remaining
   evidence limits and the exact disposable roots cleaned up. No acceptance summary may be
   copied from another agent's claim without independently checking its artifacts.

## Verification layers and results

Pure unit tests cover version/identity/map values and digest canonicalization. Integration
tests use real temporary Git histories, filesystem bindings and transactional copy failures.
CLI goldens pin every payload, refusal and presentation boundary. Existing baseline, graph,
results, setup and table regressions remain required. Native Windows and external test-bed
runs prove claims that pure path tests cannot.

The preimplementation v0.2.0 assessment passed 36 existing map/history checks; those establish
legacy behavior only. The records below distinguish implemented/local evidence from native
Windows proof. Raw machine paths, reports, complete source hashes and command transcripts stay
in the disposable run workspace, not shared evidence.

### Measured run, 2026-10-24

The candidate was installed from a wheel into an isolated environment and run outside the
source checkout. Three original test beds were cloned locally, without hard links, into fresh
run directories. V2 identity/schema migrations were committed only in these disposable clones.
Two differently nested layouts used separate maps with the same schema bytes. No traced
Markdown, Python or C# source bytes were changed for migration.

| Test bed | Project items / links | Violations / gaps | Two-layout evidence |
|---|---|---|---|
| beacon-engine | 177 / 208 | 0 / 0 | Complete project-check JSON and all three tables byte-identical |
| beacon-split | 177 / 208 | 0 / 0 | Complete project-check JSON and all three tables byte-identical |
| beacon-dotnet | 226 / 257 | 0 / 0 | Complete project-check JSON and all three tables byte-identical |

Real pytest runs in the gateway clones matched **76 automated tests / 94 runs** each.
The Python agents and the C# agent's real xUnit/TRX run each matched **53 automated tests /
67 runs**. All six runs passed and matched without duplicates or unmatched entries. Each
project's matrix combined its two reports successfully under `qmstrace.table/2`. These are
the current source pins' counts, not a replay claim for the earlier E1 pins.

A separate beacon-engine mutation probe read **11 frozen requirements** from the original
v1 `m5b/requirements/2` snapshot. A synthetic v2 `m5b/requirements/3` tag preserved the frozen
population with zero changes/suspects. Changing REQ-BCN-01's title yielded V10 and **18
suspects**. A file touch and an unrelated test addition preserved the suspect IDs. Restoring
the source cleared those change-induced chains. Disabling the API-key guard failed its
integration tests and yielded **REQ-BCN-10: fail** from the partial report, with informational
results exit 0; restoring it passed the tests. Synthetic tags are fixture data, not approval.

The probe initially used an outdated 10-item frozen expectation, then identified the 11-item
second-baseline population. Its first auth-verdict assertion targeted REQ-BCN-01; source
markers establish REQ-BCN-10. Corrected probes ran from fresh pinned clones; only their
independently checked outcomes above are recorded as passing evidence.

All nine original repositories retained their tracked-byte hashes, HEADs, tags and original
working-tree status after live checks. Original generated/untracked files were preserved.

### Measure status

| Measures | Evidence and limit |
|---|---|
| N01–N11 | Configuration/map tests and deterministic v2 command goldens; three migrated beds and two relocated layouts. V1 fallback/digests remain covered by regressions |
| N12 | **Passed on native Windows.** [Required cross-drive job](https://github.com/Lightbridge-KS/qmstrace/actions/runs/40086635317/job/120850811085) at `c4929d4`, Windows Server 2025 / Python 3.13.16; distinct canonical drive roots, real CLI commands and complete cleanup. The separate macOS smoke is not counted as N12 |
| N13–N14 | Real Git integration tests load v1/v2 historical configurations independently; the live original-v1/synthetic-v2 baseline and mutation probes pass |
| N15–N20 | Standalone/missing-map and unavailable-source tests, parser/JSON/style regressions, real JUnit/TRX reports, HTML smoke, transactional bootstrap/refusal and v2 init-preservation tests pass |
| N21 | All nine original repositories independently rehashed after the runs; no consumer, request-acceptance or release changes |
| N22 | Isolated wheel checks exercise v1/v2 parsing and missing/invalid profiles; manual builds strictly and rendered examples/navigation/diagram inspected |

### Native Windows acceptance, 2026-10-24

The [native Windows job](https://github.com/Lightbridge-KS/qmstrace/actions/runs/40086635317/job/120850811085) passed against `c4929d4`, checked out through the PR's
synthetic merge commit. `tests/check_cross_drive.py` requires two writable, distinct canonical
drive roots and invokes the actual CLI; CI supplies no same-drive smoke flag. It verifies
paths/rules/status/check, local and ledger thread/impact, JUnit results, table `/2`, graph HTML
and transactional schema copying. Command JSON and HTML must not contain generated native
checkout roots. Fixture cleanup completed before the final pass receipt. This is native
platform evidence, separate from the same-drive macOS smoke and from human approval.

The initial [Windows job](https://github.com/Lightbridge-KS/qmstrace/actions/runs/40085869280/job/120848562977)
failed on CP1252 redirected receipt bytes. Three real-process regressions reproduce that
failure; `bd356a6` makes redirected stdout/stderr UTF-8 while preserving terminal codecs.
The [next job](https://github.com/Lightbridge-KS/qmstrace/actions/runs/40086376767/job/120850053394)
passed all command assertions but failed removing read-only Git objects. `c4929d4` uses
standard temporary-directory cleanup and prints success only after cleanup. Neither failing
job is counted as completed N12 evidence. The required Windows gate remains active for
subsequent PR revisions and releases.

### Original-to-migration commit mappings

These commits identify disposable configuration overlays; original baseline tags retain their
original objects. Original traced source bytes are preserved through each migration.


| Bed / member | Original commit | V2 migration commit |
|---|---|---|
| beacon-engine / gateway | `2840b8e3d7bc16c699388c72f9a0feaf1ccca3a3` | `892efd293b282845d7e7a5d52e39a9208b4d46aa` |
| beacon-engine / agent | `84f1153131050f31a61810fa7048f148f55f2cba` | `389b77eaf569564aeb623a3f1501e58a4f45b6ef` |
| beacon-engine / ledger | `fda9080e42bb2f2fd838378d795835653784fa87` | `ebf2cbc01881f9b99c77e0ee361c71e51315bd62` |
| beacon-split / ledger | `9d0663b2b31c44ae5108bad4e7da8ee7dcb0ea26` | `25ad1792542c8af706d32621f73989aec289ad53` |
| beacon-split / gateway | `61a02e4341a0d2f639e1a9095d22cf76003b69ec` | `28f0875324d123c100417ea43ff13d5a0485404a` |
| beacon-split / agent | `c9619e5e6bde3c64fe4071321ce51d27901e3d00` | `5360750730d8984a2349cd84eed7f8bcdb83f072` |
| beacon-dotnet / ledger | `dd65081c5f3a4c54c0d2024c2fa9eab8ce45b370` | `bf13db32c9a0eadf1893f4e97f467e93d10a93ff` |
| beacon-dotnet / gateway | `028bde5ba6dd116e1588a067627f5726790f31ec` | `33ebc2da403ea0e55d5cda2618bfd9ca9d7e99ba` |
| beacon-dotnet / agent | `87fb375dbb79f4426bccd76a07985c86ea821ce1` | `5777b0405d1e2f61c1518d61e31c0fa3cfde0862` |

The final live candidate is wheel `0.3.0.dev0`, SHA-256
`3e50af1bf6126e1ee9c87bec920f43b4a3bce27786d6fb60d123203a83193f85`. It was built from
source base `cc6952dc1c6bc0bd41e583a685cb861519d9b24d` plus the uncommitted implementation.
The run record retains the source base/dirty-state provenance. Full-gate
counts and final review state belong to the [active tracker](../progress/overview-qmstrace.md#landed--030-names-only-configuration).
