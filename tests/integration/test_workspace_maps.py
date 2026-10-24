"""Machine-local maps select one scope and wire every working-tree location consumer."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from qmstrace.core.config import SchemaForm, TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.graph import Home
from qmstrace.infra import locations
from qmstrace.infra.git import GitCli
from qmstrace.infra.tree import GitTree
from qmstrace.render import text
from qmstrace.workspace import Workspace
from qmstrace.workspace._discovery import _configuration


@pytest.fixture(autouse=True)
def isolated_locations(git_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "map-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("QMSTRACE_WORKSPACE", raising=False)


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def mapped(
    file: Path, roots: dict[str, Path], project: str = "MINI", ledger: str = "ledger"
) -> Path:
    entries = "\n".join(
        f"{json.dumps(name)} = {json.dumps(os.path.relpath(path, file.parent))}"
        for name, path in roots.items()
    )
    return write(
        file,
        f'version = 1\nproject = "{project}"\nledger_repo = "{ledger}"\n[repos]\n{entries}\n',
    )


def config_at(project: Path, name: str = "service") -> TraceConfig:
    return TraceConfig.parse(
        (project / name / "qmstrace.toml").read_text(encoding="utf-8"),
        (project / "ledger/qmstrace.schema.toml").read_text(encoding="utf-8"),
    )


@pytest.mark.parametrize("scope", ["explicit", "environment", "ancestor", "user"])
@pytest.mark.verifies("DSN-QMT-10")
def test_discovery_selects_one_scope_and_never_reads_lower_scopes(
    project: Path, monkeypatch: pytest.MonkeyPatch, scope: str
) -> None:
    root = project / "service"
    roots = {name: project / name for name in ("ledger", "service", "client")}
    files = {
        "explicit": mapped(project / "explicit.toml", roots),
        "environment": mapped(project / "environment.toml", roots),
        "ancestor": mapped(root / locations.LOCAL_MAP, roots),
        "user": mapped(Path.home() / ".qmstrace/workspaces/match.toml", roots),
    }
    order = list(files)
    for higher in order[: order.index(scope)]:
        files[higher].unlink()
    # Malformed lower scopes must not even be opened; a user directory must not be listed.
    for lower in order[order.index(scope) + 1 :]:
        files[lower].write_text("not TOML = =", encoding="utf-8")
    if scope in ("explicit", "environment"):
        monkeypatch.setenv("QMSTRACE_WORKSPACE", "../environment.toml")
    read = locations._read
    reads: list[Path] = []

    def selected_only(file: Path):
        reads.append(file)
        assert file.resolve() == files[scope].resolve(), "a lower scope was read"
        return read(file)

    monkeypatch.setattr(locations, "_read", selected_only)
    if scope != "user":

        def no_user_listing(*args, **kwargs):
            pytest.fail("user directory was inspected after selecting a higher scope")

        monkeypatch.setattr(Path, "glob", no_user_listing)
    chosen = locations.discover(
        root, root, config_at(project), Path("../explicit.toml") if scope == "explicit" else None
    )
    assert chosen is not None
    assert chosen.source == scope
    assert chosen.ledger == roots["ledger"].resolve()
    assert dict(chosen.roots) == {name: path.resolve() for name, path in roots.items()}
    assert [path.resolve() for path in reads] == [files[scope].resolve()]
    assert str(project) not in chosen.notice


@pytest.mark.verifies("DSN-QMT-10")
def test_nearest_ancestor_wins_from_a_directory_inside_the_trace_root(project: Path) -> None:
    root = project / "service"
    parent = write(project / locations.LOCAL_MAP, "invalid = =")
    nearest = mapped(root / locations.LOCAL_MAP, {"ledger": project / "ledger", "service": root})
    chosen = locations.discover(root / "src/service", root, config_at(project))
    assert chosen is not None and chosen.filename == nearest.name
    assert chosen.source == "ancestor" and chosen.roots["service"] == root.resolve()
    assert parent.read_text() == "invalid = ="


@pytest.mark.parametrize("scope", ["explicit", "environment", "ancestor"])
@pytest.mark.verifies("DSN-QMT-10")
def test_invalid_selected_map_refuses_instead_of_falling_through(
    project: Path, monkeypatch: pytest.MonkeyPatch, scope: str
) -> None:
    root = project / "service"
    roots = {"ledger": project / "ledger", "service": root}
    mapped(Path.home() / ".qmstrace/workspaces/valid.toml", roots)
    invalid = write(
        root / locations.LOCAL_MAP if scope == "ancestor" else project / "invalid.toml",
        "version = = 1",
    )
    if scope == "environment":
        monkeypatch.setenv("QMSTRACE_WORKSPACE", str(invalid))
    with pytest.raises(CouldNotJudge, match="invalid TOML"):
        locations.discover(root, root, config_at(project), invalid if scope == "explicit" else None)


@pytest.mark.parametrize("selector", ["explicit", "environment"])
@pytest.mark.verifies("DSN-QMT-10")
def test_missing_explicit_or_environment_file_does_not_use_valid_ancestor(
    project: Path, monkeypatch: pytest.MonkeyPatch, selector: str
) -> None:
    root = project / "service"
    mapped(root / locations.LOCAL_MAP, {"ledger": project / "ledger", "service": root})
    missing = project / "missing.toml"
    if selector == "environment":
        monkeypatch.setenv("QMSTRACE_WORKSPACE", str(missing))
    with pytest.raises(CouldNotJudge, match="cannot be read"):
        locations.discover(
            root, root, config_at(project), missing if selector == "explicit" else None
        )


@pytest.mark.verifies("DSN-QMT-10")
def test_user_match_requires_both_project_and_canonical_current_root(project: Path) -> None:
    root = project / "service"
    user = Path.home() / ".qmstrace/workspaces"
    roots = {"ledger": project / "ledger", "service": root}
    mapped(user / "other-project.toml", roots, project="OTHER")
    mapped(user / "other-checkout.toml", {**roots, "service": project / "another-service"})
    # A syntactically valid nonmatch need not bind members of this project.
    mapped(user / "unrelated.toml", {"ledger": project / "other", "unknown": project / "unknown"})
    assert locations.discover(root, root, config_at(project)) is None
    alias = project / "service-alias"
    alias.symlink_to(root, target_is_directory=True)
    match = mapped(user / "match.toml", {**roots, "service": alias})
    chosen = locations.discover(root, root, config_at(project))
    assert chosen is not None and chosen.filename == match.name
    assert chosen.source == "user" and chosen.roots["service"] == root.resolve()


@pytest.mark.verifies("DSN-QMT-10")
def test_user_ambiguity_names_every_match_instead_of_choosing_one(project: Path) -> None:
    root = project / "service"
    for name in ("z.toml", "a.toml"):
        mapped(
            Path.home() / ".qmstrace/workspaces" / name,
            {"ledger": project / "ledger", "service": root},
        )
    with pytest.raises(CouldNotJudge) as stopped:
        locations.discover(root, root, config_at(project))
    assert "Several" in stopped.value.what
    assert "a.toml" in stopped.value.what and "z.toml" in stopped.value.what
    assert "--workspace" in stopped.value.next_move


@pytest.mark.verifies("DSN-QMT-10")
def test_all_malformed_user_files_fail_even_after_a_matching_candidate(project: Path) -> None:
    root = project / "service"
    user = Path.home() / ".qmstrace/workspaces"
    mapped(user / "a-match.toml", {"ledger": project / "ledger", "service": root})
    write(user / "b-syntax.toml", "project = = 1")
    write(user / "c-other-project.toml", 'version = 1\nproject = "OTHER"\n')
    (user / "d-unicode.toml").write_bytes(b"\xff")
    (user / "e-dangling.toml").symlink_to(user / "not-there")
    write(user / "ignored.txt", "also malformed")
    with pytest.raises(CouldNotJudge) as stopped:
        locations.discover(root, root, config_at(project))
    for filename in ("b-syntax.toml", "c-other-project.toml", "d-unicode.toml", "e-dangling.toml"):
        assert filename in stopped.value.what
    assert "ignored.txt" not in stopped.value.what


@pytest.mark.parametrize("operation", ["stat", "enumeration"])
@pytest.mark.verifies("DSN-QMT-10")
def test_unreadable_user_directory_refuses_instead_of_using_tracked_defaults(
    project: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    root = project / "service"
    user = Path.home() / ".qmstrace/workspaces"
    user.mkdir(parents=True)
    if operation == "stat":
        stat = Path.stat

        def cannot_stat(path, *args, **kwargs):
            if path == user:
                raise PermissionError("fixture denies user directory metadata")
            return stat(path, *args, **kwargs)

        monkeypatch.setattr(Path, "stat", cannot_stat)
    else:
        scandir = os.scandir

        def cannot_enumerate(path):
            if Path(path) == user:
                raise PermissionError("fixture denies user directory listing")
            return scandir(path)

        monkeypatch.setattr(os, "scandir", cannot_enumerate)
    with pytest.raises(CouldNotJudge) as stopped:
        locations.discover(root, root, config_at(project))
    assert "directory" in stopped.value.what
    assert "Fix:" in stopped.value.next_move


@pytest.mark.verifies("DSN-QMT-10")
def test_symlink_map_anchors_relative_roots_at_its_target_not_the_link(project: Path) -> None:
    root = project / "service"
    target = mapped(project / "real-maps/map.toml", {"ledger": project / "ledger", "service": root})
    link = project / "elsewhere/nested/selected.toml"
    link.parent.mkdir(parents=True)
    link.symlink_to(target)
    chosen = locations.discover(root, root, config_at(project), link)
    assert chosen is not None
    assert chosen.ledger == (project / "ledger").resolve()
    assert chosen.roots["service"] == root.resolve()


@pytest.mark.verifies("DSN-QMT-10")
def test_distinct_map_names_cannot_alias_one_canonical_checkout(project: Path) -> None:
    root = project / "service"
    alias = project / "alias"
    alias.symlink_to(root, target_is_directory=True)
    file = mapped(
        project / "map.toml", {"ledger": project / "ledger", "service": root, "client": alias}
    )
    with pytest.raises(CouldNotJudge, match="same trace root"):
        locations.discover(root, root, config_at(project), file)


@pytest.mark.parametrize("bad_binding", ["project", "current", "unknown"])
@pytest.mark.verifies("DSN-QMT-10")
def test_selected_map_is_validated_against_the_current_configuration(
    project: Path, bad_binding: str
) -> None:
    root = project / "service"
    roots = {"ledger": project / "ledger", "service": root}
    if bad_binding == "current":
        roots["service"] = project / "other-service"
    elif bad_binding == "unknown":
        roots["intruder"] = project / "intruder"
    file = mapped(
        project / "map.toml", roots, project="OTHER" if bad_binding == "project" else "MINI"
    )
    with pytest.raises(CouldNotJudge):
        locations.discover(root, root, config_at(project), file)


@pytest.mark.parametrize("bad_binding", ["ledger-root", "self-member"])
@pytest.mark.verifies("DSN-QMT-10")
def test_a_traced_ledger_cannot_be_rebound_away_from_its_schema(
    split: Path, bad_binding: str
) -> None:
    root = split / "ledger"
    roots = {name: split / name for name in ("ledger", "service", "client")}
    if bad_binding == "ledger-root":
        roots["ledger"] = split / "elsewhere"
    file = mapped(
        split / "map.toml",
        roots,
        project="SPLIT",
        ledger="service" if bad_binding == "self-member" else "ledger",
    )
    config = TraceConfig.of_schema((root / "qmstrace.schema.toml").read_text())
    with pytest.raises(CouldNotJudge):
        locations.discover(root, root, config, file)


def test_relative_paths_refuse_cross_drive_layouts_without_leaking_absolute_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def different_drives(*args):
        raise ValueError("different drives")

    monkeypatch.setattr(locations.os.path, "relpath", different_drives)
    with pytest.raises(CouldNotJudge) as stopped:
        locations.relative(tmp_path, tmp_path / "other")
    assert "different drives" in stopped.value.what
    assert str(tmp_path) not in str(stopped.value)


@pytest.mark.parametrize("selector", ["explicit", "environment"])
@pytest.mark.verifies("DSN-QMT-10")
def test_relative_selector_is_anchored_at_invocation_directory_not_trace_root(
    project: Path, monkeypatch: pytest.MonkeyPatch, selector: str
) -> None:
    root = project / "service"
    start = root / "src/service"
    selected = mapped(start / "select.toml", {"ledger": project / "ledger", "service": root})
    write(root / "select.toml", "invalid = =")
    if selector == "environment":
        monkeypatch.setenv("QMSTRACE_WORKSPACE", "select.toml")
    chosen = locations.discover(
        start, root, config_at(project), Path("select.toml") if selector == "explicit" else None
    )
    assert chosen is not None and chosen.filename == selected.name
    assert chosen.roots["service"] == root.resolve()


@pytest.mark.parametrize("problem", ["wrong-project", "invalid-toml", "invalid-utf8"])
@pytest.mark.verifies("DSN-QMT-10")
def test_mapped_ledger_project_identity_is_checked_before_reading_evidence(
    project: Path, problem: str
) -> None:
    root = project / "service"
    config = config_at(project)
    schema = project / "ledger/qmstrace.schema.toml"
    if problem == "wrong-project":
        schema.write_text(schema.read_text().replace('project = "MINI"', 'project = "OTHER"'))
    elif problem == "invalid-toml":
        schema.write_text("version = = 1")
    else:
        schema.write_bytes(b"\xff")
    file = mapped(project / "selected.toml", {"ledger": project / "ledger", "service": root})
    with pytest.raises(CouldNotJudge) as stopped:
        locations.discover(root, root, config, file)
    assert "ledger" in stopped.value.what.lower()
    assert "project" in stopped.value.what.lower()


@dataclass(frozen=True)
class Relocated:
    roots: dict[str, Path]
    file: Path
    digest: str


@pytest.fixture
def relocated(split: Path, embed: Callable[..., str], tmp_path: Path) -> Relocated:
    schema = (split / "ledger/qmstrace.schema.toml").read_text(encoding="utf-8")
    digest = TraceConfig.of_schema(schema).schema_digest
    # Embed before moving: a stale by-path schema is a separate refusal, not a map fixture.
    for name in ("service", "client"):
        config = split / name / "qmstrace.toml"
        config.write_text(embed(config.read_text(encoding="utf-8"), schema), encoding="utf-8")
    roots = {
        "ledger": tmp_path / "relocated/governance/solution",
        "service": tmp_path / "relocated/products/service-copy",
        "client": tmp_path / "relocated/clients/client-copy",
    }
    for name, root in roots.items():
        root.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(split / name, root)
    file = mapped(tmp_path / "maps/selected.toml", roots, project="SPLIT")
    return Relocated(roots, file, digest)


@pytest.mark.verifies("DSN-QMT-02", "REQ-QMT-01")
def test_relocated_local_sources_use_the_map_without_changing_trace_rules(
    relocated: Relocated,
) -> None:
    root, ledger = relocated.roots["service"], relocated.roots["ledger"]
    workspace = Workspace.open(root / "src/service", workspace=relocated.file)
    found = workspace.assessment()
    assert workspace.config.schema_digest == relocated.digest
    assert workspace.config.schema_form is SchemaForm.VERIFIED_COPY
    assert found.violations == () and found.graph.unverified() == []
    requirement = found.graph.node("REQ-SVC-01")
    assert requirement is not None and (requirement.home, requirement.repo) == (
        Home.SIBLING,
        "ledger",
    )
    agreement = next(source for source in found.externals if source.name == "agreement")
    assert agreement.declared is not None and agreement.declared > 0
    assert agreement.location == locations.relative(root, ledger / "agreement.md")
    assert found.baseline_state.register.available
    assert found.baseline_state.register.location == locations.relative(
        root, ledger / "change-requests"
    )
    assert any("workspace:" in notice.text for notice in found.notices)


@pytest.mark.verifies("DSN-QMT-10")
def test_mapped_ledger_must_name_solution_schema_folder_not_its_enclosing_git_root(
    relocated: Relocated,
) -> None:
    ledger = relocated.roots["ledger"]
    enclosing = ledger.parent
    shutil.move(ledger / ".git", enclosing / ".git")
    assert (ledger / "qmstrace.schema.toml").is_file()
    assert not (enclosing / "qmstrace.schema.toml").exists()
    mapped(relocated.file, {**relocated.roots, "ledger": enclosing}, project="SPLIT")
    with pytest.raises(CouldNotJudge) as stopped:
        Workspace.open(relocated.roots["service"], workspace=relocated.file)
    assert "no qmstrace.schema.toml" in stopped.value.what
    assert "solution trace root" in stopped.value.next_move


@pytest.mark.verifies("REQ-QMT-17", "DSN-QMT-02")
def test_nested_relocated_ledger_reads_all_mapped_repos_and_keeps_portable_locations(
    relocated: Relocated,
) -> None:
    ledger = relocated.roots["ledger"]
    found = Workspace.project(ledger / "docs/req", workspace=relocated.file)
    assert found.violations == () and found.gaps == ()
    assert found.config.schema_digest == relocated.digest
    assert {repo.name: repo.location for repo in found.repos} == {
        name: locations.relative(ledger, root) for name, root in relocated.roots.items()
    }
    assert {
        "service:tests/unit/test_api.py::test_a_call_without_a_key_is_refused",
        "client:tests/unit/test_api.py::test_a_call_without_a_key_is_refused",
    } <= {item.id for item in found.graph.items()}
    output = text.ledger_check(found, strict=True, quiet=False)
    assert str(ledger.parent.parent.parent) not in output
    assert "workspace:" in output


@pytest.mark.parametrize("operation", ["project_thread", "project_impact"])
@pytest.mark.verifies("DSN-QMT-02")
def test_project_walks_forward_the_explicit_map(relocated: Relocated, operation: str) -> None:
    argument = "REQ-SVC-01" if operation == "project_thread" else ["REQ-SVC-01"]
    found = getattr(Workspace, operation)(
        relocated.roots["ledger"], argument, workspace=relocated.file
    )
    assert found.graph.node("REQ-SVC-01") is not None
    assert found.graph.node("service:src/service/keys.py") is not None
    assert found.violations == () and found.gaps == ()


@pytest.mark.verifies("DSN-QMT-02")
def test_project_report_uses_the_mapped_repo_as_its_relative_label_anchor(
    relocated: Relocated,
) -> None:
    report = write(
        relocated.roots["service"] / "reports/result.xml",
        '<testsuite><testcase classname="tests.unit.test_api" '
        'name="test_a_call_without_a_key_is_refused"/></testsuite>',
    )
    project, view = Workspace.project_results(
        relocated.roots["ledger"], [("service", report)], workspace=relocated.file
    )
    assert project.violations == ()
    assert view.matched_cases == 1
    assert [(entry.source.repo, entry.source.label) for entry in view.reports] == [
        ("service", "reports/result.xml")
    ]


@pytest.mark.verifies("DSN-QMT-02")
def test_paths_reports_current_available_and_unmapped_members_without_scanning(
    relocated: Relocated, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = {name: path for name, path in relocated.roots.items() if name != "client"}
    mapped(relocated.file, roots, project="SPLIT")

    # A path diagnostic must still work when item contents cannot be extracted.
    def no_scan(*args, **kwargs):
        pytest.fail("paths scanned traced items")

    monkeypatch.setattr("qmstrace.workspace._scanning._scan", no_scan)
    monkeypatch.setattr("qmstrace.workspace._workspace._scan", no_scan)
    monkeypatch.setattr("qmstrace.workspace._project._scan", no_scan)
    monkeypatch.setattr(subprocess, "run", no_scan)
    view = Workspace.paths(roots["service"], workspace=relocated.file)
    assert (view.project, view.ledger) == (
        "SPLIT",
        locations.relative(roots["service"], roots["ledger"]),
    )
    assert "explicit" in view.source and "selected.toml" in view.source
    states = {state.name: state for state in view.repos}
    assert set(states) == {"client", "ledger", "service"}
    assert states["service"].current and states["service"].available
    assert not states["ledger"].current and states["ledger"].available
    assert states["client"].location is None and not states["client"].available


@pytest.mark.verifies("DSN-QMT-02")
def test_missing_mapped_directory_stays_unavailable_even_with_a_reachable_default(
    project: Path, tmp_path: Path
) -> None:
    root = project / "client"
    unavailable = tmp_path / "not-checked-out"
    file = mapped(
        tmp_path / "partial.toml",
        {
            "ledger": project / "ledger",
            "client": root,
            "service": unavailable,
        },
    )
    found = Workspace.open(root, workspace=file).assessment()
    sibling = next(state for state in found.siblings if state.name == "service")
    assert sibling.declares is None and sibling.problem is not None
    assert sibling.location == locations.relative(root, unavailable)
    paths = Workspace.paths(root, workspace=file)
    state = next(state for state in paths.repos if state.name == "service")
    assert state.location == locations.relative(root, unavailable)
    assert not state.available and not state.current


@pytest.mark.verifies("REQ-QMT-17", "DSN-QMT-02")
def test_untraced_ledger_role_is_resolved_without_becoming_a_project_member(
    project: Path, embed: Callable[..., str], tmp_path: Path
) -> None:
    schema = (project / "ledger/qmstrace.schema.toml").read_text(encoding="utf-8")
    before = Workspace.project(project / "ledger")
    roots = {
        "records": tmp_path / "moved/governance/solution",
        "service": tmp_path / "moved/products/service",
        "client": tmp_path / "moved/apps/client",
    }
    for name in ("service", "client"):
        config = project / name / "qmstrace.toml"
        config.write_text(embed(config.read_text(), schema), encoding="utf-8")
    for name, root in roots.items():
        root.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(project / ("ledger" if name == "records" else name), root)
    file = mapped(tmp_path / "map.toml", roots, ledger="records")
    found = Workspace.project(roots["records"], workspace=file)
    assert {repo.name for repo in found.repos} == {"client", "service"}
    assert {item.id for item in found.graph.items()} == {item.id for item in before.graph.items()}
    assert found.config.schema_digest == before.config.schema_digest
    assert found.violations == before.violations == ()
    paths = Workspace.paths(roots["records"], workspace=file)
    assert paths.ledger == "." and {state.name for state in paths.repos} == {"client", "service"}
    assert paths.ledger_available
    shutil.rmtree(roots["records"])
    missing = Workspace.paths(roots["service"], workspace=file)
    assert missing.ledger is not None and not missing.ledger_available
    assert "NOT AVAILABLE" in text.paths(missing)


@pytest.mark.parametrize(
    "operation", ["project", "copy_schema", "project_thread", "project_impact"]
)
def test_map_does_not_promote_a_product_invocation_to_ledger_scope(
    relocated: Relocated, operation: str
) -> None:
    arguments = {
        "project": (),
        "copy_schema": (),
        "project_thread": ("REQ-SVC-01",),
        "project_impact": (["REQ-SVC-01"],),
    }
    with pytest.raises(CouldNotJudge, match="product repo"):
        getattr(Workspace, operation)(
            relocated.roots["service"], *arguments[operation], workspace=relocated.file
        )


@pytest.mark.verifies("DSN-QMT-02")
def test_partial_local_map_does_not_read_an_omitted_repo_at_its_tracked_default(
    project: Path, tmp_path: Path
) -> None:
    root = project / "client"
    file = mapped(tmp_path / "partial.toml", {"ledger": project / "ledger", "client": root})
    found = Workspace.open(root, workspace=file).assessment()
    sibling = next(state for state in found.siblings if state.name == "service")
    assert sibling.declares is None and sibling.problem is not None
    assert "REQ-SVC-01" in found.graph.unverified()


@pytest.mark.verifies("REQ-QMT-17")
def test_partial_project_map_refuses_even_when_omitted_checkout_exists_at_default(
    split: Path, tmp_path: Path
) -> None:
    file = mapped(
        tmp_path / "partial.toml",
        {"ledger": split / "ledger", "service": split / "service"},
        project="SPLIT",
    )
    with pytest.raises(CouldNotJudge) as stopped:
        Workspace.project(split / "ledger", workspace=file)
    assert "client" in stopped.value.what


def update_schema(relocated: Relocated) -> None:
    schema = relocated.roots["ledger"] / "qmstrace.schema.toml"
    with schema.open("a", encoding="utf-8") as stream:
        stream.write(
            '\n[[rules]]\ncode = "G99"\nitem = "requirement"\n'
            'needs = "incoming:verifies"\ntext = "needs mapped evidence"\n'
        )


@pytest.mark.verifies("REQ-QMT-13")
def test_copy_schema_writes_mapped_products_once_and_preserves_ledger_same_tree_path(
    relocated: Relocated,
) -> None:
    ledger_config = relocated.roots["ledger"] / "qmstrace.toml"
    before = ledger_config.read_bytes()
    update_schema(relocated)
    config, copied = Workspace.copy_schema(relocated.roots["ledger"], workspace=relocated.file)
    assert {copy.repo for copy in copied if copy.changed} == {"client", "service"}
    assert ledger_config.read_bytes() == before
    assert next(copy for copy in copied if copy.repo == "ledger").skipped
    assert all(copy.location_notice and "selected.toml" in copy.location_notice for copy in copied)
    for name in ("client", "service"):
        assert (
            Workspace.open(relocated.roots[name], workspace=relocated.file).config.schema_digest
            == config.schema_digest
        )
    _, again = Workspace.copy_schema(relocated.roots["ledger"], workspace=relocated.file)
    assert not any(copy.changed for copy in again)


@pytest.mark.verifies("REQ-QMT-13")
@pytest.mark.parametrize("problem", ["missing-map-member", "unreadable-target"])
def test_mapped_copy_refuses_transactionally_before_writing_any_target(
    relocated: Relocated, problem: str
) -> None:
    update_schema(relocated)
    if problem == "missing-map-member":
        mapped(
            relocated.file,
            {name: root for name, root in relocated.roots.items() if name != "service"},
            project="SPLIT",
        )
    else:
        write(relocated.roots["service"] / "qmstrace.toml", "version = = 1")
    before = {name: (root / "qmstrace.toml").read_bytes() for name, root in relocated.roots.items()}
    with pytest.raises(CouldNotJudge):
        Workspace.copy_schema(relocated.roots["ledger"], workspace=relocated.file)
    assert {
        name: (root / "qmstrace.toml").read_bytes() for name, root in relocated.roots.items()
    } == before


@pytest.mark.verifies("REQ-QMT-13")
def test_cross_drive_refusal_happens_before_any_schema_copy_write(
    relocated: Relocated, monkeypatch: pytest.MonkeyPatch
) -> None:
    update_schema(relocated)
    before = {name: (root / "qmstrace.toml").read_bytes() for name, root in relocated.roots.items()}

    def different_drives(*args):
        raise ValueError("different drives")

    monkeypatch.setattr(locations.os.path, "relpath", different_drives)
    with pytest.raises(CouldNotJudge, match="different drives"):
        Workspace.copy_schema(relocated.roots["ledger"], workspace=relocated.file)
    assert {
        name: (root / "qmstrace.toml").read_bytes() for name, root in relocated.roots.items()
    } == before


@pytest.mark.verifies("REQ-QMT-13")
def test_explicit_copy_names_only_require_the_named_mapped_targets(relocated: Relocated) -> None:
    mapped(
        relocated.file,
        {name: root for name, root in relocated.roots.items() if name != "client"},
        project="SPLIT",
    )
    update_schema(relocated)
    client = relocated.roots["client"] / "qmstrace.toml"
    before = client.read_bytes()
    _, copied = Workspace.copy_schema(
        relocated.roots["ledger"], ["service"], workspace=relocated.file
    )
    assert [(copy.repo, copy.changed) for copy in copied] == [("service", True)]
    assert client.read_bytes() == before


@pytest.mark.verifies("REQ-QMT-15", "DSN-QMT-02")
def test_no_map_keeps_fallback_locations_digest_and_rendered_bytes(project: Path) -> None:
    root = project / "client"
    assert locations.discover(root, root, config_at(project, "client")) is None
    workspace = Workspace.open(root)
    first, second = workspace.assessment(), Workspace.open(root).assessment()
    assert workspace.config.schema_digest == config_at(project, "client").schema_digest
    assert [(state.name, state.location) for state in first.siblings] == [("service", "../service")]
    assert [source.location for source in first.externals] == ["../ledger/agreement.md"]
    assert text.status(first) == text.status(second)
    assert not any("workspace:" in notice.text for notice in first.notices)
    assert str(project) not in text.status(first)
    paths = Workspace.paths(root)
    assert "tracked" in paths.source and paths.ledger == "../ledger"
    assert {
        state.name: (state.location, state.available, state.current) for state in paths.repos
    } == {
        "client": (".", True, True),
        "service": ("../service", True, False),
    }


@pytest.mark.verifies("DSN-QMT-10")
def test_working_map_cannot_replace_historical_by_path_schema_with_current_rules(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project / "service"
    file = mapped(tmp_path / "selected.toml", {"ledger": project / "ledger", "service": root})
    monkeypatch.setenv("QMSTRACE_WORKSPACE", str(file))
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    # HEAD has only the old by-path config. Today's reachable ledger is not tagged evidence.
    with pytest.raises(CouldNotJudge):
        _configuration(root, GitTree(GitCli(root), revision))


@pytest.mark.verifies("DSN-QMT-10")
def test_historical_embedded_schema_ignores_even_a_broken_environment_map(
    project: Path, embed: Callable[..., str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project / "service"
    config = root / "qmstrace.toml"
    schema = (project / "ledger/qmstrace.schema.toml").read_text(encoding="utf-8")
    config.write_text(embed(config.read_text(encoding="utf-8"), schema), encoding="utf-8")
    subprocess.run(["git", "add", "qmstrace.toml"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-qm", "fixture schema copy"], cwd=root, check=True, capture_output=True
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    bad = write(tmp_path / "broken.toml", "not valid = =")
    monkeypatch.setenv("QMSTRACE_WORKSPACE", str(bad))
    config.write_text("version = = 1", encoding="utf-8")
    historical = _configuration(root, GitTree(GitCli(root), revision))
    assert historical.schema_digest == TraceConfig.of_schema(schema).schema_digest


@pytest.mark.verifies("DSN-QMT-10")
def test_unreadable_ancestor_map_does_not_fall_through(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project / "service"
    candidate = mapped(root / locations.LOCAL_MAP, {"ledger": project / "ledger", "service": root})
    original = Path.lstat

    def inaccessible(path, *args, **kwargs):
        if path == candidate:
            raise PermissionError("denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", inaccessible)
    with pytest.raises(CouldNotJudge, match="ancestor workspace map"):
        locations.discover(root, root, config_at(project))


@pytest.mark.verifies("DSN-QMT-10")
def test_nonmatching_user_candidate_aliases_are_still_invalid(project: Path) -> None:
    root = project / "service"
    mapped(
        Path.home() / ".qmstrace/workspaces/aliases.toml",
        {"ledger": project / "another-checkout", "service": project / "another-checkout"},
    )
    with pytest.raises(CouldNotJudge, match="same trace root"):
        locations.discover(root, root, config_at(project))


@pytest.mark.verifies("DSN-QMT-10")
def test_equivalent_self_path_preserves_ledger_member_identity(relocated: Relocated) -> None:
    ledger = relocated.roots["ledger"]
    schema_file = ledger / "qmstrace.schema.toml"
    schema = schema_file.read_text().replace('ledger  = "."', 'ledger  = "./."')
    assert 'ledger  = "./."' in schema
    schema_file.write_text(schema)
    mapped(
        relocated.file,
        {
            "service": ledger,
            "ledger": relocated.roots["service"],
            "client": relocated.roots["client"],
        },
        project="SPLIT",
        ledger="service",
    )
    with pytest.raises(CouldNotJudge, match="self membership"):
        locations.discover(ledger, ledger, TraceConfig.of_schema(schema), relocated.file)


@pytest.mark.verifies("DSN-QMT-10", "REQ-QMT-17")
def test_unicode_worktree_uses_its_own_mapped_trace_root(relocated: Relocated) -> None:
    source = relocated.roots["service"]

    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(source), *args], check=True, capture_output=True)

    # The fixture embeds its schema before relocation; make it available at the worktree pin.
    git("add", "qmstrace.toml")
    git("commit", "-qm", "Embed fixture schema")
    target = source.parent / "บริการ Δ"
    git("worktree", "add", "--detach", str(target), "HEAD")
    try:
        mapped(relocated.file, {**relocated.roots, "service": target}, project="SPLIT")
        workspace = Workspace.open(target / "src/service", workspace=relocated.file)
        assert workspace.root.resolve() == target.resolve()
        assert workspace.locations is not None
        assert workspace.locations.roots["service"] == target.resolve()
        assessment = workspace.assessment()
        assert not assessment.violations and not assessment.gaps
        project = Workspace.project(relocated.roots["ledger"], workspace=relocated.file)
        assert not project.violations and not project.gaps
        assert next(repo.location for repo in project.repos if repo.name == "service").endswith(
            "บริการ Δ"
        )
    finally:
        git("worktree", "remove", "--force", str(target))


@pytest.mark.verifies("DSN-QMT-02", "REQ-QMT-13", "REQ-QMT-17")
def test_two_relocated_layouts_preserve_logical_graph_and_generated_schema(
    relocated: Relocated, tmp_path: Path
) -> None:
    first = Workspace.project(relocated.roots["ledger"], workspace=relocated.file)
    Workspace.copy_schema(relocated.roots["ledger"], workspace=relocated.file)
    configs = {
        name: (root / "qmstrace.toml").read_bytes() for name, root in relocated.roots.items()
    }
    roots = {
        "ledger": tmp_path / "second/records/nested/solution",
        "service": tmp_path / "second/server",
        "client": tmp_path / "second/apps/frontend",
    }
    for name, root in roots.items():
        root.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(relocated.roots[name], root)
    file = mapped(tmp_path / "second/maps/layout.toml", roots, project="SPLIT")
    second = Workspace.project(roots["ledger"], workspace=file)
    assert first.config.schema_digest == second.config.schema_digest == relocated.digest
    assert [(i.id, i.type, i.digest) for i in first.graph.items()] == [
        (i.id, i.type, i.digest) for i in second.graph.items()
    ]
    assert [(k.src, k.dst, k.marker) for k in first.graph.links] == [
        (k.src, k.dst, k.marker) for k in second.graph.links
    ]
    assert not first.violations and not first.gaps and not second.violations and not second.gaps
    Workspace.copy_schema(roots["ledger"], workspace=file)
    assert configs == {name: (root / "qmstrace.toml").read_bytes() for name, root in roots.items()}
    repeated = Workspace.project(roots["ledger"], workspace=file)
    assert text.ledger_check(second, strict=True, quiet=False) == text.ledger_check(
        repeated, strict=True, quiet=False
    )
