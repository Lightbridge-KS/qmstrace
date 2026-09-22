# qmstrace results

!!! abstract "TL;DR"

    `qmstrace results REPORT` matches one pytest JUnit report to scanned test cases and their
    direct `verifies` links. It shows requirement verdicts, missing results, shared tests and
    unmatched entries. Exit `0` means a results view was produced, even if tests failed.
    The report's commit is not verified.

## Synopsis

``` text
--8<-- "cli/golden/help-results.txt"
```

A relative report path starts at the invocation directory, or the directory supplied with
`-C`, even when qmstrace discovers the repository above it. `-C` works before or after the
command. An explicitly supplied report is read even when Git ignores it or it is outside
the repository.

## Matching and counts

The reader accepts pytest's default JUnit output in either `xunit1` or `xunit2` format,
including nested suites and XML namespaces. The report must have a `testsuite` or `testsuites`
root. DTDs, entities and external references are refused.

Matching is exact: the report's `classname` and test name without parameters must identify
one scanned pytest test. Class methods retain their class names. Parameter IDs may contain
brackets. Custom class-name prefixes, identity collisions and entries with missing identity
attributes are reported; qmstrace does not guess a match.

A **test case** is a scanned test function. A **reported run** is a distinct full
`(classname, name)` identity, including parameters. Duplicate XML entries for the same full
identity are combined using the worst verdict and counted explicitly. This includes pytest's
separate entries for a body failure and teardown error. Duplicate entries do not establish
retry history. Global counts count each test case once, even when requirement rows overlap.

A partial set of parameter variants does not prove every possible variant ran.

## Verdicts

| Subject | Rule |
|---|---|
| Test case with reported runs | Worst of `fail`, `skip`, `pass`, in that order |
| Test case absent from the report | `no-result` |
| Requirement with directly linked test cases | Worst of `fail`, `no-result`, `skip`, `pass` |
| Requirement with no directly linked test cases | `untested` |

XML `error` and `failure` both mean `fail`. Expected failures and unexpected passes follow
pytest's XML representation: qmstrace adds no separate xfail policy.

Only direct `verifies` links count. A test of a design element does not implicitly verify
that design element's requirements. Nonpassing test details name the affected runs and show
outcome messages. A shared test names the other items it verifies.

Inspection and analysis requirements appear separately. Their linked test results, if any,
do not change their verification method or establish approval.

## Partial report example

This miniature service report contains a skipped design test, a shared failing test with a
teardown error, an absent test, and an entry that no longer matches a scanned test:

``` text
--8<-- "cli/golden/results-partial.txt"
```

A partial report retains recognized results and lists unmatched identities. A requirement
with a known failure remains `fail` even when another directly linked test has no result.

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
qmstrace does not verify which commit produced the report. Results are neither persisted nor
combined across reports.

## Exit codes

- `0`: at least one scanned test matched and the informational view was produced. Failed
  tests, partial matches and graph findings do not change this code.
- `2`: usage or configuration prevented reading, or the report was unreadable, malformed,
  unsafe, empty, unsupported, or matched no scanned tests. The diagnostic suggests a next step.
- `3`: an internal fault.

Use pytest's exit code to gate test success and [check](check.md) to gate traceability.
See [Generate and interpret a pytest report](../../how-to/read-test-results.md) for the workflow.
