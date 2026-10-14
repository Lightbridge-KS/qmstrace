---
summary: ADR-0004 — qmstrace reads C# with tree-sitter (two runtime dependencies, imported in one private module): a component is a .cs file marked in its first type's /// doc comment; an automated test is an xUnit [Fact]/[Theory] method whose literal DisplayName starts with the ID it verifies; results come from TRX, joined on class and method. Amends the blueprint's dependency rule and settles the per-language choices it left open.
read_when:
  - changing how C# source or xUnit tests are read, or adding another .NET test framework
  - changing how TRX reports are read or matched
  - adding a runtime dependency, or a parser for another language
---

# ADR-0004 — Reading C#

- **Status:** accepted, 2026-10-14
- **Amends:** [codebase blueprint](../structure/codebase-blueprint.md) — "the tool installs with
  Typer and `defusedxml`", the import matrix, and *Future language packages* (which left a new
  language's component granularity, marker syntax and test identities to be chosen);
  [data architecture](../design/data-architecture.md) *Marker syntax v0* (component and test
  rows for C#); requirement REQ-QMT-12
- **Decided by:** the developer, 2026-10-14 (the beacon-dotnet decisions, the parser choice, the
  M12 plan)

## Context

The first C# adopter's tests are xUnit `[Fact]`/`[Theory]` methods with FluentAssertions; each
`DisplayName` starts with a test case's ID, and CI writes TRX. Python's standard library parses
Python; nothing parses C#. The probes on the [beacon-dotnet](../tests/beacon-dotnet.md) bed
showed which shapes are legal and how xUnit and TRX treat each; spike S1 (2026-10-14) showed the
parser below reads all 19 of the bed's files with no error node.

## Decision

- **Parser: tree-sitter** (`tree-sitter` 0.26, `tree-sitter-c-sharp` 0.23.5, MIT, prebuilt
  wheels for macOS, Linux and Windows) as runtime dependencies, imported only in
  `extract/csharp/_syntax.py`. A parse error inside something the extractor reads — a type, a
  method, an attribute, the leading doc comment — is V08; elsewhere it is a notice, so syntax the
  grammar does not know yet (C# 14 extension blocks) does not block a valid file.
- **A component (`csharp-file`) is one `.cs` file**; its ID is its path. Its links are field
  lines (`Implements: DSN-…`) in the leading `///` doc comment of the file's first type, XML tags
  allowed around them. The same line elsewhere is a stray. A mention in prose (`(REQ-…)`) is
  neither.
- **An automated test (`xunit`) is a `[Fact]` or `[Theory]` method** (also `Xunit.`-qualified or
  with the `Attribute` suffix); its ID is `path::Outer::Inner::Method`. Its link is the ID at the
  start of its `DisplayName`, when that is a string literal (regular, verbatim or raw), as the one
  link its item type carries. A `[Theory]` is one automated test; its rows are runs.
- **Reported, never read:** a `DisplayName` that is not a literal (a constant, a concatenation,
  an interpolation), a `[Trait]` named after a link (traits never reach TRX), a custom fact
  attribute, a test inside `#if`.
- **A level** comes from the test's folder, matched without regard to case (`Unit/` → `unit`).
- **Results come from TRX**, read with `defusedxml`; the report reader dispatches on the root
  element (JUnit or TRX). A run's identity is `TestMethod@className` + `@name` — namespace,
  classes joined with `+` — never the `DisplayName`, which changes when a test is reworded. The
  extractor records each test's identities, including the concrete subclasses in the same file
  for a test declared on an abstract base. Outcomes: `Passed` → pass, `NotExecuted` → skip,
  anything else → fail. The reader reads no path, machine or user name, and no output text.

## Evidence

- Spike S1: 19/19 bed files parse cleanly; each `DisplayName` form is its own node kind;
  `#if` wraps what it guards; `///` lines are comment nodes before the type; mypy strict accepts
  the bindings; `uv lock` resolves for every platform. C# 14 extension blocks and
  null-conditional assignment give error nodes, and a test after them is still read.
- The probes (18 shapes, TRX read back) and four sanitised TRX captures from the bed.

## Consequences

- Two runtime dependencies with native wheels; the import matrix allows tree-sitter in
  `_syntax.py` only and `defusedxml` in the report readers only.
- New requirements REQ-QMT-21 (C# source) and REQ-QMT-22 (TRX); REQ-QMT-12 registers the pytest
  marker only when pytest tests are configured. A new design element, DSN-QMT-15.
- `init` has no C# starter yet: on an unconfigured C# repo it would write the Python one.
  Filed as an issue.
- **Docs to follow, in M12d and M12e:** the blueprint (§3, §6, §8, §11); *Marker syntax v0*;
  SKILL.md's C# examples; a manual how-to for a C# repo; the results contract's report formats.

## Rejected alternatives

- **A hand-written lexer.** No dependency, but every C# corner it misses is a silent misread —
  the failure *a marker is read or reported, never dropped* forbids.
- **Roslyn.** Exact, but it needs the .NET SDK wherever qmstrace runs, ledger machines included.
- **`[Trait("verifies", …)]` as the marker.** xUnit-native, but traits never reach TRX, and the
  adopter already writes the ID in the `DisplayName`.
- **JUnit XML through a logger package.** Every adopter would add a package; TRX is what
  `dotnet test` writes.
- **The namespace in the automated test's ID.** Long, and it changes with a namespace.

## Open

- A test declared on an abstract base whose subclasses live in other files: its rows are listed
  as unmatched, with the reason.
- In a repo with one type per file, helper types' files are components with no `Implements:`
  line (G06). Whether a component should be a type rather than a file waits for a real repo.
