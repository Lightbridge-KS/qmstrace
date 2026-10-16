"""Ledger command group and its handlers.

Implements: DSN-QMT-01
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from qmstrace.cli._options import Directory, _directory
from qmstrace.cli._outcome import EXIT_FAILED, EXIT_OK, outcome
from qmstrace.core.tables import table
from qmstrace.render import tables, text
from qmstrace.workspace import Workspace

ledger = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
    help="The project side's verbs — run them in the ledger repo, where qmstrace.schema.toml is.",
)


@ledger.command("copy-schema", short_help="Copy the project's trace schema into its product repos.")
@outcome
def copy_schema(
    ctx: typer.Context,
    repos: Annotated[
        list[str] | None,
        typer.Argument(
            metavar="REPO…", help="Repos the schema names under [repos]; default: every one."
        ),
    ] = None,
    directory: Directory = None,
) -> int:
    """Write the project's trace schema into each product repo as a generated, verified copy.

    The copy sits between qmstrace markers in the repo's qmstrace.toml; every other byte is
    kept. All the repos, or none: a problem in any names every problem and writes nothing.
    A second run changes nothing. Commit the updated qmstrace.toml in each repo.
    """
    config, copies = Workspace.copy_schema(_directory(ctx, directory), repos or ())
    typer.echo(text.schema_copies(config, copies))
    return EXIT_OK


@ledger.command(
    "check", short_help="Judge every repo of the project together — the gate with --strict."
)
@outcome
def ledger_check(
    ctx: typer.Context,
    strict: Annotated[
        bool, typer.Option("--strict", help="The gate: gaps fail too; suspects never fail.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", help="Findings only — what could not be verified still shows."),
    ] = False,
    directory: Directory = None,
) -> int:
    """Read every repo the schema lists under [repos] — the ledger itself too, when it holds
    documents — and judge them as one project.

    A coverage rule is met by a link in any repo; each repo's own violations are reported; a
    change to a frozen item makes what hangs off it suspect in every repo. Each repo is read
    from its working tree, not at a pin, and the output says so. A repo that cannot be read,
    or holds rules other than the ledger's schema, stops the check: exit 2.
    """
    project = Workspace.project(_directory(ctx, directory))
    typer.echo(text.ledger_check(project, strict=strict, quiet=quiet))
    return EXIT_FAILED if project.fails(strict=strict) else EXIT_OK


@ledger.command(
    "thread",
    short_help="Trace one item across every repo: what it derives from, what hangs off it.",
)
@outcome
def ledger_thread(
    ctx: typer.Context,
    item_id: Annotated[
        str,
        typer.Argument(
            metavar="ID",
            help="A requirement, design element or clause ID — or a module's or test's ID with "
            "its repo, as service:tests/unit/test_api.py::test_x.",
        ),
    ],
    directory: Directory = None,
) -> int:
    """Walk one item backward to what it derives from, and forward to what hangs off it, across
    every repo the schema lists — from the ledger.

    Each item is shown once, nearest first, under the link that reaches it first. Each repo is
    read from its working tree, not at a pin, and the output says so.
    """
    project = Workspace.project_thread(_directory(ctx, directory), item_id)
    typer.echo(text.ledger_thread(project, item_id))
    return EXIT_OK


@ledger.command(
    "impact", short_help="What changing several items affects across every repo of the project."
)
@outcome
def ledger_impact(
    ctx: typer.Context,
    item_ids: Annotated[
        list[str],
        typer.Argument(metavar="ID…", help="One or more item IDs of the project."),
    ],
    directory: Directory = None,
) -> int:
    """Show the combined downstream items and upstream origins of several starting items,
    across every repo the schema lists — from the ledger.

    The Impacts line is a candidate for review, filtered by configured baseline types. Any
    unseen starting ID rejects the whole request.
    """
    project = Workspace.project_impact(_directory(ctx, directory), item_ids)
    typer.echo(text.ledger_impact(project, item_ids))
    return EXIT_OK


TABLES = ("matrix", "requirements", "coverage")


@ledger.command(
    "table",
    short_help="The traceability matrix, requirements register or coverage summary, as JSON.",
)
@outcome
def ledger_table(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(metavar="TABLE", help="matrix, requirements or coverage.")],
    reports: Annotated[
        list[str] | None,
        typer.Option(
            "--report",
            metavar="REPO=FILE",
            help="matrix only: a JUnit or TRX report and the repo whose tests it ran; repeatable.",
        ),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option(
            "--out", help="Write a new file instead of printing; existing files are refused."
        ),
    ] = None,
    directory: Directory = None,
) -> int:
    """Emit one of the project's tables as versioned JSON (qmstrace.table/1), for a render
    layer to turn into a document.

    matrix: one row per requirement, design element and test case. requirements: one row per
    requirement. coverage: requirements covered and not, tier by tier. Columns come from the
    project's schema. Every repo is read from its working tree, not at a pin; each repo's commit,
    and whether its tree was clean, are in the document. It is a draft, never an issued
    revision. Relative --out and --report paths start at -C or the current directory.

    With --report, the matrix also carries a verdict per level and an overall one, each naming
    the reports it came from; the reports are read as one, whatever their order.
    """
    if name not in TABLES:
        raise typer.BadParameter(
            f"'{name}' is not a table qmstrace emits — use matrix, requirements or coverage.",
            param_hint="TABLE",
        )
    if reports and name != "matrix":
        raise typer.BadParameter("only the matrix carries verdicts.", param_hint="--report")
    start = _directory(ctx, directory)
    given = [_report(start, value) for value in reports or ()]
    if given:
        project, view = Workspace.project_results(start, given)
    else:
        project, view = Workspace.project(start), None
    built = table(name, project.config, project.graph, view)
    document = tables.document(project, built, view)
    if out is None:
        typer.echo(document, nl=False)
        return EXIT_OK
    Workspace.save_view(start / out, document)
    typer.echo(f"Written: {out} · {built.name} · {len(built.rows)} rows")
    typer.echo("Read from working trees, not pinned; a draft, not an issued revision. Exit 0.")
    return EXIT_OK


def _report(start: Path, value: str) -> tuple[str, Path]:
    """`REPO=FILE`, the file resolved from where qmstrace was started."""
    repo, _, file = value.partition("=")
    if not repo or not file:
        raise typer.BadParameter(
            f"'{value}' is not REPO=FILE — name the repo whose tests the report ran, e.g. "
            "agent=TestResults/unit.trx.",
            param_hint="--report",
        )
    return repo, (start / file).resolve()
