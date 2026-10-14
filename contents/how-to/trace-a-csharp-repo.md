# Trace a C# repo

!!! abstract "TL;DR"

    Read the repo's `.cs` files with `csharp-file` and its xUnit tests with `xunit`. A file links
    to its design element with an `Implements:` line in its first type's `///` comment. A test
    names the test case it runs, or what it verifies, at the start of its `DisplayName`, as a
    string literal. Then run `qmstrace check`.

## Steps

1. **Declare the two item types** in the repo's `qmstrace.toml` — components from the source
   files, automated tests from the test files. This is the fixture project's C# agent:

    ``` toml
    --8<-- "fixtures/cases/agent/qmstrace.toml"
    ```

    The type the tests are read into must carry exactly one link in the project's schema —
    `verifies` — because a `DisplayName` names an ID, not a link. A schema that gives it two is
    refused, and says so. `qmstrace init` on a repo with no configuration still writes the
    Python starter ([#38](https://github.com/Lightbridge-KS/qmstrace/issues/38)); edit `[items]`
    as above.

2. **Mark each component in its first type's leading doc comment.** A field line, with XML tags
   around it if you like; the same line in any other comment is not read, and is reported:

    ``` csharp
    --8<-- "fixtures/cases/agent/src/Agent/KeyCheck.cs"
    ```

3. **Start each test's `DisplayName` with its ID.** In a project with a Test Specification,
   that is the test case the test runs; several tests may run one. A `[Theory]` is one
   automated test, its rows its runs:

    ``` csharp
    --8<-- "fixtures/cases/agent/tests/Agent.Tests/Unit/KeyCheckTests.cs"
    ```

    The level comes from the folder the file sits in — `Unit/` is the level `unit`.

4. **Check.**

    ``` sh
    qmstrace check --strict
    ```

## What is not read

Each of these is reported as `V15`, never skipped:

| Written | Why it is not read |
|---|---|
| `DisplayName = Id + "…"`, `$"{Id} …"`, a constant | not a string literal: the tool reads source, it does not evaluate it |
| `[Trait("verifies", "REQ-…")]` | a trait never reaches a test report, so it cannot carry the trace |
| `[SkippableFact]`, any attribute derived from `FactAttribute` | not xUnit's own: its base class is in another file |
| a test inside `#if …` | it may never be built |

A test attribute in a comment is a stray: it links nothing, and the gap it leaves names it.
