"""Agent-guide blocks and the paths used to install the authoring skill.

Implements: DSN-QMT-11
"""

from __future__ import annotations

from typing import Final

from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge

BEGIN = "<!-- qmstrace:begin"
END = "<!-- qmstrace:end -->"

# Where the packaged skill is installed: the folder harnesses read for a repo's skills, named
# after the skill. Claude Code reads its own folder, so it is linked there when the repo has one.
SKILL_FILE = ".agents/skills/qmstrace/SKILL.md"
CLAUDE_LINK = ".claude/skills/qmstrace"
CLAUDE_LINK_TARGET = "../../.agents/skills/qmstrace"  # relative to the link's folder
LEGACY_SKILL = ".qmstrace/skill/SKILL.md"  # the skill's home before M9c


# The three stanza lines that name commands depend on where the agent works: a product repo is
# judged by its own verbs; a ledger that holds the documents by the ledger's, because its own
# `check --strict` fails on what only the product repos can meet (M10c, ADR-0001).
_PRODUCT_LINES: Final = {
    "walks": "- Use `qmstrace thread ID` and `qmstrace impact ID…` before changing connected "
    "items.",
    "gate": "- Run `qmstrace check` while authoring; `qmstrace check --strict` is the coverage "
    "gate.",
    "suspects": "- Suspects need review even after edits or passing tests; `qmstrace check` lists "
    "every reason.",
}
_LEDGER_LINES: Final = {
    "walks": "- Use `qmstrace ledger thread ID` and `qmstrace ledger impact ID…` before "
    "changing connected items — they walk every repo of the project.",
    "gate": "- Run `qmstrace ledger check` while authoring; `qmstrace ledger check --strict` is "
    "the coverage gate. This repo's own `qmstrace check --strict` fails on what only the product "
    "repos can meet.",
    "suspects": "- Suspects need review even after edits or passing tests; `qmstrace ledger check` "
    "lists every reason, in every repo.",
}


def stanza(template: str, config: TraceConfig, *, ledger: bool = False) -> str:
    """The agent guide's generated block — a ledger that holds the documents names the ledger's
    verbs, a product repo its own."""
    return template.format(
        **(_LEDGER_LINES if ledger else _PRODUCT_LINES),
        skill=SKILL_FILE,
        project=config.project,
        subjects=", ".join(f"{s.name} ({s.key})" for s in config.subjects.values())
        or "none declared",
        items="; ".join(
            f"{t.name} `{t.id_pattern.pattern if t.id_pattern else t.extractor}` in "
            + ", ".join(f"`{p}`" for p in t.files)
            for t in config.item_types.values()
            if t.declared_here
        ),
    )


def guide(original: str, block: str) -> str:
    if BEGIN not in original and END not in original:
        return original + ("\n" if original.endswith("\n") else "\n\n" if original else "") + block
    if original.count(BEGIN) != 1 or original.count(END) != 1:
        raise CouldNotJudge(
            "The agent guide has conflicting qmstrace markers.",
            "Fix: keep exactly one begin/end pair, then run init again.",
        )
    start, end = original.index(BEGIN), original.index(END)
    if end < start:
        raise CouldNotJudge(
            "The agent guide closes its qmstrace block before it begins.",
            "Fix: repair the begin/end pair, then run init again.",
        )
    return original[:start] + block.rstrip("\n") + original[end + len(END) :]
