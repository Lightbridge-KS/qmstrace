"""`--help` — what an agent reads before it runs anything, pinned byte for byte.

The load-bearing claims, each pinned by a test:

1. The root help lists every command in full and ends with the exit codes a pipeline branches on.
2. Each command's help is a golden; the user manual's reference pages include these files, so
   the manual cannot drift from what the tool prints.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app

GOLDEN = Path(__file__).parent / "golden"
runner = CliRunner()


def help_of(*words: str) -> str:
    result = runner.invoke(app, [*words, "--help"], prog_name="qmstrace")
    assert result.exit_code == 0
    return result.output


def test_the_root_help_ends_with_the_exit_codes(golden: Callable[[Path, str], None]) -> None:
    output = help_of()
    golden(GOLDEN / "help.txt", output)
    listed = output.split("Commands:")[1].split("Exit codes:")[0]
    assert "..." not in listed, "a command's summary is cut short in the list — give it short_help"


def test_every_command_has_a_help_golden(
    commands: list[str], golden: Callable[[Path, str], None]
) -> None:
    for name in commands:
        golden(GOLDEN / f"help-{name}.txt", help_of(name))


def test_every_verb_of_a_group_has_a_help_golden(
    subcommands: dict[str, list[str]], golden: Callable[[Path, str], None]
) -> None:
    for group, verbs in subcommands.items():
        for verb in verbs:
            golden(GOLDEN / f"help-{group}-{verb}.txt", help_of(group, verb))


@pytest.mark.parametrize("code", [0, 1, 2, 3])
def test_every_exit_code_is_explained(code: int) -> None:
    assert f"\n    {code}  " in help_of()
