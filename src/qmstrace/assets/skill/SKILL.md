---
name: qmstrace
description: Author and review trace markers in a qmstrace product repo. Read the repository's configuration through qmstrace rules before writing requirements, design, components or tests.
---

# Authoring traced content

Start with `qmstrace status` and `qmstrace rules`. The configuration owns the item names,
ID patterns, paths, fields, link types, baseline scopes and coverage rules. Examples below
use the miniature service schema; substitute the actual project's IDs and fields. Do not
copy a rule from this skill over the configured rule.

`REQ-SVC-01` and `REQ-SVC-02` are example IDs for two distinct requirements. In this
example, `REQ` is the configured requirement prefix, `SVC` is the subject key for the
service, and `01` / `02` distinguish the items; they do not indicate priority or status.
These are not built-in or reserved IDs. Read `qmstrace rules` for the actual project's
ID patterns and subject keys, and `qmstrace status` for its declared requirements. Replace
the example IDs in commands with existing project IDs; mentioning an ID does not declare it.

Links are authored at the downstream end: design satisfies requirements, components
implement design, and tests verify the items they actually check. Forward reach is derived.
An `Assumes` link carries impact without satisfying coverage. A test verifying a design
never implicitly verifies that design's requirements.

## Driving the CLI as an agent

Discover flags with `qmstrace --help` and leaf help. Prefer `--json` for assessment data:

```sh
qmstrace paths --json
qmstrace rules --json
qmstrace status --json
qmstrace thread REQ-SVC-01 --json
qmstrace impact REQ-SVC-01 REQ-SVC-02 --json
qmstrace check --strict --json
```

Use actual project IDs. `status` is the overview; `check` gives the complete work queue.
Request a thread or impact instead of dumping the entire graph. JSON is explicit; pipes
otherwise receive plain text. `NO_COLOR=1` gives plain reports and help. Both root and
leaf placements of `--json`, `-C` and `--workspace` are supported; give each once.

Parse the JSON even on a nonzero exit. Exit `0` means completed (results may contain failed
tests); `1` means the check failed; `2` means usage or inability to judge; `3` means an
internal fault. Branch on `exit_code` and `error.category`, not English messages. Read
`notices`, findings and their `next_move`; never suppress evidence limits. `--quiet` does
not remove JSON findings. Capture the command's exit before a `jq` pipeline replaces it.

`qmstrace results REPORT... --json` retains unmatched entries and unverified report
freshness. For project scope, run `qmstrace -C LEDGER ledger check --strict --json` in the
ledger trace root; a workspace map does not redirect a product invocation there.
`ledger table` already emits `qmstrace.table/2`; assessment commands emit `qmstrace.cli/2`.
Consumers ignore unknown additive fields and check the format version. The manual's
*CLI JSON format* reference defines the schema and command payloads.

`init`, `graph` and `ledger copy-schema` write files and reject `--json`; use them only for
an intended writing task. No command's successful completion certifies semantic truth,
report freshness, complete evidence or human approval.

## Repository identity and workspace profiles

In a v2 `qmstrace.toml`, `repo` is this checkout's stable project member name and
`workspace_profile` names its default local map. The copied/shared schema lists names,
not developer paths. Run `paths --json` before assuming a sibling or ledger is available.
Explicit `--workspace FILE`, `QMSTRACE_WORKSPACE` and the nearest ancestor map override
`~/.qmstrace/workspaces/<workspace_profile>.toml`. One map is selected; maps never merge.
An absent implicit profile permits local evidence only. An invalid profile or binding is
exit 2; ledger operations require every assessed member. V1 inputs retain their original
tracked defaults and discovery. A map never repairs a schema reference or historical tag.

CLI `/2` locations contain `repo`, an internal `path` and optional `line`; `repo: null`
keeps a legacy/unidentified source explicit. They are evidence labels, not filesystem paths
to join to the invocation directory. Do not change an ID when its checkout moves. Table
`/2` uses the same logical source boundary. Both output versions apply to v1 and v2 inputs.
Consumers needing output `/1` remain pinned to 0.2.0; no legacy output flag is provided.

`init` still creates v1 starters. V2 setup is explicit: prepare the schema/local identity
headers and map, use `ledger copy-schema` transactionally, then refresh managed guidance
with `init`. Preserve local skill edits before using the documented refresh procedure;
never delete workspace maps or rewrite baseline tags as part of migration.

## Marker examples

```markdown
### REQ-SVC-01 — Calls require a key
A call without a valid key is refused.

- Category: security
- Origin: AGR-1
- Verify-by: test
```

```markdown
### 2.1 DSN-SVC-01 — Check the key before dispatch
Every call passes the key check before any handler runs.

#### Traceability
- Satisfies: REQ-SVC-01
```

```python
"""Key checks.

Implements: DSN-SVC-01
"""
```

```python
import pytest


@pytest.mark.verifies("REQ-SVC-01", "DSN-SVC-01")
def test_a_call_without_a_valid_key_is_refused():
    assert True  # syntax example only; replace with a real behavioral assertion
```

```markdown
### TC-SVC-01.1 — A call without a valid key is refused
verifies: REQ-SVC-01
```

In a project with a Test Specification — a Markdown file of test cases in the ledger, read as
the schema says — a test case is declared like any document item and names what it verifies.
The automated tests then name the test case they run, `@pytest.mark.verifies("TC-SVC-01.1")`,
and several may run one; `qmstrace rules` says which a project uses.

```csharp
/// <summary>Key checks.</summary>
/// <remarks>
/// Implements: DSN-SVC-01
/// </remarks>
public static class KeyCheck { }
```

```razor
@* Implements: DSN-SVC-02 *@
@page "/records"

<h1>Records</h1>
```

```csharp
public class KeyCheckTests
{
    [Fact(DisplayName = "TC-SVC-01.1 a call without a valid key is refused")]
    public void Admits_NoKey_IsFalse() { }
}
```

In a C# repo a file's link is a field line in its first type's leading `///` comment, and an
xUnit `[Fact]` or `[Theory]` names the ID it verifies at the start of its `DisplayName`, as a
string literal. A `[Trait]` never reaches a test report and is not read. A file with **no type
to document** is marked in its own leading comment instead: a Razor page in the first
`@* … *@` of its head — its leading blank lines, comments and directives, above the first
markup or code block — and a file of top-level statements in the `//` block it opens with. A
marker a Razor page renders as text, or one below its head, is reported.

A heading that starts with the item's ID, in a file its type is read from, declares a
document item. The item is its section, down to the next heading at the same or a higher
level: sub-sections, tables and diagrams inside it are its text, and its fields and links
may sit in any of them as `Key: value` lines. A section number, bold or backticks around
the ID and a trailing attribute are layout:
`### 1.2 **REQ-SVC-02** — Records survive a restart {#records}`. Tables, diagrams and
prose may name IDs but declare nothing: never write a link as a table cell, and never
declare an item as a table row. Module links belong in the module docstring, never an
ordinary comment. Tests use a direct `pytest.mark.verifies`
decorator with literal IDs. An automated test is a test function; parameter variants are
runs of it. Put tests in the configured level folders. IDs are never reused.

## Authoring and change loop

1. Read status, rules and `thread ID`. Establish the actual requirement and its origins.
2. For frozen work, run `impact ID…`, review the candidate Impacts list and obtain the
   project's accepted change request before editing. A reservation does not declare an item.
   Cite each controlled change with a fresh `Change: CR-…` under its heading. Never infer
   acceptance from a missing register; retain NOT VERIFIED evidence limits.
3. Write requirement → design → component → tests. Link only true relationships. A shared
   test may verify several items; place the verdict on the item whose owner can act on it.
   A configuration option changes the requirement even if its default leaves behavior alone.
4. Run `check`; correct violations and explain gaps. Read each next move instead of hiding
   or deleting a marker to silence the finding.
5. Break the relevant behavior in a disposable copy of the repo — never the checkout you work
   in — run its tagged tests there, and confirm they fail; then delete the copy. A marker's
   existence cannot prove the test detects the defect.
6. Generate a report — pytest `--junitxml=report.xml`, or `dotnet test --logger trx` — and run
   `qmstrace results REPORT`. Inspect unmatched entries and missing results. The report's
   commit and freshness are not verified by this command.
7. Run `check --strict`. Review every suspect against each upstream root and governing tag;
   an edit, passing test or file touch cannot record review. Record review in the project's
   existing process. The engine has no automatic approval or review-clearance marker.

Retire document items with `Status: withdrawn`, preserving their identity and links. A
frozen withdrawal still needs a fresh change request. Withdrawn items are coverage-exempt,
but traversal and review evidence remain.

## Evidence limits

No command verifies semantic truth, report freshness or human approval merely by exiting 0.
Source notices survive quiet output. Siblings are working trees, not pins; traversal ends at
this repo's edge. Where the whole project must be judged — coverage met in another repo,
suspects across repos — `qmstrace ledger check`, run in the ledger, reads every repo together,
from working trees. Requirements without an applicable incoming `verifies` coverage rule are
listed apart in `status` and `results`; linked test outcomes are evidence, not approval of
another declared verification method.
Use `qmstrace --help`, command help and the finding's next move; the catalogue in
`qmstrace.core.findings.CODES` owns finding descriptions. Never type fabricated dates,
verdicts or test results. A progress tracker may cite an observed commit as a pointer.
