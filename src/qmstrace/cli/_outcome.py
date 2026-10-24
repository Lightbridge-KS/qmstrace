"""Exit-code policy and the boundary that turns handler outcomes into CLI exits.

Implements: DSN-QMT-01
"""

from __future__ import annotations

import functools
import sys
from collections.abc import Callable

import typer

from qmstrace.cli._invocation import CURRENT
from qmstrace.cli._json import error
from qmstrace.cli._terminal import styled
from qmstrace.core.errors import CouldNotJudge
from qmstrace.render._style import Style

# The leading \b in EXIT_CODES prevents framework reflow.
EXIT_OK, EXIT_FAILED, EXIT_COULD_NOT_JUDGE, EXIT_INTERNAL = 0, 1, 2, 3


EXIT_CODES = """\b
Exit codes:
  0  completed — informational views may include failures
  1  the check failed — violations, or gaps under the gate; the result line says which
  2  could not judge — usage, configuration, the wrong kind of repo, an unknown ID,
     an unreadable report, a shallow clone where baselines are configured, a repo of
     the project that cannot be read or holds other rules
  3  internal error — a fault in qmstrace, not in the repo"""


def outcome[**P](handler: Callable[P, int]) -> Callable[P, None]:
    """Let a handler return an exit code, and never let a traceback reach the reader."""

    @functools.wraps(handler)
    def run(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            request = CURRENT.get()
            if request.json and request.command in {"init", "graph", "ledger copy-schema"}:
                raise typer.BadParameter(
                    "--json is supported by assessment commands, not this writing command.",
                    param_hint="--json",
                )
            if request.json and request.command == "ledger table" and kwargs.get("out") is not None:
                raise typer.BadParameter(
                    "--json cannot be combined with --out; omit --out "
                    "to receive table JSON on stdout.",
                    param_hint="--out",
                )
            code = handler(*args, **kwargs)
        except CouldNotJudge as stopped:
            if CURRENT.get().json:
                error(
                    "could-not-judge",
                    stopped.display_what or stopped.what,
                    stopped.display_next_move or stopped.next_move,
                    code=2,
                )
            else:
                typer.echo(
                    Style(styled(sys.stderr)).warning(
                        f"qmstrace: {stopped.what} {stopped.next_move}"
                    ),
                    err=True,
                    color=styled(sys.stderr),
                )
            code = EXIT_COULD_NOT_JUDGE
        except typer.BadParameter:
            raise  # a usage error: the framework prints it with the usage line, and exits 2
        except Exception as bug:
            if isinstance(bug, BrokenPipeError):
                raise
            if CURRENT.get().json:
                error(
                    "internal",
                    "An internal fault prevented the command from completing.",
                    "Report this fault in qmstrace; it is not a finding in the repository.",
                    code=3,
                )
            else:
                typer.echo(
                    Style(styled(sys.stderr)).error(
                        f"qmstrace: internal error — {type(bug).__name__}: {bug}. "
                        "This is a fault in qmstrace, not in your repo."
                    ),
                    err=True,
                    color=styled(sys.stderr),
                )
            code = EXIT_INTERNAL
        raise typer.Exit(code)

    return run
