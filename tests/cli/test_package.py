"""Compatibility exports, registration and stream behavior across CLI owners."""

from importlib import import_module

import pytest
from typer.main import get_command
from typer.testing import CliRunner

from qmstrace import __version__, cli
from qmstrace.workspace import Workspace

runner = CliRunner()


@pytest.mark.parametrize(
    ("owner", "names"),
    [
        ("_app", ("app", "main")),
        ("_local", ("status", "thread", "impact", "results", "check", "rules", "init", "graph")),
        ("_ledger", ("ledger", "copy_schema", "ledger_check", "ledger_thread", "ledger_impact")),
        ("_options", ("Directory",)),
        (
            "_outcome",
            (
                "outcome",
                "EXIT_CODES",
                "EXIT_OK",
                "EXIT_FAILED",
                "EXIT_COULD_NOT_JUDGE",
                "EXIT_INTERNAL",
            ),
        ),
    ],
)
def test_cli_exports_are_the_implementation_objects(owner: str, names: tuple[str, ...]) -> None:
    implementation = import_module(f"qmstrace.cli.{owner}")
    for name in names:
        assert getattr(cli, name) is getattr(implementation, name)


def test_registration_keeps_callbacks_order_and_wrapped_signatures() -> None:
    root = ("status", "thread", "impact", "results", "check", "rules", "init", "graph")
    ledger = ("copy_schema", "ledger_check", "ledger_thread", "ledger_impact")
    assert tuple(c.callback for c in cli.app.registered_commands) == tuple(
        getattr(cli, name) for name in root
    )
    assert tuple(c.callback for c in cli.ledger.registered_commands) == tuple(
        getattr(cli, name) for name in ledger
    )
    assert [c.name for c in cli.ledger.registered_commands] == [
        "copy-schema",
        "check",
        "thread",
        "impact",
    ]
    assert len(cli.app.registered_groups) == 1
    assert cli.app.registered_groups[0].typer_instance is cli.ledger
    assert cli.app.registered_callback.callback is cli.main
    for name in (*root, *ledger):
        handler = getattr(cli, name)
        assert handler.__wrapped__.__name__ == name
    # Building every command evaluates the wrapped, postponed parameter annotations.
    assert tuple(get_command(cli.app).commands) == (*root, "ledger")


@pytest.mark.parametrize("prefix", [[], ["ledger"]])
def test_no_arguments_prints_the_same_help_on_stderr_with_exit_two(prefix: list[str]) -> None:
    explicit = runner.invoke(cli.app, [*prefix, "--help"], prog_name="qmstrace")
    implicit = runner.invoke(cli.app, prefix, prog_name="qmstrace")
    assert (explicit.exit_code, explicit.stderr_bytes) == (0, b"")
    assert (implicit.exit_code, implicit.stdout_bytes) == (2, b"")
    assert implicit.stderr_bytes == explicit.stdout_bytes


def test_version_is_eager_and_does_not_open_a_workspace(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(*args, **kwargs):
        raise AssertionError("version must not read a repository")

    monkeypatch.setattr(Workspace, "open", unexpected)
    result = runner.invoke(cli.app, ["--version", "status", "-C", "absent"], prog_name="qmstrace")
    assert result.exit_code == 0
    assert result.stdout_bytes == f"qmstrace {__version__}\n".encode()
    assert result.stderr_bytes == b""


@pytest.mark.parametrize("command", [["status"], ["ledger", "check"]])
def test_duplicate_directory_is_a_usage_error_on_stderr(command: list[str]) -> None:
    result = runner.invoke(cli.app, ["-C", "first", *command, "-C", "second"], prog_name="qmstrace")
    assert result.exit_code == 2
    assert result.stdout_bytes == b""
    assert "given twice" in result.stderr and "Usage:" in result.stderr
    assert "internal error" not in result.stderr
