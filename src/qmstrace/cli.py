"""qmstrace — command line. Wiring only: options in, an exit code out.

Exit codes
    0   no failing findings in this mode
    1   the check failed — violations, or gaps under the gate; the result line says which
    2   could not judge — usage, configuration, the wrong kind of repo, an unknown ID,
        an unreadable report, a shallow clone where baselines are configured
    3   internal error

The framework already exits 2 on a usage error, so this taxonomy never fights it. This module
never imports click: the framework vendors it privately. A handler returns an int; `outcome`
turns that — and `CouldNotJudge`, and anything unexpected — into the exit code.
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

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
    help="The trace layer under a quality-management system.",
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
        except Exception as bug:  # noqa: BLE001 — the last line of defence, by design
            typer.echo(
                f"qmstrace: internal error — {type(bug).__name__}: {bug}. "
                "This is a fault in qmstrace, not in your repo.",
                err=True,
            )
            code = EXIT_INTERNAL
        raise typer.Exit(code)

    return run


def _print_version(wanted: bool) -> None:
    if wanted:
        typer.echo(f"qmstrace {__version__}")
        raise typer.Exit(EXIT_OK)


@app.callback()
def main(
    ctx: typer.Context,
    directory: Annotated[
        Path,
        typer.Option(
            "-C",
            metavar="PATH",
            help="Run as if qmstrace had been started in PATH, as with git -C.",
        ),
    ] = Path("."),
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=_print_version, is_eager=True, help="Print the version and exit."
        ),
    ] = False,
) -> None:
    """The trace layer under a quality-management system."""
    ctx.obj = directory


@app.command()
@outcome
def status(ctx: typer.Context) -> int:
    """What was scanned, what lies around the repo, and one line per requirement."""
    typer.echo(text.status(Workspace.open(ctx.obj).assessment()))
    return EXIT_OK
