---
summary: Accepted design for M7b's local, read-only trace browser — offline HTML, graph interactions, evidence limits, architecture and deferred project-wide views; pinned renderer and measured local-view limits.
read_when:
  - planning or implementing M7b's interactive trace graph
  - deciding how graph direction, findings or historical evidence appear visually
  - extending the local browser to project-wide traversal at pins
---

# Local trace browser

**Implemented for review: 2026-09-24.** M7b follows M7's product test-bed
migration and precedes M8's slice-1 closure. This brings forward
the local part of the PRD's static trace-browser capability; the project-wide audit view
follows slice 2's traversal at pins.

The primary user is a developer inspecting relationships and findings in a product repo.
The browser helps locate an item, follow its thread and understand why it needs attention.
It presents the engine's assessment; it does not establish approval or record review.

## Delivery and command shape

Generate a single self-contained HTML file that works offline, without a server or CDN.
Interaction changes only the view. Generation assesses the workspace once, writes the
file without silently overwriting an existing file, and prints its location.

Command shape (ID is optional; --out is required):

```sh
qmstrace graph --out trace.html
qmstrace graph REQ-SVC-01 --out requirement.html
```

Generation is informational: a usable assessment may contain violations, gaps and suspects
and still exit 0. Usage or inability to assess retains exit 2; internal faults retain exit 3.
Keep the existing effective-directory and `-C` conventions. The output is a generated
working-tree snapshot, not an issued document or a live view; regeneration reads new content.

**Rejected:** a running web service or an editor in the first version. Neither is necessary
for local exploration, and editing would create another authoring surface and source of truth.

## Layout and interactions

Use a stable layout with physics off by default. Columns follow configured item types;
the familiar origin / requirement / design / component / test sequence is an example,
not a hard-coded schema. Direct links can skip columns, and cycles remain representable.

```text
Search by ID or title           Scope: all / selected thread
----------------------------------------------------------
Origins | Requirements | Design | Components | Test cases
                     Interactive graph
----------------------------------------------------------
Selected item                       Findings and evidence
ID, title, type, file:line           Gaps / violations / S01
Authored links                      Baseline and root reasons
                                    Ownership / source limits
----------------------------------------------------------
Working-tree snapshot · sibling not pinned · unread sources
```

- Search and select an item; highlight its forward and backward trace with visible-depth
  controls. Match the existing traversal semantics, including backward `Assumes` boundaries.
- Zoom, pan and drag; filter item/link types with visible counts of hidden items.
  Filtering does not recalculate coverage or make findings disappear from the assessment.
- Selecting a link shows the exact authored relationship and declaration location.
- Selecting a finding focuses its item and shows the existing diagnostic and next move.
  Findings without a current graph item remain accessible in the findings list.
- Provide a keyboard-accessible item list alongside graph navigation. Essential content
  is available without hover.

Retain authored arrow direction: `test → requirement` means the test verifies the
requirement. Forward-trace highlighting shows propagation separately; never reverse an
arrow while retaining a label that asserts the opposite relationship.

Use consistent type colors or shapes, plus separate text badges for frozen, changed,
withdrawn and suspect. These properties can coexist. Color alone cannot communicate them.
A suspect means **needs review**, not outdated, failed or necessarily in need of editing.

**Rejected:** continuously moving force layout as the default, which impedes comparison;
assuming a DAG or a mandatory hop through every item type; one mutually exclusive node
color for all findings and item properties.

## Evidence and scope

The first version includes current validated links, ownership, source notices, gaps,
violations and suspect badges. Refused links must not appear as valid graph connections;
their findings remain visible. Source limits remain visible when the graph is filtered:
sibling working trees are not pinned, unavailable sources are not verified, and traversal
stops at this repo's edge. Do not imply project-wide completeness.

The inspector exposes every S01 root, governing baseline, historical/current reach and
distance, and unchanged/edited state. Historical-only suspects remain discoverable even
when disconnected in today's graph. Passing tests or editing a dependant cannot clear them.

**Do not overlay historical and current links in the first version.** Such a picture could
suggest a path assembled from different graph versions, which M5b explicitly forbids.
A later comparison view selects one root and its governing baseline and presents separate
graph versions; a downstream-only baseline does not clear the root's chain.

Defer live refresh, graph editing, recorded-review clearance and test-result overlays.
A later results view must require an explicitly supplied report and retain M4's report
matching and unverified-freshness limits. Cross-repo traversal at pins requires slice 2.

## Architecture and renderer choice

```text
Workspace assessment → presentation-data projection → offline HTML viewer
```

Reuse `Assessment`, `TraceGraph` and structured baseline/suspect values. Python owns
judgment and traversal semantics; browser code owns layout, selection and filtering.
Any browser-side traversal must be parity-tested against the shared core, rather than
silently introducing different reach rules. This internal payload does not require a
public JSON CLI or a persistence layer. Evidence remains pointers, not embedded source archives.

**Renderer: vis-network 10.1.2, standalone UMD, embedded under its MIT license.**
Fixture, two-repo and 1,000-node synthetic interaction checks support this choice. Package
assets retain the license, version, source URL and checksum. There is no Python runtime
library or browser network dependency; Node.js 22+ runs built-in control tests in development.
**Rejected:** a custom force simulator, because fixed-position columns and maintained
pan/zoom/selection meet this local view without owning physics code.

The CLI accepts one optional initial ID. It exports the entire visible-to-run graph even
when initially focused; this is explicit in help and the manual. Python precomputes compact
indexed forward/backward reach for every included node using `TraceGraph`. This prevents a
second implementation of ancestry boundaries in JavaScript. The cost can grow quadratically;
1,000 nodes / 999 links produced approximately 5.9 MB in under one second in the local
synthetic check. This is a measured example, not a performance guarantee or project-wide
scale promise. A future lazy traversal implementation must prove parity before replacement.

The default layout uses configured external types followed by configured item types, then
any remaining visible types. Colors denote type; text badges coexist. The canvas shortens
long IDs; the searchable keyboard list and inspector retain the full IDs and source paths.
Explicit zoom, fit and reset controls complement pointer pan/zoom/drag. Source notices and
findings remain independent of graph filters. No source archives are embedded.

Verification is recorded in [slice-1 closure](../tests/slice-1-closure.md): CLI/core reach
parity, control tests, historical-only finding access, hostile text, working-tree test-bed
replays and browser inspection. Direct `file://` opening was blocked by the verification
browser's URL policy, so that smoke check is unverified; all assets are embedded and the
inspected localhost document has no external scripts or connection permission.

## References

- [Surface contract](surface-architecture.md) and [data architecture D7](data-architecture.md):
  trace, finding and suspect meanings remain authoritative.
- [targets visualization](https://docs.ropensci.org/targets/reference/tar_visnetwork.html):
  hierarchical layout, neighborhood highlighting and depth controls are interaction
  inspiration; its DAG and outdated-target semantics do not transfer to qmstrace.
- [vis-network documentation](https://visjs.github.io/vis-network/docs/network/):
  graph interaction and standalone bundle candidate.
