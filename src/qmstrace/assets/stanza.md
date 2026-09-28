<!-- qmstrace:begin — generated; edit qmstrace.toml, not this block -->
This repo is traced for project **{project}**; subjects: {subjects}.
- Read `{skill}` before changing requirements, design or tests.
- Local items: {items}. IDs are never renumbered or reused.
- Start with `qmstrace status`; `qmstrace rules` prints the actual schema and coverage rules.
{walks}
{gate}
- Frozen changes and controlled additions need a fresh accepted change request; inspect the governing baseline and request evidence before editing.
- A marker states a fact. Break the behavior in a disposable test and confirm the tagged test fails; restore the source afterwards.
{suspects}
- Collect facts with tools; never invent dates, verdicts, test results or approvals. Keep unavailable-source notices visible.
<!-- qmstrace:end -->
