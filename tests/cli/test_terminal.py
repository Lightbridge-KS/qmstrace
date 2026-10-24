"""Terminal presentation changes emphasis, never assessment or report bytes."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.cli._terminal import styled
from qmstrace.render._style import Style

ANSI = re.compile(r"\x1b\[[0-9;]*m")
runner = CliRunner()


@pytest.fixture(autouse=True)
def terminal_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("NO_COLOR", "FORCE_COLOR", "PY_COLORS", "GITHUB_ACTIONS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")


@pytest.mark.parametrize(
    ("no_color", "force", "tty", "term", "expected"),
    [
        ("1", "1", True, "xterm", False),
        ("0", "1", True, "xterm", False),
        ("", "1", False, "dumb", True),
        ("", "0", False, "xterm", False),
        ("", "", True, "dumb", False),
        ("", "", True, "xterm", True),
        ("", "", False, "xterm", False),
    ],
)
def test_style_policy_is_per_stream(
    monkeypatch: pytest.MonkeyPatch,
    no_color: str,
    force: str,
    tty: bool,
    term: str,
    expected: bool,
) -> None:
    class Stream:
        def isatty(self) -> bool:
            return tty

    monkeypatch.setenv("NO_COLOR", no_color)
    monkeypatch.setenv("FORCE_COLOR", force)
    monkeypatch.setenv("TERM", term)
    assert styled(Stream()) == expected


@pytest.mark.verifies("REQ-QMT-15", "DSN-QMT-12")
@pytest.mark.parametrize(
    "command",
    [
        ["status"],
        ["check"],
        ["check", "--quiet"],
        ["rules"],
        ["paths"],
        ["thread", "REQ-SVC-01"],
        ["impact", "REQ-SVC-01"],
    ],
)
def test_color_only_adds_ansi_to_reports(project: Path, command: list[str]) -> None:
    args = ["-C", str(project / "service"), *command]
    plain = runner.invoke(app, args, env={"NO_COLOR": "1"})
    color = runner.invoke(app, args, env={"FORCE_COLOR": "1"}, color=True)
    assert color.exit_code == plain.exit_code
    assert "\x1b[" in color.stdout
    assert ANSI.sub("", color.stdout) == plain.stdout
    assert color.stderr == plain.stderr


def test_help_mode_does_not_leak_between_invocations() -> None:
    rich = runner.invoke(app, ["check", "--help"], env={"FORCE_COLOR": "1"}, color=True)
    plain = runner.invoke(app, ["check", "--help"], env={"NO_COLOR": "1", "FORCE_COLOR": "1"})
    assert rich.exit_code == plain.exit_code == 0
    assert "╭" in rich.stdout and "╭" not in plain.stdout
    assert "\x1b[" not in plain.stdout


def test_semantic_style_preserves_literal_markup() -> None:
    value = "REQ-SVC-01 [frozen] — title [bold] Ω"
    assert ANSI.sub("", Style(True).heading(value)) == value
    assert Style().heading(value) == value


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX PTY")
def test_real_terminal_and_redirected_output(project: Path) -> None:
    import pty

    argv = [
        sys.executable,
        "-c",
        "from qmstrace.cli import app; app()",
        "-C",
        str(project / "service"),
        "status",
    ]
    env = dict(os.environ)
    plain = subprocess.run(argv, capture_output=True, env=env, check=True).stdout
    assert b"\x1b[" not in plain
    master, slave = pty.openpty()
    try:
        with subprocess.Popen(argv, stdout=slave, stderr=subprocess.PIPE, env=env) as child:
            os.close(slave)
            chunks = []
            while True:
                try:
                    block = os.read(master, 65536)
                except OSError:
                    break
                if not block:
                    break
                chunks.append(block)
            assert child.wait(timeout=30) == 0
        color = b"".join(chunks).decode().replace("\r\n", "\n")
    finally:
        os.close(master)
    assert "\x1b[" in color
    assert ANSI.sub("", color).encode() == plain


def test_results_verdicts_and_literal_long_titles_preserve_bytes(project: Path) -> None:
    root = project / "service"
    source = root / "docs/req/service-srs.md"
    literal = "A call carries a key [bold] [frozen] Ω " + "long title " * 35
    source.write_text(source.read_text().replace("A call carries a key", literal))
    (root / "report.xml").write_bytes(
        (Path(__file__).parents[1] / "fixtures/junit/service.xml").read_bytes()
    )
    args = ["-C", str(root), "results", "report.xml"]
    plain = runner.invoke(app, args)
    color = runner.invoke(app, args, env={"FORCE_COLOR": "1"}, color=True)
    assert color.exit_code == plain.exit_code == 0
    assert "\x1b[31mfail" in color.stdout and "\x1b[32mpass" in color.stdout
    assert literal.strip() in color.stdout
    assert ANSI.sub("", color.stdout) == plain.stdout


def test_narrow_rich_help_preserves_options_and_plain_mode() -> None:
    rich = runner.invoke(
        app, ["check", "--help"], env={"FORCE_COLOR": "1"}, color=True, terminal_width=48
    )
    plain = runner.invoke(app, ["check", "--help"], env={"NO_COLOR": "1"}, terminal_width=48)
    assert rich.exit_code == plain.exit_code == 0
    assert "--strict" in ANSI.sub("", rich.stdout)
    assert "--json" in ANSI.sub("", rich.stdout)
    assert "╭" not in plain.stdout


def test_force_color_survives_real_redirected_stdout(project: Path) -> None:
    argv = [
        sys.executable,
        "-c",
        "from qmstrace.cli import app; app()",
        "-C",
        str(project / "service"),
        "status",
    ]
    environment = dict(os.environ, NO_COLOR="", FORCE_COLOR="1")
    forced = subprocess.run(argv, capture_output=True, text=True, env=environment, check=True)
    assert "\x1b[" in forced.stdout
    plain = subprocess.run(
        argv, capture_output=True, text=True, env={**environment, "NO_COLOR": "1"}, check=True
    )
    assert "\x1b[" not in plain.stdout
    assert ANSI.sub("", forced.stdout) == plain.stdout


def test_force_color_survives_real_redirected_stderr(project: Path) -> None:
    argv = [
        sys.executable,
        "-c",
        "from qmstrace.cli import app; app()",
        "-C",
        str(project / "service"),
        "thread",
        "REQ-SVC-99",
    ]
    environment = dict(os.environ, NO_COLOR="", FORCE_COLOR="1")
    forced = subprocess.run(argv, capture_output=True, text=True, env=environment)
    plain = subprocess.run(
        argv, capture_output=True, text=True, env={**environment, "NO_COLOR": "1"}
    )
    assert forced.returncode == plain.returncode == 2
    assert not forced.stdout and not plain.stdout
    assert "\x1b[" in forced.stderr
    assert ANSI.sub("", forced.stderr) == plain.stderr


@pytest.mark.verifies("DSN-QMT-01", "DSN-QMT-12")
@pytest.mark.parametrize("mode", ["text", "json", "diagnostic"])
def test_redirected_cli_is_utf8_even_with_a_legacy_python_codepage(
    project: Path, mode: str
) -> None:
    root = project / "service"
    if mode == "diagnostic":
        config = root / "qmstrace.toml"
        config.write_text("unknown_setting = true\n" + config.read_text(), encoding="utf-8")
    arguments = ["status", "--json"] if mode == "json" else ["paths"]
    result = subprocess.run(
        [sys.executable, "-c", "from qmstrace.cli import app; app()", "-C", str(root), *arguments],
        env={**os.environ, "PYTHONIOENCODING": "cp1252", "NO_COLOR": "1"},
        capture_output=True,
        check=False,
    )
    assert result.returncode == (2 if mode == "diagnostic" else 0)
    output = result.stderr if mode == "diagnostic" else result.stdout
    assert "—" in output.decode("utf-8")
    assert (result.stdout if mode == "diagnostic" else result.stderr) == b""


def test_encoding_policy_is_per_stream_and_keeps_terminal_encoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from io import BytesIO, TextIOWrapper

    from qmstrace.cli._terminal import _utf8_pipes

    class Terminal(TextIOWrapper):
        def isatty(self) -> bool:
            return True

    terminal = Terminal(BytesIO(), encoding="cp1252")
    pipe = TextIOWrapper(BytesIO(), encoding="cp1252")
    with monkeypatch.context() as context:
        context.setattr(sys, "stdout", terminal)
        context.setattr(sys, "stderr", pipe)
        _utf8_pipes()
        assert terminal.encoding == "cp1252"
        assert pipe.encoding == "utf-8"
    terminal.close()
    pipe.close()
