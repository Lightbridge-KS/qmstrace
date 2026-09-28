---
summary: The catalogue of scenarios the engine's tests are built from — every behaviour the throwaway stand-in was verified to have across four experiments, the behaviours it silently got wrong that the engine must report, and the Git situations it never met. Each line becomes at least one test; each finding code must be emitted by at least one fixture.
read_when:
  - writing or reviewing a test for the engine, or adding a finding code
  - checking whether a behaviour seen in an experiment is pinned by a test
  - a command misbehaves and the question is "was this ever specified?"
---

# Scenario catalogue

The stand-in's scenarios were run as inline commands while driving the experiments and were
never saved as files. They are recorded here so that they are not lost; the engine's tests
are their durable form. Codes follow the stand-in's numbering and may be renumbered once, in
the findings catalogue, before the first release. Terms follow
[`CONTEXT.md`](../../CONTEXT.md).

**Fixture project.** A hand-made miniature — three requirements, two design elements, two
modules, four tests — kept as plain files and turned into real Git repositories at test time.
Never a bundle of the test bed: opaque in review, and it would carry a tagger's identity.

## Scanning

| Scenario | Expected |
|---|---|
| The same ID declared twice | V01, naming the first declaration |
| A test function defined twice in one file — pytest runs only the second | V01 |
| An ID with this type's prefix, or its stem, that fails the pattern — `REQ-SVC-1`, `REQ-SCV-01` | V02 |
| A link to an ID that exists nowhere | V03 — "declare it here" only if the ID matches *this* repo's pattern; otherwise "it may belong to another repo" |
| A marker pointing at the wrong type of item | V04, naming the types it may point at |
| A marker carried by the wrong type of item — `Satisfies:` under a requirement | V04, naming who may carry it |
| A required field missing; a field value outside its list — spelled exactly, case included | V05, listing the allowed values |
| A test outside a level folder, including `tests/test_x.py` at the top | V06 |
| An item declared in a file that is not scanned for its type | V07, naming the file pattern that would have caught it |
| A test file or a module that cannot be parsed; a file that is not UTF-8 | V08 — never a crash |
| An origin its source does not declare | V09, listing the real ones, in numeric order |
| A heading inside a code fence | ignored |
| Fields written with bold keys; a document with frontmatter | parsed; tolerated |
| `verifies` on a test class | inherited by its tests |
| A parametrised test function | one test case |

## What the stand-in passed silently — the engine reports

| Scenario | Expected |
|---|---|
| `- Origin: TBD` — a required link field with no ID in it; `AGR-1, AGR-X` — one part not an ID | V14, naming the part; the rest of the line still links |
| A marker under the wrong kind of item — `Satisfies:` under a requirement | V04, naming who may carry it; the stand-in dropped it as an unknown field |
| `Implements:` outside the module docstring | not a marker (M2); if that leaves the module unlinked, the gap says why (M3) |
| `verifies` with a non-literal argument, through `pytestmark`, inside `pytest.param(marks=…)`, with no IDs, as a bare decorator, under another name, on something pytest does not collect | V15 — every `mark.<link marker>` in a test module is either read or reported |
| A module with a syntax error | V08, as a test file is |
| An ignore pattern that hides a file with logic in it | `status` shows ignored-file counts per item type |
| A configuration key that is not known | a configuration error — a mistyped `requird` is a hidden rule |
| A coverage rule that needs `Assumes` | a configuration error (D10) |

## Must never look alike

| Looks like | But is | Expected |
|---|---|---|
| Nothing declared yet | An item in a file that is not read | V07, and items *and files* scanned per type in the summary |
| An item declared in the repo | A note the repo ignores — a gitignored `_playground/` quoting a heading | never read: the working tree is what a commit could carry |
| External IDs are fine | Their source could not be reached | *not verified*, in the result line; survives `--quiet` |
| Nothing is frozen | Shallow history, explicit tag exclusions, unavailable objects or not a Git repository | **could not judge** with baselines configured; otherwise judge reachable local tags and always leave remote-tag completeness unverified |
| Two counts that disagree | Test cases versus runs | every count labelled |
| This requirement failed | A test case that verifies several items failed | marked *shared*, with what else it verifies |
| No suspects | A file was touched | a suspect never clears itself |
| An empty project | A revision older than the repo's configuration | refused, with the reason |
| Covered | `Verify-by: inspection` with nothing recorded | listed apart from tested requirements, in `status` and `results` |

## Coverage

- Rules come from data; `where` narrows a rule by a field's value — exactly, as V05 spells it; an
  item missing the field gets V05 and no gap.
- No hidden exemption: a rule without `where` applies to every item of its type.
- A withdrawn item raises no coverage gap, and links with a withdrawn endpoint do not satisfy
  active items' coverage. Validation, traversal and test results remain visible. Withdrawal
  and reactivation of frozen text require a fresh citation (M5a).
- Gaps are listed and the run does not fail while authoring; under the gate it fails — every gap,
  in slice 1.
- Rules are judged on this repo's items; a link to an item not verified here counts; `Assumes`
  counts toward no rule.
- A gap whose link was refused by a violation says to fix that violation first — never to add a
  second line. A gap on a module with an `Implements:` outside its docstring names that line.
- A rule no item type this repo scans can meet is still a gap, and says so; `rules` marks it.
- `rules` prints what is in force and says which part is the project's and which the repo's.
- A rule whose direction contradicts its link type is a configuration error.
- A marker line in Markdown outside every item's section, or written as a table row, is a
  stray: the gap it leaves names it — the Markdown counterpart of the stray `Implements:`
  (recorded for later in M3, built in M9).

## Results

- One explicit pytest report, `xunit1` or `xunit2`, with `testsuite` / `testsuites`, nested suites
  and namespaces. Safe parsing refuses DTDs, entities and external references; malformed,
  unreadable, unsupported and empty reports exit 2 with a next move.
- Exact classname/unparameterized-name matching from scanned node IDs, including nested class
  methods, parameters with brackets, and identity collisions. Missing or ambiguous identities
  are unmatched; no fuzzy matching. Real pytest-generated reports verify both XML families.
- XML entries, distinct full-identity runs, matched/scanned test cases and unmatched run
  identities are labelled separately. Full-identity duplicates combine by worst verdict and
  are counted explicitly; body failure plus teardown error is one run, not inferred retries.
- Test-case precedence `fail > skip > pass`; errors fail, xfail/xpass use their XML outcome.
  Requirement precedence `fail > no-result > skip > pass`; an absent linked test is `no-result`,
  no linked tests is `untested`. Partial parameter variants do not prove a complete run set.
- Direct `verifies` only: a design-only test contributes no requirement verdict. Duplicate links
  do not inflate counts. A shared test names its other targets; global counts count it once.
- Local requirements and locally verified sibling requirements are shown. Sibling ownership,
  unpinned source and declared inspection/analysis methods survive. Unknown-type citations
  stay separate from requirement verdicts; unavailable sources and refused links remain visible.
- Inspection/analysis requirements are separate, including their linked test results without
  claiming verification or approval. Nonpassing details include identities and outcome messages.
- Informational exit 0 for recognized results, including failed tests and partial matches;
  unmatched entries listed. Zero matches exits 2 with no verdicts. Internal faults exit 3.
- Report paths resolve from the effective invocation directory before repo discovery: ignored
  reports, outside files, invocation from subdirectories and `-C` on either side are tested.
- One assessment per usable report; deterministic ordering regardless of XML entry order.
  CLI/help goldens cover partial results, sibling targets and the unavailable-sibling view.
- E1 at `e1-end`, with a schema overlay retaining `Kind`: 62 cases / 78 runs; all seven
  documented mutations flip their targeted requirement to `fail` in restored clones.
- Every view states current-working-tree matching and report commit NOT VERIFIED. No persistence,
  combined reports, freshness claim or retry history.

## The baseline guard — the nine, and what D6 adds

| Scenario | Expected |
|---|---|
| No baseline tag | nothing frozen, said as such |
| Tagged, nothing changed | every covered item frozen |
| A frozen paragraph re-wrapped | **not** a change |
| Frozen text edited, no citation | V10 — put it back, or stop and ask for a change request |
| A cited change request that does not exist | V11 — never invent one |
| A cited change request not yet accepted | V11 |
| Accepted, but the item is missing from `Impacts` | V12 — the impact analysis is incomplete; do not edit the ledger |
| Accepted and listed | clean, with suspects listed |
| A frozen heading deleted; a new item added without a citation | V13; V10 |
| The `Change:` line added or extended, nothing else | not a change |
| `Origin` gains a clause | a change |
| **Only a fresh citation counts** — an item already citing CR-002 is edited again | V10: a permanent citation does not license a later edit |
| A tag pattern from the configuration; a release tag as the product baseline | recognised |
| Two scopes cover the same item | one governing baseline per item, no duplicate findings |
| A release tag from before the repo was traced | the subject is not judged against it — nothing becomes "new since" |
| A feature branch forked before the tag was cut | the tag is not reachable and is not applied |
| A maintenance line | sees its own last release only |
| A lightweight baseline tag | reported as weaker evidence — no tagger, no date of its own |
| The repo's configuration moved between the tag and `HEAD` | the tree at the tag is read with the configuration at the tag |
| The change-request register unreachable | a fresh citation passes with a notice; verified at the ledger's import |
| Detached `HEAD` | works |
| Two governing commits are incomparable after a merge | exit 2, competing tags named |
| Several tags identify one commit | equivalent evidence, one comparison per item |
| New tag has an older date or lower number | ancestry still selects it |
| External schema path at a historical tag | exit 2; never read today's external schema |
| Embedded schema or schema file within the same Git tree | read at the historical commit |
| Traced directory inside a larger repo; linked worktree | same relative paths and comparisons |
| Historical source/configuration is malformed | exit 2, not an empty snapshot |
| Current item type, scope, pattern or subject declaration changes | historical identities are retained |
| New subject after a product release | not frozen by that release |
| Unknown or ambiguous subject key | exit 2; no ownership guess |
| Several fresh citations, one invalid | each offered citation checked; invalid one fails |
| Readable empty register; missing request; malformed request; unavailable register | distinct states; only unavailable register permits an unverified fresh citation |
| Request approval in a fence or prose section | never grants approval |
| Duplicate request metadata; wrong filename ID; malformed Impacts | malformed, never treated as unavailable |
| Repeated CLI invocations and both placements of `-C` | identical deterministic bytes |

## Suspects

- Item-level: a document item's text, a test function's own source, a module's file.
- Downstream of a changed frozen item, **transitively**, grouped by distance; the first hop
  listed in full, the rest counted.
- Existed at the baseline and unchanged → suspect. Existed and edited → still listed, worded
  differently. New since the baseline → not a suspect.
- Appending a comment to a file, or adding a test to it, clears nothing.
- A new applicable upstream baseline clears its chains.
- *Recorded, not fixed:* a field-only change makes everything downstream suspect.
- Baseline and current paths are walked independently; historical-only and current-only
  reach both count, but a path composed only by mixing versions does not.
- Removed roots retain surviving historical dependants beside V13; missing dependants are
  omitted. New intermediate nodes are traversed without becoming suspects themselves.
- Every reason uses its upstream snapshot; a downstream-only baseline cannot clear it.
  Per-root edited state and per-version shortest distances survive merged item counts.
- Overlapping roots, same-commit aliases, cycles and converging paths produce one S01 per
  local dependant, with all reasons. A self-cycle alone never makes its root suspect.
- Withdrawn roots/dependants remain labelled and traversed. Reactivation does not clear review.
- Historical local graph errors name the tag and finding with exit 2. Boundary citations
  remain unverified; today's sibling or external files cannot validate a historical graph.
- Status lists distance one and counts farther distances; check/quiet list every S01.
  Suspects alone never fail strict mode. Repeated runs and both placements of `-C` match bytes.
- Restoring/touching the E3 system-test file or adding an unrelated test preserves existing
  suspect IDs. The field-only change is measured by item identity, not the stand-in's file heuristic.

## Thread and impact

- `thread` prints the marker on each edge; an `Assumes` edge is labelled, and across repos
  carries "judged at import".
- `thread` shows each item once, nearest first, under the link that reaches it first; a second
  link into it is noted as `also` — a test that verifies a requirement and its design element.
- Forward, `thread` crosses an `Assumes` link and goes on; backward, it shows the assumed item and
  stops *(settled in M2b — otherwise `impact` would name unrelated clauses)*.
- If an ordinary backward path also reaches an assumed item, its ancestry is followed even
  when the assumption was discovered first. The ordinary path becomes the displayed parent;
  the assumption remains as `also`. Both `thread` and `impact` retain the legitimate origin.
- `thread` on a sibling's item says that what hangs off it *there* is not shown. Any ID the run
  can see can be threaded: an uncited sibling item, an uncited clause the agreement declares.
- `thread` on an ID nothing here can see — could not judge, with the closest IDs; in a pipeline
  it says the sibling could not be read, never that the item does not exist.
- The header of `thread` says what could not be read, and how many links were refused as
  violations — an empty result never looks like a clean one.
- `impact` takes several IDs and returns their union, deduplicated: downstream grouped by item
  type, upstream origins included, and the `Impacts` line carrying only the item types a
  baseline covers. An ID reserved by a change request and not yet declared is reported as
  such from readable accepted requests (M5a), but still rejects the whole request until every
  start is declared. The output says that it stops at the repo's edge.
- If any starting ID is unseen, `impact` rejects the whole request with exit 2, even when
  other starts are known. It lists the unseen IDs with nearby matches and unavailable-source
  context; it emits neither a partial impact listing nor an `Impacts:` line. M3b never calls
  an unseen ID reserved without reading a change request.
- `impact` lists starts separately from downstream items; cycles, overlapping starts and
  repeated or reordered arguments neither duplicate items nor change output bytes.
- Its candidate includes starts and downstream items of configured baseline types only;
  upstream origins are contextual. Empty candidates and omitted unknown types have explicit
  reasons. No configured baseline is treated as evidence of a currently frozen item.
- Origin types and prefixes come from configuration. Origins of unrelated downstream items
  are not added; an origin supplied as a start is not displayed twice.
- The informational command exits 0 with visible source notices and graph violations;
  missing arguments or invalid `-C` usage exit 2. Each run assesses the workspace once.
- `Assumes` is traversed and counts toward no coverage rule.

## Across repos

- A sibling's item cited from a design element or a test — accepted, and *not pinned* is said.
- A sibling's requirement re-declared locally — V01, "already declared in sibling … cite it; a
  requirement has one home".
- The sibling unreachable, its configuration unreadable, or the siblings not locatable at all (no
  ledger beside the repo) — said in the header. A citation of an ID that is not this repo's own
  then passes as *not verified here*, judged at the ledger's import; an ID matching this repo's
  own pattern is V03 regardless *(decided while planning M2 — a pipeline checks out one repo)*.
- A sibling's own findings are not reported, and its own siblings are never read.

## Configuration

- The project's trace schema by path; as an embedded generated copy; both present.
- The schema unreachable — could not judge, with the next move.
- No configuration — could not judge.
- A local pointer to the ledger absent — every external source *not verified*.
- A verb run in the wrong kind of repo says so and names the right place.
- An extractor the engine does not have; `markdown` with no ID pattern; a type whose IDs are
  derived given one — a configuration error.
- An ID pattern, `id_prefix`, agreement prefix or change-request prefix whose literal start no
  ID can have — underscores, lower case, a space — could not judge, naming the ID shape.
  Found in user acceptance: `^REQ_BCN_\d{2}$` was accepted and every requirement vanished.
  Only the literal start is judged; `^FR\.\d{2}$` still passes.

## Command line

- One golden output per registered command; a meta-test fails when a command has none.
- A meta-test fails when a catalogue code has no fixture that emits it.
- A missing argument, a bad option, an interrupt, a raised exception — each maps to its code.
- `--quiet` prints findings only; notices about what could not be verified still appear.
- The root is found by walking up to the configuration; `-C <path>` runs elsewhere — before the
  verb, as with `git`, or after it; both at once is a usage error.
- Two consecutive runs of any command give identical bytes.

## Setting up a repo

- `init` writes the trace configuration and the stanza between markers, names the subject in
  it, registers the test framework's marker, and is idempotent.
- In a scratch copy of a test-bed repo it reproduces the committed stanza byte for byte.
- Every fenced marker example in the shipped skill parses with the real extractors; every
  finding code has catalogue text. The skill and the tool cannot drift apart.


## M6 — setup

- Fresh repo: explicit subject/key or product/PROD defaults, own schema, no invented sources.
- Existing trace configuration remains byte-identical; ancestor discovery and both `-C`
  placements agree. Repeated runs change no bytes.
- Only managed guide content changes. In-repo symlink works; escaping/aliasing paths,
  conflicting markers, unreadable targets and changed skills are refused before writes.
- A later write failure restores earlier files; a failed restoration names affected files.
- Real pytest accepts `verifies` with strict markers across ini, tox, setup.cfg, native TOML
  and pyproject settings; other settings and markers survive.
- Packaged skill examples parse through the production extractors; break/restore guidance
  remains explicit. The wheel carries every asset byte-for-byte.

## M7b — offline browser

- Optional initial ID selects a thread but exports all visible-to-run items. Unseen IDs and
  an existing/unwritable output path exit 2 without replacing an artifact. `-C` and nested
  invocation resolve output from the effective directory.
- Every node type, including configured external types and unverified untyped nodes, appears
  in filters and columns. Forward/backward reach equals the shared core for every item.
- Only validated current links appear. Type/link/depth controls never recalculate findings;
  hidden counts stay labelled. Search is global and selection works by keyboard.
- Frozen/changed/withdrawn/suspect badges coexist. Historical-only suspects and deleted-root
  findings remain selectable; full S01 roots/tags/version distances/next moves survive.
- Hostile titles/metadata cannot terminate JSON or become DOM markup. Dependencies are
  embedded, output is deterministic, the CSP denies connections, and no source is edited.
- Measured test-bed and larger synthetic layouts are checked interactively before adoption
  of the pinned renderer. Direct file-opening support is a separate browser smoke check.

- Node hover displays the full title as literal text, with a full-ID fallback for untitled
  nodes. Tooltips survive redraws, wrap long text and do not change selection; keyboard
  list/inspector access remains available.

## M9 — rich Markdown

Docs written with the architecture lens skills — numbered and nested headings, tables,
Mermaid. Probes T1–T11 from user acceptance on the beacon test bed, 2026-09-24, become these
scenarios.

| Scenario | Expected |
|---|---|
| A sub-heading inside an item, and an edit under it | the edit changes the item's text: V10 on a frozen item, suspects downstream (T2) |
| A link field under a sub-heading of its item | read as the item's link (T3) |
| A plain heading at the item's level or higher | ends the item |
| A heading whose first word is ID-shaped but of no kind this repo declares (`#### IEC-62304 …`) | a sub-heading; the item goes on |
| A heading that starts with another type's ID, at any depth | ends the item; the lines under it belong to that other item, not to strays |
| `4.2`, `4.2.1.`, `**ID**`, `*ID*`, `_ID_`, `` `ID` `` before the ID; `{#…}`, `{.…}`, `{-}` after the title | declares the item, title without decoration (T4, T6) |
| Renumbering or restyling an item's heading, or a sub-heading numbered as a continuation of the item's number | not a change |
| A sub-heading number that does not continue the item's number (`#### 404 when unknown`) | text: changing it is a change |
| An ID at the end of a heading, declared nowhere | V16, naming where the heading form belongs (T5) |
| An ID at the end of a heading, declared elsewhere | a mention: nothing reported |
| A table row whose first cell is an ID of this repo's kind, declared nowhere | V16: a table declares nothing (T7) |
| A table row `\| Satisfies \| IDs \|`, or a `Satisfies:` line outside every item's section | a stray; the gap it leaves names the row or line (T8) |
| A stray in a table inside an item | named only on that item's outgoing gap |
| An ID-shaped token of no kind this repo declares (`SHA-256`, `UTF-8`, `AGR-1`) later in a heading or in a table | nothing reported |
| A file scanned for two item types | each near-miss reported once |
| A V16 inside a baseline tag's tree | the snapshot is still read — V16 declares nothing |
| A decorated heading with this repo's ID in a document not scanned for its type | V07; when the ID is declared elsewhere, the fix says not to start a heading with it |
| A second `Change:` line in a sub-section | V08, naming the first |
| A marker the item type does not carry, in its sub-section | V04 |
| A fenced example holding a shorter fence of its own | the outer fence stays open until its own closing line |
| A table and a Mermaid diagram inside an item; bold field keys; front matter; a field inside a fence | unchanged: item text; read; ignored; ignored (T1, T6b, T10, T11) |
| IDs mentioned in prose or diagrams, declared nowhere | nothing reported yet — M11 (T9) |
| An item with no sub-heading and no decoration | its digest and title are unchanged by M9 |


## M9b — the schema copy

`qmstrace ledger copy-schema`, run in a ledger, writing into the product repos its schema
names. Each line is at least one test.

| Scenario | Expected |
|---|---|
| A product repo reading the schema by path | its `[schema]` becomes a marked, verified copy; every other byte kept; the parsed configuration equals the by-path one |
| The same command run again | every repo `unchanged`; no byte written |
| The ledger's rules changed since the last copy | the block is replaced; the line says *rules changed* with the old digest |
| Only comments or layout changed in the ledger's schema | the block is replaced; *layout only — rules unchanged* |
| An unmarked copy from before M9b (the beacon products) | the markers are added; the digest is unchanged |
| A copy edited by hand (digest no longer matches) | replaced; the line says so |
| `[subjects]` before `[schema]`, comments above the next table, CRLF line endings | the copy lands where `[schema]` was; the comment block stays with its table; line endings kept |
| A `[` at the start of a line inside a multi-line array or string; `# [not a header]`; a quoted header `[ "schema" . links ]` | never taken for a header |
| No repo names | every repo in `[repos]`; named repos: only those |
| A name not in `[repos]`; a repo missing; no `qmstrace.toml` there | exit 2, naming each; nothing written in any repo |
| A repo holding its own schema; a path to another schema; a copy of another project | exit 2 with the next move; nothing written |
| Conflicting markers; schema tables split around other tables; `schema.x = …` at the root | exit 2; nothing written |
| A copy whose begin marker is present but whose digest line was deleted | could not judge — a marked block is a copy (config) |
| A second repo fails after the first was written | the first is restored; nothing is left half-written |
| Run in a product repo | exit 2, naming the ledger; a product verb run in the ledger names the product repo |
| `-C` before or after the command | the same bytes |
| A product repo checked out alone after the copy | `check` judges it; external sources are *not verified* |
| A baseline tag cut after the copy | the tagged configuration is read and judged; before the copy it could not be |
| The ledger listed as itself (`ledger = "."`, ADR-0001) | skipped, never written or refused — its `qmstrace.toml` stays byte for byte; named alone, nothing is copied |
| A ledger whose `qmstrace.toml` already holds a copy of its own schema | skipped; the line says to replace that `[schema]` with `path = "qmstrace.schema.toml"` |

## M10a — the ledger's check

`qmstrace ledger check`, run in a ledger, judging every repo in `[repos]` as one project — in
the layout of ADR-0001 (`tests/fixtures/split`) and in the older one (`tests/fixtures/mini`).
Each line is at least one test.

| Scenario | Expected |
|---|---|
| The ledger holds the documents; the product repos hold code and tests | every repo read; the ledger's G02–G04 met by the product repos; 0 gaps; the result line says *across N repos* and *working trees, not pinned* |
| The ledger's own `check --strict` in that layout | fails on G02–G04 only; each fix names `qmstrace ledger check` |
| The same test path in two repos | two items, `client:…` and `service:…`; no V01 |
| A cited ID nothing declares | V03 *in any repo of the project*, located from the ledger (`../client/…`); never *not verified* |
| Violations in several repos | each repo's are the ones its own `check` reports with every sibling read |
| A gap only a product repo can meet | the next move names the repos that declare the type — *on the test case in client or service* |
| A listed repo missing or without `qmstrace.toml`; a configuration that cannot be read | exit 2, naming it; every problem at once |
| A repo holding an older copy of the schema | exit 2, naming it and `qmstrace ledger copy-schema <repo>` |
| A traced ledger missing from `[repos]`; two names for one folder; an empty `[repos]` | exit 2, saying which |
| Run in a product repo | exit 2, naming the ledger |
| A frozen document reworded after the ledger's baseline, no request | V10 in the ledger |
| The same, citing an accepted request that lists it | no V10; S01 on the ledger's design elements (both versions) and on the product repos' tests and modules (*current reach only … not pinned; unknown whether edited*) |
| The older layout: a product repo's baseline, its requirement reworded | V10 there; the other repo's test that verifies it is suspect, current reach only |
| `--quiet` | findings and the result line; what could not be verified still shows |
| `-C` before or after the verb; two runs | the same bytes; no absolute path |

