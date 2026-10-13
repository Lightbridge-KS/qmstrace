"""Exit-code policy and the boundary that turns handler outcomes into CLI exits.

Implements: DSN-QMT-01
"""

from __future__ import annotations

import functools
from collections.abc import Callable

import typer

from qmstrace.core.errors import CouldNotJudge

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
