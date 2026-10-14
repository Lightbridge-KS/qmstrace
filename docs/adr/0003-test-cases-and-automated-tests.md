---
summary: ADR-0003 — a test case is an entry in a Test Specification (a Markdown document, planned and baselined); the code that runs one — a pytest function, an xUnit method — is an automated test. Automated tests verify test cases or verify directly; a verdict follows verifies links, so it reaches a requirement through its test cases but never through a design element. Amends the chain, marker syntax v0 and the results contract.
read_when:
  - changing what a test case is, how tests link to it, or how results give verdicts
  - designing a test-case document, or the item types a project's schema declares for tests
  - a requirement's verdict seems wrong when its tests run through a test case
---

# ADR-0003 — Test cases and automated tests

- **Status:** accepted, 2026-10-14
- **Amends:** [data architecture](../design/data-architecture.md): the chain, the D5 table
  ("a `verifies` tag on the test"), *Marker syntax v0*'s Test case row, and "A test case is a
  *test function*"; [surface architecture](../design/surface-architecture.md) *Results
  contract*: "Only direct `verifies` links contribute"; requirement REQ-QMT-10
- **Decided by:** the developer, 2026-10-14 (the beacon-dotnet decisions and the M12 plan)

## Context

The glossary already defines a **test case** as *the planned, baselined description of a test
and what it verifies*. The design, though, made it the test function: one pytest function, one
test case, links on the function.

The first C# adopter works the way the glossary reads. Its test cases are planned in a
controlled document (ISO/IEC 29110's *Test Cases and Test Procedures*), each with an ID; several
xUnit methods run one test case, each naming it at the start of its `DisplayName`, and the test
case passes only when all of them pass. Its auditor's question is *which planned test cases
verify REQ-04, and did they pass?* — not *which methods*.

`results` cannot answer it: a requirement's verdict counts only tests that `verifies` it
directly, and only requirements get verdicts.

## Decision

- **A test case is an entry in a Test Specification**: a Markdown document, like a
  requirements specification, with a heading `### <ID> — <title>` per test case and a
  `verifies:` line naming what it verifies. Its ID is authored. It is planned and can be
  baselined like any authored item.
- **An automated test is the code that runs a test case**: a pytest function, an xUnit method.
  Its ID is derived from where it is. It verifies a test case — or, in a project with no Test
  Specification, a requirement or design element directly. The schema decides which.
- **The chain gains one step:**

  ```
  automated test ─verifies→ test case ─verifies→ requirement | design element
  automated test ─verifies→ requirement | design element            (still allowed)
  ```

- **A verdict follows `verifies` links.** An item's verdict is the worst verdict of every
  automated test that reaches it along `verifies` links, directly or through other items'
  `verifies` links (`fail > no-result > skip > pass`). Requirements get verdicts; a test case is
  shown with its own. A design element carries `Satisfies`, not `verifies`, so **no verdict
  flows through a design element** — the old rule holds by the schema, not by a type name.
- **A test case no automated test runs** is `untested` and contributes nothing to what it
  verifies, as a requirement with no linked test always was: in one repo's view its tests may
  sit in another repo. The coverage rules say so instead (below).
- **Coverage rules are data, as before.** A project with a Test Specification declares, for
  example: an automated test verifies something (G07), a test case verifies something (G08), and
  an automated test runs every test case (G09).
- **A gap's next move names every way the link can be made** — on the test case in the ledger,
  and on an automated test in each repo that has them — never only the first.
- **Names.** qmstrace's own schema and its starter call pytest functions `automated_test`;
  `test_case` is the Test Specification's entry. Item type names stay data; an existing schema
  that calls pytest functions `test_case` keeps working.

## Evidence

On the [beacon-dotnet](../tests/beacon-dotnet.md) bed: 53 xUnit methods run 49 test cases, and
the (level, target) pairs they reach equal the Python agent's 53 tests exactly. With undotted
IDs, today's engine reads the Test Specification by configuration alone: G02 gaps 21 → 11 and
G04 13 → 8, met through test cases, and `thread` walks from a test case back to its
requirements and origin clauses. Breaking the backoff ceiling fails only the two tests of
`TC-BAG-03.4`, which verifies a design element — so no requirement's verdict changes, and the
failure must still be shown.

## Consequences

- `results` follows `verifies` links through test cases; its output names them, and shows
  test cases and automated tests that reach no requirement in a section of their own.
- A product repo's local `results` needs the ledger's test cases' own links — sibling items'
  declared links become visible to it, without counting as the product repo's links.
- REQ-QMT-02 (markers) and REQ-QMT-10 (results) change under CR-003.
- **Docs to follow:** in M12b — the chain, *Marker syntax v0* (rows for a test case and an
  automated test), the D5 table, the glossary; in M12c — the results contract and the manual's
  results pages.

## Rejected alternatives

- **The `DisplayName` names a requirement or design element directly.** Cheapest, and it still
  works, but the adopter's test cases stay outside the trace: qmstrace could say which methods
  verify REQ-04, not which planned test cases do.
- **The test case's ID is the automated test's own ID**, every method naming it aggregated into
  one item. One ID would be declared by many methods in code and planned again in a document,
  and each method's own result would be lost.
- **A verdict crosses exactly one test-case step.** An arbitrary depth; following `verifies`
  links, stopped by `Satisfies`, is simpler and gives the same verdict on every shape seen.
- **A test case with no automated test counts as `no-result`.** In one repo's `results`, every
  requirement whose test cases are run from another repo would read as not run.

## Open

- A test case may verify another test case: the schema's `from`/`to` lists cannot say "test
  cases verify requirements and design elements only". Targets that depend on the source type
  would close it.
