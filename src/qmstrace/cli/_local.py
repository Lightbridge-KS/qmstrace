"""Local command handlers: resolve arguments, call the workspace, render and exit.

Implements: DSN-QMT-01
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from qmstrace.cli._options import Directory, _directory
from qmstrace.cli._outcome import EXIT_FAILED, EXIT_OK, outcome
from qmstrace.render import graph as browser
from qmstrace.render import text
from qmstrace.workspace import Workspace


@outcome
def status(ctx: typer.Context, directory: Directory = None) -> int:
    """What was scanned, what lies around the repo, and one line per requirement.

    Includes governing baselines, change-request evidence and a suspect summary.
    Check lists all suspects; they never fail the gate. Not a check: it exits 0
    whatever it counts, or 2 when the evidence cannot be judged.
    """
    typer.echo(text.status(Workspace.open(_directory(ctx, directory)).assessment()))
    return EXIT_OK


@outcome
def thread(
    ctx: typer.Context,
    item_id: Annotated[
        str, typer.Argument(metavar="ID", help="A requirement, design element, test or clause ID.")
    ],
    directory: Directory = None,
) -> int:
    """Walk one item backward to what it derives from, and forward to what hangs off it.

    Each item is shown once, nearest first, under the link that reaches it first. It stops at
    this repo's edge.
    """
    assessment = Workspace.open(_directory(ctx, directory)).thread(item_id)
    typer.echo(text.thread(assessment, item_id))
    return EXIT_OK


@outcome
def impact(
    ctx: typer.Context,
    item_ids: Annotated[
        list[str], typer.Argument(metavar="ID…", help="One or more item IDs visible to this run.")
    ],
    directory: Directory = None,
) -> int:
    """Show the combined downstream items and upstream origins of several starting items.

    The Impacts line is a candidate for review, filtered by configured baseline types. It
    stops at this repo's edge. Any unseen starting ID rejects the whole request.
    """
    assessment = Workspace.open(_directory(ctx, directory)).impact(item_ids)
    typer.echo(text.impact(assessment, item_ids))
    return EXIT_OK


@outcome
def results(
    ctx: typer.Context,
    report: Annotated[
        Path,
        typer.Argument(metavar="REPORT", help="A pytest JUnit XML report or a TRX file."),
    ],
    directory: Directory = None,
) -> int:
    """Match a report to scanned tests and their explicit verifies links.

    The report is pytest JUnit XML or a TRX file (dotnet test --logger trx); its root element
    decides which. Informational: failing tests and partial matches still exit 0. Unmatched
    entries are listed; a report with no matches exits 2. Relative report paths start at -C or
    the current directory, not the discovered repo root. The report's commit is not verified.
    """
    start = _directory(ctx, directory)
    report_path = (start / report).resolve()
    view = Workspace.open(start).results(report_path)
    typer.echo(text.results(view))
    return EXIT_OK


@outcome
def check(
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
    """List every violation, gap and suspect, each with its next move.

    While authoring, gaps do not fail: they are the work not done yet. Under --strict — the gate
    a pull request passes — they do. Violations always fail. Suspects never fail, even under
    --strict: an edit or a passing test does not record review.
    """
    assessment = Workspace.open(_directory(ctx, directory)).assessment()
    typer.echo(text.check(assessment, strict=strict, quiet=quiet))
    return EXIT_FAILED if assessment.fails(strict=strict) else EXIT_OK


@outcome
def rules(ctx: typer.Context, directory: Directory = None) -> int:
    """Print the rules in force: the project's trace schema and this repo's own part.

    Read from the configuration alone — nothing is scanned.
    """
    typer.echo(text.rules(Workspace.open(_directory(ctx, directory)).config))
    return EXIT_OK


@outcome
def init(
    ctx: typer.Context,
    subject: Annotated[
        str | None, typer.Option(help="New repo subject name; default: product.")
    ] = None,
    key: Annotated[str | None, typer.Option(help="New repo ID key; default: PROD.")] = None,
    directory: Directory = None,
) -> int:
    """Initialize the selected directory; refresh managed guidance in an existing traced repo.

    Existing configuration and unrelated guide/settings content are preserved. Repeating init
    changes nothing. The starter is repo-owned, with no invented origins or baseline tags.
    Commit the generated files after reviewing the rules and scan paths.
    """
    for line in Workspace.initialize(_directory(ctx, directory), subject=subject, key=key):
        typer.echo(line)
    typer.echo("Setup complete. Review qmstrace rules, then run qmstrace status. Exit 0.")
    return EXIT_OK


@outcome
def graph(
    ctx: typer.Context,
    out: Annotated[Path, typer.Option("--out", help="New HTML file; existing files are refused.")],
    item_id: Annotated[
        str | None, typer.Argument(metavar="ID", help="Initially focus this item.")
    ] = None,
    directory: Directory = None,
) -> int:
    """Export one working-tree assessment as a self-contained, read-only HTML browser.

    ID sets the initial selection; every visible-to-run item is still included. Relative output
    paths start at -C or the current directory. No server or network is needed. Findings do not
    fail this informational command. Traversal stops at this repo's edge.
    """
    start = _directory(ctx, directory)
    workspace = Workspace.open(start)
    assessment = workspace.thread(item_id) if item_id is not None else workspace.assessment()
    workspace.save_view(start / out, browser.document(assessment, item_id))
    typer.echo(
        f"Written: {out} · {len(assessment.graph.nodes)} items · "
        f"{len(assessment.graph.links)} links"
    )
    typer.echo("Offline working-tree snapshot; findings and evidence limits are included. Exit 0.")
    return EXIT_OK
