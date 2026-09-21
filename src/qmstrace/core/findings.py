"""The findings catalogue — each code once: what is wrong, and the next move.

Every finding that reaches an agent ends with what to do, and where the wrong move is
tempting it says so. The wording lives here and nowhere else; the code that detects a problem
calls one of these functions. `CODES` is the index a meta-test holds against the scenarios
that emit each code.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from qmstrace.core.model import Finding, Item, Link

# A code's first letter is its kind, and says what it fails (data architecture § Kinds of finding).
KINDS: Final = {"V": "violation", "G": "gap", "S": "suspect"}

CODES: Final = {
    "V01": "an ID declared twice — in this repo, or already in a sibling",
    "V02": "an ID of this repo's kind that does not match its pattern",
    "V03": "a link to an ID that exists nowhere this run could read",
    "V04": "a link whose source or target is a kind of item the link type does not allow",
    "V05": "a required field missing, or a value outside its list",
    "V06": "a test with no level — not under a level folder",
    "V07": "an item declared in a file that is not scanned for its type",
    "V08": "a file that cannot be read or parsed",
    "V09": "an external ID its source does not declare",
    "V14": "a link field that holds something other than IDs",
    "V15": "a verifies marker in a form this tool does not read",
}


def _either(names: Iterable[str]) -> str:
    return " or ".join(names)


def declared_twice(item: Item, first: Item) -> Finding:
    return Finding(
        "V01",
        item.file,
        item.line,
        f"{item.id} is declared twice (first at {first.file}:{first.line}).",
        "Fix: an ID names exactly one item — give one of them another ID, or, for a module "
        "or a test function, another name.",
        item.id,
    )


def declared_in_sibling(token: str, sibling: str, file: str, line: int) -> Finding:
    return Finding(
        "V01",
        file,
        line,
        f"{token} is already declared in sibling repo '{sibling}'.",
        "Fix: do not declare it here — cite it by ID, exactly like a local item. A "
        "requirement has one home.",
        token,
    )


def malformed_id(token: str, item_type: str, pattern: str, file: str, line: int) -> Finding:
    return Finding(
        "V02",
        file,
        line,
        f"{token} does not match this repo's ID pattern for a {item_type} ({pattern}).",
        f"Fix: write the ID as [items.{item_type}] id_pattern says in qmstrace.toml — or, if "
        "this heading is prose, do not start it with an ID.",
        token,
    )


def no_such_item(link: Link, *, home: str | None, siblings_read: bool) -> Finding:
    where = "in this repo or its siblings" if siblings_read else "in this repo"
    hint = (
        f"declare it in {home}, or correct the ID"
        if home
        else "it may belong to another repo of the project — check the ID there, or correct it"
    )
    return Finding(
        "V03",
        link.file,
        link.line,
        f"{link.src} → {link.marker} → {link.dst}: no such item {where}.",
        f"Fix: {hint}.",
        link.src,
    )


def wrong_target(link: Link, target_type: str, allowed: Iterable[str]) -> Finding:
    return Finding(
        "V04",
        link.file,
        link.line,
        f"{link.src} → {link.marker} → {link.dst}: '{link.marker}' may point at "
        f"{_either(allowed)}, not at a {target_type}.",
        "Fix: point it at the right kind of item, or use the marker that fits — the trace "
        "schema's [links] lists them.",
        link.src,
    )


def wrong_carrier(link: Link, source_type: str, allowed: Iterable[str]) -> Finding:
    return Finding(
        "V04",
        link.file,
        link.line,
        f"{link.src} carries '{link.marker}', which a {source_type} may not carry — "
        f"'{link.marker}' is carried by {_either(allowed)}.",
        "Fix: move the line to the kind of item that carries it, or remove it.",
        link.src,
    )


def missing_field(item: Item, key: str, allowed: Iterable[str] = ()) -> Finding:
    values = tuple(allowed)
    hint = f" — one of: {', '.join(values)}" if values else ""
    return Finding(
        "V05",
        item.file,
        item.line,
        f"{item.id} has no '{key}:' line.",
        f"Fix: add '- {key}: …' under the heading{hint}.",
        item.id,
    )


def value_not_allowed(item: Item, key: str, value: str, allowed: Iterable[str]) -> Finding:
    return Finding(
        "V05",
        item.file,
        item.line,
        f"{item.id} has {key}: '{value}', which is not an allowed value.",
        f"Fix: use one of {', '.join(allowed)} — spelled exactly so.",
        item.id,
    )


def no_level(item: Item, levels: Iterable[str]) -> Finding:
    return Finding(
        "V06",
        item.file,
        item.line,
        f"{item.id} has no test level: its file is not under a level folder.",
        f"Fix: move the file under tests/<{' | '.join(levels)}>/ — a level is information, "
        "not a rule, and it is read from where the test sits.",
        item.id,
    )


def not_scanned_here(
    token: str, item_type: str, files: Iterable[str], file: str, line: int
) -> Finding:
    return Finding(
        "V07",
        file,
        line,
        f"{token} is declared here, but this file is not scanned for a {item_type} — so the "
        "tool cannot see it.",
        f"Fix: a {item_type} is read from {', '.join(files)}; move it there.",
        token,
    )


def cannot_parse(file: str, line: int, reason: str) -> Finding:
    return Finding(
        "V08",
        file,
        line,
        f"{file} cannot be parsed: {reason}.",
        "Fix: correct the file — nothing in it can be traced until it parses.",
    )


def cannot_read(file: str) -> Finding:
    return Finding(
        "V08",
        file,
        1,
        f"{file} cannot be read as UTF-8 text.",
        "Fix: save it as UTF-8 — nothing in it can be traced until then.",
    )


def undeclared_external(link: Link, source: str, declared: Iterable[str]) -> Finding:
    listing = ", ".join(declared) or "nothing"
    return Finding(
        "V09",
        link.file,
        link.line,
        f"{link.src} → {link.marker} → {link.dst}: the {source} declares no {link.dst} (it "
        f"declares {listing}).",
        "Fix: cite a real one, or tell the developer that nothing covers this — never invent one.",
        link.src,
    )


def not_an_id(item_id: str, marker: str, token: str, file: str, line: int) -> Finding:
    said = f"'{token}' is not an ID" if token else "the line names no ID"
    return Finding(
        "V14",
        file,
        line,
        f"{item_id} → {marker}: {said}, so it links nothing.",
        f"Fix: a '{marker}' line holds IDs only, comma-separated. If nothing real fits, remove "
        "the line and tell the developer what is missing — never invent an ID.",
        item_id,
    )


def unread_marker(file: str, line: int, marker: str, form: str) -> Finding:
    return Finding(
        "V15",
        file,
        line,
        f"a '{marker}' marker {form} — this tool does not read that form, so it links nothing.",
        f'Fix: write @pytest.mark.{marker}("ID", …) with literal IDs, directly on a test '
        "function or on its test class.",
    )
