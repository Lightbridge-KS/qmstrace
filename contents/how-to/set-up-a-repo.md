# Set up a product repo

!!! abstract "TL;DR"

    Run `qmstrace init` in the product root, review the generated rules and scan paths,
    and commit the configuration and guidance. Reuse the project's schema when joining
    an existing ledger; setup preserves an existing configuration.

1. In a new product root, run `qmstrace init --subject service --key SVC`.
   For an existing traced repo, run `qmstrace init` without subject options.
2. Review `qmstrace.toml`. Match file patterns, test levels and required fields to the
   repository. When joining a project, point `[schema]` at its [trace schema](../reference/configuration.md)
   by path rather than keeping the starter's defaults, then have the project side copy the
   schema in — [share the project's schema](share-the-schema.md).
3. Configure the actual origin sources, request register and baseline tag patterns when
   needed. Keep historical schemas recoverable from the tagged tree; see
   [baselines](../reference/baselines.md).
4. Review the managed block in `AGENTS.md` and read `.agents/skills/qmstrace/SKILL.md`.
   Keep any existing `CLAUDE.md` alias pointing at the canonical guide. A repo set up before
   the skill moved there keeps a copy in `.qmstrace/skill/`: remove `.qmstrace/` first.
5. Run `qmstrace rules`, `qmstrace status` and `qmstrace check`. Add real content and markers;
   do not manufacture requirements or evidence merely to silence a finding.
6. Run pytest with `--strict-markers` to confirm marker registration in the project's test
   invocation. If that invocation uses `-c`, register `verifies` in that explicit config too.
7. Run `qmstrace init` again; each target should be unchanged. Review and commit the files.

For the authoring loop and the final gate, follow [check your work](check-your-work.md).
The [init reference](../reference/commands/init.md) lists file ownership and refusal behavior.
