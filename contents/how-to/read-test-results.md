# Generate and interpret a pytest report

!!! abstract "TL;DR"

    Run pytest with `--junitxml=report.xml`, then run `qmstrace results report.xml` in the same
    directory. Read missing and unmatched results as limits of the report. Use pytest's exit
    code for test success; qmstrace's results command is informational.

## Generate the report

From the product repository root, run the project's pytest suite with its usual environment:

``` sh
uv run pytest --junitxml=report.xml
```

Keep pytest's normal JUnit names; do not add `--junit-prefix`. Both pytest XML families are
supported. The report may be Git-ignored; an explicit report path is still read.

## Read the results, including after pytest fails

Run this as a separate command so a failing pytest exit code does not skip it:

``` sh
qmstrace results report.xml
```

For another directory, use `qmstrace -C path/to/product results report.xml`. The report path
is relative to that directory. Repository discovery does not move the report path.

Several reports — say, one pytest run per test level — are read as one:
`qmstrace results unit.xml integration.xml`. A test reported in both keeps its worst verdict,
and the header lists each report with its entry count.

The miniature service illustrates a partial report with failed and missing results:

``` text
--8<-- "cli/golden/results-partial.txt"
```

## Follow up on incomplete evidence

1. Check the matched automated-test and run counts. A parameterized function counts as one
   automated test and can contribute several runs. Repeated XML entries are combined, not counted as
   retry attempts.
2. Inspect `fail` and `skip` details. Shared tests name other affected items. Where the
   project keeps a Test Specification, a requirement's row names the test cases its verdict
   came through, each with its own verdict. A test or a test case that reaches only a design
   element does not supply a requirement verdict; it is listed apart, so its failure still
   shows.
3. For `no-result`, run the missing test or explain why this report selected only part of
   the suite. For `untested`, add the intended test link — on the automated test, or on the
   test case it runs — or review the requirement's verification method. A few reported parameter variants do not establish a complete set.
4. Resolve unmatched entries by checking report provenance, scan patterns and default pytest
   names. Zero matched tests is an error; a partly matched report still shows recognized results.
5. Review requirements outside test-backed verification through their declared method, such
   as inspection, analysis or demonstration. Linked test results are evidence only; they do
   not complete or approve that method. A missing or invalid `Verify-by` value needs its V05
   finding corrected.

The output always states that the report's commit is **not verified**. Generate a fresh report
from the intended working tree and retain the run's provenance through the project's evidence
process. This command interprets one file; it does not certify freshness or store results.

For complete matching, aggregation and exit semantics, see [results reference](../reference/commands/results.md).
