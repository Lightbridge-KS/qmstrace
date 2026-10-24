"""Checkout maps as CLI users meet them: selection, evidence and safe writes."""

import json
import os
import shutil
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from qmstrace import __version__
from qmstrace.cli import app
from qmstrace.infra import locations
from qmstrace.infra.tree import WorkingTree

GOLDEN = Path(__file__).parent / "golden"
FIXTURES = Path(__file__).parents[1] / "fixtures"
runner = CliRunner()


@dataclass
class Mapped:
    original: Path
    repos: dict[str, Path]
    file: Path
    project: str

    def write(self, file: Path | None = None, *, omit: str | None = None) -> Path:
        target = file or self.file
        target.parent.mkdir(parents=True, exist_ok=True)
        rows = ["version = 1", f'project = "{self.project}"', 'ledger_repo = "ledger"', "[repos]"]
        rows += [
            f"{name} = {json.dumps(Path(os.path.relpath(root, target.parent)).as_posix())}"
            for name, root in sorted(self.repos.items())
            if name != omit
        ]
        target.write_text("\n".join(rows) + "\n", encoding="utf-8")
        return target


def relocate(base: Path, embed: Callable[..., str]) -> Mapped:
    """Embed before relocation; retain the original layout as a readable fallback decoy."""
    schema = (base / "ledger/qmstrace.schema.toml").read_text(encoding="utf-8")
    project = tomllib.loads(schema)["project"]
    repos = {}
    for name, folder in (("ledger", "records"), ("service", "backend"), ("client", "frontend")):
        source = base / name
        if name != "ledger":
            config = source / "qmstrace.toml"
            config.write_text(embed(config.read_text(encoding="utf-8"), schema), encoding="utf-8")
        destination = base.parent / "checkouts" / folder
        shutil.copytree(source, destination)
        repos[name] = destination
    mapped = Mapped(base, repos, base.parent / "maps/local.toml", project)
    mapped.write()
    return mapped


@pytest.fixture(autouse=True)
def invocation_directory(git_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    # git_env supplies a fresh HOME for each case, including user-map discovery tests.
    monkeypatch.setenv("USERPROFILE", str(Path.home()))
    monkeypatch.chdir(Path.home())


@pytest.fixture
def mapped(split: Path, embed: Callable[..., str]) -> Mapped:
    return relocate(split, embed)


def run(root: Path, *words: str, workspace: Path | None = None) -> Result:
    selector = ["--workspace", str(workspace)] if workspace is not None else []
    return runner.invoke(app, ["-C", str(root), *selector, *words], prog_name="qmstrace")


def refuse(result: Result, reason: str) -> None:
    assert result.exit_code == 2, result.output
    assert result.stdout == "", "a refused command must not emit a partial result"
    assert reason in result.stderr, result.output


def files_under(root: Path) -> dict[str, bytes]:
    return {
        file.relative_to(root).as_posix(): file.read_bytes()
        for file in root.rglob("*")
        if file.is_file() and ".git" not in file.relative_to(root).parts
    }


def test_paths_default_golden(split: Path, golden: Callable[[Path, str], None]) -> None:
    result = run(split / "service", "paths")
    assert result.exit_code == 0, result.output
    assert "tracked paths (no map selected)" in result.stdout
    golden(GOLDEN / "paths-default.txt", result.stdout)


def test_paths_selected_golden(mapped: Mapped, golden: Callable[[Path, str], None]) -> None:
    result = run(mapped.repos["service"], "paths", workspace=mapped.file)
    assert result.exit_code == 0, result.output
    assert "ledger: ledger:." in result.stdout
    assert "repo service: service:. — available · current repo" in result.stdout
    assert str(mapped.file.parent.parent) not in result.stdout
    golden(GOLDEN / "paths-map.txt", result.stdout)


@pytest.mark.parametrize("selected", [False, True])
def test_paths_reads_no_sources_or_git(
    mapped: Mapped, monkeypatch: pytest.MonkeyPatch, selected: bool
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("paths must not scan sources, construct a graph or read Git history")

    monkeypatch.setattr(WorkingTree, "files", forbidden)
    monkeypatch.setattr("qmstrace.infra.git.subprocess.run", forbidden)
    monkeypatch.setattr("qmstrace.core.graph.TraceGraph.build", forbidden)
    root = mapped.repos["ledger"] if selected else mapped.original / "ledger"
    result = run(root, "paths", workspace=mapped.file if selected else None)
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize("placement", ["root", "leaf"])
@pytest.mark.parametrize("directory_placement", ["root", "leaf"])
def test_relative_selector_uses_effective_minus_c_directory(
    mapped: Mapped, placement: str, directory_placement: str
) -> None:
    start = mapped.repos["service"] / "src/service"
    relative = os.path.relpath(mapped.file, start)
    before = ["-C", str(start)] if directory_placement == "root" else []
    after = ["-C", str(start)] if directory_placement == "leaf" else []
    (before if placement == "root" else after).extend(["--workspace", relative])
    result = runner.invoke(app, [*before, "paths", *after])
    assert result.exit_code == 0, result.output
    assert "explicit map local.toml" in result.stdout
    assert "repo service: service:. — available · current repo" in result.stdout


def test_explicit_overrides_environment_ancestor_and_user(
    mapped: Mapped, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = mapped.repos["service"]
    for file in (root / ".qmstrace/workspace.toml", Path.home() / ".qmstrace/workspaces/bad.toml"):
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("broken = [", encoding="utf-8")
    monkeypatch.setenv("QMSTRACE_WORKSPACE", "missing.toml")
    result = run(root, "paths", workspace=mapped.file)
    assert result.exit_code == 0, result.output
    assert "explicit map local.toml" in result.stdout


def test_environment_relative_selector_overrides_ancestor(
    mapped: Mapped, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = mapped.repos["service"]
    bad = root / ".qmstrace/workspace.toml"
    bad.parent.mkdir()
    bad.write_text("broken = [", encoding="utf-8")
    start = root / "src/service"
    monkeypatch.setenv("QMSTRACE_WORKSPACE", os.path.relpath(mapped.file, start))
    result = run(start, "paths")
    assert result.exit_code == 0, result.output
    assert "environment map local.toml" in result.stdout


def test_nearest_ancestor_is_measured_from_trace_root(mapped: Mapped) -> None:
    root = mapped.repos["service"]
    mapped.write(root / ".qmstrace/workspace.toml")
    farther = root.parent / ".qmstrace/workspace.toml"
    farther.parent.mkdir()
    farther.write_text("broken = [", encoding="utf-8")
    nested = root / "src/service/.qmstrace/workspace.toml"
    nested.parent.mkdir()
    nested.write_text("broken = [", encoding="utf-8")
    result = run(root / "src/service", "paths")
    assert result.exit_code == 0, result.output
    assert "ancestor map workspace.toml" in result.stdout


def test_user_discovery_selects_unique_matching_checkout(mapped: Mapped) -> None:
    directory = Path.home() / ".qmstrace/workspaces"
    mapped.write(directory / "selected.toml")
    other = mapped.write(directory / "other.toml")
    other.write_text(other.read_text().replace('project = "SPLIT"', 'project = "OTHER"'))
    result = run(mapped.repos["service"], "paths")
    assert result.exit_code == 0, result.output
    assert "user map selected.toml" in result.stdout


def test_malformed_user_candidate_is_never_hidden_by_valid_match(mapped: Mapped) -> None:
    directory = Path.home() / ".qmstrace/workspaces"
    mapped.write(directory / "selected.toml")
    (directory / "unrelated-broken.toml").write_text("broken = [", encoding="utf-8")
    refuse(run(mapped.repos["service"], "paths"), "User workspace-map discovery failed")


def test_multiple_user_matches_require_explicit_selection(mapped: Mapped) -> None:
    directory = Path.home() / ".qmstrace/workspaces"
    first = mapped.write(directory / "first.toml")
    mapped.write(directory / "second.toml")
    refuse(run(mapped.repos["service"], "paths"), "Several user workspace maps match")
    assert run(mapped.repos["service"], "paths", workspace=first).exit_code == 0


@pytest.mark.parametrize("stage", ["explicit", "environment", "ancestor"])
def test_invalid_selected_map_does_not_fall_back(
    mapped: Mapped, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    root = mapped.repos["service"]
    mapped.write(Path.home() / ".qmstrace/workspaces/valid.toml")
    bad = root / ".qmstrace/workspace.toml" if stage == "ancestor" else mapped.file
    bad.parent.mkdir(exist_ok=True)
    bad.write_text("broken = [", encoding="utf-8")
    if stage == "environment":
        monkeypatch.setenv("QMSTRACE_WORKSPACE", str(bad))
    result = run(root, "paths", workspace=bad if stage == "explicit" else None)
    refuse(result, "invalid TOML")


@pytest.mark.parametrize("placement", ["root", "leaf", "both"])
@pytest.mark.parametrize("command", [["paths"], ["ledger", "check", "--quiet"]])
def test_duplicate_workspace_is_usage_error_without_stdout(
    mapped: Mapped, placement: str, command: list[str]
) -> None:
    option = ["--workspace", str(mapped.file)]
    before = option * (2 if placement == "root" else 1) if placement != "leaf" else []
    after = option * (2 if placement == "leaf" else 1) if placement != "root" else []
    result = runner.invoke(app, ["-C", str(mapped.repos["ledger"]), *before, *command, *after])
    refuse(result, "given twice")


@pytest.mark.parametrize(
    "words", [["--help"], ["paths", "--help"], ["ledger", "check", "--help"], ["--version"]]
)
def test_help_and_version_do_not_read_maps(
    mapped: Mapped, monkeypatch: pytest.MonkeyPatch, words: list[str]
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("help and version must not read workspace maps")

    monkeypatch.setattr(locations, "_read", forbidden)
    monkeypatch.setenv("QMSTRACE_WORKSPACE", "missing.toml")
    result = runner.invoke(app, ["--workspace", "also-missing.toml", *words])
    assert result.exit_code == 0, result.output
    if words == ["--version"]:
        assert result.stdout == f"qmstrace {__version__}\n"


@pytest.mark.parametrize(
    "command",
    [
        ["status"],
        ["thread", "DSN-SVC-01"],
        ["ledger", "check"],
        ["ledger", "thread", "REQ-SVC-01"],
        ["ledger", "impact", "REQ-SVC-01"],
        ["ledger", "table", "matrix"],
    ],
)
def test_each_command_selects_its_map_once(
    mapped: Mapped, monkeypatch: pytest.MonkeyPatch, command: list[str]
) -> None:
    read = locations._read
    calls = []

    def counted(file: Path):
        calls.append(file)
        return read(file)

    monkeypatch.setattr(locations, "_read", counted)
    root = mapped.repos["ledger" if command[0] == "ledger" else "service"]
    result = run(root, *command, workspace=mapped.file)
    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert "workspace: explicit map local.toml" in result.stdout


@pytest.mark.parametrize("unavailable", ["omitted", "missing"])
def test_missing_member_stays_unavailable_despite_readable_legacy_path(
    mapped: Mapped, unavailable: str, golden: Callable[[Path, str], None]
) -> None:
    # Put the selected ledger back at its tracked location so ../client really is readable.
    mapped.repos["ledger"] = mapped.original / "ledger"
    if unavailable == "omitted":
        mapped.write(omit="client")
    else:
        mapped.repos["client"] = mapped.file.parent / "absent"
        mapped.write()
    result = run(mapped.repos["service"], "check", "--quiet", workspace=mapped.file)
    assert result.exit_code == 0, result.output
    assert "workspace: explicit map local.toml" in result.stdout
    assert "sibling client: NOT REACHABLE" in result.stdout
    assert "workspace map selected" in result.stdout.splitlines()[-1]
    if unavailable == "omitted":
        assert "not mapped" in result.stdout
        golden(GOLDEN / "workspace-check-quiet.txt", result.stdout)
    paths = run(mapped.repos["service"], "paths", workspace=mapped.file)
    assert paths.exit_code == 0
    assert "NOT AVAILABLE" in paths.stdout
    refuse(run(mapped.repos["ledger"], "ledger", "check", workspace=mapped.file), "client")


def test_local_results_and_graph_retain_selected_sources(
    project: Path, embed: Callable[..., str]
) -> None:
    mapped = relocate(project, embed)
    root = mapped.repos["service"]
    start = root / "src/service"
    shutil.copyfile(FIXTURES / "junit/service.xml", start / "report.xml")
    result = run(start, "results", "report.xml", workspace=mapped.file)
    assert result.exit_code == 0, result.output
    assert "workspace: explicit map local.toml" in result.stdout
    assert "verified against ledger:agreement.md" in result.stdout
    assert "ledger:change-requests" in result.stdout
    assert "source: workspace: explicit map local.toml" in result.stdout.splitlines()[-1]
    assert "REQ-SVC-01  pass" in result.stdout
    graph = run(start, "graph", "--out", "view.html", workspace=mapped.file)
    assert graph.exit_code == 0, graph.output
    html = (start / "view.html").read_text(encoding="utf-8")
    assert "workspace: explicit map local.toml" in html
    assert "ledger:agreement.md" in html
    assert not (root / "view.html").exists()
    assert str(project.parent) not in html


@pytest.mark.parametrize(
    "command", [["thread", "REQ-SVC-01"], ["impact", "REQ-SVC-01"], ["check", "--strict"]]
)
def test_ledger_text_commands_use_resolved_roots(mapped: Mapped, command: list[str]) -> None:
    result = run(mapped.repos["ledger"], "ledger", *command, workspace=mapped.file)
    assert result.exit_code == 0, result.output
    assert "workspace: explicit map local.toml" in result.stdout
    if command[0] == "check":
        assert "service:." in result.stdout and "client:." in result.stdout
    else:
        assert "service:tests/" in result.stdout and "client:tests/" in result.stdout
    assert str(mapped.original.parent) not in result.stdout


def test_ledger_matrix_is_json_with_relative_locations_and_source(mapped: Mapped) -> None:
    result = run(mapped.repos["ledger"], "ledger", "table", "matrix", workspace=mapped.file)
    assert result.exit_code == 0, result.output
    document = json.loads(result.stdout)
    assert document["format"] == "qmstrace.table/2"
    assert {r["repo"]: r["location"] for r in document["read"]} == {
        "ledger": {"repo": "ledger", "path": ".", "line": None},
        "service": {"repo": "service", "path": ".", "line": None},
        "client": {"repo": "client", "path": ".", "line": None},
    }
    assert any("workspace: explicit map local.toml" in n for n in document["notices"])
    assert str(mapped.original.parent) not in result.stdout


@pytest.mark.parametrize(
    "command",
    [
        ["check"],
        ["thread", "REQ-SVC-01"],
        ["impact", "REQ-SVC-01"],
        ["table", "matrix"],
        ["copy-schema"],
    ],
)
def test_selected_map_does_not_redirect_ledger_commands_from_product(
    mapped: Mapped, command: list[str]
) -> None:
    refuse(run(mapped.repos["service"], "ledger", *command, workspace=mapped.file), "ledger repo")


def test_schema_copy_updates_mapped_destinations_only(mapped: Mapped) -> None:
    schema = mapped.repos["ledger"] / "qmstrace.schema.toml"
    schema.write_text(
        schema.read_text().replace("no test verifies it yet.", "no test verifies this yet.")
    )
    original = files_under(mapped.original)
    before = {name: files_under(root) for name, root in mapped.repos.items()}
    result = run(mapped.repos["ledger"], "ledger", "copy-schema", workspace=mapped.file)
    assert result.exit_code == 0, result.output
    assert "service:qmstrace.toml" in result.stdout
    assert "client:qmstrace.toml" in result.stdout
    assert files_under(mapped.original) == original
    for name in ("service", "client"):
        after = files_under(mapped.repos[name])
        assert after.keys() == before[name].keys()
        assert after.pop("qmstrace.toml") != before[name]["qmstrace.toml"]
        assert after == {k: v for k, v in before[name].items() if k != "qmstrace.toml"}
    repeated = run(mapped.repos["ledger"], "ledger", "copy-schema", workspace=mapped.file)
    assert repeated.exit_code == 0, repeated.output
    assert "unchanged" in repeated.stdout


@pytest.mark.parametrize("problem", ["omitted", "missing", "invalid-config"])
def test_schema_copy_failure_writes_nothing(mapped: Mapped, problem: str) -> None:
    schema = mapped.repos["ledger"] / "qmstrace.schema.toml"
    schema.write_text(
        schema.read_text().replace("no test verifies it yet.", "no test verifies this yet.")
    )
    if problem == "omitted":
        mapped.write(omit="service")  # client would otherwise be refreshed first
    elif problem == "missing":
        mapped.repos["service"] = mapped.file.parent / "missing"
        mapped.write()
    else:
        (mapped.repos["service"] / "qmstrace.toml").write_text("broken = [", encoding="utf-8")
    before = files_under(mapped.original.parent)
    refuse(
        run(mapped.repos["ledger"], "ledger", "copy-schema", workspace=mapped.file),
        "nothing was written",
    )
    assert files_under(mapped.original.parent) == before


def test_init_preserves_workspace_and_unrelated_local_state(mapped: Mapped) -> None:
    root = mapped.repos["service"]
    file = mapped.write(root / ".qmstrace/workspace.toml")
    (root / ".qmstrace/notes.txt").write_text("local notes\n", encoding="utf-8")
    before = files_under(root / ".qmstrace")
    config = (root / "qmstrace.toml").read_bytes()
    result = run(
        root / "src/service", "init", "--workspace", os.path.relpath(file, root / "src/service")
    )
    assert result.exit_code == 0, result.output
    assert "workspace: explicit map workspace.toml" in result.stdout
    assert files_under(root / ".qmstrace") == before
    assert (root / "qmstrace.toml").read_bytes() == config
    written = files_under(root)
    assert run(root, "init").exit_code == 0
    assert files_under(root) == written


def test_new_ledger_init_reports_selected_map(mapped: Mapped) -> None:
    root = mapped.repos["ledger"]
    (root / "qmstrace.toml").unlink()
    result = run(root, "init", workspace=mapped.file)
    assert result.exit_code == 0, result.output
    assert "workspace: explicit map local.toml" in result.stdout
    assert (root / "qmstrace.toml").is_file()


@pytest.mark.parametrize("content", [None, "version = = 1"])
def test_new_init_refuses_invalid_selected_map_before_writing(
    tmp_path: Path, content: str | None
) -> None:
    root = tmp_path / "new-product"
    root.mkdir()
    file = tmp_path / "bad.toml"
    if content is not None:
        file.write_text(content, encoding="utf-8")
    refused = run(root, "init", workspace=file)
    refuse(refused, "Workspace map")
    assert list(root.iterdir()) == []


def test_init_relative_environment_selector_starts_at_invocation_directory(
    mapped: Mapped, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = mapped.repos["service"]
    nested = root / "src"
    monkeypatch.setenv("QMSTRACE_WORKSPACE", os.path.relpath(mapped.file, nested))
    result = run(nested, "init")
    assert result.exit_code == 0, result.output
    assert (root / "qmstrace.toml").is_file()
