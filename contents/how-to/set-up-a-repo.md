# Set up a product repo

!!! abstract "TL;DR"

    Install a release, run `qmstrace init` in the product root, review the generated rules
    and scan paths, and commit the configuration and guidance. Reuse the project's schema when joining
    an existing ledger; setup preserves an existing configuration.

1. Install qmstrace once per machine, from a release, with [uv](https://docs.astral.sh/uv/).
   The repository is private, so this needs read access to it:

    ``` sh
    uv tool install --python 3.13 "git+https://github.com/Lightbridge-KS/qmstrace@v0.2.0"
    ```

    The tag is the pin: `uv tool upgrade` keeps it, and a later release is installed with the
    same command and its tag. Then run `qmstrace init` again in each traced repo, so its stanza
    and skill follow the release; an unedited skill copy from the earlier release is refused
    until it is removed ([#16](https://github.com/Lightbridge-KS/qmstrace/issues/16)).

2. In a new product root, run `qmstrace init --subject service --key SVC`.
   For an existing traced repo, run `qmstrace init` without subject options.
3. Review `qmstrace.toml`. The run's first line names the starter it chose — the item types of
   the language the repo's build files name, C# or Python; pass `--language` if the repo holds
   both, and see [the starter's language](../reference/commands/init.md#the-starters-language).
   Match file patterns, test levels and required fields to the
   repository. When joining a project, point `[schema]` at its [trace schema](../reference/configuration.md)
   by path rather than keeping the starter's defaults, then have the project side copy the
   schema in — [share the project's schema](share-the-schema.md).
4. Configure the actual origin sources, request register and baseline tag patterns when
   needed. Keep historical schemas recoverable from the tagged tree; see
   [baselines](../reference/baselines.md).
5. Review the managed block in `AGENTS.md` and read `.agents/skills/qmstrace/SKILL.md`.
   Keep any existing `CLAUDE.md` alias pointing at the canonical guide. A repo set up before
   the skill moved there keeps a copy in `.qmstrace/skill/`: remove only `.qmstrace/skill/`
   first, preserving `.qmstrace/workspace.toml` and other local configuration.
6. Run `qmstrace rules`, `qmstrace status` and `qmstrace check`. Add real content and markers;
   do not manufacture requirements or evidence merely to silence a finding.
7. Where the repo's tests are pytest functions, run pytest with `--strict-markers` to confirm
   marker registration in the project's test invocation. If that invocation uses `-c`, register
   `verifies` in that explicit config too. A C# repo has no marker to register: its tests name
   what they verify in the `DisplayName` — [trace a C# repo](trace-a-csharp-repo.md).
8. Run `qmstrace init` again; each target should be unchanged. Review and commit the files.

For the authoring loop and the final gate, follow [check your work](check-your-work.md).
The [init reference](../reference/commands/init.md) lists file ownership and refusal behavior.
