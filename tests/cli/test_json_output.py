"""Versioned CLI data, errors and evidence are independent of terminal presentation."""

import json
from collections.abc import Callable
from importlib.resources import files
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.core.errors import CouldNotJudge
from qmstrace.render import text
from qmstrace.workspace import Workspace

GOLDEN = Path(__file__).parent / "golden"
REPORT = Path(__file__).parents[1] / "fixtures/junit/service.xml"
SCHEMA = json.loads(files("qmstrace").joinpath("assets/cli.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)
runner = CliRunner()


@pytest.fixture(autouse=True)
def color_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")


def invoke(args: list[str], *, code: int = 0) -> dict:
    result = runner.invoke(app, args)
    assert result.exit_code == code, result.output
    assert result.stderr == ""
    assert result.stdout.endswith("\n") and "\x1b[" not in result.stdout
    value = json.loads(result.stdout)
    VALIDATOR.validate(value)
    assert value["exit_code"] == code
    assert result.stdout == json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    return value


@pytest.mark.verifies("REQ-QMT-15", "DSN-QMT-12", "DSN-QMT-01")
@pytest.mark.parametrize(
    ("name", "command", "repo", "code"),
    [
        ("status", ["status"], "service", 0),
        ("check", ["check", "--strict"], "service", 1),
        ("rules", ["rules"], "service", 0),
        ("paths", ["paths"], "service", 0),
        ("thread", ["thread", "REQ-SVC-01"], "service", 0),
        ("impact", ["impact", "REQ-SVC-02", "REQ-SVC-01"], "service", 0),
        ("results", ["results", "report.xml"], "service", 0),
        ("ledger-check", ["ledger", "check", "--strict"], "ledger", 1),
        ("ledger-thread", ["ledger", "thread", "REQ-SVC-01"], "ledger", 0),
        ("ledger-impact", ["ledger", "impact", "REQ-SVC-01"], "ledger", 0),
    ],
)
def test_command_goldens_and_placements(
    project: Path,
    name: str,
    command: list[str],
    repo: str,
    code: int,
    golden: Callable[[Path, str], None],
) -> None:
    (project / "service/report.xml").write_bytes(REPORT.read_bytes())
    root = project / repo
    args = ["-C", str(root), *command, "--json"]
    value = invoke(args, code=code)
    first = runner.invoke(app, args).stdout
    golden(GOLDEN / f"json-{name}.json", first)
    assert first == runner.invoke(app, ["--json", *args[:-1]]).stdout
    assert first == runner.invoke(app, [*command, "--json", "-C", str(root)]).stdout
    assert str(project) not in first
    assert value["notices"]
    assert value["scope"] == ("project" if repo == "ledger" else "local")


@pytest.mark.parametrize(
    "args",
    [
        ["--json", "nonesuch"],
        ["check", "--json", "--invalid"],
        ["thread", "--json"],
        ["--json", "check", "--json"],
        ["check", "--json", "--json"],
        ["--json", "-C"],
        ["--json", "-C", "one", "check", "-C", "two"],
        ["--json", "ledger", "table", "not-a-table"],
        ["--json", "check", "--workspace", "one", "--workspace", "two"],
    ],
)
def test_parser_errors_are_one_json_document(args: list[str]) -> None:
    value = invoke(args, code=2)
    assert value["data"] is None
    assert value["error"]["category"] == "usage"
    assert value["error"]["next_move"]


@pytest.mark.parametrize(
    "command", [["init"], ["graph", "--out", "view.html"], ["ledger", "copy-schema"]]
)
def test_unsupported_commands_do_not_write(tmp_path: Path, command: list[str]) -> None:
    before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    value = invoke(["-C", str(tmp_path), "--json", *command], code=2)
    assert value["error"]["category"] == "usage"
    assert before == sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))


def test_table_alias_and_refusal(project: Path) -> None:
    args = ["-C", str(project / "ledger"), "ledger", "table", "matrix"]
    old = runner.invoke(app, args)
    alias = runner.invoke(app, [*args, "--json"], env={"FORCE_COLOR": "1"})
    assert old.exit_code == alias.exit_code == 0
    assert old.stdout == alias.stdout
    assert json.loads(alias.stdout)["format"] == "qmstrace.table/1"
    out = project / "ledger/table.json"
    invoke([*args, "--json", "--out", str(out)], code=2)
    assert not out.exists()


def test_impact_rejection_has_no_partial_data(project: Path, golden: Callable) -> None:
    result = runner.invoke(
        app, ["-C", str(project / "service"), "impact", "REQ-SVC-01", "REQ-SVC-99", "--json"]
    )
    value = invoke(
        ["-C", str(project / "service"), "impact", "REQ-SVC-01", "REQ-SVC-99", "--json"], code=2
    )
    assert value["data"] is None
    assert "Impacts:" not in result.stdout
    golden(GOLDEN / "json-could-not-judge.json", result.stdout)


def test_internal_failure_and_projection_failure_have_no_partial_output(
    project: Path, monkeypatch: pytest.MonkeyPatch, golden: Callable
) -> None:
    def broken(*args, **kwargs):
        raise RuntimeError("private machine path /private/example/private-file")

    monkeypatch.setattr(text, "status", broken)
    # JSON does not depend on rendering the human report.
    invoke(["-C", str(project / "service"), "status", "--json"])
    from qmstrace.render.json import assessment

    monkeypatch.setattr(assessment, "status", broken)
    args = ["-C", str(project / "service"), "status", "--json"]
    value = invoke(args, code=3)
    assert value["error"]["category"] == "internal"
    assert "private-file" not in runner.invoke(app, args).stdout
    golden(GOLDEN / "json-internal.json", runner.invoke(app, args).stdout)


def test_error_display_fields_preserve_plain_errors(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def stopped(*args, **kwargs):
        raise CouldNotJudge(
            "Cannot read /private/machine/secret/config.toml.",
            "Fix: read /private/machine/secret.",
            display_what="Cannot read config.toml.",
            display_next_move="Fix: restore readable configuration.",
        )

    monkeypatch.setattr(Workspace, "open", stopped)
    value = invoke(["status", "--json"], code=2)
    assert value["error"]["message"] == "Cannot read config.toml."
    plain = runner.invoke(app, ["status"])
    assert "/private/machine/secret/config.toml" in plain.stderr


def test_quiet_and_force_color_do_not_change_json(project: Path) -> None:
    args = ["-C", str(project / "service"), "check", "--json"]
    plain = runner.invoke(app, args)
    assert (
        plain.stdout
        == runner.invoke(app, [*args, "--quiet"], env={"FORCE_COLOR": "1"}, color=True).stdout
    )
    assert runner.invoke(app, ["-C", str(project / "service"), "status"]).stdout.startswith(
        "schema:"
    )


@pytest.mark.parametrize(
    "args",
    [
        ["--json", "--help"],
        ["--json", "--version"],
        ["check", "--json", "--help"],
        ["--json", "ledger", "--help"],
    ],
)
def test_eager_requests_read_nothing(args: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("workspace must not be read")

    monkeypatch.setattr(Workspace, "open", forbidden)
    monkeypatch.setattr(Workspace, "project", forbidden)
    result = runner.invoke(app, args, env={"FORCE_COLOR": "1"}, color=True)
    assert result.exit_code == 0
    assert "\x1b[" not in result.stdout and "╭" not in result.stdout
    assert not result.stdout.startswith("{")


def test_flag_values_and_delimiter_do_not_select_json(tmp_path: Path) -> None:
    for args in (["--workspace", "--json", "paths"], ["thread", "--", "--json"]):
        result = runner.invoke(app, list(args))
        assert result.exit_code == 2
        assert not result.stdout.startswith("{")
    value = invoke(["--json", "thread", "--", "--json"], code=2)
    assert value["error"]["category"] == "could-not-judge"


def test_schema_is_valid_and_published_copy_matches() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    assert json.loads(Path("contents/assets/qmstrace-cli.schema.json").read_text()) == SCHEMA
    invalid = {
        "format": "qmstrace.cli/1",
        "command": "status",
        "scope": "local",
        "exit_code": 0,
        "data": {},
        "notices": [],
        "error": None,
    }
    assert list(VALIDATOR.iter_errors(invalid))


def test_baseline_withdrawal_and_every_suspect_reason(
    project: Path, embed: Callable, golden: Callable
) -> None:
    import subprocess

    root = project / "service"
    config = root / "qmstrace.toml"
    config.write_text(
        embed(config.read_text(), (project / "ledger/qmstrace.schema.toml").read_text())
    )
    for args in (
        ("add", "qmstrace.toml"),
        ("commit", "-qm", "Embed schema"),
        ("tag", "baseline/service/requirements/1"),
    ):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    path = root / "docs/req/service-srs.md"
    path.write_text(
        path.read_text().replace(
            "### REQ-SVC-01 — A call carries a key\n",
            "### REQ-SVC-01 — A call carries a key revised\n- Status: withdrawn\n",
        )
    )
    args = ["-C", str(root), "check", "--strict", "--quiet", "--json"]
    value = invoke(args, code=1)
    assert value["data"]["counts"]["withdrawn"] == 1
    assert any(f["code"] == "V10" for f in value["data"]["violations"])
    assert value["data"]["suspects"]
    for suspect in value["data"]["suspects"]:
        assert suspect["reasons"]
        assert all(reason["baseline"]["tags"] for reason in suspect["reasons"])
    assert any("remote-tag" in n.lower() for n in value["notices"])
    assert any("NOT VERIFIED" in n for n in value["notices"])
    golden(GOLDEN / "json-baseline-suspects.json", runner.invoke(app, args).stdout)
    overview = invoke(["-C", str(root), "status", "--json"])
    assert overview["data"]["counts"] == value["data"]["counts"]
    assert overview["data"]["baselines"]["counts"]["changed"] == 1


def test_results_preserve_sibling_case_paths_and_trx_evidence(cases: Path) -> None:
    root = cases / "agent"
    report = root / "report.trx"
    report.write_bytes(
        (Path(__file__).parents[1] / "fixtures/trx/cases-agent-full.trx").read_bytes()
    )
    value = invoke(["-C", str(root), "results", "report.trx", "--json"])
    data = value["data"]
    assert data["reports"][0]["format"] == "trx"
    assert data["cases"]
    assert any(t["ownership"] == "sibling" for t in data["requirements"])
    assert data["tests"]
    assert any("commit" in n and "NOT VERIFIED" in n for n in value["notices"])


def test_paths_and_assessments_share_structured_map_provenance(project: Path) -> None:
    root = project / "service"
    local = root / ".qmstrace"
    local.mkdir()
    mapping = local / "workspace.toml"
    mapping.write_text(
        'version = 1\nproject = "MINI"\nledger_repo = "ledger"\n'
        '[repos]\nledger = "../../ledger"\nservice = ".."\nclient = "../../client"\n'
    )
    locations = invoke(["-C", str(root), "paths", "--json"])
    assert locations["data"]["workspace"] == {
        "source": "ancestor",
        "filename": "workspace.toml",
    }
    status = invoke(["-C", str(root), "status", "--json"])
    assert any("workspace:" in notice for notice in status["notices"])
    explicit = invoke(
        ["-C", str(root), "--workspace", ".qmstrace/workspace.toml", "paths", "--json"]
    )
    assert explicit["data"]["workspace"]["source"] == "explicit"


def test_unavailable_sources_and_unknown_types_remain_visible(
    project: Path, alone: Callable
) -> None:
    root = alone("client")
    value = invoke(["-C", str(root), "impact", "REQ-SVC-01", "--json"])
    assert any("NOT VERIFIED" in notice for notice in value["notices"])
    assert value["data"]["unknown_types"] == ["REQ-SVC-01"]
    assert value["data"]["candidate_ids"] == []


def test_text_and_json_assess_once(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = Workspace.assessment
    calls = []

    def counted(self):
        calls.append(self)
        return original(self)

    monkeypatch.setattr(Workspace, "assessment", counted)
    invoke(["-C", str(project / "service"), "status", "--json"])
    assert len(calls) == 1


def test_usage_error_golden(golden: Callable) -> None:
    args = ["check", "--json", "--invalid"]
    invoke(args, code=2)
    golden(GOLDEN / "json-usage.json", runner.invoke(app, args).stdout)


def test_the_bundled_agent_commands_execute(project: Path) -> None:
    import re
    import shlex

    skill = files("qmstrace").joinpath("assets/skill/SKILL.md").read_text()
    block = (
        skill.split("## Driving the CLI as an agent", 1)[1]
        .split("```sh\n", 1)[1]
        .split("```", 1)[0]
    )
    commands = [
        shlex.split(line)[1:] for line in block.splitlines() if line.startswith("qmstrace ")
    ]
    assert len(commands) == 6
    for command in commands:
        invoke(["-C", str(project / "service"), *command], code=1 if command[0] == "check" else 0)
    assert re.search(r"exit_code.*error.category", skill)


def test_non_test_method_keeps_its_passing_test_evidence(project: Path) -> None:
    root = project / "service"
    schema = project / "ledger/qmstrace.schema.toml"
    schema.write_text(
        schema.read_text().replace(
            '"test", "inspection", "analysis"', '"test", "inspection", "analysis", "demonstration"'
        )
    )
    srs = root / "docs/req/service-srs.md"
    srs.write_text(srs.read_text().replace("Verify-by: inspection", "Verify-by: demonstration"))
    source = root / "tests/unit/test_keys.py"
    source.write_text(source.read_text().replace('"REQ-SVC-01"', '"REQ-SVC-03"'))
    (root / "report.xml").write_bytes(REPORT.read_bytes())
    value = invoke(["-C", str(root), "results", "report.xml", "--json"])
    target = next(t for t in value["data"]["other_methods"] if t["id"] == "REQ-SVC-03")
    assert target["method"] == "demonstration"
    assert target["verdict"] == "pass"
    assert target["evidence_only"] is True


def test_unknown_command_does_not_borrow_a_later_command_scope() -> None:
    value = invoke(["--json", "nonesuch", "status"], code=2)
    assert value["command"] is None and value["scope"] is None


def test_impact_argument_order_and_duplicates_do_not_change_json(project: Path) -> None:
    first = runner.invoke(
        app, ["-C", str(project / "service"), "impact", "REQ-SVC-01", "REQ-SVC-02", "--json"]
    )
    second = runner.invoke(
        app,
        [
            "-C",
            str(project / "service"),
            "impact",
            "REQ-SVC-02",
            "REQ-SVC-01",
            "REQ-SVC-02",
            "--json",
        ],
    )
    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout


@pytest.mark.parametrize(
    "command", [["thread", "item_id"], ["results", "reports"], ["impact", "item_ids"]]
)
def test_positional_parameter_names_are_not_treated_as_options(
    project: Path, command: list[str]
) -> None:
    value = invoke(["-C", str(project / "service"), *command, "--json"], code=2)
    assert value["error"]["category"] == "could-not-judge"
