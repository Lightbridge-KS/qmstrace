# qmstrace results

!!! abstract "TL;DR"

    `qmstrace results REPORT...` matches pytest JUnit reports or TRX files, read as one, to
    scanned automated tests, and follows their `verifies` links to requirements — directly, or through the test cases they
    run. It shows requirement verdicts, the test cases on the way, missing results, shared tests
    and unmatched entries. Exit `0` means a results view was produced, even if tests failed.
    The report's commit is not verified.

## Synopsis

``` text
--8<-- "cli/golden/help-results.txt"
```

A relative report path starts at the invocation directory, or the directory supplied with
`-C`, even when qmstrace discovers the repository above it. `-C` works before or after the
command. An explicitly supplied report is read even when Git ignores it or it is outside
the repository. A report is shown by its path from the repository root, or, outside the
repository, by its file name alone; two reports that would be shown alike are refused, as is
a report given twice.

## Several reports

Several reports are read as one, so `qmstrace results TestResults/*.trx` reads each test
project's file in one run. A run reported in two files is one run: it keeps the worst verdict
and counts once as a duplicate, as a repeated entry within one file does. The order the reports
are given in changes nothing. With more than one report, the header lists each one with its
entry count, so a missing or truncated file is visible, and every run that did not pass names
the reports it was in. Each run also keeps the sha256 of its reports' bytes. One report
prints the same view as before.

## Matching and counts

The report's root element decides how it is read: `testsuite` or `testsuites` is pytest JUnit
XML, and TeamTest's `TestRun` is a TRX file. Any other root is refused, as are DTDs, entities
and external references.

**JUnit.** The reader accepts pytest's default output in either `xunit1` or `xunit2` format,
including nested suites and XML namespaces. Matching is exact: the report's `classname` and
test name without parameters must identify one scanned pytest test. Class methods retain their
class names. Parameter IDs may contain brackets.

**TRX**, as `dotnet test --logger trx` writes it. Matching is exact on the class and method
the result's test definition names: the class namespace-qualified, a nested class joined to
its outer class with `+`. The `DisplayName` plays no part in matching, so rewording a test does
not unmatch it; renaming or moving its method does. A result's name is its `testName`, so each
row of a `[Theory]` is a run of one automated test. Only the class, the method, the name, the
outcome and the first line of an error message are read: a TRX file's paths, machine and user
names, output, stack traces and attachments are never shown. With several test projects,
`dotnet test` writes a TRX for each: give `results` every one of them.

Custom class-name prefixes, identity collisions and entries with missing identity attributes
are reported; qmstrace does not guess a match.

An **automated test** is a scanned test function or test method. A **reported run** is a
distinct full `(classname, name)` identity, including parameters. Duplicate XML entries for the same full
identity are combined using the worst verdict and counted explicitly. This includes pytest's
separate entries for a body failure and teardown error. Duplicate entries do not establish
retry history. Global counts count each automated test once, even when requirement rows
overlap.

A partial set of parameter variants does not prove every possible variant ran.

## Verdicts

| Subject | Rule |
|---|---|
| Automated test with reported runs | Worst of `fail`, `skip`, `pass`, in that order |
| Automated test absent from the report | `no-result` |
| Test case, or requirement, that automated tests reach | Worst of their verdicts: `fail`, `no-result`, `skip`, `pass` |
| Test case, or requirement, that no automated test reaches | `untested` |

XML `error` and `failure` both mean `fail`. Expected failures and unexpected passes follow
pytest's XML representation: qmstrace adds no separate xfail policy. In a TRX file, `Passed`
means `pass` and `NotExecuted` means `skip`; any other outcome — `Failed`, `Timeout`,
`Aborted`, `Inconclusive` — or none means `fail`, and the outcome is shown beside the run.

A verdict follows `verifies` links: from an automated test to what it verifies, and on
through a test case to what the test case verifies. A requirement's row names the test cases
its verdict came through. A test case no automated test runs adds nothing: it neither passes a
requirement nor holds one back. A design element carries `Satisfies`, not `verifies`, so a test
of a design element does not imply a verdict for its requirements; such tests and test cases are
listed apart. Nonpassing test details name the affected runs and show outcome messages. A shared
test names the other items it verifies.

Requirements with no applicable incoming-`verifies` coverage rule appear separately, whether
their `Verify-by` value is `inspection`, `analysis`, `demonstration` or another configured method.
The rule's entire `where` condition applies; its code has no special meaning. A missing or
invalid method appears as `unspecified` or its authored value and remains a validation finding.
Linked direct tests and test-case paths are shown as **test evidence only**; even a pass does not
complete or approve the declared verification method.

For example, a requirement declared `Verify-by: demonstration` with a passing linked test
appears in the separate section:

``` text
--8<-- "cli/golden/results-demonstration.txt"
```

## Partial report example

This miniature service report contains a skipped design test, a shared failing test with a
teardown error, an absent test, and an entry that no longer matches a scanned test:

``` text
--8<-- "cli/golden/results-partial.txt"
```

A partial report retains recognized results and lists unmatched identities. A requirement
with a known failure remains `fail` even when another directly linked test has no result.

## Through test cases

In a project with a Test Specification, the automated tests name the test case they run, and
the test case names what it verifies. Run from the product repo, the view reads the ledger's
test cases with their own links — read for verdicts only, never counted as this repo's links:

``` text
--8<-- "cli/golden/results-cases.txt"
```

## From a TRX file

The fixture project's C# agent runs the same test cases from xUnit. In this TRX file one
`[Fact]` was skipped and one row of a `[Theory]` failed; each run is shown by its `testName`,
with its outcome and the first line of its message:

``` text
--8<-- "cli/golden/results-trx-mixed.txt"
```

## Repository boundary

Local tests can verify a sibling's requirement. The output labels its owner and the unpinned
working-tree source; it does not claim to include the sibling's own tests:

``` text
--8<-- "cli/golden/results-sibling.txt"
```

When the sibling cannot be read, a cited ID has an unknown type. Its linked test results are
shown separately and are never presented as requirement verdicts:

``` text
--8<-- "cli/golden/results-in-a-pipeline.txt"
```

Unread sources and graph violations remain visible. Matching uses the current working tree;
qmstrace does not verify which commit produced a report. Results are not persisted.

## Exit codes

- `0`: at least one scanned test matched and the informational view was produced. Failed
  tests, partial matches and graph findings do not change this code.
- `2`: usage or configuration prevented reading, or the report was unreadable, malformed,
  unsafe, empty, unsupported, or matched no scanned tests. The diagnostic suggests a next step.
- `3`: an internal fault.

Use the test runner's exit code — pytest's, or `dotnet test`'s — to gate test success and
[check](check.md) to gate traceability. See
[Generate and interpret a pytest report](../../how-to/read-test-results.md) and
[Trace a C# repo](../../how-to/trace-a-csharp-repo.md) for the workflows.
