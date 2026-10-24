"""Per-stream terminal policy and public Typer help extension points.

Implements: DSN-QMT-01
"""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from io import TextIOWrapper
from typing import Any, TextIO

from typer.core import TyperCommand, TyperGroup

from qmstrace.cli._invocation import CURRENT, select
from qmstrace.cli._json import error


def _utf8_pipes() -> None:
    """Use UTF-8 for redirected text wrappers without replacing streams or terminal codecs."""
    for stream in (sys.stdout, sys.stderr):
        if (
            isinstance(stream, TextIOWrapper)
            and not stream.isatty()
            and stream.encoding.lower().replace("_", "-") != "utf-8"
        ):
            stream.reconfigure(encoding="utf-8")


def styled(stream: TextIO | None = None) -> bool:
    """Resolve on every call; a cached terminal decision leaks between invocations."""
    if CURRENT.get().json:
        return False
    if os.environ.get("NO_COLOR"):
        return False
    forced = os.environ.get("FORCE_COLOR")
    if forced and forced != "0":
        return True
    return bool((stream or sys.stdout).isatty() and os.environ.get("TERM") != "dumb")


class TerminalCommand(TyperCommand):
    """Use Typer's Rich help only when the help stream supports styling."""

    def format_help(self, ctx: Any, formatter: Any) -> None:
        original = self.rich_markup_mode
        self.rich_markup_mode = "rich" if styled() else None
        try:
            super().format_help(ctx, formatter)
        finally:
            self.rich_markup_mode = original


class TerminalGroup(TyperGroup):
    """Group equivalent of TerminalCommand; both preserve plain help by default."""

    def main(
        self,
        args: Sequence[str] | None = None,
        prog_name: str | None = None,
        complete_var: str | None = None,
        standalone_mode: bool = True,
        windows_expand_args: bool = True,
        **extra: Any,
    ) -> Any:
        _utf8_pipes()
        arguments = list(sys.argv[1:] if args is None else args)
        request = select(arguments, self)
        token = CURRENT.set(request)
        try:
            if not request.json or request.eager:
                return super().main(
                    args=arguments,
                    prog_name=prog_name,
                    complete_var=complete_var,
                    standalone_mode=standalone_mode,
                    windows_expand_args=windows_expand_args,
                    **extra,
                )
            if request.occurrences > 1:
                error(
                    "usage",
                    "--json was given twice.",
                    "Give --json once, before the command or after the leaf command.",
                    code=2,
                )
                code = 2
            else:
                try:
                    returned = super().main(
                        args=arguments,
                        prog_name=prog_name,
                        complete_var=complete_var,
                        standalone_mode=False,
                        windows_expand_args=windows_expand_args,
                        **extra,
                    )
                    code = returned if isinstance(returned, int) else 0
                except (BrokenPipeError, KeyboardInterrupt):
                    raise
                except Exception as exc:  # noqa: BLE001 — framework usage errors use a public error protocol
                    describe = getattr(exc, "format_message", None)
                    if getattr(exc, "exit_code", None) == 2 and callable(describe):
                        error(
                            "usage",
                            str(describe()),
                            "Read qmstrace --help or the leaf command's --help "
                            "and correct the invocation.",
                            code=2,
                        )
                        code = 2
                    else:
                        error(
                            "internal",
                            "An internal fault prevented the command from completing.",
                            "Report this fault in qmstrace; it is not a finding in the repository.",
                            code=3,
                        )
                        code = 3
            if standalone_mode:
                raise SystemExit(code)
            return code
        finally:
            CURRENT.reset(token)

    def format_help(self, ctx: Any, formatter: Any) -> None:
        original = self.rich_markup_mode
        self.rich_markup_mode = "rich" if styled() else None
        try:
            super().format_help(ctx, formatter)
        finally:
            self.rich_markup_mode = original
