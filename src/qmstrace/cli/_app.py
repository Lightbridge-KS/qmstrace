"""Root application, callback, version and explicit command registration.

Implements: DSN-QMT-01
"""

from __future__ import annotations

from typing import Annotated

import typer

from qmstrace import __version__
from qmstrace.cli._ledger import ledger
from qmstrace.cli._local import check, graph, impact, init, results, rules, status, thread
from qmstrace.cli._options import Directory
from qmstrace.cli._outcome import EXIT_CODES, EXIT_OK

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
    help="The trace layer under a quality-management system.",
    epilog=EXIT_CODES,
)


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


# Register root commands explicitly, preserving their existing order.
app.command(short_help="Where am I: what was read, and one line per requirement.")(status)
app.command(short_help="Trace one item: what it derives from, and what hangs off it.")(thread)
app.command(short_help="What changing several items affects, with a candidate Impacts line.")(
    impact
)
app.command(short_help="Test verdicts per requirement, from a pytest JUnit report.")(results)
app.command(short_help="What is wrong, and what is not done yet — the gate with --strict.")(check)
app.command(short_help="What check holds this repo to, and whose each rule is.")(rules)
app.command(short_help="Set up trace configuration, agent guidance and pytest markers.")(init)
app.command(short_help="Write an offline, interactive view of the local trace graph.")(graph)
app.add_typer(
    ledger, name="ledger", short_help="The project side's verbs — run them in the ledger repo."
)
