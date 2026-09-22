"""Request metadata is an explicit preamble, not a search through approval-looking prose."""

import pytest

from qmstrace.extract.change_requests import read


@pytest.mark.parametrize(
    "text,valid",
    [
        ("# CR-001 — Edit\n- State: accepted\n- Impacts: REQ-SVC-01", True),
        ("- State: accepted\n- Impacts: src/a.py, tests/t.py::test_x", True),
        ("- Requested-by: Developer\n- State: accepted\n- Impacts: REQ-SVC-01", True),
        ("- State: accepted\n- Impacts: TBD", False),
        ("# CR-002 — Wrong identity\n- State: accepted\n- Impacts: REQ-SVC-01", False),
        ("- State: accepted\n- Impacts: REQ-SVC-01\n- State: rejected", False),
        ("- State: accepted\n- Impacts: ", False),
        ("- State: accepted\n- Impacts: REQ-SVC-01,", False),
        ("- State: accepted\n- Impacts: some prose", False),
        ("## Request\n- State: accepted\n- Impacts: REQ-SVC-01", False),
        ("```md\n- State: accepted\n- Impacts: REQ-SVC-01\n```", False),
        (
            "# Change\n- State: proposed\n- Impacts: REQ-SVC-01\n## Discussion\n- State: accepted",
            True,
        ),
    ],
)
def test_preamble(text, valid):
    value, problem = read("CR-001.md", "CR-001", text)
    assert (value is not None) == valid
    assert (problem is None) == valid
    if "State: proposed" in text:
        assert value.state == "proposed"
