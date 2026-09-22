# qmstrace rules

!!! abstract "TL;DR"

    `qmstrace rules` prints what `check` holds this repo to — the link types, the required
    fields, the coverage rules — and says which part is the project's and which the repo's own.
    It reads the configuration alone, so it answers anywhere, even where nothing else can be read.

## Synopsis

``` text
--8<-- "cli/golden/help-rules.txt"
```

## Output

A product repo that reads the project's trace schema from the ledger beside it:

``` text
--8<-- "cli/golden/rules-service.txt"
```

A repo that carries its own schema, with no ledger:

``` text
--8<-- "cli/golden/rules-solo.txt"
```

A product repo in a pipeline, carrying a verified copy of the project's schema. It declares no
design elements, and the rules say what that means for it:

``` text
--8<-- "cli/golden/rules-client-in-a-pipeline.txt"
```

## Reading the coverage rules

Each rule is one line: its code, the item type it applies to and any `where`, the link it needs,
and the words its gap uses. Then, only where it applies:

| Note | What it means |
|---|---|
| `not for Verify-by = inspection, analysis` | the rule's `where` leaves these values out — such items fall under no rule of this kind, and `qmstrace status` lists them apart |
| `applies to no item here` | this repo does not scan the rule's item type, so nothing here can raise the gap |
| `cannot be met with the item types this repo scans` | the link comes from a type this repo does not scan — the gap stays until the repo declares that type, or the item is met in another repo and judged at the ledger's import |

No rule is hidden in the tool, and no rule is restated anywhere else: this command is where to
read them. A rule is changed in the project's trace schema, not here.

Configured baseline scopes and change-request requirements are listed too. `rules` describes
the policy; `status` and `check` assess its evidence. See [baselines and change control](../baselines.md)
for ancestry selection, fresh citations and offline evidence limits.

## Exit code

`0`, or `2` when the configuration cannot be read.
