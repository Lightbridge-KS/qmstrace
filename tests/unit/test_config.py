"""The trace configuration — its shape lands in every product repo, so it is pinned hard.

The load-bearing claims, each pinned by a test:

1. The example configurations parse, and the project's part and the repo's part merge.
2. The schema comes in three forms — by path, a verified copy, the repo's own — and a copy
   that was edited by hand is refused.
3. A schema's digest does not depend on key order, comments or layout.
4. An unknown key anywhere is an error that names the file and the key.
5. A rule may not need a link that counts toward no coverage.
6. Every refusal says what is wrong *and* the next move.
"""

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from qmstrace.core.config import SchemaForm, TraceConfig, schema_digest
from qmstrace.core.errors import CouldNotJudge

Embed = Callable[..., str]

MINI = Path(__file__).parents[1] / "fixtures" / "mini"
SCHEMA = (MINI / "ledger" / "qmstrace.schema.toml").read_text(encoding="utf-8")
SERVICE = (MINI / "service" / "qmstrace.toml").read_text(encoding="utf-8")
CLIENT = (MINI / "client" / "qmstrace.toml").read_text(encoding="utf-8")
SOLO = (MINI / "solo" / "qmstrace.toml").read_text(encoding="utf-8")


def refusal(local: str, schema: str | None = SCHEMA) -> CouldNotJudge:
    with pytest.raises(CouldNotJudge) as caught:
        TraceConfig.parse(local, schema)
    return caught.value


# ── 1. the examples parse, and the two parts merge ─────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-03")
def test_the_example_parses_and_merges_the_projects_part_with_the_repos() -> None:
    config = TraceConfig.parse(SERVICE, SCHEMA)

    assert config.project == "MINI"
    assert config.ledger == "../ledger"
    assert config.repos == {"service": "../service", "client": "../client"}
    assert config.subjects["service"].key == "SVC"

    requirement = config.item_types["requirement"]
    assert requirement.required == ("Category", "Origin", "Verify-by")  # the project's
    assert "security" in requirement.values["Category"]
    assert requirement.extractor == "markdown"  # the repo's
    assert requirement.files == ("docs/req/*-srs.md",)
    assert requirement.id_prefix == "REQ-SVC-"  # derived from the pattern
    assert requirement.declared_here

    assert config.item_types["automated_test"].levels == ("unit", "integration", "system")
    assert config.item_types["component"].ignore == ("**/__init__.py",)


def test_links_rules_externals_and_baselines_are_read() -> None:
    config = TraceConfig.parse(SERVICE, SCHEMA)

    assert config.links["verifies"].targets == ("requirement", "design_element")
    assert config.links["Assumes"].counts_for_coverage is False
    assert config.links["Satisfies"].counts_for_coverage is True

    assert [rule.code for rule in config.rules] == [f"G0{n}" for n in range(1, 8)]
    narrowed = config.rules[1]
    assert (narrowed.direction, narrowed.marker) == ("incoming", "verifies")
    assert narrowed.where == {"Verify-by": "test"}

    agreement = config.externals["agreement"]
    assert (agreement.item_type, agreement.prefix) == ("origin_clause", "AGR-")
    assert agreement.declared_as.findall("- **AGR-7** — a clause") == ["AGR-7"]

    assert config.change_requests is not None
    assert config.change_requests.accepted == "accepted"

    assert config.baselines["requirements"].subject is None  # the tag pattern names it
    assert config.baselines["requirements"].tag.match("baseline/service/requirements/2")
    assert config.baselines["product"].subject == "*"
    assert config.baselines["product"].tag.match("v1.2.0")
    assert not config.baselines["product"].tag.match("v1.2.0-alpha.1")


def test_a_type_the_repo_does_not_declare_is_known_but_not_scanned() -> None:
    config = TraceConfig.parse(SOLO)
    assert set(config.item_types) == {"requirement", "automated_test"}
    without = re.sub(r"(?ms)^\[items\.component\].*?(?=^\[items\.automated_test\])", "", SERVICE)
    assert TraceConfig.parse(without, SCHEMA).item_types["component"].declared_here is False


def test_a_second_repo_of_the_project_shares_the_schema_and_differs_locally() -> None:
    service, client = TraceConfig.parse(SERVICE, SCHEMA), TraceConfig.parse(CLIENT, SCHEMA)

    assert client.schema_digest == service.schema_digest  # one project, one schema
    assert client.rules == service.rules
    assert client.subjects["client"].key == "CLT"
    assert client.item_types["requirement"].id_prefix == "REQ-CLT-"
    assert client.item_types["design_element"].declared_here is False  # known, not scanned here
    assert service.item_types["design_element"].declared_here is True


# ── 2. three forms of the schema ───────────────────────────────────────────────────────────


def test_by_path_says_where_the_schema_is() -> None:
    assert TraceConfig.schema_reference(SERVICE) == "../ledger/qmstrace.schema.toml"
    assert TraceConfig.parse(SERVICE, SCHEMA).schema_form is SchemaForm.BY_PATH


def test_a_verified_copy_gives_the_same_configuration_as_the_path(embed: Embed) -> None:
    by_path = TraceConfig.parse(SERVICE, SCHEMA)
    copy = TraceConfig.parse(embed(SERVICE, SCHEMA))

    assert copy.schema_form is SchemaForm.VERIFIED_COPY
    assert TraceConfig.schema_reference(embed(SERVICE, SCHEMA)) is None
    assert copy.schema_digest == by_path.schema_digest
    assert copy.rules == by_path.rules
    assert copy.links == by_path.links
    assert copy.item_types.keys() == by_path.item_types.keys()


@pytest.mark.verifies("DSN-QMT-03")
def test_a_copy_edited_by_hand_is_refused(embed: Embed) -> None:
    tampered = embed(SERVICE, SCHEMA).replace("no test verifies it yet.", "fine as it is.", 1)
    stopped = refusal(tampered, None)
    assert "edited by hand" in stopped.what
    assert "tell the project side" in stopped.next_move


def test_a_repo_on_its_own_carries_its_own_schema() -> None:
    config = TraceConfig.parse(SOLO)
    assert config.schema_form is SchemaForm.OWN
    assert config.ledger is None
    assert config.project == "SOLO"
    assert config.change_requests is None
    assert [rule.code for rule in config.rules] == ["G02"]


@pytest.mark.parametrize("extra", ['digest = "sha256:0"', 'project = "X"'])
def test_a_schema_table_is_a_path_or_a_copy_never_both(extra: str) -> None:
    both = SERVICE.replace('path = "../ledger/qmstrace.schema.toml"', f'path = "x.toml"\n{extra}')
    assert "either a path" in refusal(both).next_move


def test_a_schema_that_cannot_be_read_says_what_to_do() -> None:
    stopped = refusal(SERVICE, None)
    assert "'../ledger/qmstrace.schema.toml' could not be read" in stopped.what
    assert "generated copy" in stopped.next_move


def test_no_schema_at_all_is_refused() -> None:
    without = re.sub(r"(?ms)^\[schema\].*?(?=^\[subjects)", "", SERVICE)
    assert "[schema] table is missing" in refusal(without).what


# ── 3. the digest ──────────────────────────────────────────────────────────────────────────


def test_a_digest_ignores_order_comments_and_layout() -> None:
    import tomllib

    one = 'version = 1\nproject = "P"\n[links]\nA = { from = ["x"], to = ["y"] }\n'
    two = '# a comment\n[links]\nA = {to = ["y"],   from = ["x"]}\n\n'
    two = 'project = "P"\nversion = 1\n' + two
    assert schema_digest(tomllib.loads(one)) == schema_digest(tomllib.loads(two))
    assert schema_digest(tomllib.loads(one)).startswith("sha256:")
    changed = one.replace('"y"', '"z"')
    assert schema_digest(tomllib.loads(one)) != schema_digest(tomllib.loads(changed))


# ── 4. unknown keys, wrong types, versions ─────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-03")
def test_an_unknown_key_in_the_repos_file_names_the_file_and_the_key() -> None:
    stopped = refusal(SERVICE.replace('files      = ["docs/req', 'fils      = ["docs/req', 1))
    assert "qmstrace.toml" in stopped.what
    # `files` is then missing, which is reported first — the mistyped key must never pass
    assert "names no files to scan" in stopped.what or "fils" in stopped.what


def test_a_mistyped_key_beside_the_right_one_is_named() -> None:
    stopped = refusal(
        SERVICE.replace('extractor  = "markdown"', 'extractor  = "markdown"\nrequird = ["x"]', 1)
    )
    assert "unknown key 'items.requirement.requird'" in stopped.what
    assert "a rule nobody can see" in stopped.next_move


def test_an_unknown_key_in_the_schema_names_the_schema_file() -> None:
    stopped = refusal(SERVICE, SCHEMA.replace('project = "MINI"', 'project = "MINI"\nprojct = "x"'))
    assert stopped.what.startswith("qmstrace.schema.toml: unknown key 'projct'")


def test_an_unknown_key_in_a_copy_names_the_repos_file() -> None:
    from qmstrace.core import setup

    broken = SCHEMA.replace('project = "MINI"', 'project = "MINI"\nprojct = "x"')
    held, lines = setup.held_schema(SERVICE), SERVICE.splitlines(keepends=True)
    copy = (
        "".join(lines[: held.start])
        + setup.schema_block(broken, "MINI")
        + "".join(lines[held.end :])
    )  # written by hand: the transform itself refuses a schema the repo cannot load
    stopped = refusal(copy, None)
    assert stopped.what.startswith("qmstrace.toml: unknown key 'schema.projct'")


@pytest.mark.parametrize("line", ["version = 2", 'version = "1"', ""])
def test_a_version_this_engine_does_not_read_is_refused(line: str) -> None:
    assert "'version'" in refusal(SERVICE.replace("version = 1", line, 1)).what


def test_invalid_toml_is_refused_not_raised() -> None:
    assert "not valid TOML" in refusal("version = = 1").what


def test_a_wrong_type_names_the_key() -> None:
    stopped = refusal(
        SERVICE.replace('files      = ["docs/req/*-srs.md"]', 'files      = "docs/req"')
    )
    assert "'items.requirement.files' must be a list of non-empty strings" in stopped.what


# ── 5. the parts, against each other ───────────────────────────────────────────────────────


def test_an_item_type_the_project_does_not_know_is_refused() -> None:
    stopped = refusal(SERVICE + '\n[items.widget]\nextractor = "markdown"\nfiles = ["w.md"]\n')
    assert "[items.widget] is not an item type the project knows" in stopped.what
    assert "requirement" in stopped.what


def test_an_id_pattern_with_no_literal_start_needs_a_prefix() -> None:
    loose = SERVICE.replace(r"'^REQ-SVC-\d{2}$'", r"'^(REQ|RQ)-SVC-\d{2}$'")
    assert "id_prefix" in refusal(loose).next_move
    given = loose.replace('files      = ["docs/req', 'id_prefix  = "R"\nfiles      = ["docs/req', 1)
    assert TraceConfig.parse(given, SCHEMA).item_types["requirement"].id_prefix == "R"


@pytest.mark.parametrize(
    ("pattern", "start"),
    [
        (r"'^REQ_SVC_\d{2}$'", "REQ_SVC_"),  # underscores
        (r"'^req-svc-\d{2}$'", "req-svc-"),  # lower case
        (r"'^SRS FR-\d{2}$'", "SRS FR-"),  # a space
        (r"'^FR:\d{2}$'", "FR:"),  # a colon
    ],
)
@pytest.mark.verifies("DSN-QMT-03")
def test_an_id_pattern_that_no_id_can_match_is_refused(pattern: str, start: str) -> None:
    stopped = refusal(SERVICE.replace(r"'^REQ-SVC-\d{2}$'", pattern, 1))
    assert f"[items.requirement] starts with '{start}', which no ID can start with" in stopped.what
    assert "such as REQ-SVC-01" in stopped.what
    assert "id_pattern = '^REQ-SVC-" in stopped.next_move


# Only the literal start is judged: `^FR\.\d{2}$` starts with `FR` and is accepted, though
# `FR.12` is no ID — the extractor reports what then fails to link.
@pytest.mark.parametrize(
    "pattern", [r"'^REQ-SVC-\d{2}$'", r"'^R-\d+$'", r"'^REQ-SVC-0\d$'", r"'^FR\.\d{2}$'"]
)
def test_an_id_pattern_in_the_shape_is_accepted(pattern: str) -> None:
    config = TraceConfig.parse(SERVICE.replace(r"'^REQ-SVC-\d{2}$'", pattern, 1), SCHEMA)
    assert config.item_types["requirement"].id_pattern is not None


@pytest.mark.parametrize("item_id", ["REQ-SVC-01", "A-1", "R2D2-X-9", "CR-003"])
def test_every_start_of_an_id_is_a_start_the_configuration_accepts(item_id: str) -> None:
    from qmstrace.core.config._sections import _ID_START
    from qmstrace.core.model import ID_TOKEN

    assert ID_TOKEN.fullmatch(item_id)  # keeps the two shapes in step
    assert all(_ID_START.fullmatch(item_id[:end]) for end in range(1, len(item_id) + 1))


def test_an_id_prefix_that_no_id_can_start_with_is_refused() -> None:
    loose = SERVICE.replace(r"'^REQ-SVC-\d{2}$'", r"'^(REQ|RQ)-SVC-\d{2}$'")
    given = loose.replace(
        'files      = ["docs/req', 'id_prefix  = "req-"\nfiles      = ["docs/req', 1
    )
    stopped = refusal(given)
    assert "the id_prefix of [items.requirement] starts with 'req-'" in stopped.what
    assert 'id_prefix = "REQ-"' in stopped.next_move


@pytest.mark.parametrize(
    ("old", "new", "where"),
    [
        ('prefix      = "AGR-"', 'prefix      = "agr-"', "'externals.agreement.prefix'"),
        ('prefix   = "CR-"', 'prefix   = "CR_"', "'change_requests.prefix'"),
    ],
)
def test_a_ledger_prefix_that_no_id_can_start_with_is_refused(
    old: str, new: str, where: str
) -> None:
    assert old in SCHEMA
    stopped = refusal(SERVICE, SCHEMA.replace(old, new, 1))
    assert f"{where} starts with" in stopped.what
    assert "which no ID can start with" in stopped.what
    assert stopped.next_move.startswith("Fix: write the prefix in that shape")


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ('extractor  = "markdown"', 'extractor  = "markdwn"', "names the extractor 'markdwn'"),
        ("id_pattern = '^REQ-SVC-\\d{2}$'\n", "", "gives no id_pattern"),
        ('extractor = "pytest"', "extractor = \"pytest\"\nid_pattern = '^t$'", "derives each ID"),
        ('extractor = "pytest"', 'extractor = "pytest"\nid_prefix = "t"', "derives each ID"),
    ],
)
def test_an_extractor_that_cannot_read_its_type_is_refused(
    old: str, new: str, expected: str
) -> None:
    assert old in SERVICE
    assert expected in refusal(SERVICE.replace(old, new, 1)).what


@pytest.mark.verifies("DSN-QMT-03")
def test_every_extractor_the_configuration_accepts_is_one_that_ships() -> None:
    from qmstrace.core.config import EXTRACTORS
    from qmstrace.extract.base import REGISTRY

    assert set(EXTRACTORS) == set(REGISTRY)


def test_a_rule_may_not_need_a_link_that_counts_toward_no_coverage() -> None:
    stopped = refusal(
        SERVICE, SCHEMA.replace('needs = "incoming:Satisfies"', 'needs = "incoming:Assumes"')
    )
    assert "counts toward no coverage" in stopped.what
    assert "suspicion and impact" in stopped.next_move


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ('needs = "incoming:Satisfies"', 'needs = "incoming:Satisfeis"', "does not declare"),
        ('needs = "incoming:Satisfies"', 'needs = "sideways:Satisfies"', "needs = 'sideways"),
        ('code  = "G02"', 'code  = "G01"', "malformed or used twice"),
        ('code  = "G02"', 'code  = "X2"', "malformed or used twice"),
        ('item  = "component"', 'item  = "compnent"', "not an item type"),
        ('where = { "Verify-by" = "test" }', 'where = { "Verify-by" = "prayer" }', "narrows by"),
        ('where = { "Verify-by" = "test" }', 'where = { "Mood" = "test" }', "narrows by"),
        ('to = ["origin_clause"]', 'to = ["origin_claus"]', "not an item type"),
        ('covers = ["requirement"]\n', 'covers = ["requirment"]\n', "not an item type"),
        ('subject = "*"\n', "", "does not say which subject"),
        (r"'^\s*[-*]\s+\*\*(AGR-\d+)\*\*'", r"'^AGR-\d+'", "exactly one group"),
        ('needs = "incoming:Satisfies"', 'needs = "outgoing:Satisfies"', "could ever meet it"),
    ],
)
def test_a_schema_that_contradicts_itself_is_refused(old: str, new: str, expected: str) -> None:
    assert old in SCHEMA
    assert expected in refusal(SERVICE, SCHEMA.replace(old, new, 1)).what


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ('project = "MINI"', "", "'project' is missing"),
        ('project = "MINI"', "project = 7", "'project' must be a non-empty string"),
        ("coverage = false", 'coverage = "no"', "'links.Assumes.coverage' must be true or false"),
        (r"'^v\d+\.\d+\.\d+$'", "'^v(\\d+'", "must be a valid regular expression"),
        ("[repos]", "repos = 3\n[repos_]", "'repos' must be a table"),
        ("tag     = ", "tagg    = ", "'baselines.product.tag' is missing"),
    ],
)
def test_a_wrong_type_or_a_missing_key_in_the_schema_is_named(
    old: str, new: str, expected: str
) -> None:
    assert old in SCHEMA
    assert expected in refusal(SERVICE, SCHEMA.replace(old, new, 1)).what


def test_rules_must_be_an_array_of_tables() -> None:
    no_rules = re.sub(r"(?ms)^\[\[rules\]\].*?(?=^# ── what is declared)", "", SCHEMA)
    # a top-level key must come before the first table header, or it belongs to that table
    broken = no_rules.replace('project = "MINI"', 'project = "MINI"\nrules = "none"', 1)
    assert "'rules' must be an array of tables" in refusal(SERVICE, broken).what


def test_a_schema_with_no_rules_has_none() -> None:
    bare = re.sub(r"(?ms)^\[\[rules\]\].*?(?=^# ── what is declared)", "", SCHEMA)
    assert TraceConfig.parse(SERVICE, bare).rules == ()


def test_a_subjects_key_is_capitals_and_digits() -> None:
    assert "capital letters" in refusal(SERVICE.replace('key = "SVC"', 'key = "svc"')).next_move


# ── 6. the contract of a refusal ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "broken",
    [
        SERVICE.replace("version = 1", "version = 9", 1),
        SERVICE.replace('key = "SVC"', 'key = "svc"'),
        SERVICE + "\nstray = 1\n",
        "version = = 1",
    ],
)
def test_every_refusal_says_what_is_wrong_and_the_next_move(broken: str) -> None:
    stopped = refusal(broken)
    assert stopped.what and stopped.next_move.startswith("Fix:")
    assert str(stopped) == f"{stopped.what} {stopped.next_move}"


# ── 7. the schema copy's markers, and the ledger's file on its own ─────────────────────────


def test_a_marked_copy_without_its_digest_is_refused() -> None:
    from qmstrace.core import setup

    copy = setup.copy_schema(
        SERVICE, setup.held_schema(SERVICE), setup.schema_block(SCHEMA, "MINI")
    )
    assert TraceConfig.parse(copy).schema_form is SchemaForm.VERIFIED_COPY
    undigested = re.sub(r'(?m)^digest = "sha256:[0-9a-f]+"\n', "", copy, count=1)
    stopped = refusal(undigested, None)
    assert "the qmstrace markers hold a generated copy" in stopped.what
    assert "qmstrace ledger copy-schema" in stopped.next_move


def test_the_ledgers_schema_is_read_on_its_own() -> None:
    config = TraceConfig.of_schema(SCHEMA)
    assert (config.project, config.repos) == (
        "MINI",
        {"service": "../service", "client": "../client"},
    )
    assert not any(t.declared_here for t in config.item_types.values())
    assert config.schema_digest == TraceConfig.parse(SERVICE, SCHEMA).schema_digest


def test_compatibility_exports_are_the_original_objects() -> None:
    from importlib import import_module

    from qmstrace.core import config

    exports = {
        "_schema": (
            "SchemaForm",
            "ItemType",
            "LinkType",
            "CoverageRule",
            "ExternalSource",
            "ChangeRequests",
            "BaselineScope",
            "Subject",
            "EXTRACTORS",
        ),
        "_parse": ("TraceConfig",),
        "_copy": ("COPY_BEGIN", "COPY_END", "structural", "marked", "schema_digest"),
        "_toml": ("SUPPORTED_VERSION",),
    }
    for module, names in exports.items():
        implementation = import_module(f"qmstrace.core.config.{module}")
        for name in names:
            assert getattr(config, name) is getattr(implementation, name)


def test_constructors_preserve_the_calling_class() -> None:
    class ProjectConfig(TraceConfig):
        pass

    assert type(ProjectConfig.parse(SERVICE, SCHEMA)) is ProjectConfig
    assert type(ProjectConfig.of_schema(SCHEMA)) is ProjectConfig


@pytest.mark.parametrize(
    ("local", "schema", "what", "next_move"),
    [
        (
            SERVICE.replace("version = 1", "version = true", 1),
            "not valid TOML =",
            "local.toml: 'version' must be a whole number.",
            "Fix: correct its value.",
        ),
        (
            SERVICE.replace('key = "SVC"', 'key = "svc"'),
            SCHEMA.replace('project = "MINI"', 'project = "MINI"\nunknown = 1'),
            "local.toml: subject 'service' has key 'svc'.",
            "Fix: a subject's key is capital letters and digits — it appears inside item "
            "IDs, as in REQ-SVC-01.",
        ),
        (
            SERVICE,
            SCHEMA.replace('project = "MINI"', 'project = "MINI"\nzzz = 1\naaa = 2').replace(
                'needs = "incoming:Satisfies"', 'needs = "incoming:Unknown"'
            ),
            "schema.toml: unknown key 'aaa' (known here: baselines, change_requests, "
            "externals, item_types, links, project, repos, rules, tables, version).",
            "Fix: correct or remove the key — an unknown key is an error because a mistyped "
            "one would be a rule nobody can see.",
        ),
    ],
)
@pytest.mark.verifies("DSN-QMT-03")
def test_refusal_order_and_complete_diagnostics(
    local: str, schema: str, what: str, next_move: str
) -> None:
    with pytest.raises(CouldNotJudge) as caught:
        TraceConfig.parse(local, schema, local_name="local.toml", schema_name="schema.toml")
    assert (caught.value.what, caught.value.next_move) == (what, next_move)


# ── 7. the fields the ledger's tables carry ─────────────────────────────────────────────────

CASES_SCHEMA = (
    Path(__file__).parents[1] / "fixtures" / "cases" / "ledger" / "qmstrace.schema.toml"
).read_text(encoding="utf-8")


@pytest.mark.verifies("DSN-QMT-16")
def test_a_schema_without_tables_carries_no_extra_field() -> None:
    assert TraceConfig.of_schema(CASES_SCHEMA).tables.matrix_fields == ()


@pytest.mark.verifies("DSN-QMT-16")
def test_the_matrix_carries_the_requirement_fields_the_schema_lists_in_order() -> None:
    listed = CASES_SCHEMA + '\n[tables.matrix]\nfields = ["Verify-by", "Category"]\n'
    assert TraceConfig.of_schema(listed).tables.matrix_fields == ("Verify-by", "Category")


@pytest.mark.parametrize(
    ("section", "said"),
    [
        ('fields = ["Origin"]', "'Origin', which is a link marker"),
        ('fields = ["Priority"]', "'Priority', which the requirement type does not declare"),
        ('fields = ["Category", "Category"]', "'Category' twice"),
        ('fields = "Category"', "'tables.matrix.fields' must be a list of non-empty strings"),
        ('field = ["Category"]', "unknown key 'tables.matrix.field'"),
    ],
)
@pytest.mark.verifies("DSN-QMT-16")
def test_a_field_the_matrix_cannot_carry_is_refused(section: str, said: str) -> None:
    with pytest.raises(CouldNotJudge) as caught:
        TraceConfig.of_schema(CASES_SCHEMA + f"\n[tables.matrix]\n{section}\n")
    assert said in caught.value.what and caught.value.next_move.startswith("Fix:")


@pytest.mark.verifies("DSN-QMT-16")
def test_a_table_the_ledger_does_not_emit_is_refused() -> None:
    with pytest.raises(CouldNotJudge) as caught:
        TraceConfig.of_schema(CASES_SCHEMA + '\n[tables.other]\nfields = ["Category"]\n')
    assert "unknown key 'tables.other' (known here: matrix)" in caught.value.what


@pytest.mark.verifies("DSN-QMT-16")
def test_the_section_survives_a_verified_copy(embed: Embed) -> None:
    listed = CASES_SCHEMA + '\n[tables.matrix]\nfields = ["Category"]\n'
    local = (
        Path(__file__).parents[1] / "fixtures" / "cases" / "agent" / "qmstrace.toml"
    ).read_text(encoding="utf-8")
    copy = TraceConfig.parse(embed(local, listed))
    assert copy.schema_form is SchemaForm.VERIFIED_COPY
    assert copy.tables.matrix_fields == ("Category",)
