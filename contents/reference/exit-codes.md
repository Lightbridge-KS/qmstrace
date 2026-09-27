# Exit codes

!!! abstract "TL;DR"

    Every command exits with one of four codes: `0` completed successfully, `1` the check failed, `2`
    it could not judge, `3` a fault in qmstrace itself. A pipeline branches on them, and
    `qmstrace --help` prints them at its foot.

## As `--help` prints them

``` text
--8<-- "cli/golden/help.txt"
```

## Reading them in a pipeline

- **`0` means the command completed; `1` means a check failed.** For a check, `1` means
  violations — or, under the gate, gaps too. The command's last line says which.
- **`2` is no verdict at all.** The run could not judge: no `qmstrace.toml` above the folder, a
  trace schema it cannot read, a ledger repo where a product repo was expected, or a product
  repo where the ledger was. Fix what it
  names; do not read it as a pass or as a failure. A mistyped command or option exits `2` as
  well, as with most command-line tools.
- **`3` is a fault in qmstrace, not in the repo.** It prints one line, never a traceback.

`qmstrace status`, `thread`, `impact` and `results` are informational. In particular,
`results` exits `0` even when matched tests failed or some report entries did not match;
a report with no matching tests exits `2`. Use pytest's exit code to gate test success.
