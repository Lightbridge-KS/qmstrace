# qmstrace

The trace layer under a quality-management system. qmstrace keeps the **state, traceability
and audit evidence** of a software project's work products, so that an auditor's questions are
answered by query instead of by assembly. ISO/IEC 29110 is the first standard it knows; the
standard is data, not code.

It is a command-line tool installed into repositories that already exist. It holds no project
data and owns no evidence: it reads markers where people and coding agents already write —
a requirement's heading, a line under a design section, a tag on a test — judges them, and
points at evidence that stays in its home system.

> **Status.** Setup, trace queries, coverage checks,
> the project-wide check run in the ledger, baseline and change guards, suspects and the
> offline browser work locally, for Python (pytest) and C# (xUnit) repos, with JUnit and TRX
> results. Pinned imports and signatures are not built yet. See the
> [tracker](docs/progress/overview-qmstrace.md).

## Use it

Install a release as a uv tool. The repository is private, so this needs read access to it:

```sh
uv tool install --python 3.13 "git+https://github.com/Lightbridge-KS/qmstrace@v0.1.1"
```

The pin holds: `uv tool upgrade` keeps it. To move to a later release, run the same command
with its tag, then `qmstrace init` in each traced repo so its stanza and skill follow; an
unedited skill copy from the earlier release is refused until it is removed ([#16](https://github.com/Lightbridge-KS/qmstrace/issues/16)). Each
release's wheel is also attached to its [GitHub release](https://github.com/Lightbridge-KS/qmstrace/releases),
and the [CHANGELOG](CHANGELOG.md) says what changed.

```sh
qmstrace init --subject service --key SVC
qmstrace status
qmstrace rules
qmstrace check --strict
qmstrace graph --out trace.html
```

Review the generated scan patterns and rules before authoring. `thread ID` follows one item;
`impact ID…` proposes a change-request list; `results report.xml` interprets a supplied pytest
JUnit or TRX report. Informational exits do not assert approval or freshness. The HTML browser is a
self-contained snapshot with source notices and a keyboard-accessible item list.

**Using qmstrace?** The user manual is at <https://qmstrace.netlify.app/>. What follows is for
working *on* qmstrace.

## Where to read

| To understand… | Read |
|---|---|
| where the work stands | [`docs/progress/overview-qmstrace.md`](docs/progress/overview-qmstrace.md) |
| the words | [`CONTEXT.md`](CONTEXT.md) |
| what it is for, and for whom | [`docs/req/qmstrace-prd.md`](docs/req/qmstrace-prd.md) |
| the decisions, each with the alternative that lost | [`docs/design/data-architecture.md`](docs/design/data-architecture.md) |
| the commands as their users meet them | [`docs/design/surface-architecture.md`](docs/design/surface-architecture.md) |
| where code goes | [`docs/structure/codebase-blueprint.md`](docs/structure/codebase-blueprint.md) |
| what was tried, and what it showed | [`docs/tests/`](docs/tests/) |

## Develop

Needs [uv](https://docs.astral.sh/uv/), [just](https://just.systems/) and Node.js 22+ for browser
control tests (no npm installation). Python 3.13 is
fetched by uv.

```sh
just sync     # install the project and its tools
just dry      # the dry gate: format, lint, types, tests, the wheel's package data, the manual
just manual   # the user manual (contents/), served with live reload
just          # list every recipe
```

A pull request must pass `just dry`; the pipeline runs the same steps.

Install [prek](https://prek.j178.dev/) and [Gitleaks](https://github.com/gitleaks/gitleaks)
on the development machine, then enable the commit hooks:

```sh
prek install
prek run --all-files
```

The hooks run Ruff, file hygiene checks and a redacted secret scan of staged changes.
Python hook tools come from the project's locked development dependencies; Gitleaks uses
the installed binary. Fixtures and golden output are excluded from whitespace fixes.
Even with `--all-files`, the Gitleaks hook scans only staged changes. Types, tests, wheel
checks and the manual build remain in `just dry`.

## License

[MIT](LICENSE). The offline trace browser bundles vis-network under its own MIT license,
kept beside it in `src/qmstrace/assets/vendor/`.
