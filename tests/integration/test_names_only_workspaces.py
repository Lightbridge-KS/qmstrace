"""Names-only identities, named discovery and transactional migration in real Git trees."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from qmstrace.core import setup
from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.workspace import Workspace


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def map_file(file: Path, roots: dict[str, Path]) -> Path:
    return write(
        file,
        'version = 1\nproject = "MINI"\nledger_repo = "ledger"\n[repos]\n'
        + "\n".join(f"{name} = {json.dumps(str(path))}" for name, path in roots.items()),
    )


def migrate(project: Path) -> Path:
    schema_file = project / "ledger/qmstrace.schema.toml"
    schema = re.sub(
        r"\[repos\][\s\S]*?(?=\[item_types)",
        '[repos]\nledger_repo = "ledger"\nmembers = ["service", "client"]\n\n',
        schema_file.read_text(),
    ).replace("version = 1", "version = 2", 1)
    write(schema_file, schema)
    write(
        project / "ledger/qmstrace.toml",
        'version = 2\nrepo = "ledger"\n'
        'workspace_profile = "mini-service"\n[schema]\npath = "qmstrace.schema.toml"\n',
    )
    for name in ("service", "client"):
        path = project / name / "qmstrace.toml"
        local = re.sub(r"^ledger\s*=.*\n", "", path.read_text(), flags=re.M)
        local = local.replace(
            "version = 1", f'version = 2\nrepo = "{name}"\nworkspace_profile = "mini-service"', 1
        )
        write(
            path,
            setup.copy_schema(local, setup.held_schema(local), setup.schema_block(schema, "MINI")),
        )
    map_file(
        Path.home() / ".qmstrace/workspaces/mini-service.toml",
        {name: project / name for name in ("ledger", "service", "client")},
    )
    return project


@pytest.fixture
def v2(project: Path) -> Path:
    return migrate(project)


@pytest.mark.verifies("DSN-QMT-03", "DSN-QMT-10")
def test_v2_identity_schema_and_exact_named_discovery(v2: Path) -> None:
    write(Path.home() / ".qmstrace/workspaces/unrelated.toml", "invalid = =")
    opened = Workspace.open(v2 / "service")
    assert opened.config.version == 2
    assert opened.config.repo == "service"
    assert opened.locations is not None and opened.locations.source == "profile"
    assert set(opened.config.repos) == {"service", "client"}
    assert not any(opened.config.repos.values())
    view = opened.assessment()
    assert not view.violations
    assert len(view.graph.items("requirement")) == 3
    project = Workspace.project(v2 / "ledger")
    assert not project.violations
    assert all(":" in item.file for item in project.graph.items())


@pytest.mark.verifies("DSN-QMT-03")
@pytest.mark.parametrize(
    "change",
    [
        "missing-profile",
        "profile-path",
        "repo",
        "mixed",
        "duplicate",
        "empty",
        "unsafe",
        "legacy-ledger",
    ],
)
def test_v2_refuses_ambiguous_or_invalid_configuration(v2: Path, change: str) -> None:
    local = (v2 / "service/qmstrace.toml").read_text()
    schema = (v2 / "ledger/qmstrace.schema.toml").read_text()
    local = re.sub(
        r"# qmstrace:begin[\s\S]*?# qmstrace:end[^\n]*\n",
        '[schema]\npath = "../ledger/qmstrace.schema.toml"\n',
        local,
    )
    if change == "missing-profile":
        local = local.replace('workspace_profile = "mini-service"', "")
    elif change == "profile-path":
        local = local.replace('"mini-service"', '"../unsafe"')
    elif change == "repo":
        local = local.replace('repo = "service"', 'repo = "unknown"')
    elif change == "mixed":
        local = local.replace("version = 2", "version = 1", 1)
        local = re.sub(r"^(repo|workspace_profile) =.*\n", "", local, flags=re.M)
    elif change == "duplicate":
        schema = schema.replace('["service", "client"]', '["service", "service"]')
    elif change == "empty":
        schema = schema.replace('["service", "client"]', "[]")
    elif change == "unsafe":
        schema = schema.replace('["service", "client"]', '["service", "../client"]')
    else:
        local = local.replace("version = 2", 'version = 2\nledger = "../ledger"', 1)
    with pytest.raises(CouldNotJudge):
        TraceConfig.parse(local, schema)


@pytest.mark.verifies("DSN-QMT-03")
def test_v2_member_order_does_not_change_digest(v2: Path) -> None:
    source = (v2 / "ledger/qmstrace.schema.toml").read_text()
    assert (
        TraceConfig.of_schema(source).schema_digest
        == TraceConfig.of_schema(
            source.replace('["service", "client"]', '["client", "service"]')
        ).schema_digest
    )


@pytest.mark.verifies("DSN-QMT-10")
def test_absent_implicit_profile_is_local_only_but_explicit_absence_is_refused(v2: Path) -> None:
    (Path.home() / ".qmstrace/workspaces/mini-service.toml").unlink()
    opened = Workspace.open(v2 / "service")
    assert opened.locations is None
    assert any("NOT LOCATED" in notice.text for notice in opened.assessment().notices)
    with pytest.raises(CouldNotJudge, match="workspace map"):
        Workspace.project(v2 / "ledger")
    with pytest.raises(CouldNotJudge, match="cannot be read"):
        Workspace.open(v2 / "service", workspace=Path("absent.toml"))


@pytest.mark.verifies("DSN-QMT-10")
@pytest.mark.parametrize(
    "kind", ["swapped", "role", "duplicate", "project", "malformed", "dangling"]
)
def test_invalid_default_never_falls_back(v2: Path, kind: str) -> None:
    file = Path.home() / ".qmstrace/workspaces/mini-service.toml"
    roots = {name: v2 / name for name in ("ledger", "service", "client")}
    if kind == "swapped":
        roots["service"], roots["client"] = roots["client"], roots["service"]
    elif kind == "duplicate":
        roots["client"] = roots["service"]
    map_file(file, roots)
    if kind in ("role", "project", "malformed"):
        old = file.read_text()
        write(
            file,
            old.replace('ledger_repo = "ledger"', 'ledger_repo = "service"')
            if kind == "role"
            else old.replace("MINI", "OTHER")
            if kind == "project"
            else "bad = =",
        )
    elif kind == "dangling":
        file.unlink()
        file.symlink_to(file.parent / "absent.toml")
    with pytest.raises(CouldNotJudge):
        Workspace.open(v2 / "service")


@pytest.mark.verifies("DSN-QMT-10", "DSN-QMT-11")
def test_v2_copy_bootstrap_is_transactional_and_idempotent(v2: Path) -> None:
    configs = {name: v2 / name / "qmstrace.toml" for name in ("service", "client")}
    for file in configs.values():
        local = file.read_text()
        write(file, re.sub(r"# qmstrace:begin[\s\S]*?# qmstrace:end[^\n]*\n", "[schema]\n", local))
    before = {name: file.read_bytes() for name, file in configs.items()}
    write(
        configs["client"],
        configs["client"]
        .read_text()
        .replace('workspace_profile = "mini-service"', 'workspace_profile = "../bad"'),
    )
    invalid = configs["client"].read_bytes()
    with pytest.raises(CouldNotJudge):
        Workspace.copy_schema(v2 / "ledger")
    assert configs["service"].read_bytes() == before["service"]
    assert configs["client"].read_bytes() == invalid
    configs["client"].write_bytes(before["client"])
    _, copied = Workspace.copy_schema(v2 / "ledger")
    assert all(record.changed for record in copied)
    _, unchanged = Workspace.copy_schema(v2 / "ledger")
    assert not any(record.changed for record in unchanged)


@pytest.mark.verifies("DSN-QMT-10", "DSN-QMT-14")
def test_relocation_keeps_logical_graph_and_digest(v2: Path, tmp_path: Path) -> None:
    original = Workspace.project(v2 / "ledger")
    roots = {}
    for name, directory in [
        ("ledger", "records/solution"),
        ("service", "apps/deep/backend"),
        ("client", "elsewhere/frontend"),
    ]:
        roots[name] = tmp_path / "relocated" / directory
        shutil.copytree(v2 / name, roots[name])
    map_file(Path.home() / ".qmstrace/workspaces/mini-service.toml", roots)
    moved = Workspace.project(roots["ledger"])
    assert moved.config.schema_digest == original.config.schema_digest
    assert moved.graph.nodes == original.graph.nodes
    assert moved.violations == original.violations
    assert moved.gaps == original.gaps


@pytest.mark.verifies("DSN-QMT-03", "DSN-QMT-10")
@pytest.mark.parametrize("selection", ["explicit", "environment", "ancestor"])
def test_v2_overrides_do_not_read_an_invalid_named_default(
    v2: Path, monkeypatch: pytest.MonkeyPatch, selection: str
) -> None:
    root = v2 / "service"
    write(Path.home() / ".qmstrace/workspaces/mini-service.toml", "invalid = =")
    file = map_file(
        v2 / "chosen.toml", {name: v2 / name for name in ("ledger", "service", "client")}
    )
    selected = None
    if selection == "explicit":
        selected = Path("../chosen.toml")
    elif selection == "environment":
        monkeypatch.setenv("QMSTRACE_WORKSPACE", "../chosen.toml")
    else:
        write(v2 / ".qmstrace/workspace.toml", file.read_text())
    opened = Workspace.open(root, workspace=selected)
    assert opened.locations is not None and opened.locations.source == selection


@pytest.mark.verifies("DSN-QMT-10", "DSN-QMT-14")
def test_partial_v2_map_never_borrows_tracked_or_other_profile_locations(v2: Path) -> None:
    map_file(
        Path.home() / ".qmstrace/workspaces/mini-service.toml",
        {name: v2 / name for name in ("ledger", "service")},
    )
    opened = Workspace.open(v2 / "service")
    sibling = next(s for s in opened.assessment().siblings if s.name == "client")
    assert sibling.declares is None and sibling.location == "not mapped"
    with pytest.raises(CouldNotJudge, match="client: no location"):
        Workspace.project(v2 / "ledger")
    _, records = Workspace.copy_schema(v2 / "ledger", ["service"])
    assert [r.repo for r in records] == ["service"]


@pytest.mark.verifies("DSN-QMT-07", "DSN-QMT-10")
def test_v2_baseline_is_read_without_current_profile_discovery(v2: Path) -> None:
    import subprocess

    root = v2 / "service"
    for arguments in (
        ("add", "qmstrace.toml"),
        ("commit", "-qm", "V2 fixture"),
        ("tag", "-a", "baseline/service/requirements/1", "-m", "Fixture baseline"),
    ):
        subprocess.run(["git", "-C", str(root), *arguments], check=True, capture_output=True)
    opened = Workspace.open(root)
    assert opened.config.baselines
    # Real tagged-tree loading neither re-enters discover nor needs the present map.
    (Path.home() / ".qmstrace/workspaces/mini-service.toml").unlink()
    assessed = Workspace.open(root).assessment()
    assert assessed.baseline_state.baselines
    assert {c.state for c in assessed.baseline_state.comparisons} == {"frozen"}
    requirement = root / "docs/req/service-srs.md"
    write(requirement, requirement.read_text().replace("A call carries a key", "Calls carry a key"))
    changed = Workspace.open(root).assessment()
    assert any(c.state == "changed" for c in changed.baseline_state.comparisons)
    assert any(f.code == "V10" for f in changed.violations)


@pytest.mark.verifies("DSN-QMT-01", "DSN-QMT-10", "DSN-QMT-12")
@pytest.mark.parametrize(
    "command", ["status", "check", "rules", "paths", "thread", "impact", "results"]
)
def test_v2_cli_payloads_validate_and_preserve_targeted_context(
    v2: Path, command: str, golden
) -> None:
    from importlib.resources import files

    from jsonschema import Draft202012Validator
    from typer.testing import CliRunner

    from qmstrace.cli import app

    args = [command]
    if command in ("thread", "impact"):
        args += ["REQ-SVC-01"]
    if command == "results":
        args += [str(Path(__file__).parents[1] / "fixtures/junit/service.xml")]
    result = CliRunner().invoke(app, ["-C", str(v2 / "service"), *args, "--json"])
    assert result.exit_code == 0, result.output
    value = json.loads(result.stdout)
    Draft202012Validator(
        json.loads(files("qmstrace").joinpath("assets/cli.schema.json").read_text())
    ).validate(value)
    assert value["format"] == "qmstrace.cli/2"
    assert str(v2) not in result.stdout
    golden(Path(__file__).parents[1] / "cli/golden" / f"v2-{command}.json", result.stdout)
    before = CliRunner().invoke(app, ["--json", *args, "-C", str(v2 / "service")])
    assert before.stdout == result.stdout and before.exit_code == result.exit_code


@pytest.mark.verifies("DSN-QMT-11")
def test_v2_init_refresh_preserves_maps_and_refuses_local_skill_edits(v2: Path) -> None:
    root = v2 / "service"
    file = write(
        root / ".qmstrace/workspace.toml",
        (Path.home() / ".qmstrace/workspaces/mini-service.toml").read_text(),
    )
    before = file.read_bytes()
    Workspace.initialize(root)
    assert file.read_bytes() == before
    assert TraceConfig.parse((root / "qmstrace.toml").read_text()).version == 2
    skill = root / ".agents/skills/qmstrace/SKILL.md"
    write(skill, skill.read_text() + "\nLocal addition\n")
    with pytest.raises(CouldNotJudge, match="differs"):
        Workspace.initialize(root)
    assert skill.read_text().endswith("Local addition\n")


@pytest.mark.verifies("DSN-QMT-07", "DSN-QMT-10")
def test_current_v2_keeps_original_v1_baseline_configuration(project: Path) -> None:
    import subprocess

    root = project / "service"
    file = root / "qmstrace.toml"
    local = file.read_text()
    schema = (project / "ledger/qmstrace.schema.toml").read_text()
    write(
        file, setup.copy_schema(local, setup.held_schema(local), setup.schema_block(schema, "MINI"))
    )
    for args in (
        ("add", "qmstrace.toml"),
        ("commit", "-qm", "V1 copied fixture"),
        ("tag", "-a", "baseline/service/requirements/1", "-m", "V1 baseline"),
    ):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    migrate(project)
    view = Workspace.open(root).assessment()
    baseline = view.baseline_state.baselines[0]
    assert baseline.snapshot.config is not None and baseline.snapshot.config.version == 1
    assert baseline.snapshot.config.schema_digest != view.config.schema_digest
    assert {c.state for c in view.baseline_state.comparisons} == {"frozen"}


@pytest.mark.verifies("DSN-QMT-03", "DSN-QMT-10")
@pytest.mark.parametrize("problem", ["missing-local", "other-role", "other-project", "no-identity"])
def test_v2_ledger_and_other_available_roots_must_declare_coherent_identities(
    v2: Path, problem: str
) -> None:
    ledger = v2 / "ledger/qmstrace.toml"
    client = v2 / "client/qmstrace.toml"
    if problem == "missing-local":
        ledger.unlink()
    elif problem == "other-role":
        write(ledger, ledger.read_text().replace('repo = "ledger"', 'repo = "client"'))
    elif problem == "other-project":
        write(client, client.read_text().replace('project = "MINI"', 'project = "OTHER"'))
    else:
        client.unlink()
    with pytest.raises(CouldNotJudge):
        Workspace.project(v2 / "ledger")


@pytest.mark.verifies("DSN-QMT-03")
def test_ledger_with_documents_must_be_a_v2_member(v2: Path) -> None:
    ledger = v2 / "ledger/qmstrace.toml"
    write(
        ledger,
        ledger.read_text() + '\n[items.requirement]\nextractor = "markdown"\n'
        'id_pattern = "^REQ-SVC-[0-9]+$"\nfiles = ["docs/*.md"]\n',
    )
    with pytest.raises(CouldNotJudge, match=r"not in repos\.members"):
        Workspace.open(v2 / "ledger")


@pytest.mark.verifies("DSN-QMT-03", "DSN-QMT-10")
def test_v2_ledger_map_cannot_repair_its_schema_path(v2: Path) -> None:
    ledger = v2 / "ledger/qmstrace.toml"
    write(
        ledger,
        ledger.read_text().replace('path = "qmstrace.schema.toml"', 'path = "missing-schema.toml"'),
    )
    before = (v2 / "service/qmstrace.toml").read_bytes()
    for operation in (Workspace.project, Workspace.copy_schema):
        with pytest.raises(CouldNotJudge, match="authoritative"):
            operation(v2 / "ledger")
    assert (v2 / "service/qmstrace.toml").read_bytes() == before


@pytest.mark.verifies("DSN-QMT-02", "DSN-QMT-10")
def test_v2_ledger_without_profile_does_not_treat_members_as_self(v2: Path) -> None:
    (Path.home() / ".qmstrace/workspaces/mini-service.toml").unlink()
    opened = Workspace.open(v2 / "ledger")
    view = opened.assessment()
    assert {(s.name, s.location) for s in view.siblings} == {
        ("service", "not mapped"),
        ("client", "not mapped"),
    }
    assert all(s.declares is None for s in view.siblings)
    assert any("NOT LOCATED" in notice.text for notice in view.notices)


@pytest.mark.verifies("DSN-QMT-02", "DSN-QMT-10")
def test_explicit_out_of_tree_evidence_keeps_read_semantics_without_invented_ownership(
    v2: Path, tmp_path: Path
) -> None:
    outside = tmp_path / "external-agreement.md"
    outside.write_bytes((v2 / "ledger/agreement.md").read_bytes())
    schema = v2 / "ledger/qmstrace.schema.toml"
    write(
        schema,
        schema.read_text().replace(
            'source      = "agreement.md"', f"source = {json.dumps(str(outside))}"
        ),
    )
    Workspace.copy_schema(v2 / "ledger")
    view = Workspace.open(v2 / "service").assessment()
    assert not view.violations
    assert view.externals[0].location == "external-agreement.md"
    assert view.externals[0].declared == 3


@pytest.mark.verifies("DSN-QMT-12")
def test_logical_locations_do_not_repeat_a_derived_id_in_human_walks(v2: Path) -> None:
    from qmstrace.render import text

    view = Workspace.project(v2 / "ledger")
    module = "service:src/service/keys.py"
    output = text.ledger_thread(view, module)
    assert output.splitlines()[0] == module
    assert output.splitlines()[1] == "  component, in service"


@pytest.mark.verifies("DSN-QMT-03")
def test_v2_schema_only_errors_name_the_authored_key_not_a_synthetic_header() -> None:
    with pytest.raises(CouldNotJudge) as stopped:
        TraceConfig.of_schema('version = 2\nproject = "MINI"\n[repos]\nmembers = ["service"]\n')
    assert "repos.ledger_repo" in stopped.value.what
    assert "not valid TOML" not in stopped.value.what
