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
    assert "Break the relevant behavior in a disposable copy of the repo" in skill


def test_the_stanza_and_the_skill_break_a_copy_never_the_checkout() -> None:
    """Run A of E6: the stanza said "a disposable test", the skill "a disposable copy", and an
    agent broke the live checkout. Both now say the same, in the same words."""
    assets = files("qmstrace").joinpath("assets")
    skill = " ".join(assets.joinpath("skill/SKILL.md").read_text().split())
    stanza = assets.joinpath("stanza.md").read_text()
    for text in (skill, stanza):
        assert "a disposable copy of the repo — never the checkout you work in" in text
    assert "disposable test" not in stanza
    assert "qmstrace.core.findings.CODES" in skill
    assert all(CODES.values())
