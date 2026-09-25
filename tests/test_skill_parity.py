"""Packaged examples are parsed, not just checked for matching words."""

import re
from importlib.resources import files

from qmstrace.core.findings import CODES
from qmstrace.extract.base import REGISTRY


def test_all_shipped_marker_examples_parse(service) -> None:
    skill = files("qmstrace").joinpath("assets/skill/SKILL.md").read_text()
    blocks = re.findall(r"```(markdown|python)\n(.*?)\n```", skill, re.S)
    assert len(blocks) == 4
    for (_, source), kind, path in zip(
        blocks,
        ["requirement", "design_element", "component", "test_case"],
        [
            "docs/req/service-srs.md",
            "docs/design/service.md",
            "src/service.py",
            "tests/unit/test_service.py",
        ],
        strict=True,
    ):
        spec = service.item_types[kind]
        extracted = REGISTRY[spec.extractor](path, source, spec, service)
        assert len(extracted.items) == 1 and not extracted.findings
        assert extracted.links
    for heading in re.findall(r"`(#{1,6} [^`]+)`", skill):  # inline heading examples
        spec = service.item_types["requirement"]
        found = REGISTRY["markdown"]("docs/req/service-srs.md", heading + "\n", spec, service)
        assert len(found.items) == 1 and not found.findings, heading
    assert "Break the relevant behavior" in skill and "Restore the source" in skill
    assert "qmstrace.core.findings.CODES" in skill
    assert all(CODES.values())
