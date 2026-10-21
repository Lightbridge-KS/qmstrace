# Trace a C# repo

!!! abstract "TL;DR"

    Read the repo's `.cs` files with `csharp-file` and its xUnit tests with `xunit`. A file links
    to its design element with an `Implements:` line in its first type's `///` comment. A test
    names the test case it runs, or what it verifies, at the start of its `DisplayName`, as a
    string literal. Then run `qmstrace check`, and read a test run's verdicts from the TRX file
    `dotnet test --logger trx` writes with `qmstrace results`.

## Steps

1. **Let `init` declare the two item types** — components from the source files, automated tests
   from the test files. `qmstrace init` in a repo with no configuration recognises a .NET repo
   by its solution or project file and writes the C# starter, saying so on its first line, and
   writes no `pytest.ini`:

    ``` text
    --8<-- "cli/golden/init-csharp.txt"
    ```

    This is the fixture project's C# agent, whose `[items]` are the starter's with the test glob
    narrowed to its one test project:

    ``` toml
    --8<-- "fixtures/cases/agent/qmstrace.toml"
    ```

    The type the tests are read into must carry exactly one link in the project's schema —
    `verifies` — because a `DisplayName` names an ID, not a link. A schema that gives it two is
    refused, and says so.

    Two things to settle while the paths are still cheap to change. Generated source that the
    build commits — EF Core migrations, designer files — is a component with nothing to
    implement, so each one is a `G06` gap: put those paths in `ignore` rather than marking
    them. And a repo that holds a `pyproject.toml` beside its project file is refused until
    `--language csharp` says which item types to declare.

2. **Mark each component in its first type's leading doc comment.** A field line, with XML tags
   around it if you like; the same line in any other comment is not read, and is reported:

    ``` csharp
    --8<-- "fixtures/cases/agent/src/Agent/KeyCheck.cs"
    ```

    **A file with no type to document** — a Razor page, whose class is generated at build time,
    or a file of top-level statements — is marked in its own leading comment instead. Add
    `src/**/*.razor` to the component type's `files`, as the configuration above does, and mark
    the page in the first `@* … *@` of its **head**: its leading blank lines, comments and
    directives, above the first markup or `@code` block. Either order works — the comment above
    `@page`, or below it:

    ``` razor
    --8<-- "fixtures/cases/agent/src/Agent/Records.razor"
    ```

    A `///` line in a Razor page is a C# comment, which Razor renders as page text, so it links
    nothing — and is reported, as is a `@* … *@` marker below the head. A file of top-level
    statements is marked in the `//` or `///` block it opens with:

    ``` csharp
    --8<-- "fixtures/cases/agent/src/Agent/Program.cs"
    ```

    A file that **does** declare a type is never read this way: a marker above its first type
    stays a stray, so there is one place to look per file.

3. **Start each test's `DisplayName` with its ID.** In a project with a Test Specification,
   that is the test case the test runs; several tests may run one. A `[Theory]` is one
   automated test, its rows its runs:

    ``` csharp
    --8<-- "fixtures/cases/agent/tests/Agent.Tests/Unit/KeyCheckTests.cs"
    ```

    The ID ends where an ID in prose ends: `TC-SVC-01.1/O03 …` and `TC-SVC-01.1: …` both
    link `TC-SVC-01.1`. A letter, digit, hyphen or dotted number straight after it makes it no
    ID — `TC-SVC-01.1a …` is reported as `V14`. The level comes from the folder the file sits
    in — `Unit/` is the level `unit`.

4. **Check.**

    ``` sh
    qmstrace check --strict
    ```

5. **Read a test run's verdicts.** Write a TRX file, then read it as a separate command, so a
   failing run does not skip it:

    ``` sh
    dotnet test tests/Agent.Tests --logger "trx;LogFileName=report.trx" --results-directory .
    qmstrace results report.trx
    ```

    A run is matched by its class and method, never by its `DisplayName`, so rewording a test
    keeps its results and renaming its method does not. Each row of a `[Theory]` is a run of
    one automated test. Nothing of the file's build paths, machine or user names, or output is
    shown. In this run one `[Fact]` was skipped and one `[Theory]` row failed:

    ``` text
    --8<-- "cli/golden/results-trx-mixed.txt"
    ```

    With several test projects, write one TRX per project, each with its own name, and give
    `results` all of them. They are read as one; a run in two files keeps its worst verdict:

    ``` sh
    dotnet test tests/Agent.Tests --logger "trx;LogFileName=unit.trx" --results-directory TestResults
    dotnet test tests/Agent.IntegrationTests --logger "trx;LogFileName=integration.trx" --results-directory TestResults
    qmstrace results TestResults/*.trx
    ```

    Here, two runs of the agent's tests read together:

    ``` text
    --8<-- "cli/golden/results-trx-several.txt"
    ```

    !!! warning "One `LogFileName` for a whole solution overwrites"

        Given a solution and a fixed `LogFileName`, every project writes the same file and
        only the last one's results remain, without warning. qmstrace cannot see the overwrite;
        the header's entry count per report is where the shortfall shows.

## What is not read

Each of these is reported as `V15`, never skipped:

| Written | Why it is not read |
|---|---|
| `DisplayName = Id + "…"`, `$"{Id} …"`, a constant | not a string literal: the tool reads source, it does not evaluate it |
| `[Trait("verifies", "REQ-…")]` | a trait never reaches a test report, so it cannot carry the trace |
| `[SkippableFact]`, any attribute derived from `FactAttribute` | not xUnit's own: its base class is in another file |
| a test inside `#if …` | it may never be built |

A test attribute in a comment is a stray: it links nothing, and the gap it leaves names it.
