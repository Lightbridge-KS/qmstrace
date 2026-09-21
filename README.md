# qmstrace

The trace layer under a quality-management system. qmstrace keeps the **state, traceability
and audit evidence** of a software project's work products, so that an auditor's questions are
answered by query instead of by assembly. ISO/IEC 29110 is the first standard it knows; the
standard is data, not code.

It is a command-line tool installed into repositories that already exist. It holds no project
data and owns no evidence: it reads markers where people and coding agents already write —
a requirement's heading, a line under a design section, a tag on a test — judges them, and
points at evidence that stays in its home system.

> **Status: the first engine slice is being built.** The design is settled and recorded; the
> package does not yet do useful work. See [`docs/progress/`](docs/progress/).

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

Needs [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/). Python 3.13 is
fetched by uv.

```sh
just sync     # install the project and its tools
just dry      # the dry gate: format, lint, types, tests, the wheel's package data, the manual
just manual   # the user manual (contents/), served with live reload
just          # list every recipe
```

A pull request must pass `just dry`; the pipeline runs the same steps.
