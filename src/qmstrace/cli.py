"""qmstrace — command line. Wiring only: options in, an exit code out.

The exit codes are written once, in `EXIT_CODES` below, and `--help` prints them: a pipeline and
an agent branch on them. The framework already exits 2 on a usage error, so this taxonomy never
fights it. This module never imports click: the framework vendors it privately. A handler
returns an int; `outcome` turns that — and `CouldNotJudge`, and anything unexpected — into the
exit code.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from qmstrace import __version__
from qmstrace.core.errors import CouldNotJudge
from qmstrace.render import text
from qmstrace.workspace import Workspace

EXIT_OK, EXIT_FAILED, EXIT_COULD_NOT_JUDGE, EXIT_INTERNAL = 0, 1, 2, 3

# Printed at the foot of `--help`, kept as written: the leading \b stops the framework reflowing it.
EXIT_CODES = """\b
Exit codes:
  0  completed — informational views may include failures
  1  the check failed — violations, or gaps under the gate; the result line says which
  2  could not judge — usage, configuration, the wrong kind of repo, an unknown ID,
     an unreadable report, a shallow clone where baselines are configured
  3  internal error — a fault in qmstrace, not in the repo"""

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
    help="The trace layer under a quality-management system.",
    epilog=EXIT_CODES,
)


def outcome[**P](handler: Callable[P, int]) -> Callable[P, None]:
    """Let a handler return an exit code, and never let a traceback reach the reader."""

    @functools.wraps(handler)
    def run(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            code = handler(*args, **kwargs)
        except CouldNotJudge as stopped:
            typer.echo(f"qmstrace: {stopped.what} {stopped.next_move}", err=True)
            code = EXIT_COULD_NOT_JUDGE
        except typer.BadParameter:
            raise  # a usage error: the framework prints it with the usage line, and exits 2
        except Exception as bug:  # noqa: BLE001 — the last line of defence, by design
            typer.echo(
                f"qmstrace: internal error — {type(bug).__name__}: {bug}. "
                "This is a fault in qmstrace, not in your repo.",
                err=True,
            )
            code = EXIT_INTERNAL
        raise typer.Exit(code)

    return run


# `-C` is accepted on either side of the command: before it, as with `git -C`, or after it, as a
# command's own option. Each product-repo command takes it; `_directory` reconciles the two.
Directory = Annotated[
    Path | None,
    typer.Option(
        "-C",
        metavar="PATH",
        help="Run as if qmstrace had been started in PATH, as with git -C. Before or after the "
        "command.",
    ),
]


def _directory(ctx: typer.Context, after: Path | None) -> Path:
    """Where the command runs: `-C` from before the command or after it — never both."""
    before: Path | None = ctx.obj
    if before is not None and after is not None:
        raise typer.BadParameter(
            f"given twice — '{before}' before the command and '{after}' after it; give it once.",
            param_hint="'-C'",
        )
    return after or before or Path(".")


def _print_version(wanted: bool) -> None:
    if wanted:
        typer.echo(f"qmstrace {__version__}")
        raise typer.Exit(EXIT_OK)


@app.callback()
def main(
    ctx: typer.Context,
    directory: Directory = None,
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=_print_version, is_eager=True, help="Print the version and exit."
        ),
    ] = False,
) -> None:
    """The trace layer under a quality-management system."""
    ctx.obj = directory


@app.command(short_help="Where am I: what was read, and one line per requirement.")
@outcome
def status(ctx: typer.Context, directory: Directory = None) -> int:
    """What was scanned, what lies around the repo, and one line per requirement.

    Includes governing baselines and change-request evidence. Not a check: it exits 0
    whatever it counts, or 2 when the evidence cannot be judged.
    """
    typer.echo(text.status(Workspace.open(_directory(ctx, directory)).assessment()))
    return EXIT_OK


@app.command(short_help="What one item derives from, and what hangs off it.")
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


@app.command(short_help="What changing several items affects, with a candidate Impacts line.")
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


@app.command(short_help="Test verdicts per requirement, from a pytest JUnit report.")
@outcome
def results(
    ctx: typer.Context,
    report: Annotated[Path, typer.Argument(metavar="REPORT", help="A pytest JUnit XML report.")],
    directory: Directory = None,
) -> int:
    """Match a report to scanned tests and their explicit verifies links.

    Informational: failing tests and partial matches still exit 0. Unmatched entries are
    listed; a report with no matches exits 2. Relative report paths start at -C or the current
    directory, not the discovered repo root. The report's commit is not verified.
    """
    start = _directory(ctx, directory)
    report_path = (start / report).resolve()
    view = Workspace.open(start).results(report_path)
    typer.echo(text.results(view))
    return EXIT_OK


@app.command(short_help="What is wrong, and what is not done yet — the gate with --strict.")
@outcome
def check(
    ctx: typer.Context,
    strict: Annotated[
        bool, typer.Option("--strict", help="The gate: gaps fail too, not only violations.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", help="Findings only — what could not be verified still shows."),
    ] = False,
    directory: Directory = None,
) -> int:
    """List every violation and every gap, each with its next move.

    While authoring, gaps do not fail: they are the work not done yet. Under --strict — the gate
    a pull request passes — they do. Violations always fail.
    """
    assessment = Workspace.open(_directory(ctx, directory)).assessment()
    typer.echo(text.check(assessment, strict=strict, quiet=quiet))
    return EXIT_FAILED if assessment.fails(strict=strict) else EXIT_OK


@app.command(short_help="What check holds this repo to, and whose each rule is.")
@outcome
def rules(ctx: typer.Context, directory: Directory = None) -> int:
    """Print the rules in force: the project's trace schema and this repo's own part.

    Read from the configuration alone — nothing is scanned.
    """
    typer.echo(text.rules(Workspace.open(_directory(ctx, directory)).config))
    return EXIT_OK
