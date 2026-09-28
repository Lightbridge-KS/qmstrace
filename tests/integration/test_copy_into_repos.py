"""The schema copy on real repos (D9): the ledger writes, each product repo is judged alone.

The load-bearing claims, each pinned by a test:

1. Named repos only, or every repo in [repos]; a name the schema does not list is refused.
2. All or nothing: any repo that cannot take the copy — missing, holding its own schema,
   reading another schema, carrying another project's copy — names every problem, and no
   repo is written.
3. A repo that carries the copy is judged alone, with no ledger beside it.
4. A baseline tag cut after the copy is read and judged; one cut while the repo read its
   schema by path cannot be — which is why the copy comes first.
5. A ledger that holds the documents lists itself under [repos] as "."; it reads the schema it
   holds by path, so the copy skips it — and says how to undo a copy an older run wrote there.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from qmstrace.core.errors import CouldNotJudge
from qmstrace.workspace import Workspace


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def config_of(project: Path, repo: str) -> str:
    return (project / repo / "qmstrace.toml").read_text(encoding="utf-8")


# ── 1. which repos ─────────────────────────────────────────────────────────────────────────


def test_only_the_named_repos_are_copied(project: Path) -> None:
    client = config_of(project, "client")
    config, copies = Workspace.copy_schema(project / "ledger", ["service"])
    assert [c.repo for c in copies] == ["service"] and copies[0].changed
    assert "# qmstrace:begin" in config_of(project, "service")
    assert config_of(project, "client") == client
    assert config.project == "MINI"


def test_a_name_the_schema_does_not_list_is_refused(project: Path) -> None:
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.copy_schema(project / "ledger", ["service", "solo"])
    assert "solo is not in the schema's [repos] (it names: client, service)" in caught.value.what
    assert "# qmstrace:begin" not in config_of(project, "service")


def test_the_copy_is_found_from_inside_the_ledger(project: Path) -> None:
    inside = project / "ledger" / "change-requests"
    inside.mkdir()
    _, copies = Workspace.copy_schema(inside)
    assert [c.repo for c in copies] == ["client", "service"]


# ── 2. all or nothing ──────────────────────────────────────────────────────────────────────


def schema_listing(project: Path, extra: str) -> None:
    schema = project / "ledger" / "qmstrace.schema.toml"
    text = schema.read_text(encoding="utf-8")
    schema.write_text(text.replace('client  = "../client"', f'client  = "../client"\n{extra}'))


@pytest.mark.parametrize(
    ("arrange", "said"),
    [
        (lambda p: shutil.rmtree(p / "client"), "client: there is no ../client/qmstrace.toml"),
        (
            lambda p: (p / "client" / "qmstrace.toml").write_text(
                config_of(p, "client").replace("../ledger/qmstrace.schema.toml", "other.toml")
            ),
            "reads the schema at other.toml, not this ledger's qmstrace.schema.toml",
        ),
        (
            lambda p: schema_listing(p, 'solo    = "../solo"'),
            "solo: ../solo/qmstrace.toml holds a schema of its own",
        ),
    ],
    ids=["missing", "another-schema", "own-schema"],
)
@pytest.mark.verifies("REQ-QMT-13")
def test_one_repo_that_cannot_take_the_copy_stops_every_write(
    project: Path, arrange, said: str
) -> None:
    arrange(project)
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.copy_schema(project / "ledger")
    assert said in caught.value.what
    assert "nothing was written" in caught.value.what
    assert "# qmstrace:begin" not in config_of(project, "service")


def test_a_copy_of_another_projects_schema_is_refused(project: Path) -> None:
    Workspace.copy_schema(project / "ledger", ["client"])
    foreign = config_of(project, "client").replace('project = "MINI"', 'project = "OTHER"', 1)
    (project / "client" / "qmstrace.toml").write_text(foreign, encoding="utf-8")
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.copy_schema(project / "ledger")
    assert "carries project OTHER's schema, not MINI's" in caught.value.what
    assert config_of(project, "client") == foreign


# ── 3. judged alone ────────────────────────────────────────────────────────────────────────


def test_a_repo_carrying_the_copy_is_judged_with_no_ledger_beside_it(
    project: Path, tmp_path: Path
) -> None:
    Workspace.copy_schema(project / "ledger", ["service"])
    alone = tmp_path / "pipeline" / "service"
    shutil.copytree(project / "service", alone)
    view = Workspace.open(alone).assessment()
    assert view.config.schema_form.value == "a generated, verified copy"
    assert view.config.schema_digest == Workspace.open(project / "service").config.schema_digest


# ── 4. baselines ───────────────────────────────────────────────────────────────────────────

TAG = "baseline/service/requirements/1"


def test_a_baseline_cut_after_the_copy_is_read_and_judged(project: Path) -> None:
    Workspace.copy_schema(project / "ledger", ["service"])
    service = project / "service"
    git(service, "add", "-A")
    git(service, "commit", "-qm", "carry the project's schema")
    git(service, "tag", "-a", TAG, "-m", "requirements approved")
    view = Workspace.open(service).assessment()
    assert {c.state for c in view.baseline_state.comparisons} == {"frozen"}


def test_a_baseline_cut_while_reading_the_schema_by_path_cannot_be_judged(project: Path) -> None:
    service = project / "service"
    git(service, "tag", "-a", TAG, "-m", "requirements approved")
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.open(service).assessment()
    assert "outside the tagged Git tree" in caught.value.what


def test_a_schema_naming_no_repos_has_nowhere_to_go(project: Path) -> None:
    schema = project / "ledger" / "qmstrace.schema.toml"
    text = schema.read_text(encoding="utf-8")
    schema.write_text(
        text.replace('service = "../service"\n', "").replace('client  = "../client"\n', "")
    )
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.copy_schema(project / "ledger")
    assert "names no product repos under [repos]" in caught.value.what


def test_a_repo_whose_markers_conflict_is_named_with_its_own_fix(project: Path) -> None:
    Workspace.copy_schema(project / "ledger", ["client"])
    client = project / "client" / "qmstrace.toml"
    client.write_text(client.read_text() + "# qmstrace:begin — a stray\n", encoding="utf-8")
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.copy_schema(project / "ledger")
    assert "client: ../client/qmstrace.toml has conflicting qmstrace markers" in caught.value.what
    assert "# qmstrace:begin" not in config_of(project, "service")


def test_outside_any_ledger_it_says_where_to_run(tmp_path: Path) -> None:
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.copy_schema(tmp_path)
    assert "is not a project's ledger repo" in caught.value.what


# ── 5. the ledger listed as itself ─────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-13")
def test_the_ledger_listed_as_itself_is_skipped(split: Path) -> None:
    own = (split / "ledger" / "qmstrace.toml").read_bytes()
    _, copies = Workspace.copy_schema(split / "ledger")
    assert [(c.repo, c.skipped, c.changed) for c in copies] == [
        ("client", False, True),
        ("ledger", True, False),
        ("service", False, True),
    ]
    assert (split / "ledger" / "qmstrace.toml").read_bytes() == own
    assert "# qmstrace:begin" in config_of(split, "service")


def test_named_alone_the_ledger_is_skipped_and_nothing_is_written(split: Path) -> None:
    before = {repo: config_of(split, repo) for repo in ("ledger", "service", "client")}
    _, copies = Workspace.copy_schema(split / "ledger", ["ledger"])
    assert [(c.repo, c.skipped) for c in copies] == [("ledger", True)]
    assert {repo: config_of(split, repo) for repo in before} == before


def test_a_ledger_holding_a_copy_of_its_own_schema_is_told_how_to_undo_it(
    split: Path, embed
) -> None:
    ledger = split / "ledger"
    schema = (ledger / "qmstrace.schema.toml").read_text(encoding="utf-8")
    damaged = embed(config_of(split, "ledger"), schema)  # what an older copy-schema wrote here
    (ledger / "qmstrace.toml").write_text(damaged, encoding="utf-8")
    _, copies = Workspace.copy_schema(ledger, ["ledger"])
    assert copies[0].skipped
    assert 'replace that [schema] with path = "qmstrace.schema.toml"' in copies[0].before
    assert config_of(split, "ledger") == damaged
