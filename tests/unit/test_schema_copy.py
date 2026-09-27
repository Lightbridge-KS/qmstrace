"""The project's trace schema copied into a product repo's configuration (D9) — pure text.

The load-bearing claims, each pinned by a test:

1. The copy changes no rule: the configuration it produces parses to the same project, links,
   rules, item types and repos as reading the schema by path — and every byte outside the
   copy is kept. A second copy changes nothing.
2. An unmarked copy from before the markers gains them, with its digest unchanged; a copy of
   older rules, or one edited by hand, is replaced.
3. Only a line where everything above is complete TOML is a header or a marker, so layout —
   `[subjects]` first, comments, a `[` inside a multi-line string, CRLF — is kept intact.
4. What a configuration holds is named — by path, a copy, empty, its own — and anything that
   cannot be replaced safely is refused before a byte is written.
"""

import tomllib
from pathlib import Path

import pytest

from qmstrace.core import setup
from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge

MINI = Path(__file__).parents[1] / "fixtures" / "mini"
SCHEMA = (MINI / "ledger" / "qmstrace.schema.toml").read_text(encoding="utf-8")
SERVICE = (MINI / "service" / "qmstrace.toml").read_text(encoding="utf-8")
CLIENT = (MINI / "client" / "qmstrace.toml").read_text(encoding="utf-8")
BLOCK = setup.schema_block(SCHEMA, "MINI")


def copied(local: str, block: str = BLOCK) -> str:
    return setup.copy_schema(local, setup.held_schema(local), block)


def outside(text: str) -> list[str]:
    held = setup.held_schema(text)
    lines = text.splitlines(keepends=True)
    return lines[: held.start] + lines[held.end :]


def same_rules(a: TraceConfig, b: TraceConfig) -> bool:
    return (a.project, a.links, a.rules, a.repos, a.baselines.keys(), a.item_types.keys()) == (
        b.project,
        b.links,
        b.rules,
        b.repos,
        b.baselines.keys(),
        b.item_types.keys(),
    )


# ── 1. the copy changes no rule ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("local", [SERVICE, CLIENT], ids=["service", "client"])
def test_a_copy_reads_as_the_schema_by_path_and_keeps_every_other_byte(local: str) -> None:
    new = copied(local)
    by_path, copy = TraceConfig.parse(local, SCHEMA), TraceConfig.parse(new)
    assert same_rules(by_path, copy)
    assert copy.schema_digest == by_path.schema_digest
    assert copy.schema_form.value == "a generated, verified copy"
    assert outside(new) == outside(local)
    assert copied(new) == new  # a second copy changes nothing


def test_the_block_is_marked_digested_and_keeps_the_ledgers_comments() -> None:
    lines = BLOCK.splitlines()
    assert lines[0].startswith("# qmstrace:begin — the MINI trace schema, generated in its ledger")
    assert lines[1:3] == ["[schema]", f'digest = "{TraceConfig.of_schema(SCHEMA).schema_digest}"']
    assert lines[-1] == "# qmstrace:end"
    assert "[schema.links]" in lines and "[[schema.rules]]" in lines
    comments = [line for line in SCHEMA.splitlines() if line.startswith("#")]
    assert comments and all(comment in lines for comment in comments)


# ── 2. copies from before, of older rules, edited by hand ──────────────────────────────────


def test_an_unmarked_copy_gains_its_markers_and_keeps_its_digest() -> None:
    marked = copied(SERVICE)
    unmarked = "".join(
        line for line in marked.splitlines(keepends=True) if not line.startswith("# qmstrace:")
    )
    held = setup.held_schema(unmarked)
    assert (held.kind, held.edited) == ("copy", False)
    assert copied(unmarked) == marked


def test_a_copy_of_older_rules_is_replaced() -> None:
    old = copied(SERVICE)
    newer = SCHEMA.replace("no test verifies it yet.", "no test verifies this requirement.")
    held = setup.held_schema(old)
    new = setup.copy_schema(old, held, setup.schema_block(newer, "MINI"))
    assert held.digest != TraceConfig.of_schema(newer).schema_digest
    assert TraceConfig.parse(new).schema_digest == TraceConfig.of_schema(newer).schema_digest


def test_a_comment_only_change_is_layout_the_digest_stays() -> None:
    old = copied(SERVICE)
    commented = SCHEMA.replace("# ", "#  ", 1)
    new = setup.copy_schema(old, setup.held_schema(old), setup.schema_block(commented, "MINI"))
    assert new != old
    assert setup.held_schema(old).digest == TraceConfig.parse(new).schema_digest


def test_a_copy_edited_by_hand_is_seen_and_replaced() -> None:
    edited = copied(SERVICE).replace("no test verifies it yet.", "fine as it is.", 1)
    held = setup.held_schema(edited)
    assert (held.kind, held.edited) == ("copy", True)
    assert copied(edited) == copied(SERVICE)


# ── 3. layout ──────────────────────────────────────────────────────────────────────────────


def test_subjects_before_schema_and_the_comment_above_the_next_table_stay_put() -> None:
    first = SERVICE.replace(
        "[subjects.service]                  # a named body of requirements; a baseline freezes "
        'a subject\nkey = "SVC"                         # the key inside its item IDs\n',
        "",
    )
    reordered = first.replace("[schema]", '[subjects.service]\nkey = "SVC"\n\n[schema]', 1).replace(
        "[items.requirement]", "# what this repo declares\n[items.requirement]", 1
    )
    new = copied(reordered)
    assert new.index("[subjects.service]") < new.index("# qmstrace:begin")
    end = new.index("# qmstrace:end")
    assert end < new.index("# what this repo declares\n[items.requirement]")
    assert (
        not new[end:]
        .split("# what this repo declares")[0]
        .strip("\n")
        .replace("# qmstrace:end", "")
    )  # only blank lines between the copy and the comment that belongs to the next table
    assert TraceConfig.parse(new).subjects["service"].key == "SVC"


def test_crlf_line_endings_are_kept() -> None:
    crlf = SERVICE.replace("\n", "\r\n")
    new = copied(crlf)
    assert "\r\n" in new and "\n" not in new.replace("\r\n", "")


def test_a_bracket_inside_a_multi_line_string_is_never_a_header() -> None:
    tricky = SCHEMA.replace(
        'text  = "no test verifies it yet."',
        'text  = """no test verifies it yet.\n[not a header]\n# qmstrace:end\n"""',
        1,
    )
    assert tricky != SCHEMA
    new = copied(SERVICE, setup.schema_block(tricky, "MINI"))
    assert "\n[not a header]\n" in new and "[schema.not a header]" not in new
    assert TraceConfig.parse(new).rules[1].text.startswith("no test verifies it yet.\n[not a")
    assert copied(new, setup.schema_block(tricky, "MINI")) == new


def test_a_quoted_spaced_schema_header_is_found() -> None:
    quoted = SERVICE.replace("[schema]", '[ "schema" ]', 1)
    assert setup.held_schema(quoted).kind == "path"
    assert TraceConfig.parse(copied(quoted)).schema_form.value == "a generated, verified copy"


# ── 4. what is held, and what is refused ───────────────────────────────────────────────────


def test_what_a_configuration_holds_is_named() -> None:
    assert setup.held_schema(SERVICE).kind == "path"
    assert setup.held_schema(SERVICE).path == "../ledger/qmstrace.schema.toml"
    assert setup.held_schema(copied(SERVICE)).project == "MINI"
    solo = (MINI / "solo" / "qmstrace.toml").read_text(encoding="utf-8")
    assert setup.held_schema(solo).kind == "own"
    empty = SERVICE.replace('path = "../ledger/qmstrace.schema.toml"\n', "", 1)
    assert setup.held_schema(empty).kind == "empty"


@pytest.mark.parametrize(
    ("local", "said"),
    [
        (copied(SERVICE) + "# qmstrace:begin — again\n", "conflicting qmstrace markers"),
        (
            copied(SERVICE).replace("# qmstrace:end\n", "") + "# qmstrace:end\n[schema.extra]\n",
            "outside the generated block",
        ),
        (SERVICE + '\n[schema.links]\nX = { from = ["a"], to = ["b"] }\n', "split around"),
        (
            SERVICE.replace("[schema]", "", 1).replace(
                'path = "../ledger/qmstrace.schema.toml"', 'schema.path = "x.toml"', 1
            ),
            "outside its [schema] tables",
        ),
        (SERVICE.replace("[schema]", "[schemata]", 1), "has no [schema] table"),
        ("version = = 1", "is not valid TOML"),
    ],
    ids=["two-begins", "table-outside", "split", "root-keys", "none", "not-toml"],
)
def test_what_cannot_be_replaced_safely_is_refused(local: str, said: str) -> None:
    with pytest.raises(CouldNotJudge) as caught:
        setup.held_schema(local)
    assert said in caught.value.what
    assert caught.value.next_move.startswith("Fix:")


def test_rules_that_no_longer_fit_the_repo_are_refused_before_writing() -> None:
    narrower = SCHEMA.replace("[item_types.design_element]\n", "", 1)
    with pytest.raises(CouldNotJudge) as caught:
        copied(SERVICE, setup.schema_block(narrower, "MINI"))
    assert "design_element" in caught.value.what


def test_the_copy_parses_on_its_own() -> None:
    data = tomllib.loads(BLOCK)
    assert data["schema"]["project"] == "MINI"
