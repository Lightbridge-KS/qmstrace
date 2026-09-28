"""Exit codes — the contract a pipeline and an agent branch on.

The load-bearing claims, each pinned by a test:

1. A handler's returned int is the exit code.
2. `CouldNotJudge` exits 2 and prints what stopped the run *and* the next move.
3. Anything unexpected exits 3 with one line and no traceback, and says the fault is ours.
4. A usage error exits 2 — the framework's own code, which our taxonomy never fights.
5. `--version` prints the version from package metadata and exits 0.
6. Help is plain text: no box drawing for an agent to pay tokens for.
"""

import pytest
import typer
from typer.testing import CliRunner

from qmstrace import __version__
from qmstrace.cli import app, outcome
from qmstrace.core.errors import CouldNotJudge

runner = CliRunner()


def _demo() -> typer.Typer:
    demo = typer.Typer(rich_markup_mode=None)

    @demo.command()
    @outcome
    def ok() -> int:
        return 0

    @demo.command()
    @outcome
    def failed() -> int:
        return 1

    @demo.command()
    @outcome
    def stopped() -> int:
        raise CouldNotJudge("This is a shallow clone.", "Fix: fetch the tags, then run again.")

    @demo.command()
    @outcome
    def bug() -> int:
        raise RuntimeError("boom")

    return demo


@pytest.mark.verifies("DSN-QMT-01", "REQ-QMT-14")
def test_a_returned_int_is_the_exit_code() -> None:
    assert runner.invoke(_demo(), ["ok"]).exit_code == 0
    assert runner.invoke(_demo(), ["failed"]).exit_code == 1


@pytest.mark.verifies("DSN-QMT-01", "REQ-QMT-14")
def test_could_not_judge_exits_2_and_says_the_next_move() -> None:
    result = runner.invoke(_demo(), ["stopped"])
    assert result.exit_code == 2
    assert "This is a shallow clone." in result.output
    assert "Fix: fetch the tags" in result.output


@pytest.mark.verifies("DSN-QMT-01", "REQ-QMT-14")
def test_an_unexpected_exception_exits_3_without_a_traceback() -> None:
    result = runner.invoke(_demo(), ["bug"])
    assert result.exit_code == 3
    assert "internal error" in result.output
    assert "RuntimeError: boom" in result.output
    assert "not in your repo" in result.output
    assert "Traceback" not in result.output


@pytest.mark.verifies("REQ-QMT-14")
def test_a_usage_error_exits_2() -> None:
    assert runner.invoke(_demo(), ["ok", "--no-such-option"]).exit_code == 2
    assert runner.invoke(app, ["no-such-command"]).exit_code == 2


def test_version_comes_from_package_metadata() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"qmstrace {__version__}"


def test_help_is_plain_text() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert not set("─│╭╰╮╯") & set(result.output)
