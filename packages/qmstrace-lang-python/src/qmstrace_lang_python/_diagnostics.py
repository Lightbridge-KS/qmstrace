"""Python source diagnostics; the host owns their finding-code mapping.

Implements: DSN-QMT-04
"""

from collections.abc import Iterable

from qmstrace.plugin_api.v1 import Diagnostic as Finding
from qmstrace.plugin_api.v1 import Item


def no_level(item: Item, levels: Iterable[str]) -> Finding:
    return Finding(
        "missing-level",
        item.file,
        item.line,
        f"{item.id} has no test level: its file is not under a level folder.",
        f"Fix: move the file under tests/<{' | '.join(levels)}>/ — a level is information, "
        "not a rule, and it is read from where the test sits.",
        item.id,
    )


def cannot_parse(file: str, line: int, reason: str) -> Finding:
    return Finding(
        "parse",
        file,
        line,
        f"{file} cannot be parsed: {reason}.",
        "Fix: correct the file — nothing in it can be traced until it parses.",
    )


def not_an_id(
    item_id: str, marker: str, token: str, file: str, line: int, fix: str | None = None
) -> Finding:
    """V14. `fix` is the extractor's own next move where its marker is not a field line."""
    said = f"'{token}' is not an ID" if token else "the line names no ID"
    return Finding(
        "invalid-id",
        file,
        line,
        f"{item_id} → {marker}: {said}, so it links nothing.",
        fix
        or f"Fix: the '{marker}' line holds IDs only, comma-separated. If nothing real fits, "
        "remove the line and tell the developer what is missing — never invent an ID.",
        item_id,
        marker,
    )


def unread_marker(
    file: str,
    line: int,
    marker: str,
    form: str,
    fix: str | None = None,
    item: str | None = None,
) -> Finding:
    """A marker written in a form its extractor does not read; `fix` names the form it does —
    pytest's by default. `item` is the one item the marker was meant for, when it was meant for
    one; without it, the finding concerns every item of its file."""
    return Finding(
        "unread-marker",
        file,
        line,
        f"a '{marker}' marker {form} — this tool does not read that form, so it links nothing.",
        fix
        or (
            f'Fix: write @pytest.mark.{marker}("ID", …) with literal IDs, directly on a test '
            "function or on its test class."
        ),
        item=item,
        marker=marker,
    )
