"""The Python extractors — components from modules, test cases from pytest tests, from text.

The load-bearing claims, each pinned by a test:

1. A module is one component, its ID its path; it links only through its docstring — the same
   words in a comment are not a marker.
2. A test case is a test function, its ID the node ID without parameters: a parametrised
   function is one test case; a test class's marker is inherited by its tests.
3. A test's level comes from its folder; a test outside a level folder is V06.
4. A marker in a form the extractor does not read is reported (V15) — never silently no link.
5. A file that does not parse is V08, for a module as for a test.
6. A Python item's digest ignores layout and comments, and moves with the code.
"""

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.core.model import Extracted
from qmstrace.extract import pytest_tests, python_module


def module(config: TraceConfig, text: str, path: str = "src/service/keys.py") -> Extracted:
    return python_module.extract(path, text, config.item_types["component"], config)


def cases_in(config: TraceConfig, text: str, path: str = "tests/unit/test_keys.py") -> Extracted:
    return pytest_tests.extract(path, text, config.item_types["test_case"], config)


# ── 1. modules ─────────────────────────────────────────────────────────────────────────────

KEYS = '''\
"""Checks the key a call carries.

Implements: DSN-SVC-01
"""

# Implements: DSN-SVC-02  — a comment, not a marker


def check(key: str) -> bool:
    return bool(key)
'''


def test_a_module_is_a_component_that_links_through_its_docstring(service: TraceConfig) -> None:
    found = module(service, KEYS)
    (item,) = found.items
    assert (item.id, item.type, item.line, item.title) == (
        "src/service/keys.py",
        "component",
        1,
        "keys",
    )
    assert [(link.marker, link.dst, link.line) for link in found.links] == [
        ("Implements", "DSN-SVC-01", 3)
    ]
    assert found.findings == ()


def test_several_ids_and_a_bad_one_in_a_docstring(service: TraceConfig) -> None:
    found = module(service, '"""X.\n\nImplements: DSN-SVC-01, DSN-SVC-02, TBD\n"""\n')
    assert [link.dst for link in found.links] == ["DSN-SVC-01", "DSN-SVC-02"]
    (wrong,) = found.findings
    assert (wrong.code, wrong.line) == ("V14", 3)


def test_a_module_with_no_docstring_links_nothing(service: TraceConfig) -> None:
    found = module(service, "import os\n")
    assert len(found.items) == 1 and found.links == () and found.findings == ()


def test_an_empty_module_is_no_component(service: TraceConfig) -> None:
    assert module(service, "\n\n") == Extracted()


# ── 2. test cases ──────────────────────────────────────────────────────────────────────────

TESTS = """\
import pytest
from pytest import mark


@pytest.mark.verifies("REQ-SVC-01")
@pytest.mark.parametrize("key", ["", "wrong"])
def test_a_call_without_a_key_is_refused(key):
    assert key is not None


@pytest.mark.verifies("DSN-SVC-01")
class TestTheCheck:
    def test_an_empty_key_fails(self):
        assert True

    @mark.verifies("REQ-SVC-02", "DSN-SVC-02")
    def test_a_good_key_passes(self):
        assert True

    class TestNested:
        def test_deep(self):
            assert True


def helper():
    return 1
"""


def test_a_test_function_is_a_test_case_named_by_its_node_id(service: TraceConfig) -> None:
    found = cases_in(service, TESTS)
    assert [(item.id, item.line, item.level) for item in found.items] == [
        ("tests/unit/test_keys.py::test_a_call_without_a_key_is_refused", 7, "unit"),
        ("tests/unit/test_keys.py::TestTheCheck::test_an_empty_key_fails", 13, "unit"),
        ("tests/unit/test_keys.py::TestTheCheck::test_a_good_key_passes", 17, "unit"),
        ("tests/unit/test_keys.py::TestTheCheck::TestNested::test_deep", 21, "unit"),
    ]
    assert found.findings == ()


def test_a_class_marker_is_inherited_and_a_function_adds_its_own(service: TraceConfig) -> None:
    links = {(link.src.rsplit("::", 1)[-1], link.dst) for link in cases_in(service, TESTS).links}
    assert links == {
        ("test_a_call_without_a_key_is_refused", "REQ-SVC-01"),
        ("test_an_empty_key_fails", "DSN-SVC-01"),
        ("test_a_good_key_passes", "DSN-SVC-01"),
        ("test_a_good_key_passes", "REQ-SVC-02"),
        ("test_a_good_key_passes", "DSN-SVC-02"),
        ("test_deep", "DSN-SVC-01"),
    }


def test_a_link_is_placed_on_the_test_function(service: TraceConfig) -> None:
    link = next(link for link in cases_in(service, TESTS).links if link.dst == "REQ-SVC-01")
    assert (link.marker, link.file, link.line) == ("verifies", "tests/unit/test_keys.py", 7)


def test_a_test_function_defined_twice_is_two_items(service: TraceConfig) -> None:
    text = "def test_x():\n    pass\n\n\ndef test_x():\n    pass\n"
    ids = [item.id for item in cases_in(service, text).items]
    assert ids == ["tests/unit/test_keys.py::test_x"] * 2  # the graph reports V01


def test_a_literal_that_is_not_an_id_is_v14(service: TraceConfig) -> None:
    found = cases_in(service, '@pytest.mark.verifies("TBD")\ndef test_x():\n    pass\n')
    assert [finding.code for finding in found.findings] == ["V14"]


# ── 3. levels ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("path", "level"),
    [
        ("tests/integration/test_store.py", "integration"),
        ("tests/system/deep/test_flow.py", "system"),
    ],
)
def test_the_level_comes_from_the_folder(service: TraceConfig, path: str, level: str) -> None:
    (item,) = cases_in(service, "def test_x():\n    pass\n", path).items
    assert item.level == level


@pytest.mark.parametrize("path", ["tests/test_top.py", "tests/helpers/test_x.py"])
def test_a_test_outside_a_level_folder_is_v06(service: TraceConfig, path: str) -> None:
    found = cases_in(service, "def test_x():\n    pass\n", path)
    (finding,) = found.findings
    assert (finding.code, finding.item) == ("V06", f"{path}::test_x")
    assert "unit | integration | system" in finding.next_move


# ── 4. markers the extractor does not read ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("text", "form"),
    [
        ('pytestmark = pytest.mark.verifies("REQ-SVC-01")\n', "through pytestmark"),
        ('pytestmark = [pytest.mark.verifies("REQ-SVC-01")]\n', "through pytestmark"),
        (
            '@pytest.mark.parametrize("x", [pytest.param(1, marks=pytest.mark.verifies("A-1"))])\n'
            "def test_x(x):\n    pass\n",
            "inside pytest.param(marks=…)",
        ),
        ('IDS = ["REQ-SVC-01"]\n@pytest.mark.verifies(*IDS)\ndef test_x():\n    pass\n', "literal"),
        ("@pytest.mark.verifies(REQ)\ndef test_x():\n    pass\n", "not a literal string"),
        ('@pytest.mark.verifies(ids="A-1")\ndef test_x():\n    pass\n', "not a literal string"),
        ("@pytest.mark.verifies()\ndef test_x():\n    pass\n", "given no IDs"),
        ("@pytest.mark.verifies\ndef test_x():\n    pass\n", "bare decorator"),
        ('v = pytest.mark.verifies\n@v("A-1")\ndef test_x():\n    pass\n', "another name"),
        ('@pytest.mark.verifies("A-1")\ndef helper():\n    pass\n', "does not collect"),
        ('@pytest.mark.verifies("A-1")\nclass Checks:\n    pass\n', "does not collect"),
        ("@pytest.mark.verifies(1)\ndef test_x():\n    pass\n", "not a literal string"),
        (
            "class Helper:\n    class TestInner:\n"
            '        @pytest.mark.verifies("A-1")\n        def test_x(self):\n            pass\n',
            "does not collect",
        ),
    ],
)
def test_a_marker_in_a_form_that_is_not_read_is_v15(
    service: TraceConfig, text: str, form: str
) -> None:
    found = cases_in(service, "import pytest\n" + text)
    assert found.links == ()
    codes = [finding.code for finding in found.findings]
    assert codes == ["V15"], found.findings
    assert form in found.findings[0].what
    assert "@pytest.mark.verifies(" in found.findings[0].next_move


def test_other_marks_and_other_attributes_are_not_markers(service: TraceConfig) -> None:
    text = (
        "import pytest\n"
        "@pytest.mark.slow\n"
        "@pytest.mark.parametrize('a', [1])\n"
        "def test_x(a):\n"
        "    assert report.verifies is None\n"
    )
    found = cases_in(service, text)
    assert len(found.items) == 1 and found.findings == ()


# ── 5. files that do not parse ─────────────────────────────────────────────────────────────


def test_a_test_file_that_does_not_parse_is_v08(service: TraceConfig) -> None:
    (finding,) = cases_in(service, "def test_x(:\n").findings
    assert (finding.code, finding.file, finding.line) == ("V08", "tests/unit/test_keys.py", 1)


def test_a_module_that_does_not_parse_is_v08(service: TraceConfig) -> None:
    found = module(service, '"""Implements: DSN-SVC-01"""\ndef broken(:\n')
    assert found.items == ()
    assert [finding.code for finding in found.findings] == ["V08"]


# ── 6. digests ─────────────────────────────────────────────────────────────────────────────


def digests(found: Extracted) -> list[str]:
    return [item.digest for item in found.items]


def test_a_comment_or_layout_is_not_a_change(service: TraceConfig) -> None:
    edited = KEYS.replace("return bool(key)", "return bool(key)  # never empty").replace(
        "\n\n\ndef", "\n\ndef"
    )
    assert digests(module(service, KEYS)) == digests(module(service, edited))


def test_a_code_change_is_a_change(service: TraceConfig) -> None:
    edited = KEYS.replace("bool(key)", "key != ''")
    assert digests(module(service, KEYS)) != digests(module(service, edited))


def test_a_test_case_digest_covers_its_own_function_only(service: TraceConfig) -> None:
    before = digests(cases_in(service, TESTS))
    neighbour = digests(cases_in(service, TESTS.replace("return 1", "return 2")))
    own = digests(cases_in(service, TESTS.replace("assert key is not None", "assert key")))
    assert neighbour == before  # an edit beside a test is not a change to it
    assert own[0] != before[0] and own[1:] == before[1:]
