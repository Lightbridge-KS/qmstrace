# qmstrace init

!!! abstract "TL;DR"

    Set up a product directory or refresh its managed guidance. Existing trace configuration
    is preserved. The starter uses subject `product` and key `PROD`; choose these explicitly
    for a new repo. Repeating setup makes no further changes.

## Invocation

``` text
--8<-- "cli/golden/help-init.txt"
```

Run in the intended product root, or pass `-C`. When a trace configuration exists above the
invocation directory, setup refreshes that traced root. Without one, the selected directory
is the new root. A ledger directory is refused.

`--subject service --key SVC` applies only to a new configuration. Subject names use lowercase
letters, digits and hyphens; keys use uppercase letters and digits. Existing configurations
must be edited explicitly; setup never renames existing item identities.

## Written files

``` text
--8<-- "cli/golden/init-new.txt"
```

- `qmstrace.toml`: a repo-owned starter schema and scan paths, only when absent. It includes
  requirement/design/component/test types and coverage rules. It invents no origins, request
  register or baseline tag patterns. Configure those from the actual project before baselining.
- `AGENTS.md`: replace the single `qmstrace:begin` / `qmstrace:end` block, preserving surrounding
  text. A guide symlink within the product directory is followed; one outside it is refused.
- `.agents/skills/qmstrace/SKILL.md`: a copy of the packaged authoring skill, in the folder a
  coding agent's harness reads for a repo's skills; the stanza points at it as well. A
  differing local copy is refused so local edits can be preserved before replacing it. A copy
  in the earlier home, `.qmstrace/skill/SKILL.md`, is refused too: remove `.qmstrace/`, then
  run `init` again.
- `.claude/skills/qmstrace`: only when the repo already has a `.claude/` folder — a link to
  `../../.agents/skills/qmstrace`, so Claude Code lists the skill as well. It is created once
  and then left alone; anything else at that path, or a `.claude/skills` that is a file, is
  refused before any write. No link is written when `.claude/skills` and `.agents/skills`
  are already one folder, or when `.claude` or `.claude/skills` links elsewhere. Where
  symbolic links cannot be created — some Windows setups — nothing at all is written. No
  global agent configuration is changed.
- The selected root pytest configuration: register `verifies` while preserving other settings.
  Selection follows pytest's root-file priority: `pytest.toml`, `.pytest.toml`, `pytest.ini`,
  `.pytest.ini`, configured `pyproject.toml`, `tox.ini`, `setup.cfg`. Otherwise add to an existing
  `pyproject.toml`, or create `pytest.ini`. Explicit pytest `-c` overrides are outside this setup.

In a repo that already has a `.claude/` folder:

``` text
--8<-- "cli/golden/init-claude.txt"
```

Malformed configuration, conflicting managed markers and unsafe destinations are rejected
before writes. TOML edits require plain pytest table headers and an unquoted `markers` key.
Setup does not create a Git commit, baseline, requirement or test.

## Repeated setup

``` text
--8<-- "cli/golden/init-again.txt"
```

Exit `0` means setup completed; exit `2` means the input or destination could not be used;
exit `3` means an internal fault. A successful setup does not establish coverage: run `status`
and `check` next. See [set up a repo](../../how-to/set-up-a-repo.md).
