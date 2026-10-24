# Command completion and verification evidence

!!! abstract "TL;DR"

    Completing a command establishes that it produced a view. Its findings, report outcomes
    and evidence limits establish what that view can say. Color and JSON do not add approval.

## Two presentations, one assessment

Terminal emphasis helps a reader find IDs, failures and limits. JSON gives a program named
fields to branch on. Both use the same scanned graph, baseline comparisons and test verdicts.
A pipe receives plain text unless JSON is explicitly requested, so redirection does not
silently change a consumer's format.

## Completion is a different claim

`results` is informational. It can complete successfully while showing failed tests,
unmatched report entries and missing results. It does not verify which commit generated
a report. A passing linked test is evidence only for a requirement whose declared
verification method is not selected by a test-backed coverage rule.

`check` is a gate: violations fail it, and gaps also fail under strict mode. Suspects remain
informational because an edit or passing test does not record that a human reviewed the
upstream change. Local assessment stops at the repository edge; ledger assessment reads
all configured members from working trees, not pins.

These distinctions are why JSON has `exit_code`, verdicts, findings and notices, rather
than one universal success flag. Source limits remain visible in every presentation.
JSON improves composition; targeted commands and field selection make it economical.

See [CLI output](../reference/output.md), [the JSON contract](../reference/cli-json.md)
and [the agent/CI workflow](../how-to/drive-the-cli-as-an-agent.md).
