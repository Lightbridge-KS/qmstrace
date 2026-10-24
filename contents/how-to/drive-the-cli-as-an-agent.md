# Drive the CLI from an agent or CI

!!! abstract "TL;DR"

    Select JSON explicitly, establish scope and rules, then request targeted evidence.
    Capture the exit code before another shell command replaces it. Keep notices visible.

## Establish the checkout and rules

```sh
qmstrace paths --json
qmstrace rules --json
qmstrace status --json
```

For a selected layout, pass `--workspace FILE` at the root or leaf. Paths in this selector
start at the effective invocation directory after `-C`; a map does not change which
command scope was requested. See [workspace maps](../reference/workspace-maps.md).

## Inspect relevant evidence

Use actual project IDs:

```sh
qmstrace thread REQ-SVC-01 --json
qmstrace impact REQ-SVC-01 REQ-SVC-02 --json
qmstrace results report.xml --json
```

Read `notices` before using the data. Inspect unmatched report entries and missing results.
Keep requirements outside test-backed verification separate from requirement test verdicts.

## Capture the gate result

The following shell example preserves exit `1` as an assessment with findings instead of
letting `set -e` or `jq` discard that result:

```sh
if qmstrace check --strict --json > check.json; then
    check_exit=0
else
    check_exit=$?
fi
jq '{format, exit_code, counts: .data.counts, notices, error}' check.json
exit "$check_exit"
```

For detailed work, select `.data.violations`, `.data.gaps` or `.data.suspects` with `jq`.
Do not truncate notices. A targeted thread is usually smaller than a full check.

To judge the whole project, start in its ledger trace root:

```sh
qmstrace -C ./ledger ledger check --strict --json
```

## Refresh bundled agent guidance

After upgrading qmstrace, run `qmstrace init` to refresh managed guidance. If it refuses an
existing differing `.agents/skills/qmstrace/SKILL.md`, review and preserve local edits, remove
only that installed skill file, then rerun `qmstrace init` and review the diff. Init's refusal
protects local edits; this feature does not change that policy. Keep `.qmstrace/workspace.toml`
and other workspace maps. Never delete the entire `.qmstrace/` directory to refresh a skill.

The [JSON reference](../reference/cli-json.md) defines the contract; the bundled skill gives
the compact authoring workflow. [Evidence and completion](../explanation/command-evidence.md)
explains what a result can establish.
