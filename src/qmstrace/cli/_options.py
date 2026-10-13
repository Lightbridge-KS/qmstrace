"""Shared invocation-directory option and duplicate -C reconciliation.

Implements: DSN-QMT-01
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

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
