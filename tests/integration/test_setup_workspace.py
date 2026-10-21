"""Setup preserves authored files and produces runnable pytest registration."""

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.core import setup
from qmstrace.core.errors import CouldNotJudge
from qmstrace.workspace import Workspace


@pytest.mark.verifies("REQ-QMT-12")
def test_new_repo_is_idempotent_and_its_marker_runs(tmp_path: Path) -> None:
    first = Workspace.initialize(tmp_path, subject="service", key="SVC")
    assert first[0].startswith("starter: python")
    assert all(s.startswith("updated:") for s in first[1:])
    assert "service (SVC)" in (tmp_path / "AGENTS.md").read_text()
    config = Workspace.open(tmp_path).config
    assert config.schema_form.value == "the repo's own"
    assert not config.baselines and not config.externals
    second = Workspace.initialize(tmp_path)
    assert all(s.startswith("unchanged:") for s in second)
    (tmp_path / "test_example.py").write_text(
        'import pytest\n@pytest.mark.verifies("REQ-SVC-01")\ndef test_it(): assert True\n'
    )
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "--strict-markers", "-q"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr


def test_refresh_existing_nested_config_and_symlinked_guide(project: Path) -> None:
    root = project / "service"
    before = (root / "qmstrace.toml").read_bytes()
    (root / "guide.md").write_text("Before\n")
    (root / "AGENTS.md").symlink_to("guide.md")
    Workspace.initialize(root / "src")
    assert (root / "AGENTS.md").is_symlink()
    assert (root / "guide.md").read_text().startswith("Before\n")
    assert (root / "qmstrace.toml").read_bytes() == before
    assert all(s.startswith("unchanged:") for s in Workspace.initialize(root))
    with pytest.raises(CouldNotJudge, match="Starter options"):
        Workspace.initialize(root, subject="wrong")


@pytest.mark.parametrize(
    "guide", ["<!-- qmstrace:begin -->", "<!-- qmstrace:end --><!-- qmstrace:begin -->"]
)
def test_bad_guides_write_nothing(tmp_path: Path, guide: str) -> None:
    (tmp_path / "AGENTS.md").write_text(guide)
    with pytest.raises(CouldNotJudge):
        Workspace.initialize(tmp_path)
    assert not (tmp_path / "qmstrace.toml").exists()
    assert (tmp_path / "AGENTS.md").read_text() == guide


def test_symlink_outside_repo_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "guide.md"
    outside.write_text("keep")
    (root / "AGENTS.md").symlink_to(outside)
    with pytest.raises(CouldNotJudge, match="leaves"):
        Workspace.initialize(root)
    assert outside.read_text() == "keep"
    assert not (root / "qmstrace.toml").exists()


def test_edited_skill_is_preserved(tmp_path: Path) -> None:
    Workspace.initialize(tmp_path)
    skill = tmp_path / setup.SKILL_FILE
    skill.write_text("edited")
    with pytest.raises(CouldNotJudge, match="skill differs"):
        Workspace.initialize(tmp_path)
    assert skill.read_text() == "edited"


@pytest.mark.parametrize(
    "name,content",
    [
        ("pyproject.toml", '[project]\nname="example"\n'),
        ("tox.ini", "[pytest]\naddopts = -q\n"),
        ("setup.cfg", "[tool:pytest]\naddopts = -q\n"),
        ("pytest.toml", '[pytest]\naddopts = ["-q"]\n'),
        ("pyproject.toml", '[tool.pytest]\naddopts = ["-q"]\n'),
        ("pyproject.toml", '[tool.pytest.ini_options]\nmarkers = ["slow: expensive"]\n'),
    ],
)
def test_existing_settings_remain_runnable(tmp_path: Path, name: str, content: str) -> None:
    (tmp_path / name).write_text(content)
    Workspace.initialize(tmp_path)
    assert not (tmp_path / "pytest.ini").exists()
    assert all(s.startswith("unchanged:") for s in Workspace.initialize(tmp_path))
    (tmp_path / "test_it.py").write_text(
        'import pytest\n@pytest.mark.verifies("REQ-PROD-01")\ndef test_it(): pass\n'
    )
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "--strict-markers", "-q"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr


def test_init_cli_goldens(tmp_path: Path, golden) -> None:
    runner = CliRunner()
    first = runner.invoke(app, ["-C", str(tmp_path), "init"])
    assert first.exit_code == 0, first.output
    golden(Path("tests/cli/golden/init-new.txt"), first.output)
    again = runner.invoke(app, ["init", "-C", str(tmp_path)])
    assert again.exit_code == 0
    golden(Path("tests/cli/golden/init-again.txt"), again.output)
    assert runner.invoke(app, ["init", "-C", str(tmp_path)]).output == again.output


def test_invalid_inputs_are_usage_failures(tmp_path: Path, project: Path) -> None:
    for path, options in [
        (tmp_path / "missing", []),
        (tmp_path, ["--subject", "../bad"]),
        (tmp_path, ["--key", "bad"]),
    ]:
        result = CliRunner().invoke(app, ["init", "-C", str(path), *options])
        assert result.exit_code == 2, result.output


# ── the skill's home, and the link Claude Code reads ────────────────────────────────────────


def test_the_skill_is_linked_where_the_repo_has_claude(tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir()
    first = Workspace.initialize(tmp_path)
    assert f"updated: {setup.CLAUDE_LINK}" in first
    assert os.readlink(tmp_path / setup.CLAUDE_LINK) == setup.CLAUDE_LINK_TARGET
    packaged = (tmp_path / setup.SKILL_FILE).read_text()
    assert (tmp_path / setup.CLAUDE_LINK / "SKILL.md").read_text() == packaged
    assert f"unchanged: {setup.CLAUDE_LINK}" in Workspace.initialize(tmp_path)
    assert f"`{setup.SKILL_FILE}`" in (tmp_path / "AGENTS.md").read_text()


@pytest.mark.parametrize("claude", [None, "link"])
def test_no_link_without_a_claude_folder_of_its_own(tmp_path: Path, claude: str | None) -> None:
    if claude == "link":
        (tmp_path / "elsewhere").mkdir()
        (tmp_path / ".claude").symlink_to("elsewhere")
    done = Workspace.initialize(tmp_path)
    assert not any(".claude" in line for line in done)
    assert not os.path.lexists(tmp_path / setup.CLAUDE_LINK)
    assert claude or not (tmp_path / ".claude").exists()


@pytest.mark.parametrize(
    "canonical,linked", [(".agents/skills", ".claude/skills"), (".claude/skills", ".agents/skills")]
)
def test_one_skills_folder_needs_no_link(tmp_path: Path, canonical: str, linked: str) -> None:
    (tmp_path / canonical).mkdir(parents=True)
    (tmp_path / linked).parent.mkdir(exist_ok=True)
    (tmp_path / linked).symlink_to(Path("..") / canonical)
    done = Workspace.initialize(tmp_path)
    assert not any(line.endswith(setup.CLAUDE_LINK) for line in done)
    assert (tmp_path / setup.CLAUDE_LINK / "SKILL.md").is_file()
    assert (tmp_path / setup.SKILL_FILE).is_file()


def _occupy(root: Path, how: str) -> None:
    link = root / setup.CLAUDE_LINK
    if how == "skills-file":
        (root / ".claude").mkdir()
        (root / ".claude/skills").write_text("not a folder")
        return
    link.parent.mkdir(parents=True)
    if how == "folder":
        link.mkdir()
    elif how == "file":
        link.write_text("a file")
    elif how == "dangling":
        link.symlink_to("../../nowhere")
    elif how == "elsewhere":
        (root / "docs").mkdir()
        link.symlink_to("../../docs")
    elif how == "outside":
        link.symlink_to(root.parent)


@pytest.mark.parametrize(
    "how", ["folder", "file", "dangling", "elsewhere", "outside", "skills-file"]
)
@pytest.mark.verifies("REQ-QMT-12")
def test_what_setup_did_not_write_is_refused(tmp_path: Path, how: str) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _occupy(root, how)
    with pytest.raises(CouldNotJudge, match="holds something setup did not write"):
        Workspace.initialize(root)
    assert not (root / "qmstrace.toml").exists()
    assert not (root / ".agents").exists()


def test_a_skill_in_the_old_home_is_refused(tmp_path: Path) -> None:
    old = tmp_path / setup.LEGACY_SKILL
    old.parent.mkdir(parents=True)
    old.write_text("an earlier copy")
    with pytest.raises(CouldNotJudge, match="skill has moved"):
        Workspace.initialize(tmp_path)
    assert old.read_text() == "an earlier copy"
    assert not (tmp_path / "qmstrace.toml").exists()
    assert not (tmp_path / ".agents").exists()


def test_init_cli_golden_with_claude(tmp_path: Path, golden) -> None:
    (tmp_path / ".claude").mkdir()
    done = CliRunner().invoke(app, ["-C", str(tmp_path), "init"])
    assert done.exit_code == 0, done.output
    golden(Path("tests/cli/golden/init-claude.txt"), done.output)


# ── a ledger that holds the documents (M10c, ADR-0001) ──────────────────────────────────────

LEDGER_GATE = "`qmstrace ledger check --strict` is the coverage gate"


@pytest.mark.verifies("REQ-QMT-19")
def test_an_untraced_ledger_is_set_up_to_hold_the_documents(
    project: Path, golden: Callable[[Path, str], None]
) -> None:
    ledger = project / "ledger"
    first = CliRunner().invoke(
        app, ["init", "-C", str(ledger), "--subject", "service", "--key", "SVC"]
    )
    assert first.exit_code == 0, first.output
    golden(Path("tests/cli/golden/init-ledger.txt"), first.output)
    config = Workspace.open(ledger).config
    assert (config.ledger, config.schema_form.value, config.project) == (".", "by path", "MINI")
    assert [t.name for t in config.item_types.values() if t.declared_here] == [
        "requirement",
        "design_element",
    ]
    guide = (ledger / "AGENTS.md").read_text()
    assert LEDGER_GATE in guide and "qmstrace ledger thread ID" in guide
    assert not (ledger / "pytest.ini").exists() and not (ledger / "pyproject.toml").exists()
    again = Workspace.initialize(ledger)
    assert all(line.startswith(("unchanged:", "next:")) for line in again)


def test_it_is_found_from_inside_an_untraced_ledger(project: Path) -> None:
    inside = project / "ledger" / "change-requests"
    inside.mkdir()
    Workspace.initialize(inside)
    assert (project / "ledger" / "qmstrace.toml").is_file()
    assert not (inside / "qmstrace.toml").exists()


@pytest.mark.verifies("REQ-QMT-19")
def test_a_traced_ledgers_stanza_names_the_ledgers_verbs(split: Path) -> None:
    done = Workspace.initialize(split / "ledger")
    assert not any(line.startswith("next:") for line in done)  # it lists itself already
    guide = (split / "ledger" / "AGENTS.md").read_text()
    assert LEDGER_GATE in guide
    assert "`qmstrace ledger check` lists every reason, in every repo" in guide
    assert "`qmstrace check --strict` is the coverage gate" not in guide


def test_a_product_repos_stanza_keeps_its_own_verbs(split: Path) -> None:
    Workspace.initialize(split / "service")
    guide = (split / "service" / "AGENTS.md").read_text()
    assert "`qmstrace check --strict` is the coverage gate" in guide
    assert "ledger check" not in guide


@pytest.mark.verifies("REQ-QMT-12", "REQ-QMT-21")
def test_init_in_a_csharp_repo_writes_no_pytest_settings(cases: Path) -> None:
    agent = cases / "agent"
    before = sorted(p.name for p in agent.iterdir())
    result = CliRunner().invoke(app, ["-C", str(agent), "init"])
    assert result.exit_code == 0, result.output
    after = sorted(p.name for p in agent.iterdir())
    assert (
        {".agents", "AGENTS.md"} <= set(after) - set(before) <= {".agents", ".claude", "AGENTS.md"}
    )
    assert not (agent / "pytest.ini").exists() and not (agent / "pyproject.toml").exists()
    stanza = (agent / "AGENTS.md").read_text(encoding="utf-8")
    assert "component `csharp-file` in `src/**/*.cs`" in stanza
    assert "automated_test `xunit` in `tests/Agent.Tests/**/*Tests.cs`" in stanza


# ── the starter a repo's shape chooses — #38 (ADR-0006) ─────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-12")
@pytest.mark.parametrize(
    ("build_file", "why"),
    [
        ("App.csproj", "App.csproj"),
        ("App.sln", "App.sln"),
        ("App.slnx", "App.slnx"),
        ("App/App.csproj", "App/App.csproj"),
        ("src/App/App.csproj", "src/App/App.csproj"),
    ],
)
def test_a_dotnet_repo_gets_the_csharp_starter(tmp_path: Path, build_file: str, why: str) -> None:
    built = tmp_path / build_file
    built.parent.mkdir(parents=True, exist_ok=True)
    built.touch()
    written = Workspace.initialize(tmp_path, subject="agent", key="AGT")
    assert written[0] == f"starter: csharp ({why})"
    types = Workspace.open(tmp_path).config.item_types
    assert types["component"].extractor == "csharp-file"
    assert types["automated_test"].extractor == "xunit"
    assert types["requirement"].extractor == "markdown"
    assert not (tmp_path / "pytest.ini").exists() and not (tmp_path / "pyproject.toml").exists()
    assert "component `csharp-file` in `src/**/*.cs`" in (tmp_path / "AGENTS.md").read_text()


@pytest.mark.verifies("REQ-QMT-12")
def test_a_python_repo_and_a_bare_one_keep_the_python_starter(tmp_path: Path) -> None:
    (tmp_path / "declared").mkdir()
    (tmp_path / "declared" / "pyproject.toml").write_text("[project]\nname = 'p'\n")
    declared = Workspace.initialize(tmp_path / "declared")
    assert declared[0] == "starter: python (pyproject.toml)"
    (tmp_path / "bare").mkdir()
    bare = Workspace.initialize(tmp_path / "bare")
    assert bare[0] == "starter: python (the default; no build file names a language)"
    for repo in ("declared", "bare"):
        types = Workspace.open(tmp_path / repo).config.item_types
        assert types["component"].extractor == "python-module"
        assert types["automated_test"].extractor == "pytest"


@pytest.mark.verifies("REQ-QMT-12")
def test_a_repo_of_two_languages_is_refused_and_writes_nothing(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'p'\n")
    (tmp_path / "App.csproj").touch()
    with pytest.raises(CouldNotJudge, match=r"two languages: pyproject\.toml and App\.csproj"):
        Workspace.initialize(tmp_path)
    assert not (tmp_path / "qmstrace.toml").exists() and not (tmp_path / "AGENTS.md").exists()
    written = Workspace.initialize(tmp_path, language="csharp")
    assert written[0] == "starter: csharp (--language)"
    assert Workspace.open(tmp_path).config.item_types["component"].extractor == "csharp-file"


@pytest.mark.verifies("REQ-QMT-12")
def test_language_overrides_what_the_build_files_say(tmp_path: Path) -> None:
    (tmp_path / "dotnet").mkdir()
    (tmp_path / "dotnet" / "App.csproj").touch()
    written = Workspace.initialize(tmp_path / "dotnet", language="python")
    assert written[0] == "starter: python (--language)"
    types = Workspace.open(tmp_path / "dotnet").config.item_types
    assert types["component"].extractor == "python-module"
    assert (tmp_path / "dotnet" / "pytest.ini").exists()


@pytest.mark.verifies("REQ-QMT-12")
def test_a_language_with_no_starter_is_refused_before_any_write(tmp_path: Path) -> None:
    with pytest.raises(CouldNotJudge, match="no rust starter"):
        Workspace.initialize(tmp_path, language="rust")
    assert not any(tmp_path.iterdir())


@pytest.mark.verifies("REQ-QMT-12", "REQ-QMT-19")
def test_a_ledger_declares_no_language(project: Path) -> None:
    ledger = project / "ledger"
    with pytest.raises(CouldNotJudge, match="not its code"):
        Workspace.initialize(ledger, language="csharp")
    assert not (ledger / "qmstrace.toml").exists()
    written = Workspace.initialize(ledger, subject="service", key="SVC")
    assert not any(line.startswith("starter:") for line in written)


@pytest.mark.verifies("REQ-QMT-12")
def test_the_starter_options_need_a_configuration_to_create(tmp_path: Path) -> None:
    Workspace.initialize(tmp_path)
    for options in ({"subject": "other"}, {"key": "OTHER"}, {"language": "csharp"}):
        with pytest.raises(CouldNotJudge, match="Starter options"):
            Workspace.initialize(tmp_path, **options)  # type: ignore[arg-type]


def test_init_csharp_cli_golden(tmp_path: Path, golden: Callable[[Path, str], None]) -> None:
    (tmp_path / "App.csproj").touch()
    result = CliRunner().invoke(
        app, ["-C", str(tmp_path), "init", "--subject", "agent", "--key", "AGT"]
    )
    assert result.exit_code == 0, result.output
    golden(Path("tests/cli/golden/init-csharp.txt"), result.output)
    written = (tmp_path / "qmstrace.toml").read_text(encoding="utf-8")
    golden(Path("tests/cli/golden/init-csharp-config.toml"), written)
