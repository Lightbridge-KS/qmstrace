---
name: qmstrace
description: Author and review trace markers in a qmstrace product repo. Read the repository's configuration through qmstrace rules before writing requirements, design, components or tests.
---

# Authoring traced content

Start with `qmstrace status` and `qmstrace rules`. The configuration owns the item names,
ID patterns, paths, fields, link types, baseline scopes and coverage rules. Examples below
use the miniature service schema; substitute the actual project's IDs and fields. Do not
copy a rule from this skill over the configured rule.

Links are authored at the downstream end: design satisfies requirements, components
implement design, and tests verify the items they actually check. Forward reach is derived.
An `Assumes` link carries impact without satisfying coverage. A test verifying a design
never implicitly verifies that design's requirements.

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

A heading that starts with the item's ID, in a file its type is read from, declares a
document item. The item is its section, down to the next heading at the same or a higher
level: sub-sections, tables and diagrams inside it are its text, and its fields and links
may sit in any of them as `Key: value` lines. A section number, bold or backticks around
the ID and a trailing attribute are layout:
`### 1.2 **REQ-SVC-02** — Records survive a restart {#records}`. Tables, diagrams and
prose may name IDs but declare nothing: never write a link as a table cell, and never
declare an item as a table row. Module links belong in the module docstring, never an
ordinary comment. Tests use a direct `pytest.mark.verifies`
decorator with literal IDs. Test cases have function identities; parameter variants are
runs of that case. Put tests in the configured level folders. IDs are never reused.

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
5. Break the relevant behavior in a disposable copy, run its tagged tests, and confirm failure.
   Restore the source and rerun. A marker's existence cannot prove the test detects the defect.
6. Generate a pytest JUnit report and run `qmstrace results REPORT`. Inspect unmatched entries
   and missing results. The report's commit and freshness are not verified by this command.
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
from working trees. Inspection/analysis requirements remain separate from tested requirements.
Use `qmstrace --help`, command help and the finding's next move; the catalogue in
`qmstrace.core.findings.CODES` owns finding descriptions. Never type fabricated dates,
verdicts or test results. A progress tracker may cite an observed commit as a pointer.
