# CLI output modes

!!! abstract "TL;DR"

    A terminal receives color and emphasis. Pipes receive plain text. Set `NO_COLOR=1`
    for fully plain reports and help. Styling changes presentation, never judgment.

## Terminal selection

Selection is evaluated for each invocation and output stream:

1. A nonempty `NO_COLOR` disables all styles, even when its value is `0`.
2. Otherwise a nonempty `FORCE_COLOR` other than `0` forces styles.
3. Otherwise styles require a terminal and `TERM` other than `dumb`.

Help uses Rich layout only in styled mode; plain help has no boxes. Report layout and
identifiers remain complete. No pager, spinner or automatic truncation is introduced.
Removing ANSI style sequences from a styled report gives the plain report's bytes.

## Encoding

Redirected standard output and standard error use UTF-8, including text receipts, JSON
and handled diagnostics. This is independent of a legacy Windows/Python pipe code page;
no environment override is needed. Real terminal streams keep their native encoding.
Encoding selection happens at the CLI boundary and does not alter generated file contents.

## Meaning

Headings and IDs use cyan/bold. Violations and failed test verdicts use red; gaps,
suspects and evidence warnings use yellow. Passing test verdicts use green. Secondary
locations may be dimmed. Text labels retain the meaning when color is unavailable.

A green test verdict is evidence from a report, not approval. Exit zero means the command
completed; informational commands can report failed tests or violations. See
[exit codes](exit-codes.md).

```sh
qmstrace status
NO_COLOR=1 qmstrace check --strict
FORCE_COLOR=1 qmstrace thread REQ-SVC-01
```

Generated HTML, schema copies and table JSON never contain terminal styles.

## Structured assessment output

`--json` explicitly selects machine output and disables all terminal styles, including
when FORCE_COLOR is set. Redirection alone does not select JSON. Help/version stay plain
text and do not read maps. See [the JSON format](cli-json.md) and
[the agent/CI workflow](../how-to/drive-the-cli-as-an-agent.md).
